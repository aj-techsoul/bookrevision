import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const levels = [
  { value: 'high_school',    label: 'High School' },
  { value: 'undergraduate',  label: 'Undergraduate' },
  { value: 'graduate',       label: 'Graduate / Postgrad' },
  { value: 'professional',   label: 'Professional' },
  { value: 'other',          label: 'Other' },
];

export default function SignUp() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', email: '', password: '', confirm: '', education_level: 'high_school'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [success, setSuccess] = useState('');
  const [showPass, setShowPass]   = useState(false);
  const [showConf, setShowConf]   = useState(false);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    if (!form.name.trim() || !form.email.trim() || !form.password) {
      setError('Please fill in all required fields.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(form.email)) { setError('Please enter a valid email address.'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return; }

    setLoading(true); setError(''); setSuccess('');
    try {
      const res = await axios.post('/api/auth/signup', {
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        education_level: form.education_level,
      });
      setSuccess('Account created successfully.');
      localStorage.setItem('edu-token',    res.data.access_token);
      localStorage.setItem('edu-username', res.data.user.name);
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg === 'Email already registered' || msg === 'Email already exists.') {
        setError('This email is already registered. Please sign in instead.');
      } else if (msg === 'Invalid email address.') {
        setError('Invalid email address.');
      } else if (msg === 'Password is too weak.') {
        setError('Password is too weak.');
      } else {
        setError(msg || 'Sign up failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const inputGroupStyle = { position: 'relative' };
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
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Create your free account</div>
          </div>
        </div>

        <h1 className="auth-title">Get Started</h1>
        <p className="auth-sub">Join thousands of students learning with AI.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="signup-name">Full Name <span style={{color:'var(--danger)'}}>*</span></label>
            <input
              id="signup-name" className="form-input" type="text" name="name"
              placeholder="Jane Smith" value={form.name} onChange={handleChange}
              autoComplete="name" required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-email">Email Address <span style={{color:'var(--danger)'}}>*</span></label>
            <input
              id="signup-email" className="form-input" type="email" name="email"
              placeholder="you@example.com" value={form.email} onChange={handleChange}
              autoComplete="email" required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-level">Education Level</label>
            <select
              id="signup-level" className="form-select" name="education_level"
              value={form.education_level} onChange={handleChange}
            >
              {levels.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-password">Password <span style={{color:'var(--danger)'}}>*</span></label>
            <div style={inputGroupStyle}>
              <input
                id="signup-password" className="form-input" type={showPass ? 'text' : 'password'}
                name="password" placeholder="Min. 6 characters" value={form.password}
                onChange={handleChange} autoComplete="new-password" required
                style={{ paddingRight: 40 }}
              />
              <button type="button" style={eyeBtnStyle} onClick={() => setShowPass(p => !p)} tabIndex={-1}>
                {showPass ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-confirm">Confirm Password <span style={{color:'var(--danger)'}}>*</span></label>
            <div style={inputGroupStyle}>
              <input
                id="signup-confirm" className="form-input" type={showConf ? 'text' : 'password'}
                name="confirm" placeholder="••••••••" value={form.confirm}
                onChange={handleChange} autoComplete="new-password" required
                style={{ paddingRight: 40 }}
              />
              <button type="button" style={eyeBtnStyle} onClick={() => setShowConf(p => !p)} tabIndex={-1}>
                {showConf ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {success && <div className="alert alert-success mb-4">🎉 {success}</div>}
          {error && <div className="alert alert-error mb-4">⚠️ {error}</div>}

          <button
            id="signup-submit" type="submit" className="btn btn-primary btn-full"
            style={{ marginTop: 8 }} disabled={loading}
          >
            {loading ? <><div className="spinner" />  Creating Account…</> : '🚀 Create Account'}
          </button>
        </form>

        <div className="divider-label" style={{ margin: '24px 0' }}>or</div>

        <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/signin" style={{ color: 'var(--accent)', fontWeight: 600, textDecoration: 'none' }}>
            Sign In →
          </Link>
        </p>
        <p style={{ textAlign: 'center', marginTop: 12 }}>
          <Link to="/" style={{ fontSize: 13, color: 'var(--text-muted)', textDecoration: 'none' }}>← Back to Home</Link>
        </p>
      </div>
    </div>
  );
}
