import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Paper, Typography } from '@mui/material';
import { getJSON } from '../api';

const CATEGORY_COLORS = {
  enzyme: '#4caf50',
  chemical_catalyst: '#90caf9',
  catalyst_poison: '#ff5252',
  enzyme_inhibitor: '#ff8a80',
  zeolite: '#ce93d8',
  environmental_stressor: '#ffb74d',
};

// Header + legend height estimate (title ~40px + legend ~30px + margins ~20px)
const HEADER_HEIGHT = 90;
const GRAPH_TOTAL_HEIGHT = 550;
const GRAPH_CANVAS_HEIGHT = GRAPH_TOTAL_HEIGHT - HEADER_HEIGHT;
const PAPER_PADDING = 20;

const MolecularGraph = ({ highlightedMolecule }) => {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const graphRef = useRef();
  const paperRef = useRef();
  const [canvasWidth, setCanvasWidth] = useState(1200);

  // Fetch graph data
  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const json = await getJSON('/molecules');
        setData(json);
      } catch (e) {
        console.error('Failed to fetch graph data', e);
      } finally {
        setLoading(false);
      }
    };
    fetchGraphData();
  }, []);

  // Measure the PAPER element's width (not the canvas container)
  // This avoids the chicken-and-egg sizing loop
  useEffect(() => {
    const measure = () => {
      if (paperRef.current) {
        const w = paperRef.current.offsetWidth - PAPER_PADDING * 2;
        if (w > 0) setCanvasWidth(w);
      }
    };

    // Measure after a short delay to ensure layout is complete
    const timer = setTimeout(measure, 100);
    window.addEventListener('resize', measure);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', measure);
    };
  }, [loading]);

  // Configure D3 forces — keep nodes close together
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force('charge').strength(-80);
      graphRef.current.d3Force('link').distance(50);
      graphRef.current.d3Force('center').strength(0.8);
    }
  }, [data.nodes.length]);

  // Auto-fit all nodes after data loads
  useEffect(() => {
    if (data.nodes.length > 0 && graphRef.current) {
      const timeout = setTimeout(() => {
        graphRef.current.zoomToFit(600, 60);
      }, 800);
      return () => clearTimeout(timeout);
    }
  }, [data.nodes.length, canvasWidth]);

  // Zoom to highlighted molecule
  useEffect(() => {
    if (!highlightedMolecule || !graphRef.current) return;
    const node = data.nodes.find((n) => n.id === highlightedMolecule);
    if (node && node.x != null && node.y != null) {
      graphRef.current.centerAt(node.x, node.y, 800);
      graphRef.current.zoom(3, 800);
    }
  }, [highlightedMolecule, data]);

  const filteredData = useMemo(() => {
    if (!highlightedMolecule) return { nodes: [], links: [] };
    
    const hNodes = new Set();
    const hLinks = new Set();
    
    // Add searched node
    const rootNode = data.nodes.find(n => n.id === highlightedMolecule);
    if (rootNode) hNodes.add(rootNode);
    
    // Add neighbors and links
    data.links.forEach((link) => {
      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
      
      if (srcId === highlightedMolecule || tgtId === highlightedMolecule) {
        hLinks.add(link);
        const neighborId = srcId === highlightedMolecule ? tgtId : srcId;
        const neighbor = data.nodes.find(n => n.id === neighborId);
        if (neighbor) hNodes.add(neighbor);
      }
    });
    
    return { nodes: Array.from(hNodes), links: Array.from(hLinks) };
  }, [highlightedMolecule, data]);

  const { highlightNodes, highlightLinks } = useMemo(() => {
    const hNodes = new Set();
    const hLinks = new Set();
    if (highlightedMolecule) {
      hNodes.add(highlightedMolecule);
      filteredData.links.forEach((link) => {
        const srcId = typeof link.source === 'object' ? link.source.id : link.source;
        const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
        if (srcId === highlightedMolecule || tgtId === highlightedMolecule) {
          hLinks.add(link);
          hNodes.add(srcId);
          hNodes.add(tgtId);
        }
      });
    }
    return { highlightNodes: hNodes, highlightLinks: hLinks };
  }, [highlightedMolecule, filteredData]);

  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const isHighlighted = highlightedMolecule && node.id === highlightedMolecule;
      const isNeighbor = highlightedMolecule && highlightNodes.has(node.id) && !isHighlighted;
      const isDimmed = highlightedMolecule && !highlightNodes.has(node.id);

      const baseColor = CATEGORY_COLORS[node.category] || '#aaaaaa';
      const color = isHighlighted ? '#ffeb3b' : isNeighbor ? '#ce93d8' : isDimmed ? '#333333' : baseColor;

      const radius = Math.sqrt(node.val || 5) * 2.5;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();

      // Highlighted ring
      if (isHighlighted) {
        ctx.strokeStyle = '#ffeb3b';
        ctx.lineWidth = 3 / globalScale;
        ctx.stroke();
      }

      // Draw label
      const label = node.id.replace(/_/g, ' ');
      const fontSize = Math.max(11 / globalScale, 3);
      ctx.font = `500 ${fontSize}px "Inter", sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isDimmed ? '#444' : '#ffffff';

      // Text background for readability
      if (!isDimmed) {
        const textWidth = ctx.measureText(label).width;
        ctx.fillStyle = 'rgba(18, 18, 18, 0.7)';
        ctx.fillRect(
          node.x - textWidth / 2 - 3,
          node.y + radius + 2,
          textWidth + 6,
          fontSize + 4
        );
        ctx.fillStyle = '#ffffff';
      }
      ctx.fillText(label, node.x, node.y + radius + 4);
    },
    [highlightedMolecule, highlightNodes]
  );

  const nodePointerAreaPaint = useCallback((node, color, ctx) => {
    const radius = Math.sqrt(node.val || 5) * 2.5;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fill();
  }, []);

  const linkColor = useCallback(
    (link) => {
      if (highlightLinks.has(link)) return '#ffeb3b';
      if (link.type === 'interaction') {
        const sev = (link.severity || '').toLowerCase();
        if (sev === 'high') return '#ff5252';
        if (sev === 'moderate') return '#ffb74d';
        return '#ff8a80';
      }
      return highlightedMolecule ? '#2a2a2a' : '#555555';
    },
    [highlightedMolecule, highlightLinks]
  );

  const linkWidth = useCallback(
    (link) =>
      highlightLinks.has(link) ? 3.0 : link.type === 'interaction' ? Math.max(2.0, link.value) : 1.2,
    [highlightLinks]
  );

  const legendEntries = [
    { label: 'Enzyme', color: '#4caf50' },
    { label: 'Chemical Catalyst', color: '#90caf9' },
    { label: 'Catalyst Poison', color: '#ff5252' },
    { label: 'Zeolite', color: '#ce93d8' },
    { label: 'Stressor', color: '#ffb74d' },
  ];

  return (
    <Paper
      ref={paperRef}
      elevation={4}
      style={{
        padding: `${PAPER_PADDING}px`,
        backgroundColor: '#1e1e1e',
        color: '#fff',
        borderRadius: '16px',
        border: '1px solid #333',
      }}
    >
      <Typography
        variant="h6"
        gutterBottom
        style={{ fontWeight: 'bold', color: '#90caf9', marginBottom: '8px' }}
      >
        Knowledge Graph
        {highlightedMolecule && (
          <span
            style={{
              fontSize: '0.75rem',
              color: '#ce93d8',
              marginLeft: '12px',
              fontWeight: 'normal',
            }}
          >
            — {highlightedMolecule.replace(/_/g, ' ')}
          </span>
        )}
      </Typography>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
        {legendEntries.map((e) => (
          <span
            key={e.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.75rem',
              color: '#888',
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: e.color,
                display: 'inline-block',
              }}
            />
            {e.label}
          </span>
        ))}
      </div>

      {loading ? (
        <Typography style={{ color: '#aaa' }}>Loading Knowledge Base…</Typography>
      ) : !highlightedMolecule ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#121212', borderRadius: '12px' }}>
          <Typography style={{ color: '#666', fontStyle: 'italic' }}>
            Search for a molecule or run a discovery query to visualize the Knowledge Graph
          </Typography>
        </div>
      ) : filteredData.nodes.length === 0 ? (
        <Typography color="error">No data found for "{highlightedMolecule}"</Typography>
      ) : (
        <div
          style={{
            width: canvasWidth,
            height: GRAPH_CANVAS_HEIGHT,
            borderRadius: '12px',
            background: '#121212',
          }}
        >
          <ForceGraph2D
            ref={graphRef}
            width={canvasWidth}
            height={GRAPH_CANVAS_HEIGHT}
            graphData={filteredData}
            nodeCanvasObject={nodeCanvasObject}
            nodeCanvasObjectMode={() => 'replace'}
            nodePointerAreaPaint={nodePointerAreaPaint}
            nodeLabel={(node) => `${node.id} · ${node.category}`}
            linkColor={linkColor}
            linkWidth={linkWidth}
            linkDirectionalParticles={(link) =>
              highlightLinks.has(link) || link.type === 'interaction' ? 3 : 0
            }
            linkDirectionalParticleSpeed={(link) => link.value * 0.015}
            linkDirectionalArrowLength={(link) => (link.type === 'interaction' ? 5 : 0)}
            linkDirectionalArrowRelPos={1}
            backgroundColor="#121212"
            warmupTicks={200}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            onEngineStop={() => {
              if (graphRef.current && !highlightedMolecule) {
                graphRef.current.zoomToFit(400, 60);
              }
            }}
          />
        </div>
      )}
    </Paper>
  );
};

export default MolecularGraph;
