import { useCallback, useEffect, useRef, useState } from 'react'
import { useGenerate } from './hooks/useGenerate'
import { api } from './api/client'
import type { ArtifactFile, HistoryItem } from './types/api'
import './App.css'

// ── Constants ──────────────────────────────────────────────────────────────
const EXAMPLES = [
  'Build a movie recommendation flow with MovieFilterComponent for genre and mood filtering',
  'Create a sentiment analysis pipeline with a custom PolarityDetector component',
  'Build a RAG flow with document input, embedder, vector store, retriever and LLM',
  'Build a vision flow that accepts image uploads and classifies movie posters into genres',
  'Create a text summarization chatbot flow with an OpenAI model',
]

const FILE_COLOR: Record<string, string> = {
  json:     '#5b8cff',
  python:   '#2ec27e',
  markdown: '#e5a020',
  text:     '#8899bb',
}

const FILE_ICON: Record<string, string> = {
  json:     '{ }',
  python:   '🐍',
  markdown: '📝',
  text:     '📄',
}

const TOOL_ICON: Record<string, string> = {
  write_file:                    '💾',
  read_file:                     '📖',
  edit_file:                     '✏️',
  list_files:                    '📋',
  generate_node_id:              '🔑',
  validate_flow_json:            '✅',
  validate_component_python:     '🔍',
  get_langflow_schema_template:  '📐',
}

// ── App ────────────────────────────────────────────────────────────────────
export default function App() {
  const [description, setDescription] = useState('')
  const [apiKey, setApiKey]           = useState('')
  const [activeTab, setActiveTab]     = useState<string | null>(null)
  const [history, setHistory]         = useState<HistoryItem[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [copied, setCopied]           = useState<string | null>(null)
  const [apiStatus, setApiStatus]     = useState<'unknown' | 'ok' | 'error'>('unknown')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { status, data, error, generate, reset } = useGenerate()

  // Health check on mount
  useEffect(() => {
    api.health()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'))
  }, [])

  // Auto-select first artifact tab when results arrive
  useEffect(() => {
    if (data?.artifacts?.length) setActiveTab(data.artifacts[0].filename)
  }, [data])

  // Refresh history after successful generation
  useEffect(() => {
    if (status === 'success') {
      api.history().then(r => setHistory(r.items)).catch(() => {})
    }
  }, [status])

  // Load initial history
  useEffect(() => {
    api.history().then(r => setHistory(r.items)).catch(() => {})
  }, [])

  const handleGenerate = useCallback(() => {
    if (!description.trim()) return
    generate(description.trim(), apiKey || undefined)
  }, [description, apiKey, generate])

  const handleExample = (ex: string) => {
    setDescription(ex)
    textareaRef.current?.focus()
  }

  const handleCopy = (content: string, key: string) => {
    navigator.clipboard.writeText(content)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  const activeArtifact: ArtifactFile | null =
    data?.artifacts.find(a => a.filename === activeTab) ?? null

  return (
    <div className="app">

      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <span className="logo">⚡ Agentic Coding Assistant</span>
          <span className="badge">Pi-style Agent</span>
          <span className="badge green">+ Vision</span>
        </div>
        <div className="header-right">
          <div className={`api-dot ${apiStatus}`} title={`API ${apiStatus}`} />
          <span className="api-label">
            {apiStatus === 'ok' ? 'API online' : apiStatus === 'error' ? 'API offline' : 'Checking…'}
          </span>
          <button className="history-btn" onClick={() => setShowHistory(v => !v)}>
            🕐 History {history.length > 0 && `(${history.length})`}
          </button>
        </div>
      </header>

      <div className="layout">

        {/* ── Sidebar ── */}
        <aside className="sidebar">

          {/* API Key */}
          <div className="section">
            <div className="section-label">ANTHROPIC API KEY</div>
            <input
              type="password"
              className="input"
              placeholder="sk-ant-... (or set env var)"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
            />
            <div className="hint">
              Leave blank if <code>ANTHROPIC_API_KEY</code> is set server-side.
            </div>
          </div>

          {/* Prompt */}
          <div className="section prompt-section">
            <div className="section-label">DESCRIBE YOUR FLOW</div>
            <textarea
              ref={textareaRef}
              className="textarea"
              placeholder="Build a movie recommendation flow with MovieFilterComponent for genre and mood filtering then LLM generates personalized recommendations"
              value={description}
              onChange={e => setDescription(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) handleGenerate() }}
              rows={5}
            />
            <button
              className={`generate-btn ${status === 'loading' ? 'loading' : ''}`}
              onClick={handleGenerate}
              disabled={status === 'loading' || !description.trim()}
            >
              {status === 'loading'
                ? <><span className="spinner" /> Generating…</>
                : '▶  Generate Flow'}
            </button>
          </div>

          {/* Examples */}
          <div className="section">
            <div className="section-label">EXAMPLES</div>
            <div className="examples">
              {EXAMPLES.map((ex, i) => (
                <button key={i} className="example-chip" onClick={() => handleExample(ex)}>
                  {ex}
                </button>
              ))}
            </div>
          </div>

          {/* Tool log */}
          {data && (
            <div className="section tool-log-section">
              <div className="section-label">TOOL CALLS ({data.tool_call_count})</div>
              <div className="tool-log">
                {data.tool_calls.map((tc, i) => (
                  <div key={i} className="tool-entry">
                    <span className="tool-icon">{TOOL_ICON[tc.tool] ?? '🔧'}</span>
                    <div className="tool-body">
                      <div className="tool-name">{tc.tool}</div>
                      <div className="tool-result">{tc.result.slice(0, 80)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* ── Main panel ── */}
        <main className="main">

          {/* Idle */}
          {status === 'idle' && (
            <div className="empty-state">
              <div className="empty-icon">⚡</div>
              <div className="empty-title">Agentic Coding Assistant</div>
              <div className="empty-sub">
                Describe any Langflow pipeline in plain English.<br />
                The agent generates <code>flow.json</code> + Python component in seconds.
              </div>
              <div className="empty-hint">Press <kbd>⌘ Enter</kbd> to generate</div>
            </div>
          )}

          {/* Loading */}
          {status === 'loading' && (
            <div className="empty-state">
              <div className="pulse-ring" />
              <div className="empty-title">Agent running…</div>
              <div className="empty-sub">
                Claude is calling tools to build your flow.<br />
                This usually takes 20–40 seconds.
              </div>
            </div>
          )}

          {/* Error */}
          {status === 'error' && (
            <div className="empty-state">
              <div className="empty-icon error-icon">⚠</div>
              <div className="empty-title">Generation failed</div>
              <div className="empty-sub error-text">{error}</div>
              <button className="reset-btn" onClick={reset}>Try again</button>
            </div>
          )}

          {/* Success */}
          {status === 'success' && data && (
            <div className="results">

              {/* Stats bar */}
              <div className="stats-bar">
                <div className="stat">
                  <span className="stat-num">{data.file_count}</span>
                  <span className="stat-label">files</span>
                </div>
                <div className="stat-divider" />
                <div className="stat">
                  <span className="stat-num">{data.tool_call_count}</span>
                  <span className="stat-label">tool calls</span>
                </div>
                <div className="stat-divider" />
                <div className="stat">
                  <span className="stat-num">{data.duration_seconds}s</span>
                  <span className="stat-label">duration</span>
                </div>
                <div className="stat-divider" />
                <div className="stat">
                  <span className="stat-num green-text">✓</span>
                  <span className="stat-label">success</span>
                </div>
                <button className="reset-btn small" onClick={reset}>New flow</button>
              </div>

              {/* File tabs */}
              <div className="file-tabs">
                {data.artifacts.map(a => (
                  <button
                    key={a.filename}
                    className={`file-tab ${activeTab === a.filename ? 'active' : ''}`}
                    onClick={() => setActiveTab(a.filename)}
                    style={{
                      borderBottomColor: activeTab === a.filename
                        ? FILE_COLOR[a.file_type] : 'transparent',
                    }}
                  >
                    <span>{FILE_ICON[a.file_type] ?? '📄'}</span>
                    {a.filename}
                    <span className="file-size">{(a.size / 1000).toFixed(1)}kb</span>
                  </button>
                ))}
              </div>

              {/* File content */}
              {activeArtifact && (
                <div className="file-pane">
                  <div className="file-toolbar">
                    <span
                      className="file-type-badge"
                      style={{
                        background: FILE_COLOR[activeArtifact.file_type] + '22',
                        color: FILE_COLOR[activeArtifact.file_type],
                        borderColor: FILE_COLOR[activeArtifact.file_type] + '44',
                      }}
                    >
                      {activeArtifact.file_type}
                    </span>
                    <span className="file-chars">
                      {activeArtifact.size.toLocaleString()} chars
                    </span>
                    <div className="file-actions">
                      <button
                        className="action-btn"
                        onClick={() => handleCopy(activeArtifact.content, activeArtifact.filename)}
                      >
                        {copied === activeArtifact.filename ? '✓ Copied' : 'Copy'}
                      </button>
                      <a
                        className="action-btn"
                        href={api.downloadUrl(data.run_id, activeArtifact.filename)}
                        download={activeArtifact.filename}
                      >
                        ↓ Download
                      </a>
                    </div>
                  </div>
                  <pre className="code-block"><code>{activeArtifact.content}</code></pre>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* ── History drawer ── */}
      {showHistory && (
        <div className="history-overlay" onClick={() => setShowHistory(false)}>
          <div className="history-drawer" onClick={e => e.stopPropagation()}>
            <div className="drawer-header">
              <span>Generation History</span>
              <button onClick={() => setShowHistory(false)}>✕</button>
            </div>
            {history.length === 0
              ? <div className="drawer-empty">No generations yet</div>
              : history.map(item => (
                  <div key={item.run_id} className="history-item">
                    <div className="history-desc">{item.description}</div>
                    <div className="history-meta">
                      <span className="green-text">✓</span>
                      {item.file_count} files · {item.tool_call_count} calls ·{' '}
                      {new Date(item.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                ))
            }
          </div>
        </div>
      )}
    </div>
  )
}
