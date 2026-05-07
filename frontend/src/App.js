import React, { useState } from 'react';
import {
  Container, Typography, TextField, Button, Paper, Grid,
  Tabs, Tab, Box, CircularProgress, Select, MenuItem,
  InputLabel, FormControl, Alert, Chip, Divider,
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import MolecularGraph from './components/MolecularGraph';
import AgentDashboard from './components/AgentDashboard';
import CompoundCard from './components/CompoundCard';
import { postJSON } from './api';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#ce93d8' },
    background: { default: '#121212', paper: '#1e1e1e' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", sans-serif',
  },
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);

  // Inputs
  const [compoundQuery, setCompoundQuery] = useState('');
  const [lookupQuery, setLookupQuery] = useState('');
  const [reactionMol1, setReactionMol1] = useState('');
  const [reactionMol2, setReactionMol2] = useState('');
  const [discoverClass, setDiscoverClass] = useState('');
  const [discoverSimilar, setDiscoverSimilar] = useState('');
  const [discoverMinActivity, setDiscoverMinActivity] = useState('');
  const [discoverMinSelectivity, setDiscoverMinSelectivity] = useState('');

  // Feedback form
  const [fbMolecule, setFbMolecule] = useState('');
  const [fbActivity, setFbActivity] = useState('');
  const [fbSelectivity, setFbSelectivity] = useState('');

  // Results
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultType, setResultType] = useState('compound');

  const handleTabChange = (_, newValue) => {
    setTabValue(newValue);
    setResult(null);
  };

  const submitQuery = async (path, payload, type) => {
    setLoading(true);
    setResult(null);
    setResultType(type);
    try {
      const data = await postJSON(path, payload);
      setResult(data);
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const hasDiscoveryFilter = Boolean(
    discoverClass
    || discoverSimilar.trim()
    || discoverMinActivity.trim()
    || discoverMinSelectivity.trim()
  );

  const runDiscovery = () => {
    const payload = {
      type: 'discover',
      criterion: 'activity_score',
      order: 'desc',
    };
    if (discoverClass) payload.target_class = discoverClass;
    if (discoverSimilar.trim()) payload.similar_to = discoverSimilar.trim();
    if (discoverMinActivity.trim()) payload.min_activity = parseFloat(discoverMinActivity);
    if (discoverMinSelectivity.trim()) payload.min_selectivity = parseFloat(discoverMinSelectivity);
    submitQuery('/query', payload, 'discover');
  };

  // ---- Result renderers ----

  const renderResult = () => {
    if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}><CircularProgress /></Box>;
    if (!result) return null;
    if (result.error) return <Alert severity="error" sx={{ mt: 2 }}>{result.error}</Alert>;

    if (resultType === 'compound' || resultType === 'lookup') {
      return <CompoundCard compound={result} resultType={resultType} />;
    }

    if (resultType === 'interaction') {
      const riskColor = result.risk_level === 'High' ? '#ff5252' : (result.risk_level === 'Moderate' ? '#ffb74d' : '#4caf50');
      return (
        <Paper elevation={4} style={{ padding: '20px', backgroundColor: '#2a2a2a', marginTop: '20px', borderRadius: '12px' }}>
          {result.mode && (
            <Alert severity={result.mode === 'openai-primary' ? 'success' : 'info'} sx={{ mb: 2 }}>
              {result.mode === 'openai-primary'
                ? `OpenAI primary analysis${result.openai_model ? ` (${result.openai_model})` : ''}`
                : `Local analysis${result.fallback_reason ? `: ${result.fallback_reason}` : ''}`}
            </Alert>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="h6" style={{ color: '#90caf9' }}>
              {result.compound_1} ↔ {result.compound_2}
            </Typography>
            <Chip
              label={result.risk_level || 'Unknown'}
              size="small"
              style={{
                backgroundColor: riskColor,
                color: '#fff',
                fontWeight: 'bold',
              }}
            />
          </Box>

          {/* Explicit interactions */}
          {Array.isArray(result.explicit_interactions) && result.explicit_interactions.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" style={{ color: '#ffb74d', marginBottom: '6px' }}>Explicit Interactions</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {result.explicit_interactions.map((ix, i) => {
                  const sevColor = ix.severity === 'high' ? '#ff5252' : ix.severity === 'moderate' ? '#ffb74d' : '#4caf50';
                  return (
                    <Chip
                      key={i}
                      label={`${ix.drug} — ${(ix.effect || '').replace(/_/g, ' ')} (${ix.severity})`}
                      size="small"
                      variant="outlined"
                      style={{ borderColor: sevColor, color: sevColor }}
                    />
                  );
                })}
              </Box>
            </Box>
          )}

          {/* Shared targets */}
          {Array.isArray(result.shared_targets) && result.shared_targets.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" style={{ color: '#90caf9', marginBottom: '6px' }}>Shared Targets</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {result.shared_targets.map((t, i) => (
                  <Chip key={i} label={t.replace(/_/g, ' ')} size="small" style={{ backgroundColor: '#333', color: '#fff' }} />
                ))}
              </Box>
            </Box>
          )}

          {/* Warnings */}
          {Array.isArray(result.warnings) && result.warnings.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="subtitle2" style={{ color: '#888', marginBottom: '4px' }}>Warnings</Typography>
              <ul style={{ color: '#ccc', marginTop: 0, paddingLeft: '18px' }}>
                {result.warnings.map((w, i) => <li key={i} style={{ marginBottom: 4 }}>{w}</li>)}
              </ul>
            </Box>
          )}

          {/* OpenAI analysis */}
          {result.openai_analysis && (
            <Paper style={{ padding: '15px', backgroundColor: '#333', marginTop: '12px', borderLeft: '4px solid #ce93d8', borderRadius: '8px' }}>
              <Typography variant="subtitle2" style={{ color: '#ce93d8', marginBottom: '5px' }}>OpenAI Analysis</Typography>
              {result.openai_analysis.summary && (
                <Typography variant="body2" sx={{ mb: 1 }}>{result.openai_analysis.summary}</Typography>
              )}
              {result.openai_analysis.risk_interpretation && (
                <Typography variant="body2" sx={{ mb: 1 }}>{result.openai_analysis.risk_interpretation}</Typography>
              )}
              {(result.openai_analysis.mitigation_steps || result.openai_analysis.mitigations)?.length > 0 && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Mitigations: {(result.openai_analysis.mitigation_steps || result.openai_analysis.mitigations).join('; ')}
                </Typography>
              )}
              {result.openai_analysis.validation_tests?.length > 0 && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Validation: {result.openai_analysis.validation_tests.join('; ')}
                </Typography>
              )}
            </Paper>
          )}
        </Paper>
      );
    }

    if (resultType === 'discover') {
      return (
        <Paper elevation={4} style={{ padding: '20px', backgroundColor: '#2a2a2a', marginTop: '20px', borderRadius: '12px' }}>
          {result.mode && (
            <Alert severity={result.mode === 'openai-primary' ? 'success' : 'info'} sx={{ mb: 2 }}>
              {result.mode === 'openai-primary'
                ? `OpenAI primary ranking${result.openai_model ? ` (${result.openai_model})` : ''}`
                : `Local ranking${result.fallback_reason ? `: ${result.fallback_reason}` : ''}`}
            </Alert>
          )}
          <Typography variant="h6" color="primary" sx={{ mb: 1 }}>Discovery Results</Typography>
          {result.analysis?.stats && (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
              {[
                { label: 'Mean', val: result.analysis.stats.mean },
                { label: 'Top', val: result.analysis.stats.maximum },
                { label: 'Median', val: result.analysis.stats.median },
                { label: 'Min', val: result.analysis.stats.minimum },
              ].map(({ label, val }) => val != null && (
                <Paper key={label} style={{ padding: '8px 14px', backgroundColor: '#333', borderRadius: '8px', textAlign: 'center' }}>
                  <Typography variant="caption" style={{ color: '#888', display: 'block' }}>{label}</Typography>
                  <Typography variant="body2" color="primary" style={{ fontWeight: 'bold' }}>{val.toFixed(3)}</Typography>
                </Paper>
              ))}
            </Box>
          )}

          <Grid container spacing={2} style={{ marginTop: '4px' }}>
            {(result.analysis?.ranked_candidates || []).map((comp, idx) => (
              <Grid item xs={12} sm={6} md={4} key={idx}>
                <Paper style={{ padding: '14px', backgroundColor: '#333', borderRadius: '8px', height: '100%' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="subtitle2" color="primary" style={{ fontWeight: 'bold', wordBreak: 'break-all' }}>
                      #{idx + 1} {comp.molecule}
                    </Typography>
                  </Box>
                  <Divider style={{ borderColor: '#444', marginBottom: '8px' }} />
                  {comp.properties?.activity_score != null && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" style={{ color: '#888' }}>Activity</Typography>
                      <Typography variant="caption" style={{ color: '#4caf50', fontWeight: 'bold' }}>{comp.properties.activity_score.toFixed(3)}</Typography>
                    </Box>
                  )}
                  {comp.properties?.selectivity != null && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" style={{ color: '#888' }}>Selectivity</Typography>
                      <Typography variant="caption" style={{ color: '#90caf9' }}>{comp.properties.selectivity.toFixed(3)}</Typography>
                    </Box>
                  )}
                  {comp.properties?.stability_h != null && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="caption" style={{ color: '#888' }}>Stability</Typography>
                      <Typography variant="caption" style={{ color: '#ffb74d' }}>{comp.properties.stability_h}h</Typography>
                    </Box>
                  )}
                  {comp.openai_rationale && (
                    <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#ce93d8', fontStyle: 'italic' }}>
                      {comp.openai_rationale}
                    </Typography>
                  )}
                </Paper>
              </Grid>
            ))}
            {(!result.analysis?.ranked_candidates || result.analysis.ranked_candidates.length === 0) && (
              <Grid item xs={12}>
                <Typography>{result.message || 'No results found.'}</Typography>
              </Grid>
            )}
          </Grid>

          {result.openai_analysis && (
            <Paper style={{ padding: '15px', backgroundColor: '#333', marginTop: '20px', borderLeft: '4px solid #ce93d8', borderRadius: '8px' }}>
              <Typography variant="subtitle2" style={{ color: '#ce93d8', marginBottom: '5px' }}>OpenAI Discovery Analysis</Typography>
              {result.openai_analysis.summary && (
                <Typography variant="body2" sx={{ mb: 1 }}>{result.openai_analysis.summary}</Typography>
              )}
              {result.openai_analysis.recommendation && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong style={{ color: '#90caf9' }}>Recommendation:</strong> {result.openai_analysis.recommendation}
                </Typography>
              )}
              {result.openai_analysis.caveats && (
                <Typography variant="body2" sx={{ color: '#aaa' }}>
                  <strong>Caveats:</strong> {result.openai_analysis.caveats}
                </Typography>
              )}
            </Paper>
          )}
        </Paper>
      );
    }

    if (resultType === 'feedback') {
      // Backend returns: { id, created_at, payload: { molecule, actual_activity, ... } }
      const payload = result.payload || {};
      return (
        <Paper elevation={4} style={{ padding: '20px', backgroundColor: '#2a2a2a', marginTop: '20px', borderRadius: '12px' }}>
          <Alert severity="success" sx={{ mb: 2 }}>Experiment logged successfully</Alert>
          <Typography variant="h6" color="primary" sx={{ mb: 1 }}>Experiment Record</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', pb: 1 }}>
              <Typography variant="body2" style={{ color: '#888' }}>Molecule</Typography>
              <Typography variant="body2" style={{ fontWeight: 'bold', color: '#fff' }}>{payload.molecule || '—'}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', pb: 1 }}>
              <Typography variant="body2" style={{ color: '#888' }}>Actual Activity</Typography>
              <Typography variant="body2" style={{ fontWeight: 'bold', color: '#4caf50' }}>
                {payload.actual_activity != null ? payload.actual_activity.toFixed(3) : '—'}
              </Typography>
            </Box>
            {payload.actual_selectivity != null && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', pb: 1 }}>
                <Typography variant="body2" style={{ color: '#888' }}>Actual Selectivity</Typography>
                <Typography variant="body2" style={{ fontWeight: 'bold', color: '#90caf9' }}>{payload.actual_selectivity.toFixed(3)}</Typography>
              </Box>
            )}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #444', pb: 1 }}>
              <Typography variant="body2" style={{ color: '#888' }}>Record ID</Typography>
              <Typography variant="caption" style={{ color: '#666', fontFamily: 'monospace' }}>{result.id}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" style={{ color: '#888' }}>Logged At</Typography>
              <Typography variant="caption" style={{ color: '#666' }}>
                {result.created_at ? new Date(result.created_at).toLocaleString() : '—'}
              </Typography>
            </Box>
          </Box>
        </Paper>
      );
    }

    return <pre style={{ color: '#aaa', fontSize: '0.75rem' }}>{JSON.stringify(result, null, 2)}</pre>;
  };

  let highlightedMolecule = null;
  if (result && !result.error && resultType === 'compound') {
    highlightedMolecule = result.molecule;
  } else if (result && !result.error && resultType === 'interaction') {
    highlightedMolecule = result.compound_1 || reactionMol1;
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="xl" style={{ paddingTop: '24px', paddingBottom: '40px' }}>

        {/* Page header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" align="center" style={{
            fontWeight: 'bold',
            background: '-webkit-linear-gradient(45deg, #90caf9 30%, #ce93d8 90%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            BioAgents
          </Typography>
          <Typography variant="caption" align="center" display="block" sx={{ color: '#555', mt: 0.5 }}>
            AI-Driven Molecular Discovery · Chemical Catalysis · Synthetic Biology
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {/* Top Row: Input on left, Service Runtime on right */}
          <Grid item xs={12} md={8}>
            <Paper elevation={3} style={{ borderRadius: '12px', overflow: 'hidden', height: '100%' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider', backgroundColor: '#1e1e1e' }}>
                <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
                  <Tab label="MeTTa Knowledge" />
                  <Tab label="Discovery Engine" />
                  <Tab label="Reaction Sim" />
                  <Tab label="PubChem API" />
                  <Tab label="Feedback Loop" />
                </Tabs>
              </Box>

              {/* Tab 0: Internal KB */}
              <TabPanel value={tabValue} index={0}>
                <Typography gutterBottom style={{ color: '#aaa', fontSize: '0.875rem' }}>
                  Query local MeTTa Agent for exact properties of known catalysts and enzymes.
                </Typography>
                <TextField
                  fullWidth label="Compound Name (e.g., Cu_ZnO_Al2O3)" variant="outlined"
                  value={compoundQuery} onChange={(e) => setCompoundQuery(e.target.value)}
                  style={{ marginBottom: '15px', marginTop: '10px' }}
                  onKeyDown={(e) => e.key === 'Enter' && submitQuery('/query', { type: 'compound', molecule: compoundQuery }, 'compound')}
                />
                <Button variant="contained" color="primary" fullWidth
                  disabled={!compoundQuery.trim()}
                  onClick={() => submitQuery('/query', { type: 'compound', molecule: compoundQuery }, 'compound')}>
                  Analyze
                </Button>
              </TabPanel>

              {/* Tab 1: Discovery Pipeline */}
              <TabPanel value={tabValue} index={1}>
                <Typography gutterBottom style={{ color: '#aaa', fontSize: '0.875rem' }}>
                  Run multi-agent Research → Analysis pipeline.
                </Typography>
                <FormControl fullWidth style={{ marginBottom: '15px', marginTop: '10px' }}>
                  <InputLabel>Target Class</InputLabel>
                  <Select value={discoverClass} label="Target Class" onChange={(e) => setDiscoverClass(e.target.value)}>
                    <MenuItem value="">Any Class</MenuItem>
                    <MenuItem value="chemical_catalyst">Chemical Catalyst</MenuItem>
                    <MenuItem value="enzyme">Enzyme</MenuItem>
                    <MenuItem value="zeolite">Zeolite</MenuItem>
                    <MenuItem value="catalyst_poison">Catalyst Poison / Deactivator</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth label="Similar To (optional)" variant="outlined"
                  value={discoverSimilar} onChange={(e) => setDiscoverSimilar(e.target.value)}
                  style={{ marginBottom: '15px' }}
                />
                <Grid container spacing={2} style={{ marginBottom: '15px' }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth label="Min Activity" variant="outlined" type="number"
                      inputProps={{ min: 0, max: 1, step: 0.01 }}
                      value={discoverMinActivity} onChange={(e) => setDiscoverMinActivity(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth label="Min Selectivity" variant="outlined" type="number"
                      inputProps={{ min: 0, max: 1, step: 0.01 }}
                      value={discoverMinSelectivity} onChange={(e) => setDiscoverMinSelectivity(e.target.value)}
                    />
                  </Grid>
                </Grid>
                <Button variant="contained" color="secondary" fullWidth
                  disabled={!hasDiscoveryFilter}
                  onClick={runDiscovery}>
                  Execute Discovery Pipeline
                </Button>
              </TabPanel>

              {/* Tab 2: Reactions */}
              <TabPanel value={tabValue} index={2}>
                <Typography gutterBottom style={{ color: '#aaa', fontSize: '0.875rem' }}>
                  Check for adverse interactions using Reaction Agent.
                </Typography>
                <Grid container spacing={2} style={{ marginTop: '5px' }}>
                  <Grid item xs={6}>
                    <TextField fullWidth label="Compound 1" value={reactionMol1} onChange={(e) => setReactionMol1(e.target.value)} />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField fullWidth label="Compound 2" value={reactionMol2} onChange={(e) => setReactionMol2(e.target.value)} />
                  </Grid>
                </Grid>
                <Button variant="contained" color="error" fullWidth style={{ marginTop: '15px' }}
                  disabled={!reactionMol1.trim() || !reactionMol2.trim()}
                  onClick={() => submitQuery('/query', {
                    type: 'interaction', mol1: reactionMol1, mol2: reactionMol2,
                  }, 'interaction')}>
                  Simulate Interaction
                </Button>
              </TabPanel>

              {/* Tab 3: PubChem */}
              <TabPanel value={tabValue} index={3}>
                <Typography gutterBottom style={{ color: '#aaa', fontSize: '0.875rem' }}>
                  Live query to external PubChem database.
                </Typography>
                <TextField
                  fullWidth label="Search String (e.g., aspirin, methanol)" variant="outlined"
                  value={lookupQuery} onChange={(e) => setLookupQuery(e.target.value)}
                  style={{ marginBottom: '15px', marginTop: '10px' }}
                  onKeyDown={(e) => e.key === 'Enter' && submitQuery('/query', { type: 'lookup', query: lookupQuery }, 'lookup')}
                />
                <Button variant="contained" color="info" fullWidth
                  disabled={!lookupQuery.trim()}
                  onClick={() => submitQuery('/query', { type: 'lookup', query: lookupQuery }, 'lookup')}>
                  Fetch from PubChem
                </Button>
              </TabPanel>

              {/* Tab 4: Feedback Loop */}
              <TabPanel value={tabValue} index={4}>
                <Typography gutterBottom style={{ color: '#aaa', fontSize: '0.875rem' }}>
                  Log experimental results to compare predicted vs. actual performance.
                </Typography>
                <TextField
                  fullWidth label="Molecule Name" variant="outlined"
                  value={fbMolecule} onChange={(e) => setFbMolecule(e.target.value)}
                  style={{ marginBottom: '12px', marginTop: '10px' }}
                />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth label="Actual Activity (0-1)" variant="outlined" type="number"
                      inputProps={{ min: 0, max: 1, step: 0.01 }}
                      value={fbActivity} onChange={(e) => setFbActivity(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth label="Actual Selectivity (0-1, optional)" variant="outlined" type="number"
                      inputProps={{ min: 0, max: 1, step: 0.01 }}
                      value={fbSelectivity} onChange={(e) => setFbSelectivity(e.target.value)}
                    />
                  </Grid>
                </Grid>
                <Button variant="contained" color="warning" fullWidth style={{ marginTop: '15px' }}
                  disabled={!fbMolecule.trim() || !fbActivity.trim()}
                  onClick={() => {
                    const payload = {
                      molecule: fbMolecule,
                      actual_activity: parseFloat(fbActivity),
                    };
                    if (fbSelectivity.trim()) payload.actual_selectivity = parseFloat(fbSelectivity);
                    submitQuery('/experiments/log', payload, 'feedback');
                  }}>
                  Log Experiment
                </Button>
              </TabPanel>
            </Paper>
          </Grid>

          {/* Right Column (Top Row): Agent Dashboard */}
          <Grid item xs={12} md={4}>
            <AgentDashboard />
          </Grid>

          {/* Middle Row: Results Area */}
          <Grid item xs={12}>
            {renderResult()}
          </Grid>

          {/* Bottom Row: Knowledge Graph (Full Width) */}
          <Grid item xs={12}>
            <MolecularGraph highlightedMolecule={highlightedMolecule} />
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

export default App;
