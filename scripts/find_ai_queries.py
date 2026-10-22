#!/usr/bin/env python3
"""
find_ai_queries.py - Step 3 of the ai-queries-finder skill.

Reads the queries pulled from Google Search Console (GSC) with the AI-query regexes and works out:

  A) Which queries look like AI prompts - tagged with every regex family they match and an
     AI-likelihood score (0-100) built from the family weights in references/regex-library.json.
  B) Intent (informational / commercial / transactional / local / brand) and a topic cluster per query.
  C) Where each query stands - position bucket, "AI Overview likely taking the click" flag,
     recommended action type and a click estimate if the action works.
  D) Cluster totals and a priority order, so the strategy is written per topic, not per query.

Accepted inputs (one or more files, mix freely):
  * GSC web-UI export (.zip, or .xlsx with Queries / Pages / Filters tabs)
  * CSV / TSV / XLSX with columns like query, clicks, impressions, ctr, position (page optional)
  * The same query in several files (e.g. one export per regex family) is kept once, not summed.

Usage:
  python find_ai_queries.py INPUT [INPUT ...] -o work/ai-queries.json
         [--brand "acme,acme co"] [--locations "gold coast,brisbane"]
         [--total-clicks 1234 --total-impressions 98765] [--date-range "Last 3 months (...)"]
         [--min-score 30] [--min-impr 1]
  python find_ai_queries.py --print-regex      # print every family regex + the master regex
  python find_ai_queries.py --check-regex      # check every regex is GSC (RE2) safe and <= 4096 chars
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

LIBRARY = Path(__file__).resolve().parent.parent / "references" / "regex-library.json"
GSC_REGEX_LIMIT = 4096

# Expected organic CTR by position - same conservative curve as website-clicks-improver.
CTR_CURVE = {
    1: 0.25, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.055, 6: 0.040, 7: 0.032, 8: 0.026,
    9: 0.022, 10: 0.019, 11: 0.012, 12: 0.011, 13: 0.010, 14: 0.009, 15: 0.008,
    20: 0.006, 25: 0.004, 30: 0.003, 50: 0.002, 100: 0.001,
}

COLUMN_ALIASES = {
    "page": {"page", "pages", "top pages", "landing page", "url", "page url", "address"},
    "query": {"query", "queries", "top queries", "search query", "keyword", "keywords", "search term"},
    "clicks": {"clicks", "url clicks", "click"},
    "impressions": {"impressions", "impr", "impression", "url impressions"},
    "ctr": {"ctr", "url ctr", "site ctr", "click through rate", "clickthrough rate"},
    "position": {"position", "average position", "avg position", "avg pos", "avg. position", "pos", "rank"},
}

INTENT_RULES = [
    ("Transactional", r"\b(buy|price|prices|pricing|cost|costs|quote|quotes|hire|book|booking|order|cheap|for sale|"
                      r"near me|deal|deals|discount|install|installer|installers|contractor|contractors|company|companies)\b"),
    ("Commercial", r"\b(best|top|vs|versus|review|reviews|compare|comparison|alternative|alternatives|worth|"
                   r"recommend|recommended|better|pros and cons|rated)\b"),
]

STOPWORDS = set("""
a an the and or but if then than to of in on at by for from with without into onto over under about as is are was were
be been being am do does did done doing have has had having can could should would will shall may might must
i im i'm ive i've my me we our ours us you your yours he she it its they them their this that these those there here
what whats what's when where why how which who whom whose
give show tell help explain list compare recommend suggest find create write generate make summarise summarize
describe plan calculate teach guide walk act pretend please need want looking look like get got go going
best top good better great most more less much many very really just also any some all every each other another
vs versus difference between pros cons way ways thing things something anything one two three new old
step steps beginner beginners example examples tips tip idea ideas guide guides 2024 2025 2026 2027 own
chatgpt chat gpt openai gemini claude perplexity copilot ai llm https http www com
worth safe possible legal true normal ok okay long often near
""".split())


# --------------------------------------------------------------------------------------
# Regex library
# --------------------------------------------------------------------------------------
def load_library(path: Path = LIBRARY) -> dict:
    lib = json.loads(path.read_text(encoding="utf-8"))
    for f in lib["families"]:
        f["compiled"] = re.compile(f["regex"])
    return lib


def strip_flags(rx: str) -> str:
    return rx[4:] if rx.startswith("(?i)") else rx


def master_regex(lib: dict) -> str:
    """OR of every in_master family - the one regex to paste into GSC first."""
    parts = [strip_flags(f["regex"]) for f in lib["families"] if f.get("in_master")]
    return "(?i)" + "|".join(parts)


RE2_UNSUPPORTED = [(r"\(\?[=!]", "lookahead"), (r"\(\?<[=!]", "lookbehind"), (r"\\[1-9]", "backreference"),
                   (r"\(\?>", "atomic group"), (r"[*+?}]\+", "possessive quantifier")]


def check_regex(rx: str) -> list[str]:
    problems = []
    if len(rx) > GSC_REGEX_LIMIT:
        problems.append(f"{len(rx)} chars (GSC limit is {GSC_REGEX_LIMIT})")
    for pat, what in RE2_UNSUPPORTED:
        if re.search(pat, rx):
            problems.append(f"uses a {what} (not supported by RE2 / GSC)")
    try:
        re.compile(rx)
    except re.error as e:
        problems.append(f"does not compile: {e}")
    return problems


# --------------------------------------------------------------------------------------
# Reading GSC exports
# --------------------------------------------------------------------------------------
def norm_header(h: str) -> str:
    h = str(h).strip().lower().replace("﻿", "")
    h = re.sub(r"[^a-z0-9 ]+", " ", h)
    return re.sub(r"\s+", " ", h).strip()


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        n = norm_header(col)
        for target, aliases in COLUMN_ALIASES.items():
            if n in {norm_header(a) for a in aliases} and target not in rename.values():
                rename[col] = target
                break
    return df.rename(columns=rename)


EURO_DECIMAL = re.compile(r"^-?\d+,\d{1,2}%?$")
EURO_THOUSANDS = re.compile(r"^\d{1,3}(\.\d{3})+(,\d+)?$")


def is_european(df: pd.DataFrame) -> bool:
    for c in ("clicks", "impressions", "position", "ctr"):
        if c in df.columns:
            vals = df[c].astype(str).str.strip().head(500)
            if vals.str.match(EURO_DECIMAL).any():
                return True
            if c in ("clicks", "impressions") and vals.str.match(EURO_THOUSANDS).any():
                return True
    return False


def to_number(s: pd.Series, european: bool = False) -> pd.Series:
    s = s.astype(str).str.replace("%", "", regex=False).str.strip()
    if european:
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        s = s.str.replace(",", "", regex=False)
    s = s.replace({"": None, "nan": None, "None": None, "-": None})
    return pd.to_numeric(s, errors="coerce")


def read_csv_bytes(data: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc, sep=None, engine="python", dtype=str,
                               keep_default_na=False)
        except Exception:
            continue
    raise ValueError("could not parse CSV")


def clean(df: pd.DataFrame, source: str, warnings: list) -> pd.DataFrame | None:
    df = map_columns(df)
    if "query" not in df.columns:
        return None  # Pages / Countries / Devices tab etc.
    missing = [c for c in ("clicks", "impressions") if c not in df.columns]
    if missing:
        raise SystemExit(f"{source}: missing column(s) {', '.join(missing)}. Found: {', '.join(map(str, df.columns))}")
    euro = is_european(df)
    if euro:
        warnings.append(f"{source}: decimal-comma number format (e.g. 4,2) detected and converted.")
    for c in ("clicks", "impressions", "position"):
        if c in df.columns:
            df[c] = to_number(df[c], euro)
    if "position" not in df.columns:
        warnings.append(f"{source}: no Position column - turn on 'Average position' in GSC before exporting. "
                        "Buckets and click estimates need it.")
        df["position"] = float("nan")
    df["clicks"] = df["clicks"].fillna(0)
    df = df[df["impressions"].fillna(0) > 0].copy()
    df["query"] = df["query"].astype(str).str.strip()
    df = df[(df["query"] != "") & (df["query"].str.lower() != "nan")]
    keys = ["page", "query"] if "page" in df.columns else ["query"]
    if "page" in df.columns:
        df["page"] = df["page"].astype(str).str.strip()
    if df.duplicated(subset=keys).any():  # one row per date / device / country -> sum
        warnings.append(f"{source}: duplicate {' + '.join(keys)} rows were summed.")
        df = (df.assign(_w=df["position"] * df["impressions"])
              .groupby(keys, as_index=False)
              .agg(clicks=("clicks", "sum"), impressions=("impressions", "sum"), _w=("_w", "sum")))
        df["position"] = df["_w"] / df["impressions"]
        df = df.drop(columns="_w")
    return df[keys + ["clicks", "impressions", "position"]].assign(_source=source)


def date_from_filters(df: pd.DataFrame) -> str | None:
    cols = {norm_header(c): c for c in df.columns}
    f, v = cols.get("filter") or cols.get("filters"), cols.get("value")
    if not f or not v:
        return None
    for _, row in df.iterrows():
        if str(row[f]).strip().lower().startswith("date"):
            return str(row[v]).strip()
    return None


def read_input(path: Path, warnings: list, dates: set) -> list[pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    suffix = path.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.lower().endswith(".csv"):
                    tables[Path(n).stem] = read_csv_bytes(z.read(n))
    elif suffix in (".xlsx", ".xls"):
        for name, df in pd.read_excel(path, sheet_name=None, dtype=str, keep_default_na=False).items():
            tables[name] = df
    else:
        tables[path.stem] = read_csv_bytes(path.read_bytes())
    out = []
    for name, df in tables.items():
        if {"filter", "value"} <= {norm_header(c) for c in df.columns}:
            d = date_from_filters(df)
            if d:
                dates.add(d)
            continue
        c = clean(df, f"{path.name} [{name}]", warnings)
        if c is not None and len(c):
            out.append(c)
    return out


# --------------------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------------------
def expected_ctr(pos: float) -> float:
    if pos != pos:  # NaN
        return 0.0
    keys = sorted(CTR_CURVE)
    p = max(1.0, float(pos))
    if p >= keys[-1]:
        return CTR_CURVE[keys[-1]]
    for lo, hi in zip(keys, keys[1:]):
        if lo <= p <= hi:
            t = (p - lo) / (hi - lo)
            return CTR_CURVE[lo] + t * (CTR_CURVE[hi] - CTR_CURVE[lo])
    return CTR_CURVE[1]


# Question types that exist in every niche. Their words are folded into one concept token so
# "how much", "price" and "expensive" land in the same topic.
CONCEPTS = {
    "cost": r"\b(how much|cost|costs|price|prices|pricing|priced|expensive|cheap|cheaper|cheapest|pay|afford|"
            r"affordable|budget|quote|quotes|rates?)\b",
    "time": r"\b(how long|how soon|how quickly|take to|cure|curing|dry|drying|last|lasts|lifespan|years)\b",
    "care": r"\b(clean|cleaning|cleaner|maintain|maintenance|care|wash|remove|stain|stains|marks)\b",
    "problems": r"\b(peel|peeling|bubble|bubbles|crack|cracks|cracked|wrong|fix|repair|problem|problems|fail|failing)\b",
    "safety": r"\b(safe|safety|toxic|slippery|slip|standards?|compliant|compliance|regulations?)\b",
    "diy": r"\b(diy|myself|yourself|by hand|hire a professional|professional)\b",
    "choose": r"\b(worth|best|better|vs|versus|difference|compare|comparison|alternatives?|recommend|recommended|"
              r"choose|choosing|options|which)\b",
}
# [choose] is broad, so a specific word shared by 3+ queries wins over it (e.g. "flake" for flake-vs-metallic)
BROAD_CONCEPTS = {"[choose]"}
CONCEPT_RX = {k: re.compile(v) for k, v in CONCEPTS.items()}
CORE_SHARE = 0.35  # words in more than 35% of AI-style queries are the site's core topic, not a cluster


def stem(w: str) -> str:
    if len(w) > 6 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("ses", "xes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def content_tokens(q: str, brand: list[str], locations: list[str]) -> list[str]:
    text = q.lower()
    for b in brand + locations:
        text = text.replace(b, " ")
    concepts = []
    for name, rx in CONCEPT_RX.items():
        if rx.search(text):
            concepts.append(f"[{name}]")
            text = rx.sub(" ", text)
    words = re.findall(r"[a-z0-9][a-z0-9'-]*", text)
    return concepts + [stem(w) for w in words if w not in STOPWORDS and len(w) > 2 and not w.isdigit()]


def intent_of(q: str, is_brand: bool, locations: list[str]) -> str:
    ql = q.lower()
    if is_brand:
        return "Brand"
    if "near me" in ql or any(loc in ql for loc in locations):
        return "Local"
    for name, rx in INTENT_RULES:
        if re.search(rx, ql):
            return name
    return "Informational"


def bucket_and_action(pos: float, ctr: float) -> tuple[str, str, int, bool]:
    """Returns (bucket, action type, target position, AI-Overview-likely flag)."""
    if pos != pos:
        return "Unknown", "Check position in GSC", 5, False
    exp = expected_ctr(pos)
    aio = pos <= 5 and exp > 0 and ctr < 0.4 * exp
    if pos <= 3:
        return ("Top 3", "Win the AI citation (answer is likely summarised)" if aio else "Defend & get cited", 1, aio)
    if pos <= 10:
        return ("4-10", "Win the AI citation (answer is likely summarised)" if aio else "Answer upgrade", 3, aio)
    if pos <= 20:
        return "11-20", "Striking distance: expand + internal links", 5, False
    return "21+", "Content gap: new section or page", 8, False


def classify(df: pd.DataFrame, lib: dict, brand: list[str], locations: list[str], min_score: int) -> list[dict]:
    tiers = sorted(lib["tiers"].items(), key=lambda kv: -kv[1])
    rows = []
    for r in df.itertuples(index=False):
        q = r.query
        fams = [f for f in lib["families"] if f["compiled"].search(q)]
        score = min(100, sum(f["weight"] for f in fams))
        tier = next(name for name, cut in tiers if score >= cut)
        is_brand = any(b in q.lower() for b in brand)
        ctr = r.clicks / r.impressions if r.impressions else 0.0
        bucket, action, target, aio = bucket_and_action(r.position, ctr)
        rows.append({
            "query": q,
            "page": getattr(r, "page", "") or "",
            "words": len(q.split()),
            "families": [f["id"] for f in fams],
            "score": score,
            "tier": tier,
            "ai_style": score >= min_score,
            "intent": intent_of(q, is_brand, locations),
            "brand": is_brand,
            "clicks": int(r.clicks),
            "impressions": int(r.impressions),
            "ctr": round(ctr, 4),
            "position": None if r.position != r.position else round(float(r.position), 1),
            "bucket": bucket,
            "aio_likely": aio,
            "action_type": action,
            "target_position": target,
            "target_ctr": round(expected_ctr(target), 4),
            "_tokens": content_tokens(q, brand, locations),
        })
    return rows


def pick_head(tokens: list[str], df: Counter, core: set[str]) -> str:
    """Order: question-type concept ([cost], [time]...) > specific word shared by 3+ queries > [choose] >
    specific word shared by 2+ > core word > (misc)."""
    toks = set(tokens)

    def best(cands, key):
        cands = sorted(cands, key=key)
        return cands[0] if cands else None

    words = [t for t in toks if t not in core and not t.startswith("[")]
    steps = [
        lambda: best((t for t in toks if t.startswith("[") and t not in BROAD_CONCEPTS and df[t] >= 2),
                     lambda t: (-df[t], t)),
        lambda: best((t for t in words if df[t] >= 3), lambda t: (df[t], t)),
        lambda: best((t for t in toks if t in BROAD_CONCEPTS and df[t] >= 2), lambda t: t),
        lambda: best((t for t in words if df[t] >= 2), lambda t: (df[t], t)),
        lambda: best(toks & core, lambda t: (-df[t], t)),
    ]
    for step in steps:
        head = step()
        if head:
            return head
    return "(misc)"


def cluster(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Topic clustering, deterministic and explainable: words used across most of the site's AI-style
    queries (the core topic, e.g. 'epoxy') are background; each query joins the topic of its question
    type ([cost], [time]...) or its most specific shared word. Returns (clusters, core words)."""
    ai = [r for r in rows if r["ai_style"] and not r["brand"]]
    df = Counter(t for r in ai for t in set(r["_tokens"]))
    core = {t for t, n in df.items() if len(ai) >= 10 and n / len(ai) > CORE_SHARE and not t.startswith("[")}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in ai:
        r["_head"] = pick_head(r["_tokens"], df, core)
        groups[r["_head"]].append(r)
    for head in [h for h, m in groups.items() if len(m) < 2 and h != "(misc)"]:  # one-query topics -> Other
        for r in groups.pop(head):
            r["_head"] = "(misc)"
            groups["(misc)"].append(r)
    clusters = []
    for head, members in groups.items():
        impr = sum(m["impressions"] for m in members)
        clicks = sum(m["clicks"] for m in members)
        posw = sum((m["position"] or 0) * m["impressions"] for m in members)
        co = Counter(t for m in members for t in set(m["_tokens"]) if t != head and t not in core and not t.startswith("["))
        second = [t for t, n in co.most_common(2) if n >= 2]
        gain = sum(max(0.0, m["impressions"] * m["target_ctr"] - m["clicks"]) for m in members)
        clusters.append({
            "head": head,
            "label": label_for(head, second) if head not in core else f"General {head} questions",
            "queries": len(members),
            "clicks": clicks,
            "impressions": impr,
            "ctr": round(clicks / impr, 4) if impr else 0,
            "position": round(posw / impr, 1) if impr else None,
            "est_extra_clicks": round(gain),
            "avg_score": round(sum(m["score"] for m in members) / len(members)),
            "intents": dict(Counter(m["intent"] for m in members).most_common()),
            "buckets": dict(Counter(m["bucket"] for m in members).most_common()),
            "aio_likely": sum(1 for m in members if m["aio_likely"]),
            "pages": [p for p, _ in Counter(m["page"] for m in members if m["page"]).most_common(3)],
            "top_queries": [m["query"] for m in sorted(members, key=lambda m: -m["impressions"])[:8]],
        })
    # Priority: impressions weighted by AI-likelihood, plus the click gain. "(misc)" always last.
    clusters.sort(key=lambda c: (c["head"] == "(misc)", -(c["impressions"] * c["avg_score"] / 100 + 20 * c["est_extra_clicks"])))
    for i, c in enumerate(clusters, 1):
        c["id"] = f"T{i}"
        c["priority"] = "High" if i <= 3 and c["head"] != "(misc)" else ("Medium" if i <= 8 else "Low")
    by_head = {c["head"]: c["id"] for c in clusters}
    for r in ai:
        r["cluster"] = by_head[r.pop("_head")]
    return clusters, sorted(core)


CONCEPT_LABELS = {"[cost]": "Cost & price", "[time]": "How long / timing", "[care]": "Cleaning & care",
                  "[problems]": "Problems & fixes", "[safety]": "Safety & standards", "[diy]": "DIY vs professional",
                  "[choose]": "Choosing & comparing"}


def label_for(head: str, second: list[str]) -> str:
    if head == "(misc)":
        return "Other AI-style queries"
    base = CONCEPT_LABELS.get(head, head.capitalize())
    return f"{base}: {', '.join(second)}" if second else base


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--brand", default="", help="comma-separated brand terms")
    ap.add_argument("--locations", default="", help="comma-separated service areas / cities (local intent)")
    ap.add_argument("--total-clicks", type=float, help="site total clicks for the same period (no filter)")
    ap.add_argument("--total-impressions", type=float, help="site total impressions for the same period")
    ap.add_argument("--date-range", default="")
    ap.add_argument("--site", default="")
    ap.add_argument("--min-score", type=int, default=30, help="AI-likelihood score that counts as AI-style (default 30)")
    ap.add_argument("--min-impr", type=int, default=1, help="ignore queries below this many impressions")
    ap.add_argument("--library", type=Path, default=LIBRARY)
    ap.add_argument("--print-regex", action="store_true")
    ap.add_argument("--check-regex", action="store_true")
    args = ap.parse_args()

    lib = load_library(args.library)
    master = master_regex(lib)

    if args.print_regex or args.check_regex:
        bad = 0
        for f in lib["families"] + [{"id": "MASTER", "name": "Master (paste this first)", "regex": master}]:
            problems = check_regex(f["regex"]) if args.check_regex else []
            bad += bool(problems)
            print(f"{f['id']:<7} {f['name']}  [{len(f['regex'])} chars]{'  PROBLEM: ' + '; '.join(problems) if problems else ''}")
            if args.print_regex:
                print(f"        {f['regex']}\n")
        if args.check_regex:
            print("RESULT:", "FAIL" if bad else "PASS")
            sys.exit(1 if bad else 0)
        return

    if not args.inputs or not args.out:
        ap.error("give at least one input file and -o")

    warnings: list[str] = []
    dates: set[str] = set()
    frames = []
    for p in args.inputs:
        if not p.exists():
            sys.exit(f"Not found: {p}")
        frames += read_input(p, warnings, dates)
    if not frames:
        sys.exit("No query data found. Export the Queries tab from GSC (see references/gsc-browser-workflow.md).")
    data = pd.concat(frames, ignore_index=True)
    keys = ["page", "query"] if "page" in data.columns and data["page"].notna().all() else ["query"]
    if "page" in data.columns and keys == ["query"]:
        warnings.append("Some files have a Page column and some don't - pages were dropped; queries kept once.")
    before = len(data)
    # The same query in several exports (one per regex family) is the same data - keep it once, never sum.
    data = data.sort_values("impressions", ascending=False).drop_duplicates(subset=keys)
    if len(data) < before and len(args.inputs) > 1:
        warnings.append(f"{before - len(data)} rows appeared in more than one export and were kept once.")
    data = data[data["impressions"] >= args.min_impr]

    brand = [b.strip().lower() for b in args.brand.split(",") if b.strip()]
    locations = [loc.strip().lower() for loc in args.locations.split(",") if loc.strip()]
    rows = classify(data, lib, brand, locations, args.min_score)
    clusters, core = cluster(rows)
    for r in rows:
        r.pop("_tokens", None)
        r.setdefault("cluster", "")
    rows.sort(key=lambda r: (not r["ai_style"], -r["impressions"]))

    ai_rows = [r for r in rows if r["ai_style"]]
    fam_stats = []
    for f in lib["families"]:
        m = [r for r in ai_rows if f["id"] in r["families"]]
        fam_stats.append({"id": f["id"], "name": f["name"], "regex": f["regex"], "weight": f["weight"],
                          "catches": f["catches"], "in_master": f.get("in_master", False),
                          "queries": len(m), "clicks": sum(r["clicks"] for r in m),
                          "impressions": sum(r["impressions"] for r in m)})
    if len(rows) >= 999 and len(args.inputs) == 1:
        warnings.append("About 1,000 rows: the GSC interface caps tables at 1,000 rows. Export each regex family "
                        "separately (or use the API / Search Analytics for Sheets) to see the rest.")

    out = {
        "settings": {"site": args.site, "brand": brand, "locations": locations, "min_score": args.min_score,
                     "min_impr": args.min_impr, "core_terms": core},
        "date_range": args.date_range or "; ".join(sorted(dates)),
        "master_regex": master,
        "totals": {
            "site_clicks": args.total_clicks, "site_impressions": args.total_impressions,
            "rows_read": len(rows), "ai_queries": len(ai_rows),
            "ai_clicks": sum(r["clicks"] for r in ai_rows),
            "ai_impressions": sum(r["impressions"] for r in ai_rows),
            "aio_likely": sum(1 for r in ai_rows if r["aio_likely"]),
            "est_extra_clicks": round(sum(c["est_extra_clicks"] for c in clusters)),
        },
        "families": fam_stats,
        "clusters": clusters,
        "queries": rows,
        "warnings": warnings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    t = out["totals"]
    print(f"Read {t['rows_read']} queries -> {t['ai_queries']} AI-style (score >= {args.min_score}), "
          f"{t['ai_impressions']:,} impressions, {t['ai_clicks']:,} clicks")
    print(f"{len(clusters)} topic clusters; {t['aio_likely']} queries where an AI answer likely takes the click; "
          f"~{t['est_extra_clicks']:,} extra clicks available")
    for c in clusters[:10]:
        print(f"  {c['id']:<4} {c['priority']:<6} {c['label'][:40]:<40} {c['queries']:>4} q  {c['impressions']:>7,} impr  pos {c['position']}")
    for w in warnings:
        print("WARN:", w)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
