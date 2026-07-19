import React, { createContext, useContext, useState, useEffect } from 'react';

const StudyContext = createContext(null);

const STORAGE_KEY = 'edusummarize_study_session';

const initialState = {
  // Summary
  summaryInput: '',
  summaryLevel: '150w',
  summaryResult: null,
  summaryMultiResult: null,

  // Simplify
  simplifyInput: '',
  simplifyLevel: 'high_school',
  simplifyResult: null,
  simplifyWordInput: '',
  simplifyWordResult: null,
  simplifyTab: 0,

  // Quiz
  quizInput: '',
  quizNumQuestions: 5,
  quizDifficulty: 'medium',
  quizResult: null,
  quizAnswers: {},
  quizSubmitted: false,

  // Flashcards
  flashcardInput: '',
  flashcardNumCards: 10,
  flashcardResult: null,
  flashcardIndex: 0,
  flashcardFlipped: false,

  // Keywords
  keywordsInput: '',
  keywordTopN: 10,
  keywordsResult: null,
  keywordsPhrasesResult: null,

  // General / Legacy
  uploadedText: '',
  timestamp: null,
};

export function StudyProvider({ children }) {
  const [studySession, setStudySession] = useState(initialState);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setStudySession(parsed);
      }
    } catch (e) {
      console.error('Failed to load study session:', e);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save to localStorage whenever state changes
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(studySession));
      } catch (e) {
        console.error('Failed to save study session:', e);
      }
    }
  }, [studySession, isLoaded]);

  const updateSession = (updates) => {
    setStudySession(prev => ({
      ...prev,
      ...updates,
      timestamp: Date.now(),
    }));
  };

  const clearSession = () => {
    setStudySession(initialState);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = {
    studySession,
    updateSession,
    clearSession,
    isLoaded,
  };

  return <StudyContext.Provider value={value}>{children}</StudyContext.Provider>;
}

export function useStudySession() {
  const context = useContext(StudyContext);
  if (!context) {
    throw new Error('useStudySession must be used within a StudyProvider');
  }
  return context;
}
