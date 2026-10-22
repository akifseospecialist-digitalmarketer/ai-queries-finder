# GSC browser workflow

How Steps 1-4 of the skill run in a real browser. Tested on a live property in October 2026. Search Console
changes now and then: if something below isn't on screen, use the nearest match and say what you used.

## Ground rules

- **Read only.** Don't change settings, users, sitemaps, removals or anything else.
- **Signed in by the user.** Never type a password.
- **Ask before downloading.** Export > Download CSV saves a file. Reading tables from the page needs no download.

## Signed in?

| You land on | Meaning |
|---|---|
| `search.google.com/search-console?resource_id=...` (Overview) | Signed in. Carry on |
| `search.google.com/search-console/about` | **Not signed in** (public marketing page). Ask the user to sign in |
| `accounts.google.com/...signin...` | Sign-in in progress. Wait for the user; in a side-panel browser make sure the pane is showing that tab |

## Picking the property

The property picker is the "Search property" button (top left). Its entries are `[role=option]` elements whose
text is the property id, e.g. `sc-domain:example.com` (Domain property) or `https://example.com/` (URL-prefix).
Read the list for the user rather than guessing. Opening the picker can switch the view to another property when
focus moves - harmless (nothing changes), but check `resource_id` in the URL before reading data.

## Use URLs, not menus

GSC stores the whole view in the URL. `find_ai_queries.py --gsc-urls PROPERTY` prints every link you need.

| Parameter | Effect |
|---|---|
| `resource_id=` | The property, URL-encoded (`https%3A%2F%2Fexample.com%2F` or `sc-domain%3Aexample.com`) |
| `metrics=CLICKS%2CIMPRESSIONS%2CCTR%2CPOSITION` | All four metric cards on (the table only shows metrics whose cards are on) |
| `num_of_months=3` | Date range: last 3 months (tested: 6 works too) |
| `breakdown=page` | Opens the Pages tab instead of Queries |
| `query=~<regex>` | Query filter, **Custom (regex)**, matches regex. URL-encode the `~` and the regex |
| `/performance/search-analytics/ai` | The **Generative AI features** report (Beta) |

Why: the "+ Add filter" menu tends to close before the filter dialog opens when driven by automated clicks. The
`query=~` URL applies the same filter in one step. After opening, confirm on screen:
- the chip **Query: Custom (regex)** is there and the totals dropped,
- the date chip says **3 months**, Search type **Web**.

## The two reports

### Performance (Search results)

Cards: Total clicks, Total impressions, Average CTR, Average position. Values are rounded ("68.2k"). Tabs: Queries,
Pages, Countries, Devices, Search appearance, Days.

With a query filter on, GSC shows *"Chart totals and table results might be partial when filters are applied"*:
anonymised (rare) queries are left out of the table. Long AI prompts are rare by nature, so the regex view
**undercounts** AI-style demand - say so in the report.

### Generative AI features (Beta)

`/performance/search-analytics/ai?resource_id=...`, also linked from the Performance page ("Get more details on your
site's performance in generative AI features"). Shows **Total impressions** only, with a daily chart and tabs Pages,
Countries, Devices, Days. **No queries.** Default range 3 months; Search type and + Add filter are available.

Use it for: total AI-feature impressions and the trend, and which pages Google's AI features show. Page rows add up
to more than the card total because one AI answer can show several of your pages.

## Reading a table

1. Scroll to **Rows per page** (`listbox "Number of rows per page"`), open it, choose **500**. There can be two such
   lists (one per tab); click the visible `[role=option]` "500".
2. Extract visible rows:
   ```js
   [...document.querySelectorAll('tr')].filter(tr => tr.getBoundingClientRect().height > 0)
     .map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.split('\n')[0].trim()))
     .filter(r => r.length >= 2 && r[0])
   ```
   URL cells can include hover-menu text ("Copy URL to clipboard / Open in new tab / Inspect URL") - keep the first
   line only.
3. Check the counter ("1-260 of 260"); page on with the next arrow if needed.
4. Save as **TSV** with a header row. Queries contain commas and quotes (`"epoxy flooring" -site:reddit.com`); TSV
   keeps them intact. Numbers can stay as shown (`34,440`, `0.7%`).

Large tables cost a lot of tokens to transcribe. If the user allows downloads, **Export > Download CSV** gives the same
data as a zip the script reads directly.

## The 1,000-row cap

The interface shows at most 1,000 rows per table. If the master regex returns about 1,000, open each family link
(R01-R12) and save each table. The script keeps duplicates once. For everything, use the GSC API / Search Analytics
for Sheets with operator `includingRegex`.

## Finding the page for a query

Click the query row in the Queries table (it becomes a filter) and switch to the Pages tab. For whole topics, use
the AI Feature Pages tab of the workbook, which maps pages to topics by URL.

## Common snags

| What you see | What it means / do |
|---|---|
| Filter menu closes, no dialog | Use the `query=~` URL |
| "Invalid regular expression" | Run `--check-regex`; open one family link at a time |
| Few or zero regex rows | Small site or anonymised long tail. Lean on the Generative AI features report |
| Position column missing | `metrics=` lacks POSITION - use the link from `--gsc-urls` |
| Last 2 days missing | Normal: GSC lags ~2 days |
