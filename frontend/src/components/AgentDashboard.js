import React, { useState, useEffect } from 'react';
import { Paper, Typography, Chip, Box, CircularProgress } from '@mui/material';
import { getJSON } from '../api';

const AgentDashboard = () => {
  const [agents, setAgents] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const data = await getJSON('/agents/status');
      setAgents(data);
    } catch (e) {
      console.error('Failed to fetch agent status', e);
      setAgents({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Paper elevation={2} style={{ padding: '20px', backgroundColor: '#1e1e1e', color: '#fff', borderRadius: '12px', height: '100%' }}>
      <Typography variant="subtitle2" gutterBottom style={{ color: '#90caf9', fontWeight: 'bold', marginBottom: '16px' }}>
        Service Runtime
      </Typography>

      {loading ? (
        <CircularProgress color="secondary" size={20} />
      ) : Object.keys(agents).length === 0 ? (
        <Typography variant="caption" style={{ color: '#ff6666' }}>Cannot connect to BioAgents API</Typography>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {Object.entries(agents).map(([name, info]) => (
          <Chip
              key={name}
              icon={
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: info.status === 'Ready' ? '#4caf50' : '#ff5252',
                  display: 'inline-block', marginLeft: 6,
                }} />
              }
              label={name}
              size="small"
              variant="outlined"
              style={{
                borderColor: info.status === 'Ready' ? '#4caf50' : '#ff5252',
                color: info.status === 'Ready' ? '#4caf50' : '#ff5252',
                fontSize: '0.72rem',
              }}
            />
          ))}
        </Box>
      )}
    </Paper>
  );
};

export default AgentDashboard;
