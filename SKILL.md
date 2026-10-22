---
name: ai-queries-finder
description: Finds the AI-style queries hidden in Google Search Console (long conversational prompts, questions, "help me / compare / explain" requests, AI Mode follow-ups like "show me photos", queries naming ChatGPT or Gemini, AI-agent searches) plus the pages Google's own Generative AI features report shows, and turns them into a strategy to win AI visibility faster. Opens GSC in the browser, sets the last 3 months, applies a library of RE2-tested regex filters through the URL, reads the Generative AI features report, clusters everything by topic and builds an Excel working sheet with an optimisation plan per topic plus a 7/30/90-day AI visibility plan. Use whenever someone asks to find AI queries, ChatGPT / AI Mode / AI Overview / LLM queries, prompt-style or conversational queries in Search Console, wants GSC regex filters for AI queries, or asks how to improve AI visibility, AEO, GEO or AI citations from their GSC data.
---

# AI Queries Finder

One job: **find where AI search already touches the site, and say exactly how to win more of it.**

Two sources, used together:
- **Generative AI features report** (GSC > Performance, Beta): impressions in AI Overviews / AI Mode **by page**. No queries.
- **Regex filters** on the normal Performance report: the **queries** that look like AI prompts. Rare long prompts are
  often anonymised by Google, so this view undercounts; the AI report fills the gap.

| Step | What happens | Tool |
|---|---|---|
| 1 | Get the property, build the GSC links | `find_ai_queries.py --gsc-urls` |
| 2 | Site totals and Pages table (Web, last 3 months, all metrics) | Browser |
| 3 | Generative AI features report: every page | Browser |
| 4 | Master regex filter: every matching query (single families past the row cap) | Browser |
| 5 | Score, tag, cluster, map pages to topics | `find_ai_queries.py` |
| 6 | Check who AI cites for the top topics | Web search / browser |
| 7 | Write the plan per topic + the AI visibility plan | You, with `references/ai-visibility-playbook.md` |
| 8-9 | Build and verify the Excel working sheet | `build_report.py` · `verify_workbook.py` |

Scripts live in this skill's `scripts/` folder (Python 3.9+, `pandas openpyxl`; install them if missing). The skill
folder may be read-only, so **work from a writable folder** and call scripts by full path:

```bash
SKILL_DIR=/path/to/ai-queries-finder   # the folder this SKILL.md is in
mkdir -p work outputs
```

Use `python3` (or `python` if that's what the environment has). Client data stays in `work/`, never in the skill folder.

---

## Browser rules (not optional)

- Use whatever browser tool you have (Claude in Chrome, the built-in browser, computer use). No browser: see
  **Fallbacks**.
- **Read only.** Never change GSC settings, users, sitemaps or removals.
- **The user signs in.** If `search.google.com/search-console` redirects to `/search-console/about` or to
  `accounts.google.com`, the browser is not signed in: stop and ask the user to sign in themselves (and, in a side
  panel browser, to make sure the pane is showing). Never type a password.
- **Ask before downloading.** Export > Download CSV saves a file; get a yes first. Reading the tables (below) needs no
  download.

## Step 1 - Property and links

Ask for (don't block - defaults and `[placeholders]` are fine): the **GSC property**, **brand name(s)**, **service
areas / cities**, language variant. If the user doesn't know the exact property, open Search Console and read the
property picker (`[role=option]` items) for them to choose from.

GSC keeps the date range, metrics, tab and filters **in the URL**, so you never need the filter menus (which often
close under automated clicks):

```bash
python3 "$SKILL_DIR"/scripts/find_ai_queries.py --gsc-urls "sc-domain:example.com"   # or "https://example.com/"
```

It prints: site totals, Pages, Generative AI features, the MASTER regex, and each family R01-R12. The parameters:
`metrics=CLICKS,IMPRESSIONS,CTR,POSITION`, `num_of_months=3`, `breakdown=page` (Pages tab),
`query=~<url-encoded regex>` (Query filter, Custom regex). Check on screen that the date chip says
**3 months** and Search type **Web**.

## Step 2 - Site totals and Pages

Open link 1. Note **Total clicks** and **Total impressions** (cards round to "68.2k": that's fine for the share; say
it's rounded). Open link 2 (Pages tab) and read the whole table (**Reading a table** below) into
`work/gsc-pages.tsv` with header `page	clicks	impressions	ctr	position`.

## Step 3 - Generative AI features report

Open link 3 (`/performance/search-analytics/ai`). Note **Total impressions** and the date range, glance at the daily
chart (rising? falling? say so). Read the **Pages** tab into `work/gsc-ai-features-pages.tsv`
(`page	impressions`). If the report isn't there for the property, say so and carry on with regex only.

## Step 4 - Master regex queries

Open the MASTER link. Confirm the chip **Query: Custom (regex)** is showing and the totals dropped. GSC shows "Chart
totals and table results might be partial when filters are applied" - expected (anonymised queries). Read the
Queries table into `work/gsc-master-queries.tsv` (`query	clicks	impressions	ctr	position`).

**About 1,000 rows?** The interface caps tables at 1,000. Open each family link (R01-R12) and save each table
(`work/gsc-R01.tsv`...). Duplicates across files are kept once by the script, never summed.

### Reading a table

1. Scroll to **Rows per page** (`listbox "Number of rows per page"`), open it, pick **500** (click the visible
   `[role=option]` "500"; there can be a hidden second list).
2. Extract the visible rows with the page's DOM, e.g.:
   ```js
   [...document.querySelectorAll('tr')].filter(tr => tr.getBoundingClientRect().height > 0)
     .map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.split('\n')[0].trim()))
     .filter(r => r.length >= 2 && r[0])
   ```
   `split('\n')[0]` matters: URL cells can carry hover-menu text ("Copy URL to clipboard...").
3. Check the counter ("1-260 of 260"). If there's a next page, click it and repeat.
4. Write the rows as **TSV** (tab-separated). Queries can contain quotes and commas (`"epoxy flooring" -site:x.com`),
   which break CSV.

## Step 5 - Analyse

```bash
python3 "$SKILL_DIR"/scripts/find_ai_queries.py work/gsc-master-queries.tsv \
  --ai-pages work/gsc-ai-features-pages.tsv --ai-total 4830 --pages work/gsc-pages.tsv \
  -o work/ai-queries.json --brand "acme,acme flooring" --locations "gold coast,brisbane" \
  --total-clicks 575 --total-impressions 68200 --date-range "Last 3 months (21 Jul - 20 Oct 2026)" \
  --site https://example.com/
```

Per query: matched families, AI score (0-100; High >= 50, Medium >= 30), intent, topic, position bucket,
**AI-Overview-likely flag** (position <= 5, 20+ impressions, CTR under 40% of expected), action and click estimate.
Two special groups:
- **AI Mode follow-ups**: short prompts with no topic word ("show me photos", "which is cheaper?") - people
  mid-conversation with Google's AI. Treat them as content requirements (galleries, price comparisons).
- **AI agent / tool searches** (`site:`, `intitle:`, quoted): reported, never optimised for.

Per page: AI-feature impressions, Search impressions, the AI share of the page's impressions and the matching topic.
Read the warnings and pass on the ones that matter.

## Step 6 - See who AI cites (top 3 topics)

Search the top query of each High topic on Google (AI Overview / AI Mode sources) and, if available, ChatGPT /
Perplexity / Gemini. Note **who is cited** and **the answer format** (list, table, steps, images). Never guess
citations you didn't see.

## Step 7 - Write the strategy (judgement lives here)

Read `references/ai-visibility-playbook.md` first. Then write `work/strategy.json`:

```json
{
  "site_name": "Acme Flooring",
  "headline": "2-3 sentences: AI-feature impressions + trend, where they land, the single biggest move.",
  "clusters": {
    "T1": {
      "target_url": "https://example.com/page/",
      "page_action": "Update existing page | New section | New page | Covered by T3",
      "diagnosis": "Why this topic isn't winning AI answers - cite the evidence.",
      "answer_block": "40-60 word answer-first paragraph.",
      "question_headings": ["..."],
      "faq": [{"q": "...", "a": "..."}],
      "format_block": "Table ('| a | b |' rows), numbered steps or checklist",
      "schema": ["FAQPage", "Service"],
      "internal_links": ["..."],
      "off_site": ["..."],
      "notes": "Facts to confirm, e.g. [price]"
    }
  },
  "pages": {"https://example.com/most-ai-shown-page/": "what to do with this page"},
  "quick_wins": [{"action": "...", "why": "...", "effort": "Low", "impact": "High", "timeframe": "Days 1-7"}],
  "plan": [{"phase": "Days 8-30", "action": "...", "kpi": "...", "effort": "Medium", "impact": "High"}],
  "measurement": ["..."]
}
```

Cover **every High and Medium topic** and the **10 most AI-shown pages** (`pages`). Hard rules:
- `answer_block`: **40-60 words**, answers in the first sentence (checked by verify). Use `""` for topics covered
  elsewhere (`page_action: "Covered by T3"`) or follow-up groups.
- Never invent facts, prices, stats, years or citations: `[placeholder]` + `notes`.
- Every number in `headline`, `diagnosis` and `pages` must come from the data. Check counts before you write them.
- Look for **split pages** (several URLs for one intent, all ranking badly) - a frequent cause of weak AI visibility.
- Don't promise citations. Never write "near me" into copy.

## Step 8 - Build

```bash
python3 "$SKILL_DIR"/scripts/build_report.py --data work/ai-queries.json --strategy work/strategy.json \
  -o "outputs/<domain>-ai-queries-<YYYY-MM-DD>.xlsx" --md outputs/summary.md
```

Tabs: Summary, AI Queries, AI Feature Pages, Regex Library, Topic Clusters, Opportunities, Optimization Plan,
AI Visibility Plan, Method & Notes. Totals, shares, CTRs, word counts and click estimates are live formulas.

## Step 9 - Verify and deliver

```bash
python3 "$SKILL_DIR"/scripts/verify_workbook.py outputs/<file>.xlsx
```

Must print `RESULT: PASS` (all tabs, no formula errors, every regex RE2-safe and <= 4,096 chars, answer blocks
40-60 words). Then send the workbook with a short reply: AI-feature impressions + trend, AI-style queries and their
share, the top 3 topics with one move each, the 7-day quick wins, and anything to confirm.

End with: *Built with ai-queries-finder by Akif Qureshi | SEO Specialist - algoblueprints.com*

---

## Fallbacks

| Problem | Do this |
|---|---|
| No browser tool | Give the user the `--gsc-urls` links; they export each view (Export > Download CSV) and upload the zips |
| Redirect to `/about` or a sign-in page | Stop; the user signs in. Never enter credentials |
| Filter menu won't open | Don't click through it - use the `query=~` URL from `--gsc-urls` |
| User won't allow downloads | Read the tables (Step 4, **Reading a table**) |
| No Generative AI features report | Say so; run the regex part only |
| GSC rejects a regex | `--check-regex`; open one family link at a time |
| ~1,000 rows | Single families, or the GSC API / Search Analytics for Sheets |
| Very few AI-style queries (< 20) | Normal for small sites (anonymised long tail). Lean on the AI features report; widen to 16 months |
| No Python | Score by hand with the regex library; deliver the plan as a table |
