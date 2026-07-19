import React, { useState } from 'react';
import axios from 'axios';
import { useStudySession } from '../context/StudyContext';

const LEVELS = [
  { value: 'elementary',   label: '🧒 Elementary' },
  { value: 'middle_school',label: '📚 Middle School' },
  { value: 'high_school',  label: '🏫 High School' },
  { value: 'college',      label: '🎓 College' },
];

export default function Simplify() {
  const { studySession, updateSession } = useStudySession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const text = studySession.simplifyInput || '';
  const level = studySession.simplifyLevel || 'high_school';
  const result = studySession.simplifyResult;
  const wordResult = studySession.simplifyWordResult;
  const tab = studySession.simplifyTab || 0;
  const word = studySession.simplifyWordInput || '';

  const setText = (value) => updateSession({ simplifyInput: value });
  const setLevel = (value) => updateSession({ simplifyLevel: value });
  const setResult = (value) => updateSession({ simplifyResult: value });
  const setWordResult = (value) => updateSession({ simplifyWordResult: value });
  const setTab = (value) => { setError(''); updateSession({ simplifyTab: value }); };
  const setWord = (value) => updateSession({ simplifyWordInput: value });

  const handleSimplify = async () => {
    if (!text.trim()) { setError('Please enter some text.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post('/api/simplify/simplify', { text, level });
      setResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || 'Simplification failed.'); }
    finally { setLoading(false); }
  };

  const handleELI10 = async () => {
    if (!text.trim()) { setError('Please enter some text.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post('/api/simplify/eli10', { text });
      setResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || 'ELI10 failed.'); }
    finally { setLoading(false); }
  };

  const handleWordSimplify = async () => {
    if (!word.trim()) { setError('Please enter a word.'); return; }
    setLoading(true); setError(''); setWordResult(null);
    try {
      const res = await axios.post('/api/simplify/simplify-word', { word });
      setWordResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || 'Word simplification failed.'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h1 className="page-title">✨ Text Simplifier</h1>
      <p className="page-desc">Rewrite complex text into plain, easy-to-understand language at any reading level.</p>

      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['📄 Text Simplification', '🔤 Word Simplifier'].map((label, i) => (
          <button key={i} onClick={() => { setTab(i); setError(''); }}
            style={{
              padding: '9px 18px', borderRadius: 'var(--radius-sm)', fontFamily: 'inherit',
              fontWeight: 600, fontSize: 14, cursor: 'pointer', border: '2px solid',
              borderColor: tab === i ? 'var(--accent)' : 'var(--border)',
              background: tab === i ? 'rgba(108,99,255,0.1)' : 'var(--bg-surface2)',
              color: tab === i ? 'var(--accent)' : 'var(--text-secondary)',
              transition: 'all 0.18s',
            }}
          >{label}</button>
        ))}
      </div>

      {/* Text Tab */}
      {tab === 0 && (
        <div className="card">
          <div className="form-group">
            <label className="form-label">Text to Simplify</label>
            <textarea id="simplify-text" className="form-textarea" style={{ minHeight: 140 }}
              placeholder="Paste your complex text here…"
              value={text} onChange={e => setText(e.target.value)} />
          </div>

          <div className="form-group">
            <label className="form-label">Reading Level</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {LEVELS.map(l => (
                <button key={l.value} onClick={() => setLevel(l.value)} style={{
                  padding: '8px 14px', borderRadius: 'var(--radius-sm)', border: '2px solid',
                  borderColor: level === l.value ? 'var(--accent)' : 'var(--border)',
                  background: level === l.value ? 'rgba(108,99,255,0.1)' : 'var(--bg-surface2)',
                  color: level === l.value ? 'var(--accent)' : 'var(--text-secondary)',
                  fontFamily: 'inherit', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                  transition: 'all 0.18s',
                }}>{l.label}</button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button id="btn-simplify" className="btn btn-primary" onClick={handleSimplify} disabled={loading} style={{ flex: 1 }}>
              {loading ? <><div className="spinner" /> Simplifying…</> : '✨ Simplify Text'}
            </button>
            <button id="btn-eli10" className="btn btn-secondary" onClick={handleELI10} disabled={loading} style={{ flex: 1 }}>
              {loading ? <><div className="spinner spinner-dark" /> …</> : '👶 Explain Like I\'m 10'}
            </button>
          </div>

          {error && <div className="alert alert-error mt-3">{error}</div>}

          {result && (
            <div style={{ marginTop: 20, animation: 'fadeSlideIn 0.3s ease' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                {result.level ? `${result.level.replace('_', ' ').toUpperCase()} Level` : 'ELI10 Explanation'}
              </div>
              <div className="result-box">
                <p>{result.simplified_text || result.explanation}</p>
              </div>
              <div className="stats-row mt-2">
                <div className="stat-pill">📝 Original: {result.original_length} words</div>
                <div className="stat-pill">✂️ Result: {result.simplified_length || result.explanation_length} words</div>
              </div>
              <div className="result-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => navigator.clipboard.writeText(result.simplified_text || result.explanation)}>📋 Copy</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Word Tab */}
      {tab === 1 && (
        <div className="card">
          <div className="form-group">
            <label className="form-label">Complex Word or Phrase</label>
            <input id="simplify-word" className="form-input" type="text"
              placeholder="e.g. photosynthesis, exacerbate, ubiquitous…"
              value={word} onChange={e => setWord(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleWordSimplify()} />
          </div>

          <button id="btn-word-simplify" className="btn btn-primary btn-full" onClick={handleWordSimplify} disabled={loading}>
            {loading ? <><div className="spinner" /> Looking up…</> : '🔍 Find Simpler Word'}
          </button>

          {error && <div className="alert alert-error mt-3">{error}</div>}

          {wordResult && (
            <div className="card mt-4" style={{ animation: 'fadeSlideIn 0.3s ease', border: '2px solid var(--border)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <div className="text-muted text-small">Original</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>{wordResult.original}</div>
                </div>
                <div style={{ fontSize: 24, textAlign: 'center', color: 'var(--text-muted)' }}>↓</div>
                <div>
                  <div className="text-muted text-small">Simpler Alternative</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent)' }}>{wordResult.simpler}</div>
                </div>
                <div className={`alert ${wordResult.found ? 'alert-success' : 'alert-info'}`}>
                  {wordResult.found ? '✅ Simpler alternative found' : 'ℹ️ No simpler alternative — original retained'}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
