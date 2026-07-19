import React, { useState } from 'react';
import axios from 'axios';
import { useStudySession } from '../context/StudyContext';

export default function Keywords() {
  const { studySession, updateSession } = useStudySession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const text = studySession.keywordsInput || '';
  const topN = studySession.keywordTopN || 10;
  const keywords = studySession.keywordsResult;
  const phrases = studySession.keywordsPhrasesResult;

  const setText = (value) => updateSession({ keywordsInput: value });
  const setTopN = (value) => updateSession({ keywordTopN: value });
  const setKeywords = (value) => updateSession({ keywordsResult: value });
  const setPhrases = (value) => updateSession({ keywordsPhrasesResult: value });

  const handleKeywords = async () => {
    if (!text.trim()) { setError('Please enter some text.'); return; }
    setLoading(true); setError(''); setKeywords(null); setPhrases(null);
    try {
      const res = await axios.post('/api/keywords/extract', { text, top_n: topN });
      setKeywords(res.data.keywords);
    } catch (err) { setError(err.response?.data?.detail || 'Keyword extraction failed.'); }
    finally { setLoading(false); }
  };

  const handlePhrases = async () => {
    if (!text.trim()) { setError('Please enter some text.'); return; }
    setLoading(true); setError(''); setKeywords(null); setPhrases(null);
    try {
      const res = await axios.post('/api/keywords/extract-phrases', { text, top_n: topN });
      setPhrases(res.data.phrases);
    } catch (err) { setError(err.response?.data?.detail || 'Phrase extraction failed.'); }
    finally { setLoading(false); }
  };

  const copyList = list => navigator.clipboard.writeText(
    Array.isArray(list) ? list.map(i => typeof i === 'string' ? i : i.word).join(', ') : ''
  );

  // Score to colour
  const scoreColor = score => {
    if (score > 0.7) return 'var(--accent)';
    if (score > 0.4) return 'var(--success)';
    return 'var(--text-muted)';
  };

  return (
    <div>
      <h1 className="page-title">🔑 Keyword Extractor</h1>
      <p className="page-desc">Extract important keywords and key phrases from any text.</p>

      <div className="card">
        <div className="form-group">
          <label className="form-label">Source Text</label>
          <textarea id="keywords-text" className="form-textarea" style={{ minHeight: 140 }}
            placeholder="Paste text to extract keywords from…"
            value={text} onChange={e => setText(e.target.value)} />
        </div>

        <div className="form-group">
          <label className="form-label">Number of Results: <strong>{topN}</strong></label>
          <input type="range" min={5} max={20} value={topN}
            onChange={e => setTopN(parseInt(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}>
            <span>5</span><span>20</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button id="btn-extract-keywords" className="btn btn-primary" onClick={handleKeywords} disabled={loading} style={{ flex: 1 }}>
            {loading ? <><div className="spinner" /> Extracting…</> : '🔑 Keywords'}
          </button>
          <button id="btn-extract-phrases" className="btn btn-secondary" onClick={handlePhrases} disabled={loading} style={{ flex: 1 }}>
            {loading ? <><div className="spinner spinner-dark" /> …</> : '💬 Key Phrases'}
          </button>
        </div>

        {error && <div className="alert alert-error mt-3">{error}</div>}
      </div>

      {/* Keywords Result */}
      {keywords && (
        <div className="card mt-4" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
          <div className="card-header">
            <div className="card-title">🔑 Top Keywords</div>
            <button className="btn btn-ghost btn-sm" onClick={() => copyList(keywords)}>📋 Copy All</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {keywords.map((kw, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 14px', borderRadius: '999px',
                border: '1px solid var(--border)',
                background: 'var(--bg-surface2)',
                fontSize: 13, fontWeight: 600,
              }}>
                <span style={{ color: scoreColor(kw.score) }}>⬤</span>
                <span style={{ color: 'var(--text-primary)' }}>{kw.word}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{kw.score.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phrases Result */}
      {phrases && (
        <div className="card mt-4" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
          <div className="card-header">
            <div className="card-title">💬 Key Phrases</div>
            <button className="btn btn-ghost btn-sm" onClick={() => copyList(phrases)}>📋 Copy All</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {phrases.map((phrase, i) => (
              <div key={i} style={{
                padding: '7px 16px', borderRadius: '999px',
                background: 'rgba(108,99,255,0.1)',
                border: '1px solid rgba(108,99,255,0.25)',
                fontSize: 13, fontWeight: 600, color: 'var(--accent)',
              }}>
                {phrase}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
