import React, { useState } from 'react';

import { postJSON } from './api';
import './app.css';

const DISCOVERY_DEFAULTS = {
  seed: 'aspirin',
  input_type: 'name',
  objective: 'Explore structurally valid analogs with balanced oral drug-like properties.',
  target: 'PTGS2',
  max_candidates: 6,
};

const REACTION_DEFAULT = {
  reactants: ['CC(=O)O', 'CO'],
  reaction_smarts: '[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5]',
};

const NAV_ITEMS = [
  { id: 'discovery', label: 'Discovery' },
  { id: 'compare', label: 'Compare' },
  { id: 'reaction', label: 'Reaction' },
];

export default function App() {
  const [view, setView] = useState('discovery');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const run = async (path, payload, kind) => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await postJSON(path, payload);
      setResult({ kind, data });
      setHistory((current) => [
        {
          id: data.run_id || crypto.randomUUID(),
          kind,
          label: runLabel(kind, data),
          status: data.status || data.assessment || 'COMPLETED',
          createdAt: data.created_at || new Date().toISOString(),
          data,
        },
        ...current,
      ].slice(0, 8));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const switchView = (nextView) => {
    setView(nextView);
    setError('');
    setResult(null);
  };

  return (
    <div className="app-shell">
      <Header />
      <aside className="sidebar">
        <p className="sidebar-label">Workspace</p>
        <nav aria-label="Workspace">
          {NAV_ITEMS.map(({ id, label }) => (
            <button
              className={`nav-item ${view === id ? 'active' : ''}`}
              key={id}
              onClick={() => switchView(id)}
              type="button"
            >
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-canvas">
        <div className="workspace-header">
          <div className="workspace-title-block">
            <h1>{pageTitle(view)}</h1>
            <p className="workspace-description">{pageDescription(view)}</p>
          </div>
          {history.length > 0 && <HistoryMenu history={history} onSelect={(item) => setResult({ kind: item.kind, data: item.data })} />}
        </div>

        <div className="workspace-grid">
          <section className="control-pane" aria-label="Experiment controls">
            {view === 'discovery' && <DiscoveryForm loading={loading} onRun={(payload) => run('/workflows/discovery', payload, 'discovery')} />}
            {view === 'compare' && <ComparisonForm loading={loading} onRun={(payload) => run('/workflows/compare', payload, 'compare')} />}
            {view === 'reaction' && <ReactionForm loading={loading} onRun={(payload) => run('/workflows/reaction', payload, 'reaction')} />}
            {error && <ErrorBanner message={error} onClose={() => setError('')} />}
            {loading && <LoadingState view={view} />}
          </section>
          {!loading && result && (
            <section className="output-pane" aria-label="Workflow output">
              {result.kind === 'discovery' && <DiscoveryResult result={result.data} />}
              {result.kind === 'compare' && <ComparisonResult result={result.data} />}
              {result.kind === 'reaction' && <ReactionResult result={result.data} />}
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

function Header() {
  return (
    <header className="topbar">
      <div className="brand-copy">
        <span>BioAgents</span>
      </div>
    </header>
  );
}

function DiscoveryForm({ loading, onRun }) {
  const [form, setForm] = useState(DISCOVERY_DEFAULTS);
  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const submit = (event) => {
    event.preventDefault();
    onRun({ ...form, max_candidates: Number(form.max_candidates) });
  };

  return (
    <form className="run-spec" onSubmit={submit}>
      <div className="spec-header">
        <div className="spec-title"><strong>Discovery parameters</strong></div>
        <button className="primary-button" type="submit" disabled={loading || !form.seed.trim() || form.objective.trim().length < 5}>
          Run discovery
        </button>
      </div>
      <div className="form-grid discovery-grid">
        <Field label="Seed compound" hint="Resolvable name or a valid molecular structure" composite wide>
          <div className="compound-input-row">
            <SegmentedControl
              label="Seed input format"
              value={form.input_type}
              options={[{ value: 'name', label: 'Name' }, { value: 'smiles', label: 'SMILES' }]}
              onChange={(value) => update('input_type', value)}
            />
            <input
              aria-label="Seed compound"
              value={form.seed}
              onChange={(event) => update('seed', event.target.value)}
              placeholder={form.input_type === 'name' ? 'e.g. aspirin' : 'e.g. CC(=O)Oc1ccccc1C(=O)O'}
              required
            />
          </div>
        </Field>
        <Field label="Target context">
          <input value={form.target} onChange={(event) => update('target', event.target.value)} placeholder="e.g. PTGS2" />
        </Field>
        <Field label="Candidate count">
          <select value={form.max_candidates} onChange={(event) => update('max_candidates', event.target.value)}>
            {[3, 4, 6, 8, 10, 12].map((count) => <option key={count} value={count}>{count}</option>)}
          </select>
        </Field>
        <Field label="Optimization objective" wide>
          <textarea value={form.objective} onChange={(event) => update('objective', event.target.value)} rows={3} required />
        </Field>
      </div>
    </form>
  );
}

function ComparisonForm({ loading, onRun }) {
  const [form, setForm] = useState({ left: 'aspirin', right: 'acetaminophen', input_type: 'name' });
  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  return (
    <form className="run-spec" onSubmit={(event) => { event.preventDefault(); onRun(form); }}>
      <div className="spec-header">
        <div className="spec-title"><strong>Comparison parameters</strong></div>
        <button className="primary-button" type="submit" disabled={loading || !form.left.trim() || !form.right.trim()}>
          Compare evidence
        </button>
      </div>
      <div className="form-grid compare-grid">
        <div className="segment-field">
          <span className="field-label">Input format</span>
          <SegmentedControl
            label="Comparison input format"
            value={form.input_type}
            options={[{ value: 'name', label: 'Names' }, { value: 'smiles', label: 'SMILES' }]}
            onChange={(value) => update('input_type', value)}
          />
        </div>
        <Field label="Compound A"><input value={form.left} onChange={(event) => update('left', event.target.value)} required /></Field>
        <Field label="Compound B"><input value={form.right} onChange={(event) => update('right', event.target.value)} required /></Field>
      </div>
    </form>
  );
}

function ReactionForm({ loading, onRun }) {
  const [form, setForm] = useState(REACTION_DEFAULT);
  const updateReactant = (index, value) => setForm((current) => ({
    ...current,
    reactants: current.reactants.map((reactant, itemIndex) => itemIndex === index ? value : reactant),
  }));
  const addReactant = () => setForm((current) => ({ ...current, reactants: [...current.reactants, ''] }));
  const removeReactant = (index) => setForm((current) => ({
    ...current,
    reactants: current.reactants.filter((_, itemIndex) => itemIndex !== index),
  }));
  return (
    <form className="run-spec" onSubmit={(event) => { event.preventDefault(); onRun(form); }}>
      <div className="spec-header">
        <div className="spec-title"><strong>Reaction parameters</strong></div>
        <button className="primary-button" type="submit" disabled={loading || form.reactants.some((item) => !item.trim()) || !form.reaction_smarts.trim()}>
          Apply transform
        </button>
      </div>
      <div className="reaction-form-grid">
        <div>
          <div className="section-label-row">
            <span className="field-label">Reactant SMILES</span>
            <button className="text-button" type="button" onClick={addReactant} disabled={form.reactants.length >= 4}>Add reactant</button>
          </div>
          <div className="reactant-list">
            {form.reactants.map((reactant, index) => (
              <div className="reactant-row" key={index}>
                <span>{index + 1}</span>
                <input aria-label={`Reactant ${index + 1}`} value={reactant} onChange={(event) => updateReactant(index, event.target.value)} required />
                <button className="text-button quiet" type="button" onClick={() => removeReactant(index)} disabled={form.reactants.length === 1}>Remove</button>
              </div>
            ))}
          </div>
        </div>
        <Field label="Reaction SMARTS">
          <textarea
            className="mono"
            value={form.reaction_smarts}
            onChange={(event) => setForm((current) => ({ ...current, reaction_smarts: event.target.value }))}
            rows={5}
            required
          />
        </Field>
      </div>
    </form>
  );
}

function DiscoveryResult({ result }) {
  return (
    <div className="results-stack">
      <RunSummary result={result} />
      <section className="seed-evidence-grid">
        <StructurePanel profile={result.seed} title="Standardized seed" subtitle={result.identity?.resolution_source} />
        <EvidencePanel evidence={result.evidence} />
      </section>
      <section className="result-section">
        <SectionHeading
          title="Candidate hypotheses"
          meta={`${result.candidates?.length || 0} validated structures`}
        />
        {result.candidates?.length ? (
          <div className="candidate-list">
            {result.candidates.map((candidate) => <CandidateRow key={candidate.canonical_smiles} candidate={candidate} />)}
          </div>
        ) : <EmptyEvidence message="No valid analog hypotheses survived structure validation and deduplication." />}
      </section>
    </div>
  );
}

function ComparisonResult({ result }) {
  return (
    <div className="results-stack">
      <div className="assessment-banner">
        <div><strong>{humanize(result.assessment)}</strong><span>{result.interpretation}</span></div>
      </div>
      <section className="comparison-results">
        <StructurePanel profile={result.left.structure} title={result.left.identity?.query || 'Compound A'} subtitle={result.left.identity?.resolution_source} />
        <div className="similarity-meter">
          <span>2D similarity</span>
          <strong>{formatNumber(result.structure_comparison?.tanimoto_similarity, 3)}</strong>
          <small>{result.structure_comparison?.interpretation}</small>
        </div>
        <StructurePanel profile={result.right.structure} title={result.right.identity?.query || 'Compound B'} subtitle={result.right.identity?.resolution_source} />
      </section>
      <section className="result-section">
        <SectionHeading title="Shared assay targets" meta={`${result.shared_targets?.length || 0} overlaps`} />
        {result.shared_targets?.length ? <TargetTable targets={result.shared_targets} comparison /> : <EmptyEvidence message="No supported target overlap was present in the bounded ChEMBL records retrieved." />}
      </section>
    </div>
  );
}

function ReactionResult({ result }) {
  return (
    <div className="results-stack">
      <div className="assessment-banner">
        <div><strong>{humanize(result.status)}</strong><span>{result.limitation}</span></div>
      </div>
      <section className="result-section">
        <SectionHeading title="Enumerated products" meta={`${result.product_set_count} unique product sets`} />
        <div className="product-grid">
          {(result.products || []).map((product, index) => (
            <article className="product-item" key={product.product_smiles}>
              <span className="rank-number">{String(index + 1).padStart(2, '0')}</span>
              {product.structure_svg ? <StructureSvg svg={product.structure_svg} /> : <div className="multi-product">Multiple products</div>}
              <code>{product.product_smiles}</code>
            </article>
          ))}
        </div>
        {!result.products?.length && <EmptyEvidence message="The reactants did not match the supplied reaction transform." />}
      </section>
    </div>
  );
}

function RunSummary({ result }) {
  return (
    <div className="run-summary">
      <div>
        <span className="run-kicker">Run complete</span>
        <h2>{result.objective}</h2>
        <p>{result.target ? `Target context: ${result.target}` : 'No target context supplied'}</p>
      </div>
      <div className="run-meta">
        <StatusPill status={result.status} />
        <code>{result.run_id}</code>
      </div>
    </div>
  );
}

function StructurePanel({ profile, title, subtitle }) {
  if (!profile) return null;
  const descriptors = profile.descriptors || {};
  return (
    <article className="structure-panel">
      <div className="panel-heading">
        <div><h3>{title}</h3><span>{subtitle}</span></div>
        <StatusPill status={profile.quality_gates?.status || 'UNKNOWN'} />
      </div>
      <StructureSvg svg={profile.structure_svg} />
      <code className="smiles-line">{profile.canonical_smiles}</code>
      <div className="metric-grid">
        <Metric label="MW" value={formatNumber(descriptors.molecular_weight, 1)} unit="g/mol" />
        <Metric label="cLogP" value={formatNumber(descriptors.clogp, 2)} />
        <Metric label="TPSA" value={formatNumber(descriptors.tpsa, 1)} unit="Å²" />
        <Metric label="QED" value={formatNumber(descriptors.qed, 3)} />
        <Metric label="HBD / HBA" value={`${descriptors.h_bond_donors ?? '—'} / ${descriptors.h_bond_acceptors ?? '—'}`} />
        <Metric label="Rotors" value={descriptors.rotatable_bonds ?? '—'} />
      </div>
      {(profile.quality_gates?.warnings || []).map((warning) => (
        <div className="inline-warning" key={warning}>{warning}</div>
      ))}
    </article>
  );
}

function EvidencePanel({ evidence }) {
  const molecule = evidence?.molecule;
  return (
    <article className="evidence-panel">
      <div className="panel-heading">
        <div><h3>Bioactivity evidence</h3><span>Live ChEMBL records</span></div>
        <StatusPill status={evidence?.evidence_grade || 'NONE'} />
      </div>
      {molecule ? (
        <>
          <div className="identity-block">
            <div><span>ChEMBL ID</span><strong>{molecule.chembl_id}</strong></div>
            <div><span>Preferred name</span><strong>{molecule.preferred_name || 'Not assigned'}</strong></div>
            <div><span>Max phase</span><strong>{molecule.max_phase ?? '—'}</strong></div>
            <div><span>Assays returned</span><strong>{evidence.activity_count_returned ?? 0}</strong></div>
          </div>
          <TargetTable targets={evidence.targets || []} />
        </>
      ) : <EmptyEvidence message={evidence?.reason || 'No matching ChEMBL molecule record was found.'} compact />}
      {(evidence?.provenance || []).map((source) => (
        <a className="source-link" href={source.url} target="_blank" rel="noreferrer" key={source.url}>
          {source.provider}: {source.resource}
        </a>
      ))}
    </article>
  );
}

function CandidateRow({ candidate }) {
  const descriptors = candidate.descriptors || {};
  return (
    <article className="candidate-row">
      <div className="candidate-rank"><span>{String(candidate.rank).padStart(2, '0')}</span><strong>{formatNumber(candidate.triage?.score, 3)}</strong><small>triage</small></div>
      <div className="candidate-structure"><StructureSvg svg={candidate.structure_svg} /></div>
      <div className="candidate-main">
        <div className="candidate-title-row">
          <div><h3>{candidate.name}</h3><span>{humanize(candidate.generation_source)}</span></div>
          <StatusPill status={candidate.quality_gates?.status} />
        </div>
        <code>{candidate.canonical_smiles}</code>
        <p>{candidate.hypothesis}</p>
        <div className="candidate-facts">
          <span>QED <strong>{formatNumber(descriptors.qed, 3)}</strong></span>
          <span>MW <strong>{formatNumber(descriptors.molecular_weight, 1)}</strong></span>
          <span>Similarity <strong>{formatNumber(candidate.similarity_to_seed, 3)}</strong></span>
          <span>Alerts <strong>{candidate.alerts?.length || 0}</strong></span>
        </div>
      </div>
      <div className="candidate-rationale">
        <span>Structural change</span><p>{candidate.intended_change}</p>
        <span>Rationale</span><p>{candidate.rationale}</p>
      </div>
    </article>
  );
}

function TargetTable({ targets, comparison = false }) {
  if (!targets?.length) return <EmptyEvidence message="No normalized target records in this result window." compact />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Target</th><th>ID</th>{comparison ? <><th>A</th><th>B</th></> : <><th>Max pChEMBL</th><th>Records</th></>}</tr></thead>
        <tbody>
          {targets.slice(0, 8).map((target) => (
            <tr key={target.target_chembl_id}>
              <td>{target.target_name}</td>
              <td><code>{target.target_chembl_id}</code></td>
              {comparison ? <><td>{target.left_max_pchembl}</td><td>{target.right_max_pchembl}</td></> : <><td>{target.max_pchembl_value}</td><td>{target.measurement_count}</td></>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Field({ label, hint, children, wide = false, composite = false }) {
  const Tag = composite ? 'div' : 'label';
  return <Tag className={`field ${wide ? 'wide' : ''}`}><span className="field-label">{label}</span>{children}{hint && <small>{hint}</small>}</Tag>;
}

function SegmentedControl({ label, value, options, onChange }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button aria-pressed={value === option.value} className={value === option.value ? 'selected' : ''} type="button" key={option.value} onClick={() => onChange(option.value)}>{option.label}</button>
      ))}
    </div>
  );
}

function SectionHeading({ title, meta }) {
  return <div className="section-heading"><div><h2>{title}</h2></div>{meta && <span>{meta}</span>}</div>;
}

function StructureSvg({ svg }) {
  if (!svg) return <div className="structure-placeholder">No structure available</div>;
  return <div className="structure-svg" dangerouslySetInnerHTML={{ __html: svg }} />;
}

function Metric({ label, value, unit }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong>{unit && <small>{unit}</small>}</div>;
}

function StatusPill({ status }) {
  const normalized = String(status || 'UNKNOWN').toLowerCase();
  return <span className={`status-pill ${normalized}`}>{humanize(status || 'UNKNOWN')}</span>;
}

function ErrorBanner({ message, onClose }) {
  return <div className="error-banner"><span>{message}</span><button className="text-button quiet" onClick={onClose}>Dismiss</button></div>;
}

function LoadingState({ view }) {
  return <div className="loading-state"><div><strong>Running {view} workflow</strong><span>Validating structures and gathering evidence</span></div></div>;
}

function EmptyEvidence({ message, compact = false }) {
  return <div className={`empty-evidence ${compact ? 'compact' : ''}`}><span>{message}</span></div>;
}

function HistoryMenu({ history, onSelect }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="history-menu">
      <button className="secondary-button" type="button" onClick={() => setOpen((value) => !value)}>Recent runs</button>
      {open && <div className="history-popover">{history.map((item) => <button key={item.id} type="button" onClick={() => { onSelect(item); setOpen(false); }}><span>{item.label}</span><small>{humanize(item.status)}</small></button>)}</div>}
    </div>
  );
}

function pageTitle(view) {
  if (view === 'compare') return 'Compare structures against evidence.';
  if (view === 'reaction') return 'Enumerate an explicit transformation.';
  return 'Design analogs from a validated seed.';
}

function pageDescription(view) {
  if (view === 'compare') return 'Inspect 2D similarity beside retrieved assay-target overlap.';
  if (view === 'reaction') return 'Validate reactants and enumerate products from a reaction SMARTS rule.';
  return 'Resolve a structure, retrieve evidence, and rank chemically valid analogs.';
}

function runLabel(kind, data) {
  if (kind === 'discovery') return data.seed?.name || data.seed?.formula || 'Discovery run';
  if (kind === 'compare') return 'Compound comparison';
  return `${data.product_set_count || 0} reaction products`;
}

function humanize(value) {
  return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatNumber(value, digits = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : '—';
}
