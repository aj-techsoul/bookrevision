import React, { useState } from 'react';
import axios from 'axios';
import { useStudySession } from '../context/StudyContext';

const LEVELS = [
  { value: '1line',  label: '1-Line',    desc: 'Ultra-concise single sentence' },
  { value: 'bullet', label: 'Bullets',   desc: 'Key points as bullet list' },
  { value: '50w',    label: '50 Words',  desc: 'Short paragraph summary' },
  { value: '150w',   label: '150 Words', desc: 'Detailed paragraph summary' },
];

export default function Summary() {
  const { studySession, updateSession } = useStudySession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const text = studySession.summaryInput || '';
  const level = studySession.summaryLevel || '150w';
  const result = studySession.summaryResult;
  const multiResult = studySession.summaryMultiResult;

  const setText = (value) => updateSession({ summaryInput: value });
  const setLevel = (value) => updateSession({ summaryLevel: value });
  const setResult = (value) => updateSession({ summaryResult: value });
  const setMultiResult = (value) => updateSession({ summaryMultiResult: value });

  const validate = () => {
    if (!text.trim()) { setError('Please enter some text to summarize.'); return false; }
    return true;
  };

  const handleSummarize = async () => {
    if (!validate()) return;
    setLoading(true); setError(null); setResult(null); setMultiResult(null);
    try {
      const res = await axios.post('/api/summary/summarize', { text, level });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Summarization failed.');
    } finally { setLoading(false); }
  };

  const handleMulti = async () => {
    if (!validate()) return;
    setLoading(true); setError(null); setResult(null); setMultiResult(null);
    try {
      const res = await axios.post('/api/summary/summarize-multi', { text });
      setMultiResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Summarization failed.');
    } finally { setLoading(false); }
  };

  const copy = str => navigator.clipboard.writeText(str);

  return (
    <div>
      <h1 className="page-title">📝 AI Summary</h1>
      <p className="page-desc">Generate multi-level summaries. Works on large texts via chunked processing.</p>

      <div className="card">
        {/* Text Input */}
        <div className="form-group">
          <label className="form-label">Text to Summarize</label>
          <textarea
            id="summary-text"
            className="form-textarea"
            style={{ minHeight: 160 }}
            placeholder="Paste your text here… (any length — large documents are handled automatically)"
            value={text}
            onChange={e => setText(e.target.value)}
          />
          {text && (
            <div className="text-muted" style={{ textAlign: 'right' }}>
              ~{text.split(/\s+/).filter(Boolean).length} words
            </div>
          )}
        </div>

        {/* Level Selector */}
        <div className="form-group">
          <label className="form-label">Summary Level</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
            {LEVELS.map(l => (
              <button
                key={l.value}
                onClick={() => setLevel(l.value)}
                style={{
                  padding: '10px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: `2px solid ${level === l.value ? 'var(--accent)' : 'var(--border)'}`,
                  background: level === l.value ? 'rgba(108,99,255,0.1)' : 'var(--bg-surface2)',
                  color: level === l.value ? 'var(--accent)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: 13,
                  fontFamily: 'inherit',
                  transition: 'all 0.18s',
                }}
              >
                <div>{l.label}</div>
                <div style={{ fontSize: 10, fontWeight: 400, opacity: 0.7, marginTop: 2 }}>{l.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button id="btn-summarize" className="btn btn-primary" onClick={handleSummarize} disabled={loading} style={{ flex: 1 }}>
            {loading ? <><div className="spinner" /> Summarizing…</> : '✨ Generate Summary'}
          </button>
          <button id="btn-all-levels" className="btn btn-secondary" onClick={handleMulti} disabled={loading} style={{ flex: 1 }}>
            {loading ? <><div className="spinner spinner-dark" /> Processing…</> : '📊 All Levels'}
          </button>
        </div>

        {error && <div className="alert alert-error mt-3">{error}</div>}
      </div>

      {/* Single Result */}
      {result && (
        <div className="card mt-4" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
          <div className="card-header">
            <div className="card-title">{level.toUpperCase()} Summary</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {result.was_chunked && <span className="badge badge-warning">📄 Chunked</span>}
              <span className="badge badge-accent">{result.summary_length} words</span>
            </div>
          </div>
          <div className="result-box">
            <p style={{ whiteSpace: 'pre-line' }}>{result.summary}</p>
          </div>
          <div className="stats-row">
            <div className="stat-pill">📝 Original: {result.original_length} words</div>
            <div className="stat-pill">✂️ Summary: {result.summary_length} words</div>
            {result.original_tokens && <div className="stat-pill">🔢 {result.original_tokens} tokens</div>}
          </div>
          <div className="result-actions">
            <button className="btn btn-secondary btn-sm" onClick={() => copy(result.summary)}>📋 Copy</button>
          </div>
        </div>
      )}

      {/* Multi-level Results */}
      {multiResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          {LEVELS.map(l => {
            const r = multiResult[l.value];
            if (!r) return null;
            return (
              <div key={l.value} className="card" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
                <div className="card-header">
                  <div className="card-title">{l.label}</div>
                  {r.was_chunked && <span className="badge badge-warning">📄 Chunked</span>}
                </div>
                {r.error
                  ? <div className="alert alert-error">{r.error}</div>
                  : <div className="result-box"><p style={{ whiteSpace: 'pre-line' }}>{r.summary}</p></div>}
                {r.summary && (
                  <div className="result-actions mt-2">
                    <button className="btn btn-secondary btn-sm" onClick={() => copy(r.summary)}>📋 Copy</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
