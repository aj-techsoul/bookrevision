import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

export default function Chat() {
  const [messages, setMessages] = useState(() => {
    try {
      const stored = localStorage.getItem('edu-chat-messages');
      if (stored) {
        const { data, timestamp } = JSON.parse(stored);
        if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
          return data;
        }
      }
    } catch (e) {}
    return [
      { role: 'bot', content: '👋 Hello! Upload a document first, then ask me anything about it.' }
    ];
  });

  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef        = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    localStorage.setItem('edu-chat-messages', JSON.stringify({
      data: messages,
      timestamp: Date.now()
    }));
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const res = await axios.post('/api/chat/chat', {
        question,
        k: 4,
        confidence_threshold: 0.3,
      });
      setMessages(prev => [
        ...prev,
        {
          role: 'bot',
          content: res.data.answer,
          confidence: res.data.confidence,
          sources: res.data.sources,
          found: res.data.found,
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'bot', content: '⚠️ Sorry, something went wrong. Please make sure a document is uploaded.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const clearChat = () => setMessages([{ role: 'bot', content: '👋 Hello! Upload a document first, then ask me anything about it.' }]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <h1 className="page-title">💬 AI Chat</h1>
        <button className="btn btn-ghost btn-sm" onClick={clearChat}>🗑 Clear</button>
      </div>
      <p className="page-desc">Ask questions about your uploaded documents using natural language.</p>

      <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 580 }}>
        {/* Messages */}
        <div className="chat-messages" style={{ flex: 1, maxHeight: 'none', overflowY: 'auto', padding: '4px 0' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role === 'user' ? 'user' : 'bot'}`}>
              <div>{msg.content}</div>
              {msg.role === 'bot' && msg.confidence !== undefined && (
                <div style={{ fontSize: 11, opacity: 0.7, marginTop: 6 }}>
                  📊 Confidence: {(msg.confidence * 100).toFixed(1)}% · {msg.sources?.length || 0} sources
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble bot">
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <div className="spinner spinner-dark" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Thinking…
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
          <div className="chat-input-row">
            <input
              id="chat-input"
              className="form-input"
              type="text"
              placeholder="Ask a question about your document… (Enter to send)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button
              id="chat-send"
              className="btn btn-primary"
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              ➤
            </button>
          </div>
          <div className="text-muted mt-2" style={{ fontSize: 12 }}>
            Tip: Upload a document on the Upload page before chatting.
          </div>
        </div>
      </div>
    </div>
  );
}
