import React from 'react';
import { useNavigate } from 'react-router-dom';

const features = [
  { icon: '📤', color: '#6c63ff', bg: 'rgba(108,99,255,0.12)', title: 'PDF Upload',     desc: 'Upload PDFs, DOCX, or TXT files and extract text instantly.',       path: '/upload'     },
  { icon: '📝', color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  title: 'AI Summary',     desc: 'Generate concise 1-line, bullet, 50-word, or 150-word summaries.',   path: '/summary'    },
  { icon: '✨', color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', title: 'Simplifier',     desc: 'Rewrite complex text into plain, easy-to-understand language.',       path: '/simplify'   },

  { icon: '🧠', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)',title: 'Quiz Generator', desc: 'Auto-generate multiple-choice quizzes from your study material.',     path: '/quiz'       },
  { icon: '🃏', color: '#fb7185', bg: 'rgba(251,113,133,0.12)',title: 'Flashcards',     desc: 'Create flip-card flashcards to memorize key concepts faster.',        path: '/flashcards' },
  { icon: '🔑', color: '#34d399', bg: 'rgba(52,211,153,0.12)', title: 'Keywords',       desc: 'Extract key terms and important phrases from any document.',          path: '/keywords'   },
];

const stats = [
  { value: '10K+', label: 'Documents Processed' },
  { value: '95%',  label: 'Summary Accuracy' },
  { value: '7',    label: 'AI Tools Built-in' },
  { value: 'Free', label: 'Always & Forever' },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div>
      {/* Hero */}
      <div className="hero">
        <div className="hero-badge">
          🚀 AI-Powered Learning Platform
        </div>
        <h1>
          Study Smarter with<br />
          <span className="gradient-text">AI-Powered Summaries</span>
        </h1>
        <p className="hero-sub">
          Upload any document and instantly get summaries, quizzes, flashcards,
          and AI chat — everything you need to learn faster.
        </p>
        <div className="hero-cta">
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/upload')}>
            📤 Upload a Document
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => navigate('/blog')}>
            📰 Read the Blog
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 48 }}>
        {stats.map(s => (
          <div key={s.label} className="card" style={{ padding: '16px 28px', textAlign: 'center', minWidth: 120 }}>
            <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--accent)' }}>{s.value}</div>
            <div className="text-muted" style={{ marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Feature Grid */}
      <div style={{ marginBottom: 12 }}>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>
          Everything You Need to Learn
        </h2>
        <p className="text-muted">Seven powerful AI tools in one seamless platform.</p>
      </div>
      <div className="feature-grid">
        {features.map(f => (
          <div key={f.path} className="feature-card" onClick={() => navigate(f.path)} style={{ cursor: 'pointer' }}>
            <div className="feature-card-icon" style={{ background: f.bg, color: f.color }}>
              {f.icon}
            </div>
            <div className="feature-card-title">{f.title}</div>
            <div className="feature-card-desc">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
