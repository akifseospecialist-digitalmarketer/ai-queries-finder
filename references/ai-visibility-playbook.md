# AI visibility playbook

How to turn AI-style queries into citations and clicks. Use it for Step 6. Every recommendation in the workbook
should trace back to a rule here **and** to evidence in the data (position, CTR, AIO flag, who is cited).

What's known for sure: AI answers (AI Overviews, AI Mode, ChatGPT search, Perplexity, Copilot) are assembled from
pages a retrieval system can find, read and quote. Nobody outside those companies knows the exact weighting, so
**never promise a citation**. Promise the things that raise the odds, and how you'll measure them.

---

## 1. Read the data before writing anything

| Signal in the workbook | What it usually means | Lead with |
|---|---|---|
| Top 3 + **AIO likely** | You rank, but the answer is summarised above you, so clicks go elsewhere | Be the quoted source: answer block + unique proof (numbers, photos, experience) the summary can't include |
| Top 3, CTR normal | You're winning | Defend: freshness, schema, keep the answer block current |
| 4-10 | Relevant but not the best answer | Answer upgrade: question H2 + 40-60 word answer + list/table |
| 11-20 | Topic covered thinly | Expand the section, add internal links from strong pages |
| 21+ / no page | Topic not covered | New section on the closest page, or a new page if the cluster is big enough to stand alone (5+ queries or 500+ impressions) |
| Many R01/R04/R05 queries | People describe their situation ("I have a 2-car garage with cracks...") | Scenario sections: "If you have X, do Y" |
| Many R06/R07 queries | AI is building shortlists | Comparison tables, "best for" statements, and getting onto third-party lists |
| R10 queries (tool names, URLs) | Prompts leaking through from assistants | Treat as the clearest view of real prompts: mirror their wording in headings |
| **AI Mode follow-ups** ("show me photos", "which is cheaper?", "are they slippery") | People mid-conversation with Google's AI, asking for the next thing | Content requirements: a captioned photo gallery, a price-comparison table, short yes/no answers |
| **Agent searches** (`site:`, `intitle:`, quoted phrases) | AI tools researching | Don't optimise for them; a sign AI tools are crawling the topic |
| Page has high **AI-feature impressions but ranks 30+** | AI fan-out finds the page even though classic ranking doesn't | Quick upside: answer-first block + proof; it's already being considered |
| High **AI share** of a page's impressions (e.g. 30-50%) | The page's topic is answered by AI more than by blue links | Optimise that page for citation first; titles that give a reason to click |
| **Split pages**: several URLs for one intent, all ranking 40+ | Cannibalisation - neither Google nor AI knows which page is the answer | Pick one owner page, merge and 301 the rest |

## 2. On-page: make each answer quotable

Retrieval systems lift **passages**, not pages. Each target query needs a passage that stands on its own.

1. **Question heading.** H2/H3 written as the question, in the searcher's words (from the cluster's queries).
2. **Answer-first block: 40-60 words** straight under the heading. First sentence answers the question
   completely. Then the key condition or number. No "Great question" / "In this article".
3. **Then the depth:** steps (numbered), a comparison (table), or factors (bullets). Match the format the
   AI answer already uses for that query (Step 5 of the skill).
4. **Proof the summary can't fake:** your own numbers, prices or ranges, timeframes, photos, a named expert,
   a short case ("We resurfaced a 40 m² garage in Southport in 2 days..."). Unique facts are what get cited
   *and* what earns the click.
5. **Entities spelled out:** full product/service names, the brand, the place, standards and materials - not
   "it" and "this". Passages are read out of context.
6. **Freshness:** a visible "Updated [month year]" with real changes, current-year facts.
7. **One page per topic.** Don't split one intent across several thin pages.

Templates:

| Query type | Block shape |
|---|---|
| What is / definition | Definition sentence -> what it's used for -> one distinguishing fact |
| How to | One-line outcome -> numbered steps (5-9) -> time/cost/tools line |
| How long / how much | Range with conditions ("Most X last 10-20 years; [factor] changes it most") -> table of factors |
| X vs Y | One-line verdict by situation -> comparison table (price, lifespan, best for, downsides) |
| Best / recommend | Criteria first -> shortlist with "best for" -> how to choose |
| Should I / is it worth | Direct yes/no + condition -> who it suits / who it doesn't |
| Scenario (first-person, long prompt) | "If you [situation], [recommendation] because [reason]" -> what to check next |

## 3. Technical: let AI systems in

| Check | Why | How |
|---|---|---|
| robots.txt allows **OAI-SearchBot**, **ChatGPT-User**, **PerplexityBot**, **Claude-SearchBot / Claude-User**, **Bingbot**, **Googlebot** | Blocked crawlers can't retrieve or cite the page | Read `/robots.txt`. Blocking training bots (GPTBot, Google-Extended, CCBot) is a separate choice and doesn't stop search citations |
| No firewall/CDN bot blocking | Cloudflare and similar tools can block AI crawlers by default | Ask the user to check the bot settings |
| Content in the HTML | Many AI crawlers don't run JavaScript | View source: is the answer block in the raw HTML? |
| **Bing Webmaster Tools** + **IndexNow** | Several AI assistants lean on Bing's index; IndexNow tells Bing about changes in minutes | Verify the site in Bing, import from GSC, enable IndexNow (most CMSs have a plugin) |
| Schema | Clarifies entities and page type | `Organization`/`LocalBusiness` sitewide, `Service`/`Product`, `Article` with `author` and `dateModified`, `FAQPage` where there's a real FAQ, `HowTo`-style steps in plain HTML lists |
| Indexing | Unindexed pages can't be cited | URL Inspection > Request indexing after each update |

Skip `llms.txt` as a priority: there's no evidence the major assistants use it for citations. Fine to add, not a
quick win.

## 4. Off-site: become the brand AI already trusts

AI answers to "best" and "vs" prompts lean heavily on third-party pages: lists, reviews, forums, directories.
For R06/R07-heavy clusters:

- Find the pages cited in Step 5 and ask for inclusion (listicles, comparison posts, local directories).
- Keep reviews flowing on the platforms the AI answer quotes (Google Business Profile, industry sites).
- Answer real threads (Reddit, Quora, industry forums) helpfully, as yourself, without spam.
- Get your facts consistent everywhere: name, services, areas, prices/ranges, years. Inconsistent facts get
  dropped from answers.
- PR / original data: one small study or price survey gives AI something to quote that nobody else has.

## 5. Measurement (put it in the plan)

- **GSC Generative AI features report:** total impressions and the top pages, monthly, against this report's
  baseline. The most direct measure Google gives of AI visibility.
- **GSC master regex:** keep the link from `--gsc-urls`. Compare AI-style impressions, clicks and CTR monthly.
- **GA4 AI referrals:** Reports > Acquisition > Traffic acquisition, filter *Session source* matches regex
  `chatgpt\.com|openai|perplexity|gemini\.google|copilot|claude\.ai|you\.com|meta\.ai`.
- **Prompt tracking:** the top query of each High cluster, asked monthly in ChatGPT, Perplexity, Gemini and Google
  AI Mode. Record cited yes/no and which competitors are cited. (A spreadsheet is enough; tools can automate it.)
- **Bing Webmaster Tools:** Bing's reporting includes Copilot data - check the AI performance report if the
  account has it.

## 6. Fast-track order (how to raise visibility fastest)

Do these in this order; each step uses work from the one before.

**Days 1-7 - unblock and fix the biggest leaks**
1. robots.txt / firewall: make sure AI search crawlers can fetch the site.
2. Bing Webmaster Tools + IndexNow on.
3. The 5 most AI-shown pages (Generative AI features report) and the top 3 clusters: add the question heading +
   40-60 word answer block. Request indexing in GSC and submit via IndexNow.
4. If follow-ups ask for photos, add a captioned gallery (finish, room, place in every caption and alt text).
5. Pick one owner page for any split intent (cost, "best X") and point the others at it.
6. Fix titles on AIO-flagged pages so the click is worth it ("Costs, timelines and 12 real jobs" beats "Epoxy floors").

**Days 8-30 - build out the winners**
7. Full plan for every High and Medium cluster: format block, FAQ, schema, internal links.
8. New sections / pages for 21+ clusters with enough demand.
9. Off-site: outreach to the lists and sources AI already cites for the top 3 topics.

**Days 31-90 - compound**
10. Original data or case studies for the top topic.
11. Refresh: re-pull the Generative AI features report and the master regex, compare with the baseline, move effort to what moved.
12. Review thin variant pages (city / suburb copies) that get no AI impressions: add local proof or merge.
13. Expand to the next clusters; repeat the prompt tracking monthly.

## 7. Anti-patterns (never recommend)

- Keyword-stuffed FAQ blocks or 30-question FAQs nobody asked.
- Separate thin pages for each long prompt.
- Hidden text "for AI", cloaking, or AI-only pages.
- Fake reviews, fake stats, invented citations.
- Promising "guaranteed ChatGPT ranking".
