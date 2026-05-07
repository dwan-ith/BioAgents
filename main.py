"""
BioAgents Bureau Runner
=======================
Starts all standalone agents in a single process using the uAgents Bureau.
"""

from uagents import Bureau

from agents.compound_agent import agent as compound_agent
from agents.reaction_agent import agent as reaction_agent
from agents.research_agent import agent as research_agent
from agents.analysis_agent import agent as analysis_agent
from agents.database_agent import agent as database_agent
from agents.llm_agent import agent as llm_agent
from agents.feedback_agent import agent as feedback_agent
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    print("Starting BioAgents Bureau...")
    bureau = Bureau(endpoint=["http://localhost:8000/submit"], port=8000)
    
    bureau.add(compound_agent)
    bureau.add(reaction_agent)
    bureau.add(research_agent)
    bureau.add(analysis_agent)
    bureau.add(database_agent)
    bureau.add(llm_agent)
    bureau.add(feedback_agent)
    
    bureau.run()
