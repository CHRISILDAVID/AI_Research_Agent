import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, FileText } from 'lucide-react';

/**
 * Renders the research report as formatted Markdown with
 * source citations, export options, and premium styling.
 */
export default function ResearchReport({ report }) {
  if (!report?.content) return null;

  const handleDownload = () => {
    const blob = new Blob([report.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research-report.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ width: '100%' }}>
      <div className="message agent" style={{ maxWidth: '100%' }}>
        <div className="message-label" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileText size={12} />
            Research Report
          </span>
          <button
            onClick={handleDownload}
            style={{
              background: 'none',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 10px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 11,
              fontFamily: 'var(--font-sans)',
              transition: 'all var(--transition-fast)',
            }}
            onMouseEnter={e => {
              e.target.style.borderColor = 'var(--accent-primary)';
              e.target.style.color = 'var(--accent-primary)';
            }}
            onMouseLeave={e => {
              e.target.style.borderColor = 'var(--border-subtle)';
              e.target.style.color = 'var(--text-secondary)';
            }}
          >
            <Download size={11} /> Download .md
          </button>
        </div>
        <div className="report-container">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
