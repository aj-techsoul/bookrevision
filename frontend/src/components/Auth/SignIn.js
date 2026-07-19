import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

export default function SignIn() {
  const navigate = useNavigate();
  const [form, setForm]       = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [showPass, setShowPass] = useState(false);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    if (!form.email.trim() || !form.password) { setError('Please fill in all fields.'); return; }
    setLoading(true); setError('');
    try {
      const res = await axios.post('/api/auth/signin', {
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });
      localStorage.setItem('edu-token',    res.data.access_token);
      localStorage.setItem('edu-username', res.data.user.name);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Sign in failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const eyeBtnStyle = {
    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
    background: 'none', border: 'none', cursor: 'pointer', fontSize: 16,
    color: 'var(--text-muted)', padding: '2px 4px',
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="auth-logo-icon">🎓</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>EduSummarize AI</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Welcome back</div>
          </div>
        </div>

        <h1 className="auth-title">Sign In</h1>
        <p className="auth-sub">Enter your credentials to access your account.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="signin-email">Email Address</label>
            <input
              id="signin-email"
              className="form-input"
              type="email"
              name="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signin-password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="signin-password"
                className="form-input"
                type={showPass ? 'text' : 'password'}
                name="password"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
                style={{ paddingRight: 40 }}
              />
              <button type="button" style={eyeBtnStyle} onClick={() => setShowPass(p => !p)} tabIndex={-1}>
                {showPass ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {error && (
            <div className="alert alert-error mb-4">⚠️ {error}</div>
          )}

          <button
            id="signin-submit"
            type="submit"
            className="btn btn-primary btn-full"
            style={{ marginTop: 8 }}
            disabled={loading}
          >
            {loading ? <><div className="spinner" />  Signing In…</> : '🔓 Sign In'}
          </button>
        </form>

        <div className="divider-label" style={{ margin: '24px 0' }}>or</div>

        <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/signup" style={{ color: 'var(--accent)', fontWeight: 600, textDecoration: 'none' }}>
            Create one →
          </Link>
        </p>

        <p style={{ textAlign: 'center', marginTop: 12 }}>
          <Link to="/" style={{ fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none' }}>
            ← Back to Home
          </Link>
        </p>
      </div>
    </div>
  );
}
