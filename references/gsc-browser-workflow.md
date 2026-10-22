# GSC browser workflow

The exact clicks for Steps 1-3 of the skill. The Search Console interface changes now and then: if a label below
isn't on screen, look for the nearest match and say what you used.

## Ground rules

- **Read only.** Don't change settings, users, sitemaps, removals or anything else in GSC.
- **Signed in by the user.** On a Google sign-in page, stop and ask the user to sign in. Never type a password.
- **Ask before downloading.** Export > Download CSV saves a file. Get a yes first; otherwise read the table.

## 1. Open the report

1. Go to `https://search.google.com/search-console`.
2. Property picker (top left) > choose the property the user named. A **Domain** property covers every
   subdomain and protocol, so prefer it when both exist.
3. Left menu > **Performance** > **Search results**.

## 2. Set it up

| Control | Set to | Why |
|---|---|---|
| Search type | **Web** | Image / video / news queries are a different behaviour |
| Date | **Last 3 months** | Enough long-tail data; long prompts are rare per day. Note the exact dates shown |
| Metric cards | **All four on** (Clicks, Impressions, CTR, Position) | The table only includes the metrics whose cards are on |

Write down the unfiltered **Total clicks** and **Total impressions**.

> AI Mode and AI Overview impressions are counted inside these Web totals. Search Console does not label
> which queries came from AI features - that's why this skill finds them by their shape (length, phrasing,
> intent) with regex.

## 3. Add the regex filter

1. Click **+ Add filter** (or **+ New** in older layouts) > **Query**.
2. The dropdown says "Queries containing". Change it to **Custom (regex)**.
3. Keep **Matches regex**. Paste the regex exactly as printed by `find_ai_queries.py --print-regex`.
4. **Apply.** The totals and chart update; the filter shows as a chip at the top.

To swap regex: click the chip > edit the text > Apply. The interface keeps one Query filter at a time; a Page
filter can be added on top of it.

### Checks after applying

- The totals dropped (if they didn't, the filter didn't apply).
- Open the Queries table and scan the first rows: they should read like questions or sentences.
- Note the filtered totals for the summary.

## 4. Pull the data

### Option A - Export (preferred, needs the user's OK)

**Export** (top right) > **Download CSV**. The zip holds `Queries.csv`, `Pages.csv`, `Countries.csv`, `Devices.csv`,
`Search appearance.csv`, `Dates.csv` and `Filters.csv`. The script reads the zip directly and takes the date range
from `Filters.csv`.

### Option B - Read the table

1. Queries tab > bottom of the table > **Rows per page** > largest value.
2. Read each page of the table (page text or accessibility tree), then click the next-page arrow until the
   counter ("1-500 of 812") is exhausted.
3. Save as CSV with header `query,clicks,impressions,ctr,position`. Numbers as shown (the script handles
   `1,234`, `4.2%` and decimal commas).

### The 1,000-row cap

The interface never shows more than **1,000 rows** per table. If the master regex returns about 1,000, run each
family regex separately and pull each one. Every family is narrower, so together they surface far more of the long
tail. For the complete set use the GSC API, Search Analytics for Sheets or a GSC connector - same regexes,
`queryFilter` with operator `includingRegex`.

## 5. Find the page for a query

Filter Query = **exact** query (not regex) > **Pages** tab. The top row is the page Google shows for it. With
several pages listed, the one with the most impressions is the target; the others are cannibalisation to note.

## Common snags

| What you see | What it means / do |
|---|---|
| "Invalid regular expression" | A character the GSC parser doesn't accept. Run `--check-regex`, paste one family at a time |
| Zero rows | Small site or new property. Widen to 16 months, try single families (R03, R09 usually return something) |
| Table missing Position | The Average position card is off - turn it on, re-read |
| "Data is processing" / last 2 days missing | Normal: GSC lags ~2 days |
| Anonymised queries | GSC hides very rare queries for privacy, so totals with a filter can be lower than the rows suggest. Say so if the gap is large |
