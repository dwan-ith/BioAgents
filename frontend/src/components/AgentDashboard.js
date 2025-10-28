import React from 'react';
import { Paper, Typography, List, ListItem, ListItemText } from '@mui/material';

const AgentDashboard = () => {
  const agents = [
    { name: 'CompoundAgent', status: 'Active' },
    { name: 'ReactionAgent', status: 'Active' },
    { name: 'ResearchAgent', status: 'Active' },
    { name: 'AnalysisAgent', status: 'Active' },
    { name: 'DatabaseAgent', status: 'Active' },
  ];

  return (
    <Paper elevation={3} style={{ padding: '20px' }}>
      <Typography variant="h5" gutterBottom>
        Agent Status Dashboard
      </Typography>
      <List>
        {agents.map((agent, index) => (
          <ListItem key={index}>
            <ListItemText primary={agent.name} secondary={`Status: ${agent.status}`} />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default AgentDashboard;