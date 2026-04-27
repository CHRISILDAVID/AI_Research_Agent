import { ChevronRight } from 'lucide-react';

/**
 * Real-time agent status panel showing the pipeline state,
 * active agent, and research metrics.
 */
export default function AgentStatus({ status, events }) {
  if (!status) return null;

  const currentNode = status.current_agent || status.node || '';
  const statusText = status.status || 'running';

  const nodes = ['supervisor', 'researcher', 'writer'];

  const getNodeState = (node) => {
    if (node === currentNode) return 'active';
    // Check if this node has already been visited
    const visited = events?.some(e =>
      e.event === 'agent_step' && e.data?.node === node
    );
    return visited ? 'completed' : '';
  };

  return (
    <div className="agent-status-panel">
      <div className="agent-status-header">
        <div className={`status-dot ${statusText}`} />
        <span className="agent-status-title">
          {statusText === 'starting' && '🚀 Initializing research pipeline...'}
          {statusText === 'researching' && '🔍 Research agent gathering information...'}
          {statusText === 'writing' && '✍️ Writer agent composing report...'}
          {statusText === 'completed' && '✅ Research complete!'}
          {statusText === 'error' && '❌ Research encountered an error'}
          {!['starting', 'researching', 'writing', 'completed', 'error'].includes(statusText) && '⏳ Processing...'}
        </span>
      </div>

      {/* Agent Pipeline Visualization */}
      <div className="agent-pipeline">
        {nodes.map((node, i) => (
          <span key={node} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`pipeline-node ${getNodeState(node)}`}>
              {node === 'supervisor' && '🧠'}
              {node === 'researcher' && '🔬'}
              {node === 'writer' && '📝'}
              {' '}{node.charAt(0).toUpperCase() + node.slice(1)}
            </span>
            {i < nodes.length - 1 && (
              <ChevronRight size={14} className="pipeline-arrow" />
            )}
          </span>
        ))}
      </div>

      {/* Metrics */}
      <div className="status-metrics">
        <div className="metric-card">
          <div className="metric-value">{status.sources_count || 0}</div>
          <div className="metric-label">Sources Found</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{status.chunks_stored || 0}</div>
          <div className="metric-label">Chunks Indexed</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">
            {status.has_report ? '✓' : '—'}
          </div>
          <div className="metric-label">Report</div>
        </div>
      </div>
    </div>
  );
}
