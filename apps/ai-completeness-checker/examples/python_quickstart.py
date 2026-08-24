"""Minimal end-to-end example.

Prerequisites:
    pip install -e ../packages/core-py[anthropic]
    export ANTHROPIC_API_KEY=...
    export CHECKER_LLM_PROVIDER=anthropic

Run:
    python python_quickstart.py
"""
import asyncio

from ai_completeness_checker import CompletenessChecker


# A plausible "answer" from some other AI to a security architecture question.
# Nothing here is factually wrong — it's just incomplete.
ANSWER_FROM_SOME_OTHER_MODEL = """
Our authentication system uses OAuth2 with JWT tokens for session management.
Users log in via their corporate SSO provider, and tokens expire after 24
hours. For authorization, we use role-based access control with three tiers:
admin, editor, and viewer. All data in transit is encrypted using TLS 1.3,
and data at rest is encrypted with AES-256.
"""


async def example_explicit_topics() -> None:
    checker = CompletenessChecker()  # reads config from environment

    report = await checker.check(
        answer=ANSWER_FROM_SOME_OTHER_MODEL.strip(),
        document_type="security architecture",
        expected_topics=[
            "Authentication",
            "Authorization",
            "Encryption",
            "Logging and Monitoring",
            "Functionality Overview",
            "Risks and Threat Model",
        ],
        auto_derive_topics=False,
    )

    print("=== Explicit topics ===")
    print(f"Completeness score: {report.completeness_score}/100")
    print(report.summary)
    print()
    for c in report.topic_coverage:
        print(f"{c.topic.name:<28} {c.status.value:<20} {c.quality.value}")
        print(f"    {c.explanation}")
    print()


async def example_auto_derived_topics() -> None:
    checker = CompletenessChecker()

    report = await checker.check(
        answer=ANSWER_FROM_SOME_OTHER_MODEL.strip(),
        question="Describe the security architecture of the system.",
        document_type="security architecture",
        auto_derive_topics=True,  # no expected_topics given -> tool infers them
    )

    print("=== Auto-derived topics ===")
    print(f"Completeness score: {report.completeness_score}/100")
    print(report.summary)
    print()
    for c in report.topic_coverage:
        print(f"{c.topic.name:<28} {c.status.value:<20} {c.quality.value}")


async def main() -> None:
    await example_explicit_topics()
    await example_auto_derived_topics()


if __name__ == "__main__":
    asyncio.run(main())
