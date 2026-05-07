---
name: research
description: Research a topic using web search and synthesize findings into an actionable briefing with curated resources. Triggers on requests to research, look up, survey, or find resources about a technology, pattern, tool, or concept -- especially when the user needs a synthesized understanding rather than a single answer. Does NOT trigger for code-specific Q&A ("how do I do X in Angular"), direct implementation questions, or head-to-head solution comparisons (use explore-solutions for those).
---

# Topic Research

Given a topic or question, search the web, read the most relevant pages, and deliver a synthesis of key findings backed by a curated resource list. Prioritize accuracy and usefulness over breadth.

## Workflow

### 1. Parse the Request

- Extract the core question or topic from the user's message
- Determine scope: broad survey vs. focused deep-dive
- Identify constraints: specific language/framework, recency requirements
- Detect audience level: if the user's phrasing suggests beginner knowledge (e.g., "what is", "getting started", "how does X work"), prioritize tutorials and overviews; if it suggests expert knowledge (e.g., "performance characteristics of", "trade-offs between X internals", "migration path from"), prioritize benchmarks, advanced trade-offs, and deep technical content

### 2. Conduct Web Research

- Run 2-4 `WebSearch` queries with varied phrasing (e.g., conceptual, "best practices", "vs alternative", "tutorial")
- **When to fetch**: if a search result snippet directly answers the question, fetching may be unnecessary -- use the snippet. If you need to verify claims, check methodology, or extract specific details, fetch the full page with `WebFetch`. Always fetch before citing a resource in the resource list.
- Never cite a resource you have not opened
- Source priority (highest first):
  1. Official documentation and specifications
  2. Authoritative technical blogs (engineering blogs from known companies, respected authors)
  3. Academic papers or industry reports
  4. High-signal community discussions (Stack Overflow accepted answers, HN threads with expert replies)
- Prefer content from the last 2 years unless the topic is stable/foundational
- **Conflict resolution**: when sources disagree, official docs take precedence over blogs, and newer content over older (assuming equal authority). In the synthesis, present the disagreement explicitly -- state what each side claims and which source is more authoritative, rather than silently picking one

### 3. Curate Best Resources

- Select 4-8 resources. If 2 excellent official docs fully answer the question, stopping at 2 is better than padding to 4. Never add filler to hit a count.
- Order resources by value: most useful first.
- Follow the output format below for each resource entry.

### Depth Negotiation

- **When to stop**: if additional queries yield results you have already seen and the sources reach clear consensus, conclude. Do not search further just to fill a quota.
- **When to expand**: if sources disagree, coverage is thin, or a key subtopic is unaddressed, add 1-2 more targeted queries before synthesizing.

### 4. Synthesize Key Findings

Write a summary placed **before** the resource list, covering these elements (combine into 3-4 paragraphs):

1. **Direct answer** -- address the user's question or define the topic upfront
2. **Core concepts** -- the essential ideas, patterns, or trade-offs
3. **Consensus and controversy** -- what experts agree on; where they diverge
4. **Practical takeaway** -- actionable recommendation or next step

## Output Format

```markdown
## Key Findings

[3-4 paragraphs covering: direct answer, core concepts, consensus/controversy, practical takeaway]

## Resources

### 1. [Resource Title](URL)
**Type**: Official Docs | Blog | Tutorial | Paper | Discussion
[2-3 sentences: what's there and why it matters]

### 2. [Resource Title](URL)
...
```

## Guidelines

- **Verify before citing**: `WebFetch` every resource before including it. If a page fails to load or content does not match, drop it.
- **Quality over quantity**: fewer excellent resources beat many mediocre ones. Never pad with filler.
- **When results are thin**: rephrase queries or broaden scope. If sources are genuinely scarce, say so.
- **Mix resource types** when possible (official docs, tutorials, deep-dive articles, discussions).
- **For complex topics**: organize resources by subtopic or difficulty level.
- **No hallucinated URLs**: every URL must come from a `WebSearch` result or a link found on a fetched page. Never construct URLs from memory.
- **Fetch failures**: if `WebFetch` fails on multiple resources, note the fetch issues transparently in the synthesis (e.g., "Several sources could not be accessed; findings are based on the N resources that were available"). Do not silently omit the gap.
- **Recency gaps**: if a topic has no recent sources (e.g., all results are 3+ years old), acknowledge the recency gap explicitly and note whether the topic is stable enough for older sources to remain reliable.
