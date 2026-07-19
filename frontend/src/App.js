import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { StudyProvider } from './context/StudyContext';
import './index.css';

import Sidebar    from './components/Sidebar';
import Landing    from './components/Landing';
import Upload     from './components/Upload';
import Summary    from './components/Summary';
import Simplify   from './components/Simplify';

import Quiz       from './components/Quiz';
import Flashcards from './components/Flashcards';
import Keywords   from './components/Keywords';
import Blog       from './components/Blog';
import SignIn     from './components/Auth/SignIn';
import SignUp     from './components/Auth/SignUp';

// Page titles for the topbar
const PAGE_TITLES = {
  '/':          '🏠 Home',
  '/upload':    '📤 Upload Document',
  '/summary':   '📝 AI Summary',
  '/simplify':  '✨ Simplify',

  '/quiz':      '🧠 Quiz Generator',
  '/flashcards':'🃏 Flashcards',
  '/keywords':  '🔑 Keywords',
  '/blog':      '📰 Blog',
  '/signin':    '🔓 Sign In',
  '/signup':    '🚀 Sign Up',
};

// Auth pages shown without sidebar layout
const AUTH_PATHS = ['/signin', '/signup'];

function AppLayout() {
  const location = useLocation();
  const isAuth = AUTH_PATHS.includes(location.pathname);

  if (isAuth) {
    return (
      <Routes>
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
      </Routes>
    );
  }

  const title = PAGE_TITLES[location.pathname] || 'bookrevision';

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        {/* Top Bar */}
        <header className="topbar">
          <div className="topbar-title">{title}</div>
          <div className="topbar-actions">
            <span className="badge badge-accent">v1.0</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-wrapper">
          <Routes>
            <Route path="/"           element={<Landing />} />
            <Route path="/upload"     element={<Upload />} />
            <Route path="/summary"    element={<Summary />} />
            <Route path="/simplify"   element={<Simplify />} />

            <Route path="/quiz"       element={<Quiz />} />
            <Route path="/flashcards" element={<Flashcards />} />
            <Route path="/keywords"   element={<Keywords />} />
            <Route path="/blog"       element={<Blog />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <StudyProvider>
        <Router>
          <AppLayout />
        </Router>
      </StudyProvider>
    </ThemeProvider>
  );
}

export default App;
