# BioAgents

## Overview

BioAgents is a decentralized, evidence-aware molecular discovery workbench designed to operate at the intersection of computational chemistry and language-model-based reasoning. It systematizes the process of drug-analogue postulation by strictly enforcing deterministic molecular standardizations, querying verified public assay databases, executing explicit reaction rules, and proposing machine-validated structural hypotheses. 

This repository constitutes a research implementation and is not a clinical decision-support system. It makes no deterministic claims regarding binding affinity, in vivo toxicity, clinical drug-drug interactions, reaction yields, synthetic feasibility, or definitive experimental success. Its primary domain is strictly bound to computational hypothesis formulation and evidence retrieval.

## Capabilities

### 1. The Discovery Workflow

The engine executes a rigorous multi-agent pipeline to extrapolate candidate molecules from a given seed structure:

1. **Resolution & Representation**: Resolves compound nomenclature through the PubChem nomenclature standard or directly accepts canonicalized SMILES representations.
2. **Canonicalization**: Imposes strict structure sanitization and normalization using the RDKit chemoinformatics framework.
3. **Property Gatekeeping**: Computes deterministic 2D descriptors, constructs Morgan fingerprints, evaluates Quantitative Estimate of Druglikeness (QED), applies Lipinski Rule-of-Five and Veber filters, and flags PAINS/BRENK structural alerts.
4. **Evidence Retrieval**: Maps standard InChIKeys directly to the ChEMBL ontology, synchronously pulling bounded assay profiles, target evidence, and immutable provenance URLs.
5. **Generative Hypothesis Engine**: Interfaces with external Large Language Models (LLMs) configured as the primary generation heuristic, when enabled, to synthesize conceptually justifiable analogue hypotheses.
6. **Integrity Validation**: Strictly rejects malformed, topologically disconnected, isomorphic, or chemically inviable analogue structures before inclusion in the output result set.
7. **Deterministic Fallback (BRICS)**: Compensates for upstream generation failures by dynamically employing RDKit-based BRICS (Breaking of Retrosynthetically Interesting Chemical Substructures) fragmentation and recombination of the seed molecule.
8. **Triage Scoring**: Assigns a triage score derived from a composite heuristic of QED scores, structural similarity (Tanimoto coefficients), and deterministic property gates. This metric strictly represents a prioritization heuristic, not pharmacological activity.
9. **Traceability**: Delivers a fully resolved execution trace encapsulating timings, system provenance, failure counts, and rigorously circumscribed capability claims.

### 2. Empirical Compound Comparison

The comparison subsystems compute precise deterministic 2D topological overlaps and descriptor variances between arbitrary molecular inputs. It cross-references the independently retrieved ChEMBL target assays for both compounds, reporting corroborated target overlaps as potential mechanistic intersections. Absence of overlapping targets is explicitly bounded as `INSUFFICIENT_EVIDENCE`, actively avoiding false confirmations of non-interaction.

### 3. Transformation and Reaction Rules

BioAgents exposes engines for explicit chemical transformations. Operating strictly on formalized RDKit reaction SMARTS matrices and reactant SMILES structures, the agent validates valency, sequentially applies transformations, forces chemical sanitization of outputs, eliminates symmetrical duplicates, and returns enumerations. It operates agnostically of inferred experimental conditions, predicted yields, or catalyst selection parameters.

## Agent System Architecture

The fundamental HTTP runtime relies on cooperative, synchronous abstractions to maintain reliability in stateless and serverless infrastructures:

* **OrchestratorAgent**: Orchestrates cross-agent lifecycle management for discovery, comparative, and reaction procedures.
* **ChemistryAgent**: Manages exhaustive structural validation, RDKit integrations, descriptor computations, and geometric evaluation.
* **EvidenceAgent**: Manages ChEMBL querying logic, payload deserialization, and bounding of empirical bioactivity records.
* **DatabaseAgent**: Resolves molecular queries through PubChem subsystems to retrieve validated identities and external parameter constants.
* **LLMAgent**: Bridges requests to language model providers (e.g., OpenAI) for generative heuristics, equipped with automated protocol degradation functions.
* **Legacy Compatibility**: Houses legacy catalyst and enzyme agent archetypes referencing the initial MeTTa knowledge-base design.

For distributed topologies, the system includes a `uAgents` integration allowing structured IPC bridging over typed message protocols (`DiscoveryWorkflowRequest` / `DiscoveryWorkflowResponse`), permitting cross-cluster discovery. BioAgents transparently specifies the active execution mode in outgoing payloads.

## System Interfaces and Application Programming Interface (API)

Primary Web Endpoints:

```text
GET  /api/health
GET  /api/capabilities
GET  /api/agents/status
POST /api/workflows/discovery
POST /api/workflows/compare
POST /api/workflows/reaction
```

Standard Discovery Request Structure:

```json
{
  "seed": "aspirin",
  "input_type": "name",
  "objective": "Explore structurally valid analogues with balanced oral drug-like properties.",
  "target": "PTGS2",
  "max_candidates": 6
}
```

The system degrades gracefully. Standalone operations against SMILES matrices function entirely offline. LLM unavailability, API malformation, or network timeouts automatically resolve to deterministic offline BRICS permutation strategies without critical process interruption.

## Deployment and Administration

### Environment Prerequisites

The system is tested against Python 3.10+ and Node.js 22.12+.

### Initialization

```bash
git clone https://github.com/dwan-ith/BioAgents.git
cd BioAgents
python -m pip install -r requirements.txt
cp .env.example .env
python server.py
```

Frontend Initialization:

```bash
cd frontend
npm ci
npm start
```

Access the dashboard natively via `http://localhost:3000`. 
Environment variables (e.g., `OPENAI_API_KEY`, `OPENAI_MODEL`) must exclusively reside on secure backends; the client boundary does not negotiate secrets.

### Distributed `uAgents` Runtime

```bash
python -m pip install -r requirements-agents.txt
python main.py
```

Administrators must populate private `BIOAGENTS_<AGENT>_SEED` identifiers via environment secrets prior to production registration. Default repository identities encapsulate public primitives strictly for testing.

### Stateless Edge Infrastructure (Vercel)

The system deploys natively via `vercel.json`, facilitating automatic Vite frontend builds and transparently routing `/api/*` requests to the Flask lambda. Configurations dictate an arbitrary maximum timeout limit (defaulting to 60 seconds) to ensure complex remote evidence lookups complete reliably. Log retention across cold-starts relies on persistent off-site logging solutions.

## Quality Assurance and Regression Diagnostics

The codebase includes comprehensive test vectors analyzing failure-mode responses for molecular abstractions.

```bash
python -m unittest discover -s tests -v
python -m ruff check server.py agents services knowledge models tests api

cd frontend
npm ci
npm test
npm run build
```

The coverage matrices validate parsing determinism, descriptor fidelity, uniqueness filters, transformation constraints, evidence sanitation, and Vercel boundary specifications.

## Scientific and Medical Disclaimers

The structural candidates materialized by this framework explicitly constitute computational hypotheses. Toxicological alerts identify generalized structural risks and are not specific toxicity predictors. Remote bioactivity records from ChEMBL reflect heterogeneous methodologies necessitating rigorous manual assessment. Topological similarity profiles never guarantee pharmacological safety. Absolute verification protocols necessitate domain expert interrogation, comprehensive synthesis planning, and definitive ex vivo/in vivo validation paradigms.
