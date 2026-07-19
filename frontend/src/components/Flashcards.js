import React, { useState } from 'react';
import axios from 'axios';
import { useStudySession } from '../context/StudyContext';

export default function Flashcards() {
  const { studySession, updateSession } = useStudySession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const text = studySession.flashcardInput || '';
  const numCards = studySession.flashcardNumCards || 10;
  const cards = studySession.flashcardResult;
  const index = studySession.flashcardIndex || 0;
  const flipped = studySession.flashcardFlipped || false;

  const setText = (value) => updateSession({ flashcardInput: value });
  const setNumCards = (value) => updateSession({ flashcardNumCards: value });
  const setCards = (value) => updateSession({ flashcardResult: value });
  const setIndex = (value) => updateSession({ flashcardIndex: value });
  const setFlipped = (value) => updateSession({ flashcardFlipped: value });

  const handleGenerate = async () => {
    if (!text.trim()) { setError('Please enter some text first.'); return; }
    setLoading(true); setError(''); setCards(null); setIndex(0); setFlipped(false);
    try {
      const res = await axios.post('/api/flashcards/generate', { text, num_cards: numCards });
      setCards(res.data.flashcards);
    } catch (err) { setError(err.response?.data?.detail || 'Flashcard generation failed.'); }
    finally { setLoading(false); }
  };

  const next = () => { if (cards && index < cards.length - 1) { setIndex(i => i + 1); setFlipped(false); } };
  const prev = () => { if (index > 0) { setIndex(i => i - 1); setFlipped(false); } };

  return (
    <div>
      <h1 className="page-title">🃏 Flashcard Generator</h1>
      <p className="page-desc">Create flip-card flashcards to memorize key concepts faster.</p>

      <div className="card">
        <div className="form-group">
          <label className="form-label">Source Text</label>
          <textarea id="flashcard-text" className="form-textarea" style={{ minHeight: 140 }}
            placeholder="Paste the text you want to turn into flashcards…"
            value={text} onChange={e => setText(e.target.value)} />
        </div>

        <div className="form-group">
          <label className="form-label">Number of Cards: <strong>{numCards}</strong></label>
          <input
            id="flashcard-count"
            type="range" min={3} max={20} value={numCards}
            onChange={e => setNumCards(parseInt(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}>
            <span>3</span><span>20</span>
          </div>
        </div>

        <button id="btn-generate-flashcards" className="btn btn-primary btn-full" onClick={handleGenerate} disabled={loading}>
          {loading ? <><div className="spinner" /> Generating…</> : '🃏 Generate Flashcards'}
        </button>
        {error && <div className="alert alert-error mt-3">{error}</div>}
      </div>

      {cards && cards.length > 0 && (
        <div style={{ marginTop: 24 }}>
          {/* Progress */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="text-muted text-small">Card {index + 1} of {cards.length}</div>
            <div className="progress-bar-track" style={{ width: 160, margin: 0 }}>
              <div className="progress-bar-fill" style={{ width: `${((index + 1) / cards.length) * 100}%` }} />
            </div>
          </div>

          {/* Flashcard */}
          <div className="flashcard-container" style={{ marginBottom: 20 }}>
            <div
              className={`flashcard ${flipped ? 'flipped' : ''}`}
              onClick={() => setFlipped(f => !f)}
              style={{ minHeight: 200 }}
            >
              <div className="flashcard-face flashcard-front">
                <div>
                  <div className="flashcard-label">Front · Click to flip</div>
                  <div className="flashcard-text">{cards[index].front}</div>
                </div>
              </div>
              <div className="flashcard-face flashcard-back">
                <div>
                  <div className="flashcard-label" style={{ color: 'var(--text-muted)' }}>Answer</div>
                  <div className="flashcard-text">{cards[index].back}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <button id="btn-prev-card" className="btn btn-secondary" onClick={prev} disabled={index === 0}>
              ← Previous
            </button>
            <button className="btn btn-ghost" onClick={() => setFlipped(f => !f)}>
              🔄 Flip
            </button>
            <button id="btn-next-card" className="btn btn-secondary" onClick={next} disabled={index === cards.length - 1}>
              Next →
            </button>
          </div>

          {/* All Cards Preview */}
          <div style={{ marginTop: 28 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>All Cards</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {cards.map((card, i) => (
                <div key={i} onClick={() => { setIndex(i); setFlipped(false); }}
                  style={{
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    border: `2px solid ${i === index ? 'var(--accent)' : 'var(--border)'}`,
                    background: i === index ? 'rgba(108,99,255,0.08)' : 'var(--bg-surface2)',
                    cursor: 'pointer',
                    transition: 'all 0.18s',
                  }}
                >
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 2 }}>Card {i + 1}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{card.front}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
