import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Paper, Grid } from '@mui/material';
import MolecularGraph from './components/MolecularGraph';
import AgentDashboard from './components/AgentDashboard';

function App() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch('http://localhost:5000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (response.ok) {
        const data = await response.json();
        setResult(data);
        const nodes = [
          { id: 'Aspirin', group: 1 },
          { id: 'Caffeine', group: 1 },
          { id: 'Ibuprofen', group: 1 }
        ];
        const links = [
          { source: 'Aspirin', target: 'Caffeine', value: 1 },
          { source: 'Aspirin', target: 'Ibuprofen', value: 2 }
        ];
        setGraphData({ nodes, links });
      } else {
        console.error('Error:', response.status);
      }
    } catch (error) {
      console.error('Exception:', error);
    }
  };

  return (
    <Container maxWidth="lg" style={{ marginTop: '20px' }}>
      <Typography variant="h3" gutterBottom align="center" color="primary">
        BioAgents Dashboard
      </Typography>
      <Paper elevation={3} style={{ padding: '20px', marginBottom: '20px' }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Enter Query (e.g., Find similar to Aspirin with low toxicity)"
              variant="outlined"
              value={query}
              onChange={handleQueryChange}
            />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" color="primary" fullWidth onClick={handleSubmit}>
              Submit Query
            </Button>
          </Grid>
        </Grid>
      </Paper>
      {result && (
        <Paper elevation={3} style={{ padding: '20px', marginBottom: '20px' }}>
          <Typography variant="h5">Results:</Typography>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </Paper>
      )}
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <AgentDashboard />
        </Grid>
        <Grid item xs={6}>
          <MolecularGraph data={graphData} />
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;