"""Minimal end-to-end example, using the exact scenario this tool was
designed around: "research 3 cloud architecture options, compare them, find
the costs, and recommend one."

Prerequisites:
    pip install -e ../packages/core-py[anthropic]
    export ANTHROPIC_API_KEY=...
    export SUPERVISOR_LLM_PROVIDER=anthropic
    # optionally: export SUPERVISOR_SEARCH_PROVIDER=tavily and TAVILY_API_KEY=...
    #   to enable web verification of the "pricing date" criterion

Run:
    python python_quickstart.py
"""
import asyncio

from ai_workflow_supervisor import WorkflowSupervisor


TASK = "Research 3 cloud architecture options, compare them, find the costs, and recommend one."

# An INCOMPLETE agent output on purpose: it skips a third alternative in
# depth, never mentions security, and doesn't date the pricing. Nothing here
# is factually wrong — it's just an unfinished job, which is exactly what
# this tool exists to catch before the agent calls it "done."
INCOMPLETE_AGENT_OUTPUT = """
We looked at AWS and GCP for the new service. AWS EC2 t3.micro instances
run about $0.0104/hr on-demand, while GCP's e2-micro is roughly $0.0084/hr.
Both platforms offer autoscaling and managed Kubernetes (EKS and GKE
respectively), so scalability is comparable. Azure was also considered
briefly. Overall, we recommend GCP for the lower compute cost.
"""

# A more thorough version of the same task, addressing every criterion.
COMPLETE_AGENT_OUTPUT = """
We compared three cloud providers for the new service: AWS, GCP, and Azure.

Pricing (as of March 2025, on-demand, us-east/us-central region):
- AWS EC2 t3.micro: $0.0104/hr
- GCP e2-micro: $0.0084/hr
- Azure B1s: $0.0104/hr

Scalability: all three offer managed Kubernetes (EKS, GKE, AKS) with
autoscaling; GCP's autoscaler had the fastest scale-up in our benchmark.

Security: all three support VPC isolation, IAM-based access control, and
encryption at rest by default. AWS has the most mature compliance
certification set (relevant for our SOC 2 requirements).

Recommendation: GCP, for the best balance of cost and autoscaling
performance, with AWS as a fallback if compliance certification breadth
becomes a hard requirement.
"""


async def run_example(label: str, agent_output: str) -> None:
    supervisor = WorkflowSupervisor()  # reads config from environment

    report = await supervisor.supervise(
        task=TASK,
        agent_output=agent_output.strip(),
    )

    print(f"=== {label} ===")
    print(f"task_complete:    {report.task_complete}")
    print(f"completion_score: {report.completion_score}/100")
    print(report.summary)
    if report.blocking_failures:
        print("Blocking failures:")
        for failure in report.blocking_failures:
            print(f"  - {failure}")
    print()
    for r in report.item_results:
        marker = "PASS" if r.status.value == "satisfied" else ("PART" if r.status.value == "partially_satisfied" else "FAIL")
        req = "required" if r.item.required else "optional"
        print(f"[{marker:>4} | {req:>8}] {r.item.description}")
        print(f"           {r.explanation}")
    print()


async def main() -> None:
    await run_example("Incomplete output", INCOMPLETE_AGENT_OUTPUT)
    await run_example("Complete output", COMPLETE_AGENT_OUTPUT)


if __name__ == "__main__":
    asyncio.run(main())
