import React, { useState } from 'react';
import axios from 'axios';
import { useStudySession } from '../context/StudyContext';

const DIFFICULTY = ['easy', 'medium', 'hard'];
const NUM_Q = [3, 5, 10];

export default function Quiz() {
  const { studySession, updateSession } = useStudySession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const text = studySession.quizInput || '';
  const numQ = studySession.quizNumQuestions || 5;
  const diff = studySession.quizDifficulty || 'medium';
  const quiz = studySession.quizResult;
  const answers = studySession.quizAnswers || {};
  const submitted = studySession.quizSubmitted || false;

  const setText = (value) => updateSession({ quizInput: value });
  const setNumQ = (value) => updateSession({ quizNumQuestions: value });
  const setDiff = (value) => updateSession({ quizDifficulty: value });
  const setQuiz = (value) => updateSession({ quizResult: value });
  const setAnswers = (value) => updateSession({ quizAnswers: value });
  const setSubmitted = (value) => updateSession({ quizSubmitted: value });

  const handleGenerate = async () => {
    if (!text.trim()) { setError('Please enter some text first.'); return; }
    setLoading(true); setError(''); setQuiz(null); setAnswers({}); setSubmitted(false);
    try {
      const res = await axios.post('/api/quiz/generate', { text, num_questions: numQ, difficulty: diff });
      setQuiz(res.data.quiz);
    } catch (err) { setError(err.response?.data?.detail || 'Quiz generation failed.'); }
    finally { setLoading(false); }
  };

  const score = quiz ? quiz.reduce((acc, q, i) => acc + (answers[i] === q.correct ? 1 : 0), 0) : 0;
  const pct   = quiz ? Math.round((score / quiz.length) * 100) : 0;
  const allAnswered = quiz ? quiz.every((_, i) => answers[i]) : false;

  return (
    <div>
      <h1 className="page-title">🧠 Quiz Generator</h1>
      <p className="page-desc">Auto-generate multiple-choice quizzes from any text or document.</p>

      <div className="card">
        <div className="form-group">
          <label className="form-label">Source Text</label>
          <textarea id="quiz-text" className="form-textarea" style={{ minHeight: 140 }}
            placeholder="Paste study material here…"
            value={text} onChange={e => setText(e.target.value)} />
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label className="form-label">Questions</label>
            <div style={{ display: 'flex', gap: 6 }}>
              {NUM_Q.map(n => (
                <button key={n} onClick={() => setNumQ(n)} style={{
                  flex: 1, padding: '8px 4px', borderRadius: 'var(--radius-sm)',
                  border: `2px solid ${numQ === n ? 'var(--accent)' : 'var(--border)'}`,
                  background: numQ === n ? 'rgba(108,99,255,0.1)' : 'var(--bg-surface2)',
                  color: numQ === n ? 'var(--accent)' : 'var(--text-secondary)',
                  fontFamily: 'inherit', fontWeight: 700, fontSize: 14, cursor: 'pointer',
                  transition: 'all 0.18s',
                }}>{n}</button>
              ))}
            </div>
          </div>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label className="form-label">Difficulty</label>
            <div style={{ display: 'flex', gap: 6 }}>
              {DIFFICULTY.map(d => {
                const emoji = d === 'easy' ? '🟢' : d === 'medium' ? '🟡' : '🔴';
                return (
                  <button key={d} onClick={() => setDiff(d)} style={{
                    flex: 1, padding: '8px 4px', borderRadius: 'var(--radius-sm)',
                    border: `2px solid ${diff === d ? 'var(--accent)' : 'var(--border)'}`,
                    background: diff === d ? 'rgba(108,99,255,0.1)' : 'var(--bg-surface2)',
                    color: diff === d ? 'var(--accent)' : 'var(--text-secondary)',
                    fontFamily: 'inherit', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                    transition: 'all 0.18s',
                    textTransform: 'capitalize',
                  }}>{emoji} {d}</button>
                );
              })}
            </div>
          </div>
        </div>

        <button id="btn-generate-quiz" className="btn btn-primary btn-full" onClick={handleGenerate} disabled={loading}>
          {loading ? <><div className="spinner" /> Generating Quiz…</> : '🧠 Generate Quiz'}
        </button>
        {error && <div className="alert alert-error mt-3">{error}</div>}
      </div>

      {/* Score Card */}
      {submitted && (
        <div className="card mt-4" style={{
          animation: 'fadeSlideIn 0.3s ease',
          background: pct >= 70 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.08)',
          borderColor: pct >= 70 ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
        }}>
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div style={{ fontSize: 48 }}>{pct >= 70 ? '🎉' : '📚'}</div>
            <div style={{ fontSize: 36, fontWeight: 800, color: pct >= 70 ? 'var(--success)' : 'var(--danger)' }}>
              {score} / {quiz.length}
            </div>
            <div style={{ fontSize: 16, color: 'var(--text-secondary)', marginTop: 4 }}>
              {pct}% — {pct >= 70 ? 'Great job!' : 'Keep studying!'}
            </div>
          </div>
        </div>
      )}

      {/* Questions */}
      {quiz && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 20 }}>
          {quiz.map((q, i) => (
            <div key={i} className="card" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
              <div style={{ marginBottom: 14 }}>
                <span className="badge badge-accent" style={{ marginRight: 8 }}>Q{i + 1}</span>
                <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{q.question}</span>
              </div>
              {Object.entries(q.options || {}).map(([key, val]) => {
                let cls = 'quiz-option';
                if (answers[i] === key) cls += ' selected';
                if (submitted && key === q.correct) cls += ' correct';
                if (submitted && answers[i] === key && key !== q.correct) cls += ' wrong';
                return (
                  <div key={key} className={cls}
                    onClick={() => !submitted && setAnswers({ ...answers, [i]: key })}>
                    <div className="quiz-option-key">{key}</div>
                    <div style={{ fontSize: 14 }}>{val}</div>
                    {submitted && key === q.correct && <span style={{ marginLeft: 'auto', color: 'var(--success)' }}>✓</span>}
                    {submitted && answers[i] === key && key !== q.correct && <span style={{ marginLeft: 'auto', color: 'var(--danger)' }}>✗</span>}
                  </div>
                );
              })}
            </div>
          ))}

          {!submitted && (
            <button id="btn-submit-quiz" className="btn btn-primary btn-full" onClick={() => setSubmitted(true)} disabled={!allAnswered}>
              {allAnswered ? '📊 Submit Answers' : `Answer all ${quiz.length} questions to submit`}
            </button>
          )}
          {submitted && (
            <button className="btn btn-secondary btn-full" onClick={() => { setQuiz(null); setAnswers({}); setSubmitted(false); setText(''); }}>
              🔄 Generate New Quiz
            </button>
          )}
        </div>
      )}
    </div>
  );
}
