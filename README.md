# BioAgents
Decentralized AI Agents for Synthetic Biology


## Overview
BioAgents is a multi-agent system where each molecule is an autonomous AI agent. Agents communicate using Fetch.ai's uAgents, reason with SingularityNET's MeTTa Knowledge Graphs, and collaborate on Agentverse. This project enables decentralized drug discovery by simulating molecular interactions, predicting reactions, and proposing new compounds.

## Features
- Autonomous agents for compounds, reactions, research, analysis, and database integration.
- MeTTa-based knowledge representation for molecular properties and reasoning.
- Inter-agent communication via Chat Protocol.
- React frontend with dashboard for visualizing agent interactions and molecular graphs.
- Integration with ASI:One for user queries.

## Tech Stack
- Backend: Python, uAgents, Hyperon (MeTTa), Flask (for frontend proxy).
- Frontend: React, Material-UI, D3.js.
- Knowledge: MeTTa files for graphs.

## Setup
1. Clone the repo: `git clone https://github.com/yourusername/BioAgents.git`
2. Install Python deps: `pip install -r requirements.txt`
3. Install frontend deps: `cd frontend && npm install`
4. Load MeTTa knowledge: Run `python knowledge/metta_handler.py` to initialize.
5. Run agents in separate terminals:
   - `python agents/compound_agent.py`
   - `python agents/reaction_agent.py`
   - `python agents/research_agent.py`
   - `python agents/analysis_agent.py`
   - `python agents/database_agent.py`
6. Run backend server: `python server.py`
7. Start frontend: `cd frontend && npm start`
8. Access dashboard at `http://localhost:3000`
9. For ASI:One integration, ensure agents are registered on Agentverse with Chat Protocol enabled.

