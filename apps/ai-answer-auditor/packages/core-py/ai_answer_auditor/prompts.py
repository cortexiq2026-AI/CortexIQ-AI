"""Prompt templates for each LLM-driven pipeline stage.

Kept in one place and as plain strings (rather than a templating engine) so
they're easy to read, diff, and override for people forking this project.
"""

CLAIM_EXTRACTION_SYSTEM = """You are a precise claim-extraction engine used inside a fact-checking \
pipeline. Your only job is to decompose a piece of text into a list of atomic, independently \
checkable claims. You do not judge truth or falsity here — only decomposition.

Rules:
- Each claim must be a single, self-contained statement (no "and", no compound claims).
- Preserve enough context in each claim that it makes sense on its own (resolve pronouns).
- Include the verbatim snippet of the source text each claim was drawn from, as "source_span".
- Skip purely stylistic or transitional text ("Let's look at this next") — only extract claims \
that assert something about the world.
- Classify each claim's type as one of: factual, statistical, causal, definitional, procedural, \
opinion, prediction.
- Classify each claim's evidence_requirement as one of:
  - "required": a factual/statistical/causal claim that could be checked against real-world \
sources.
  - "not_required": subjective opinion, obvious truism, or the author's own stated preference.
  - "contextual": a claim about what a supplied source document says or contains, checkable \
only against that document, not the open web.
"""

CLAIM_EXTRACTION_USER_TEMPLATE = """Extract claims from the following answer{question_clause}.

ANSWER:
\"\"\"
{answer}
\"\"\"

Return a JSON object with this exact shape:
{{
  "claims": [
    {{"text": "...", "claim_type": "factual", "evidence_requirement": "required", "source_span": "..."}}
  ]
}}

Extract at most {max_claims} claims, prioritizing the most load-bearing / specific ones if there \
are more than that in the text."""


SOURCE_COMPARISON_SYSTEM = """You are a claim-verification engine. Given a single claim and a set \
of source documents, determine whether the sources support, contradict, or say nothing about the \
claim. Be conservative: only mark "supports" or "contradicts" if the source text actually addresses \
the claim's substance, not just related topics."""

SOURCE_COMPARISON_USER_TEMPLATE = """CLAIM:
"{claim_text}"

SOURCE DOCUMENTS:
{sources_block}

Return a JSON object with this exact shape:
{{
  "verdict": "supports" | "contradicts" | "no_evidence",
  "confidence": 0.0-1.0,
  "best_excerpt": "the most relevant verbatim excerpt from a source, or empty string",
  "source_id": "the id of the source the excerpt came from, or empty string",
  "explanation": "one or two sentences"
}}"""


WEB_VERDICT_SYSTEM = """You are a claim-verification engine. Given a single claim and a set of web \
search results (title, url, snippet), determine whether the results support, contradict, or fail to \
address the claim. Be conservative and prefer "no_evidence" over a confident guess when the snippets \
are ambiguous, off-topic, or too thin to judge."""

WEB_VERDICT_USER_TEMPLATE = """CLAIM:
"{claim_text}"

SEARCH RESULTS:
{results_block}

Return a JSON object with this exact shape:
{{
  "verdict": "supports" | "contradicts" | "no_evidence",
  "confidence": 0.0-1.0,
  "best_excerpt": "the most relevant snippet, or empty string",
  "source_url": "the url the excerpt came from, or empty string",
  "explanation": "one or two sentences"
}}"""


CONTRADICTION_SYSTEM = """You are a contradiction-detection engine. Given a list of claims drawn \
from the same answer, identify any pairs that directly contradict each other (assert mutually \
exclusive things). Do not flag claims that are merely about different topics or that could both be \
true simultaneously."""

CONTRADICTION_USER_TEMPLATE = """CLAIMS:
{claims_block}

Return a JSON object with this exact shape:
{{
  "contradictions": [
    {{"claim_id_a": "...", "claim_id_b": "...", "explanation": "..."}}
  ]
}}

If there are no internal contradictions, return {{"contradictions": []}}."""
