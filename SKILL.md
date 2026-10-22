---
name: ai-queries-finder
description: Finds the AI-style queries hidden in Google Search Console (long conversational prompts, questions, "help me / compare / explain" requests, queries naming ChatGPT or Gemini, leaked prompts) and turns them into a strategy to win AI visibility faster. Opens GSC in the browser, sets the last 3 months, applies a library of tested regex filters, pulls the matching queries, clusters them by topic and builds an Excel working sheet with an optimisation plan per topic plus a 7/30/90-day AI visibility plan. Use whenever someone asks to find AI queries, ChatGPT / AI Mode / AI Overview / LLM queries, prompt-style or conversational queries in Search Console, wants GSC regex filters for AI queries, or asks how to improve AI visibility, AEO, GEO or AI citations from their GSC data.
---

# AI Queries Finder

One job: **find the queries in Search Console that look like AI prompts, and say exactly how to win them.**

| Step | What happens | Tool |
|---|---|---|
| 1-2 | Open GSC in the browser, last 3 months, all four metrics on, read site totals | Browser |
| 3 | Apply the master regex (then single families if needed) and pull every matching query + page | Browser |
| 4 | Score, tag, cluster and prioritise the queries | `find_ai_queries.py` |
| 5 | Check who AI already cites for the top topics | Web search / browser |
| 6 | Write the optimisation plan per topic + the AI visibility plan | You, using `references/ai-visibility-playbook.md` |
| 7-8 | Build and verify the Excel working sheet | `build_report.py` · `verify_workbook.py` |

Scripts live in this skill's `scripts/` folder (Python 3.9+, `pandas openpyxl`; install them if missing). The skill
folder may be read-only, so **work from a writable folder** and call scripts by full path:

```bash
SKILL_DIR=/path/to/ai-queries-finder   # the folder this SKILL.md is in
mkdir -p work outputs
```

Use `python3` (or `python` if that's what the environment has).

---

## Step 0 - Before you open the browser

Ask for (don't block on it - use defaults and `[placeholders]`):
- the **GSC property** (domain property `sc-domain:example.com` or URL-prefix property)
- **brand name(s)** - brand queries are kept out of the clusters
- **service areas / cities** (for local intent), language variant to write in (default: match the site)

Browser rules - these are not optional:
- Use whatever browser tool you have (Claude in Chrome, the built-in browser, computer use). If none, go to
  **Fallback: no browser** at the bottom.
- The user must already be **signed in to Google**. If you hit a sign-in page, stop and ask them to sign in
  themselves. Never type a password, never change GSC settings, users or permissions. This skill only reads.
- Downloading the export is a file download: **ask the user before clicking Download**. If they say no, read
  the table from the page instead (Step 3b).

## Step 1 - Open the Performance report

Go to `https://search.google.com/search-console`, pick the property, then **Performance > Search results**
(full click path and screenshots of what to look for: `references/gsc-browser-workflow.md`).

1. **Search type: Web** (the default).
2. **Date: Last 3 months**. Write the exact dates shown into `--date-range` later.
3. Click all four metric cards so **Total clicks, Total impressions, Average CTR and Average position** are all
   on. The table only shows the columns whose cards are on, and position is needed for the plan.

## Step 2 - Read the site totals

With **no query filter**, note Total clicks and Total impressions. They become `--total-clicks` /
`--total-impressions` so the report can show what share of the site's search the AI-style queries are.

## Step 3 - Apply the regex filters and pull the queries

Get the regexes (never retype them from memory):

```bash
python3 "$SKILL_DIR"/scripts/find_ai_queries.py --print-regex
```

**3a. Master regex first.** `+ Add filter` (or `+ New`) > **Query** > change the dropdown to **Custom (regex)** >
**Matches regex** > paste the MASTER regex > Apply. Note the filtered totals. Then on the **Queries** tab:
- **Export** > **Download CSV** (ask the user first) - saves a zip with `Queries.csv`, `Pages.csv`, `Filters.csv`.
  Keep it as `work/gsc-master.zip`.
- Or **3b. read the table**: set Rows per page to the maximum, read every page of the table and save
  `work/gsc-master-queries.csv` with header `query,clicks,impressions,ctr,position`. Check the row count
  against the "1-500 of N" counter so nothing is missed.

**3c. Hit the 1,000-row cap?** The GSC interface shows at most 1,000 rows per table. If the master filter
returns ~1,000, run each family regex (R01-R10) as its own filter and export each one
(`work/gsc-R01.zip`...). Duplicates across exports are handled by the script (kept once, never summed).
Families R06-R08 are not in the master: run them separately when the user wants comparison, best-of or
constraint queries in their own right.

**3d. Pages.** With the master filter still on, open the **Pages** tab and keep that table too (it's in the zip, or
read it to `work/gsc-master-pages.csv`). These are the pages AI-style searches already land on.

Regex tips: GSC uses RE2 (no lookaheads, max 4,096 characters). If GSC rejects a regex, run
`find_ai_queries.py --check-regex` and tell the user which one failed.

## Step 4 - Analyse

```bash
python3 "$SKILL_DIR"/scripts/find_ai_queries.py work/gsc-*.zip work/*.csv -o work/ai-queries.json \
  --brand "acme,acme flooring" --locations "gold coast,brisbane" \
  --total-clicks 4210 --total-impressions 388000 --date-range "Last 3 months (23 Jul - 21 Oct 2026)" \
  --site https://example.com
```

What it gives you, per query: matched families, AI-likelihood score (0-100, tiers High >= 50, Medium >= 30),
intent, topic cluster, position bucket, **AI-Overview-likely flag** (position <= 5 but CTR under 40% of what that
position should earn - the answer is probably being summarised above the results), action type and a click
estimate. Per cluster (`T1`, `T2`...): totals, priority, top queries, pages.

Tune it: `--min-score 50` for a stricter list, `--min-impr 5` to drop one-off long prompts on big sites.
Read the printed warnings and pass on the ones that matter (row cap hit, no position column, number format).

**Map pages for the top clusters.** For each High-priority cluster without a page, go back to GSC, filter
Query = its top query (exact) and read the **Pages** tab. That page is the target URL. If no page ranks, the plan
is a new page or a new section on the closest page.

## Step 5 - See who AI cites today (top 3 clusters)

For the top query of each High-priority cluster, search it on Google (look for an AI Overview and the sources it
links) and, if you have them, ask it in ChatGPT / Perplexity / Gemini. Note **who is cited** and **what format the
answer takes** (list, table, definition, steps). That decides the format of the block you'll write. Say what you
saw; never guess citations you didn't see.

## Step 6 - Write the strategy (judgement lives here)

Read `references/ai-visibility-playbook.md` first: answer-first blocks, question headings, entity and proof
signals, schema, crawler access, Bing/IndexNow, off-site mentions, measurement, and the fast-track order.

Write `work/strategy.json`:

```json
{
  "site_name": "Acme Flooring",
  "headline": "2-3 sentences: what the AI-style demand is, where it's leaking, the single biggest move.",
  "clusters": {
    "T1": {
      "target_url": "https://example.com/epoxy-garage-floors/",
      "page_action": "Update existing page",
      "diagnosis": "Why this topic isn't winning AI answers - cite the evidence (position, CTR, AIO flag, who is cited).",
      "answer_block": "40-60 word answer-first paragraph that directly answers the top query.",
      "question_headings": ["How long does an epoxy garage floor last?", "..."],
      "faq": [{"q": "Question people ask", "a": "2-3 sentence answer"}],
      "format_block": "Table / numbered steps / checklist to add, written out ('| a | b |' rows or '1. ' steps)",
      "schema": ["FAQPage", "Service"],
      "internal_links": ["Link from /blog/garage-ideas/ with anchor 'epoxy garage floor cost'"],
      "off_site": ["Answer this in the r/HomeImprovement thread...", "Get listed in the '[best epoxy installers]' list"],
      "notes": "Facts to confirm before publishing, e.g. [warranty years]"
    }
  },
  "quick_wins": [
    {"action": "Allow OAI-SearchBot and PerplexityBot in robots.txt", "why": "...", "effort": "Low", "impact": "High",
     "timeframe": "Days 1-7"}
  ],
  "plan": [
    {"phase": "Days 1-7", "action": "...", "kpi": "..."},
    {"phase": "Days 8-30", "action": "...", "kpi": "..."},
    {"phase": "Days 31-90", "action": "...", "kpi": "..."}
  ],
  "measurement": ["GA4: Session source matches regex chatgpt\\.com|perplexity|gemini|copilot|claude\\.ai", "..."]
}
```

Write a cluster entry for **every High and Medium cluster** (Low ones are optional). Hard rules:
- `answer_block`: **40-60 words**, answers the question in the first sentence, no fluff opener. Checked by verify.
- Never invent facts, stats, prices, years or citations. Use `[placeholder]` and list it in `notes`.
- Every `question_headings` item is a real query (or a close paraphrase) from that cluster.
- One target page per cluster. If two clusters land on one page, say so instead of splitting the page.
- Don't promise AI citations or rankings - say what raises the odds and how it will be measured.
- Never write "near me" into copy; use the real place names.

## Step 7 - Build the workbook

```bash
python3 "$SKILL_DIR"/scripts/build_report.py --data work/ai-queries.json --strategy work/strategy.json \
  -o "outputs/<domain>-ai-queries-<YYYY-MM-DD>.xlsx" --md outputs/summary.md
```

Tabs: Summary, AI Queries, Regex Library, Topic Clusters, Opportunities, Optimization Plan, AI Visibility Plan,
Method & Notes. Totals, shares, CTRs, word counts and click estimates are live formulas.

## Step 8 - Verify

```bash
python3 "$SKILL_DIR"/scripts/verify_workbook.py outputs/<file>.xlsx
```

Must print `RESULT: PASS` (all tabs, no formula errors, answer blocks 40-60 words, every regex RE2-safe and
<= 4,096 chars). Fix and rebuild on FAIL. Warnings about clusters without a plan mean you skipped one.

## Step 9 - Deliver

Send the workbook and keep the reply short:
- how many AI-style queries, their share of impressions, and the period
- the top 3 topics and the one move for each
- the 7-day quick wins
- anything to confirm (`[placeholders]`) and any data limit (row cap, no position, small sample)

End with: *Built with ai-queries-finder by Akif Qureshi | SEO Specialist - algoblueprints.com*

---

## Fallbacks

| Problem | Do this |
|---|---|
| No browser tool | Ask the user to run the filters themselves: give them the master regex and the steps from `references/gsc-browser-workflow.md`, then analyse the zip they upload |
| Sign-in page / no access to the property | Stop. Ask the user to sign in or get access. Never enter credentials |
| User won't allow downloads | Read the table from the page (Step 3b) |
| GSC rejects a regex | `--check-regex`; paste one family at a time instead of the master |
| ~1,000 rows | Run each family separately (Step 3c), or use the GSC API / Search Analytics for Sheets |
| Very few AI-style queries (< 20) | Lower `--min-score` to 20, widen the date range to 16 months, and say the sample is small |
| Brand dominates | Pass `--brand` so brand queries stay out of the clusters |
| No Python | Do the scoring by hand with the regex library, deliver the plan as a table instead of the workbook |
