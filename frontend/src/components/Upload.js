import React, { useState, useCallback } from 'react';
import axios from 'axios';

export default function Upload() {
  const [file, setFile]         = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult]     = useState(() => {
    try {
      const stored = localStorage.getItem('edu-upload-result');
      if (stored) {
        const { data, timestamp } = JSON.parse(stored);
        if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
          return data;
        }
      }
    } catch (e) {}
    return null;
  });
  const [error, setError]       = useState(null);

  const validateFile = selectedFile => {
    if (!selectedFile) return false;
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
      setError(`Unsupported file type. Supported: ${allowedExtensions.join(', ')}`);
      setFile(null);
      return false;
    }
    const MAX_SIZE_MB = 10;
    if (selectedFile.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds the ${MAX_SIZE_MB}MB limit.`);
      setFile(null);
      return false;
    }
    return true;
  };

  const handleDrop = useCallback(e => {
    e.preventDefault(); setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setError(null); setResult(null); localStorage.removeItem('edu-upload-result');
      if (validateFile(dropped)) {
        setFile(dropped);
      }
    }
  }, [result]);

  const handleFileChange = e => {
    const selected = e.target.files[0];
    if (selected) {
      setError(null); setResult(null); localStorage.removeItem('edu-upload-result');
      if (validateFile(selected)) {
        setFile(selected);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) { setError('Please select a file first.'); return; }
    
    // Validate file size and type again before uploading
    if (!validateFile(file)) return;

    // Prevent duplicate uploads
    if (result && result.filename === file.name) {
      setError('This file is already active. Please select a different file.');
      return;
    }

    setUploading(true); setError(null); setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    const headers = { 'Content-Type': 'multipart/form-data' };
    const token = localStorage.getItem('edu-token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await axios.post('/api/upload', formData, {
        headers,
        onUploadProgress: e => setProgress(Math.round((e.loaded * 100) / e.total)),
      });
      setResult(res.data);
      localStorage.setItem('edu-upload-result', JSON.stringify({
        data: res.data,
        timestamp: Date.now()
      }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const copyText = () => {
    if (result?.full_text) navigator.clipboard.writeText(result.full_text);
  };

  return (
    <div>
      <h1 className="page-title">📤 Upload Document</h1>
      <p className="page-desc">Upload a PDF, DOCX, or TXT file to start AI-powered analysis.</p>

      {/* Drop Zone */}
      <div
        className={`dropzone ${dragging ? 'dragover' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <div className="dropzone-icon">
          {file || result ? '📄' : '☁️'}
        </div>
        {file ? (
          <>
            <div className="dropzone-title">{file.name}</div>
            <div className="dropzone-sub">{(file.size / 1024 / 1024).toFixed(2)} MB · Click to change</div>
          </>
        ) : result ? (
          <>
            <div className="dropzone-title">{result.filename}</div>
            <div className="dropzone-sub">Active Document · Click to upload a new one</div>
          </>
        ) : (
          <>
            <div className="dropzone-title">Drag & Drop your file here</div>
            <div className="dropzone-sub">or click to browse · PDF, DOCX, TXT supported</div>
          </>
        )}
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>
            <span>Processing document…</span>
            <span>{progress}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="text-muted mt-2" style={{ fontSize: 12 }}>
            Extracting text, generating embeddings…
          </div>
        </div>
      )}

      {/* Upload Button */}
      {!uploading && file && (
        <button
          id="upload-btn"
          className="btn btn-primary btn-full mt-4"
          onClick={handleUpload}
          disabled={!file}
        >
          🚀 Upload & Process Document
        </button>
      )}

      {/* Error */}
      {error && <div className="alert alert-error mt-4">⚠️ {error}</div>}

      {/* Result */}
      {result && (
        <div className="card mt-4" style={{ animation: 'fadeSlideIn 0.3s ease' }}>
          <div className="card-header">
            <div>
              <div className="card-title">✅ Document Processed</div>
              <div className="card-subtitle">{result.filename}</div>
            </div>
            <span className="badge badge-success">Ready</span>
          </div>

          {/* Stats */}
          <div className="stats-row">
            <div className="stat-pill">📄 {result.stats.total_chunks} chunks</div>
            <div className="stat-pill">📝 {result.stats.total_words?.toLocaleString()} words</div>
            <div className="stat-pill">⏱ {result.stats.estimated_reading_time_minutes} min read</div>
            <div className="stat-pill">🔑 ID: {result.document_id?.slice(0, 8)}…</div>
          </div>

          {/* Text Preview */}
          {result.full_text && (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginTop: 16, marginBottom: 8 }}>
                Extracted Text Preview {result.full_text_truncated && '(first 5000 chars)'}
              </div>
              <div className="result-box">
                <p style={{ maxHeight: 220, overflowY: 'auto' }}>{result.full_text}</p>
              </div>
              <div className="result-actions">
                <button className="btn btn-secondary btn-sm" onClick={copyText}>📋 Copy Text</button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
