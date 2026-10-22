# Regex library

Copy-paste regexes for **Search Console > Performance > + Add filter > Query > Custom (regex) > Matches regex**.
Generated from [`regex-library.json`](regex-library.json) (the file the scripts read). Edit the JSON, then
regenerate this page; run `python scripts/find_ai_queries.py --check-regex` before committing.

GSC uses **RE2**: no lookaheads/lookbehinds, no backreferences, max **4,096 characters**. Every regex here is
tested against RE2.

## Master regex (paste this first)

OR of every family marked *in master*. Catches long prompts, questions, requests, first-person context,
how/why reasoning and AI-tool mentions in one filter.

```
(?i)^\S+(\s+\S+){9,}$|^\S+(\s+\S+){6,8}$|^(who|whom|whose|what|whats|what's|when|where|why|how|which|is|are|was|were|am|can|could|should|would|will|do|does|did|has|have)\s|^(give|show|tell|help|explain|list|compare|recommend|suggest|find|create|write|generate|make|summarise|summarize|describe|plan|calculate|teach|guide|walk|act|pretend|please|i need|i want|im looking|i'm looking|i am looking|looking for|can you|could you)\b|\b(i|im|i'm|ive|i've|my|me|we|our|mine)\b|\b(how (to|do|does|can|long|much|many|often)|why (is|do|does|are|would)|what (is|are|does|happens|should)|is it (safe|worth|possible|legal|true|normal|ok|okay|better)|does it|can i|should i|do i need)\b|(chatgpt|chat gpt|openai|gpt-?[0-9]|gemini|claude|perplexity|copilot|ai overview|ai mode|\bllm\b|https?://|www\.|\.com/)
```

## Families

| ID | Family | Weight | In master | What it catches |
|---|---|:-:|:-:|---|
| R01 | Long prompt (10+ words) | 35 | Yes | Full-sentence prompts typed or passed through by AI assistants and AI Mode. The strongest single signal. |
| R02 | Conversational length (7-9 words) | 15 | Yes | Queries longer than classic keywords but shorter than full prompts. |
| R03 | Question opener | 30 | Yes | Queries that start like a question to an assistant: what, how, why, can, should, is... |
| R04 | Instruction / request | 30 | Yes | Commands written for an AI: give me, explain, compare, list, write, help me, I need, I'm looking for... |
| R05 | First-person context | 20 | Yes | Personal situations people describe to an AI: my garage, I have, we need, our team... |
| R06 | Comparison | 15 | - | X vs Y, alternatives, differences, pros and cons, which is better. |
| R07 | Recommendation / best-of | 10 | - | Best, top 10, recommended, worth it, should I buy/hire - the queries AI answers with shortlists of brands. |
| R08 | Constraints & specifics | 10 | - | Extra conditions people add when they expect a tailored answer: for beginners, under $500, step by step, without, checklist. |
| R09 | How / why / is-it reasoning | 15 | Yes | Explanation and decision questions anywhere in the query: how long, why does, is it worth, do I need, can I. |
| R10 | AI tool mention / leaked prompt | 40 | Yes | Queries naming an AI tool, or URL-prefixed prompts like the ChatGPT queries reported leaking into GSC in late 2025. |

### R01 - Long prompt (10+ words)

Full-sentence prompts typed or passed through by AI assistants and AI Mode. The strongest single signal.

```
^\S+(\s+\S+){9,}$
```

### R02 - Conversational length (7-9 words)

Queries longer than classic keywords but shorter than full prompts.

```
^\S+(\s+\S+){6,8}$
```

### R03 - Question opener

Queries that start like a question to an assistant: what, how, why, can, should, is...

```
(?i)^(who|whom|whose|what|whats|what's|when|where|why|how|which|is|are|was|were|am|can|could|should|would|will|do|does|did|has|have)\s
```

### R04 - Instruction / request

Commands written for an AI: give me, explain, compare, list, write, help me, I need, I'm looking for...

```
(?i)^(give|show|tell|help|explain|list|compare|recommend|suggest|find|create|write|generate|make|summarise|summarize|describe|plan|calculate|teach|guide|walk|act|pretend|please|i need|i want|im looking|i'm looking|i am looking|looking for|can you|could you)\b
```

### R05 - First-person context

Personal situations people describe to an AI: my garage, I have, we need, our team...

```
(?i)\b(i|im|i'm|ive|i've|my|me|we|our|mine)\b
```

### R06 - Comparison

X vs Y, alternatives, differences, pros and cons, which is better.

```
(?i)\b(vs|versus|compare|compared|comparison|alternative|alternatives|difference between|differences between|better than|pros and cons|which is better)\b
```

### R07 - Recommendation / best-of

Best, top 10, recommended, worth it, should I buy/hire - the queries AI answers with shortlists of brands.

```
(?i)\b(best|top \d+|top rated|recommend|recommended|most reliable|most popular|most affordable|cheapest|worth it|should i (buy|use|choose|get|hire|go with))\b
```

### R08 - Constraints & specifics

Extra conditions people add when they expect a tailored answer: for beginners, under $500, step by step, without, checklist.

```
(?i)\b(for beginners|for a small|for small|for my|for someone|step by step|under \$?\d+|less than|on a budget|without|checklist|template|example|examples|in 20\d\d|for 20\d\d)\b
```

### R09 - How / why / is-it reasoning

Explanation and decision questions anywhere in the query: how long, why does, is it worth, do I need, can I.

```
(?i)\b(how (to|do|does|can|long|much|many|often)|why (is|do|does|are|would)|what (is|are|does|happens|should)|is it (safe|worth|possible|legal|true|normal|ok|okay|better)|does it|can i|should i|do i need)\b
```

### R10 - AI tool mention / leaked prompt

Queries naming an AI tool, or URL-prefixed prompts like the ChatGPT queries reported leaking into GSC in late 2025.

```
(?i)(chatgpt|chat gpt|openai|gpt-?[0-9]|gemini|claude|perplexity|copilot|ai overview|ai mode|\bllm\b|https?://|www\.|\.com/)
```

## How the score works

Each query gets the sum of the weights of every family it matches, capped at 100.
**High** >= 50, **Medium** >= 30. Queries under 30 (default `--min-score`) are listed but not treated as AI-style.

| Example query | Families | Score |
|---|---|:-:|
| `how long does epoxy garage floor last` | R02, R03, R09 | 60 |
| `i have cracks in my garage floor can i still get epoxy coating` | R01, R05, R09 | 70 |
| `give me a checklist for preparing a garage floor for epoxy` | R01, R04, R05, R08 | 95 |
| `https://openai.com/index/chatgpt/ best epoxy flooring company gold coast reviews` | R02, R07, R10 | 65 |
| `is epoxy flooring slippery when wet` | R03 | 30 |
| `epoxy vs polished concrete` | R06 | 15 |
| `epoxy flooring gold coast` | - | 0 |

## Using them elsewhere

- **GSC API / Search Analytics for Sheets:** `dimensionFilterGroups` > filter `query`, operator `includingRegex`, expression = the regex.
- **Looker Studio:** filter *Query* > *RegExp Contains*. Looker uses RE2 too.
- **Exclude instead of include:** GSC's *Doesn't match regex* with R01 shows only short, classic keyword searches - useful as a comparison.
- **Brand:** keep brand terms out with `--brand` in the script; the GSC interface keeps one Query filter at a time, so an exclusion can't be stacked on the AI regex there.
