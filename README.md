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
1. Clone the repo: `git clone https://github.com/dwan-ith/BioAgents.git`
2. Install Python deps: `pip install -r requirements.txt`
3. Optional: set `OPENAI_API_KEY` to enable OpenAI-primary analysis and generation.
   Without it, the API still runs with deterministic local fallback logic.
4. Run backend server: `python server.py`
5. Install frontend deps: `cd frontend && npm install`
6. Start frontend: `npm start`
7. Access dashboard at `http://localhost:3000`

The default Flask API does not require a uAgents Bureau. It imports the
committed `services/` package directly so a fresh clone can run immediately.

## Deploy on Vercel
This repository is configured for Vercel from the repo root:

- `vercel.json` builds the React app from `frontend/`.
- `api/index.py` exposes the Flask app as a Vercel Python Function.
- The frontend calls `/api` in production and `http://localhost:5000` in local React dev.

In Vercel project settings, use the repository root as the Root Directory and keep the detected
framework as "Other" if prompted. Add `OPENAI_API_KEY` as an environment variable only if you want
OpenAI-primary analysis; otherwise the local fallback still works. For local Vercel testing, use
Vercel CLI `48.2.10` or newer for Flask support.

## uAgents Runtime
Run these only if you want the standalone distributed-agent experiment:

   - `pip install -r requirements-agents.txt`
   - `python main.py` to start all agents in one Bureau, or
   - run agents in separate terminals:
   - `python agents/compound_agent.py`
   - `python agents/reaction_agent.py`
   - `python agents/research_agent.py`
   - `python agents/analysis_agent.py`
   - `python agents/database_agent.py`

For ASI:One integration, ensure agents are registered on Agentverse with Chat Protocol enabled.

## Tests
Run the backend regression suite:

```bash
python -m unittest discover -s tests -v
```
