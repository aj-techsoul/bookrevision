import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useStudySession } from '../context/StudyContext';

const navItems = [
  { path: '/',          label: 'Home',       icon: '🏠', section: 'main' },
  { path: '/upload',    label: 'Upload',     icon: '📤', section: 'tools' },
  { path: '/summary',   label: 'Summary',    icon: '📝', section: 'tools' },
  { path: '/simplify',  label: 'Simplify',   icon: '✨', section: 'tools' },

  { path: '/quiz',      label: 'Quiz',       icon: '🧠', section: 'tools' },
  { path: '/flashcards',label: 'Flashcards', icon: '🃏', section: 'tools' },
  { path: '/keywords',  label: 'Keywords',   icon: '🔑', section: 'tools' },
  { path: '/blog',      label: 'Blog',       icon: '📰', section: 'more' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const { clearSession, studySession } = useStudySession();

  const authToken = localStorage.getItem('edu-token');
  const userName  = localStorage.getItem('edu-username') || '';

  const handleSignOut = () => {
    localStorage.removeItem('edu-token');
    localStorage.removeItem('edu-username');
    navigate('/signin');
  };

  const handleClearSession = () => {
    // eslint-disable-next-line no-restricted-globals
    if (window.confirm('Clear all generated content? This will remove your summaries, quizzes, flashcards, and keywords.')) {
      clearSession();
    }
  };

  const hasContent = studySession.timestamp !== null;

  const sections = {
    main:  navItems.filter(i => i.section === 'main'),
    tools: navItems.filter(i => i.section === 'tools'),
    more:  navItems.filter(i => i.section === 'more'),
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <svg viewBox="0 0 24 24"><path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3zM5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82z"/></svg>
        </div>
        <div className="sidebar-logo-text">book<span>revision</span></div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {/* Main */}
        {sections.main.map(item => (
          <button
            key={item.path}
            className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        {/* Tools */}
        <div className="sidebar-section-label">AI Tools</div>
        {sections.tools.map(item => (
          <button
            key={item.path}
            className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        {/* More */}
        <div className="sidebar-section-label">Explore</div>
        {sections.more.map(item => (
          <button
            key={item.path}
            className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {/* Theme Toggle */}
        <button className="theme-toggle" onClick={toggleTheme} style={{width:'100%',border:'none',cursor:'pointer',textAlign:'left'}}>
          <span className="theme-toggle-label">
            {theme === 'dark' ? '🌙' : '☀️'}
            {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
          </span>
          <div className={`toggle-track ${theme === 'dark' ? 'on' : ''}`}>
            <div className="toggle-thumb" />
          </div>
        </button>

        {/* Clear Session Button */}
        {hasContent && (
          <button 
            className="btn btn-ghost btn-sm" 
            style={{width:'100%', justifyContent:'flex-start', marginTop: 8, color: 'var(--danger)'}} 
            onClick={handleClearSession}
          >
            🗑️ Clear Session
          </button>
        )}

        {/* Auth */}
        {authToken ? (
          <div style={{display:'flex', flexDirection:'column', gap:6}}>
            <div style={{fontSize:12, color:'var(--text-muted)', padding:'4px 4px 0'}}>
              👤 {userName || 'User'}
            </div>
            <button className="btn btn-ghost btn-sm" style={{width:'100%', justifyContent:'flex-start'}} onClick={handleSignOut}>
              🚪 Sign Out
            </button>
          </div>
        ) : (
          <div style={{display:'flex', gap:8}}>
            <button className="btn btn-secondary btn-sm" style={{flex:1}} onClick={() => navigate('/signin')}>Sign In</button>
            <button className="btn btn-primary btn-sm" style={{flex:1}} onClick={() => navigate('/signup')}>Sign Up</button>
          </div>
        )}
      </div>
    </aside>
  );
}
