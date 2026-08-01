"""Typed uAgent adapter for the evidence-aware discovery workflow."""

from __future__ import annotations

import sys
from pathlib import Path

from uagents import Agent, Context

sys.path.append(str(Path(__file__).parent.parent))

from agents.config import agent_kwargs
from exceptions import BioAgentError
from models.messages import DiscoveryWorkflowRequest, DiscoveryWorkflowResponse
from services.chembl_service import ChEMBLService
from services.chemistry_service import ChemistryService
from services.database_service import DatabaseService
from services.llm_service import LLMService
from services.workflow_service import DiscoveryWorkflowService

agent = Agent(**agent_kwargs("workflow", "DiscoveryWorkflowAgent", 8010))
service = DiscoveryWorkflowService(
    chemistry=ChemistryService(),
    database=DatabaseService(),
    evidence=ChEMBLService(),
    llm=LLMService(),
)


@agent.on_message(model=DiscoveryWorkflowRequest, replies=DiscoveryWorkflowResponse)
async def handle_request(ctx: Context, sender: str, msg: DiscoveryWorkflowRequest):
    try:
        result = service.discover(
            seed=msg.seed,
            input_type=msg.input_type,
            objective=msg.objective,
            target=msg.target,
            max_candidates=msg.max_candidates,
        )
        await ctx.send(sender, DiscoveryWorkflowResponse(status="success", run=result))
    except BioAgentError as exc:
        ctx.logger.warning("Discovery workflow rejected: %s", exc.message)
        await ctx.send(sender, DiscoveryWorkflowResponse(status="error", error=exc.message))
    except Exception:
        ctx.logger.exception("Discovery workflow failed unexpectedly")
        await ctx.send(
            sender,
            DiscoveryWorkflowResponse(status="error", error="Unexpected workflow failure."),
        )


if __name__ == "__main__":
    agent.run()
