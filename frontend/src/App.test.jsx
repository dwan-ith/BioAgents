import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';
import { postJSON } from './api';

vi.mock('./api', () => ({
  postJSON: vi.fn(),
}));

const discoveryResult = {
  schema_version: 'bioagents.discovery.v2',
  run_id: 'run-123',
  created_at: '2026-08-01T00:00:00Z',
  status: 'CANDIDATES_PROPOSED',
  objective: 'Improve property balance.',
  target: 'PTGS2',
  seed: {
    name: 'Aspirin',
    canonical_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
    structure_svg: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
    descriptors: {
      molecular_weight: 180.159,
      clogp: 1.31,
      tpsa: 63.6,
      qed: 0.55,
      h_bond_donors: 1,
      h_bond_acceptors: 3,
      rotatable_bonds: 2,
    },
    quality_gates: { status: 'PASS', warnings: [] },
  },
  identity: { resolution_source: 'PubChem PUG REST' },
  evidence: {
    evidence_grade: 'MODERATE',
    molecule: { chembl_id: 'CHEMBL25', preferred_name: 'ASPIRIN', max_phase: 4 },
    activity_count_returned: 12,
    targets: [{ target_chembl_id: 'CHEMBL230', target_name: 'COX-2', max_pchembl_value: 7.1, measurement_count: 3 }],
    provenance: [],
  },
  candidates: [{
    rank: 1,
    name: 'Analog 1',
    canonical_smiles: 'O=C(O)c1ccccc1C(=O)O',
    structure_svg: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
    generation_source: 'rdkit-brics-local',
    intended_change: 'Fragment recombination.',
    rationale: 'Deterministic local proposal.',
    hypothesis: 'Property balance may change.',
    similarity_to_seed: 0.71,
    alerts: [],
    descriptors: { qed: 0.62, molecular_weight: 166.1 },
    quality_gates: { status: 'PASS' },
    triage: { score: 0.72 },
  }],
  workflow: { execution_mode: 'cooperative in-process agents', trace: [{ agent: 'StructureAgent', operation: 'resolve seed', status: 'completed', duration_ms: 12.2 }] },
  decision_boundary: { supported: ['structure validation'], not_claimed: ['clinical safety'] },
};

describe('BioAgents workbench', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the discovery workflow as the primary screen', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /Design analogs from a validated seed/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Run discovery/i })).toBeInTheDocument();
    expect(screen.queryByText('System ready')).not.toBeInTheDocument();
    expect(screen.queryByText('Research use only')).not.toBeInTheDocument();
  });

  it('submits the rigorous workflow contract and renders evidence and candidates', async () => {
    postJSON.mockResolvedValue(discoveryResult);
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /Run discovery/i }));
    await waitFor(() => expect(postJSON).toHaveBeenCalledWith('/workflows/discovery', expect.objectContaining({
      seed: 'aspirin',
      input_type: 'name',
      target: 'PTGS2',
      max_candidates: 6,
    })));
    expect(await screen.findByText('Candidate hypotheses')).toBeInTheDocument();
    expect(screen.getByText('CHEMBL25')).toBeInTheDocument();
    expect(screen.getByText('Analog 1')).toBeInTheDocument();
    expect(screen.queryByText('Workflow trace')).not.toBeInTheDocument();
  });

  it('switches to an explicit reaction-rule workflow', () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: 'Reaction' }));
    expect(screen.getByRole('heading', { name: /Enumerate an explicit transformation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Apply transform/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Reactant 1')).toHaveValue('CC(=O)O');
  });
});
