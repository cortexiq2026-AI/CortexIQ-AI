"""Minimal end-to-end example.

Prerequisites:
    pip install -e ../packages/core-py[anthropic,search]
    export ANTHROPIC_API_KEY=...
    export AUDITOR_LLM_PROVIDER=anthropic
    # optionally: export AUDITOR_SEARCH_PROVIDER=tavily and TAVILY_API_KEY=...

Run:
    python python_quickstart.py
"""
import asyncio

from ai_answer_auditor import Auditor, SourceDocument


ANSWER_FROM_SOME_OTHER_MODEL = """
The Eiffel Tower was completed in 1889 for the World's Fair and stands 330
meters tall, making it the tallest structure in Paris. It was designed by
Gustave Eiffel and was originally intended to be dismantled after 20 years,
but it was kept because it proved useful for radio transmission.
"""

SOURCE_DOC = """
The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in
Paris, France. It is named after the engineer Gustave Eiffel, whose company
designed and built the tower. Locally nicknamed "La dame de fer", it was
constructed as the centerpiece of the 1889 World's Fair and was initially
criticized by some of France's leading artists and intellectuals for its
design. The tower is 330 metres tall and was the tallest man-made structure
in the world for 41 years. It was to be dismantled in 1909, but was kept
after it proved valuable for communication purposes.
"""


async def main() -> None:
    auditor = Auditor()  # reads AUDITOR_LLM_PROVIDER / AUDITOR_SEARCH_PROVIDER etc. from env

    report = await auditor.audit(
        answer=ANSWER_FROM_SOME_OTHER_MODEL.strip(),
        question="Tell me about the Eiffel Tower.",
        sources=[SourceDocument(id="eiffel_wiki", title="Eiffel Tower", text=SOURCE_DOC.strip())],
    )

    print(f"Verification score:  {report.verification_score}/100")
    print(f"Completeness score:  {report.completeness_score}/100")
    print(f"Total claims:        {report.total_claims}")
    print(f"Unsupported claims:  {report.unsupported_claims}")
    print(f"Contradicted claims: {report.contradicted_claims}")
    print(f"Needs human review:  {report.needs_human_review}")
    print()
    print(report.summary)
    print()
    for v in report.claim_verifications:
        print(f"[{v.status.value:>18}] ({v.confidence:.2f}) {v.claim.text}")


if __name__ == "__main__":
    asyncio.run(main())
