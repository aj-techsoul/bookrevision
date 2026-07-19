import React, { useState } from 'react';

const posts = [
  {
    id: 1,
    tag: 'Study Tips',
    title: 'How AI Summarization is Changing the Way Students Study',
    desc: 'Discover how large language models can condense 50-page lecture notes into a crisp paragraph — and why this actually helps long-term retention.',
    emoji: '🧠',
    bg: 'linear-gradient(135deg, #6c63ff22, #8b85ff11)',
    author: 'Dr. Aisha Rahman',
    date: 'Jul 12, 2026',
    readTime: '5 min read',
    content: `Artificial intelligence is reshaping education in profound ways. Traditionally, students spent hours highlighting textbooks and writing manual notes. With AI summarization tools, this process can be reduced to seconds.

Research shows that spaced repetition combined with concise summaries leads to 40% better recall after 30 days compared to passive re-reading. When a student uploads a 50-page chapter and receives a crisp 150-word overview, they're not losing depth — they're gaining a scaffold on which to hang finer details.

The key is to use AI summaries as a starting point, not an endpoint. Read the summary, identify gaps in your understanding, then dive into the original text for those specific areas. This active engagement dramatically outperforms passive reading of the full text.

EduSummarize's multi-level summary feature (1-line, bullet, 50-word, 150-word) was designed with this learning science in mind.`,
  },
  {
    id: 2,
    tag: 'Product',
    title: 'Why Chunked Summarization Matters for Long PDFs',
    desc: 'Most AI summarizers silently truncate your document at 700 words. Here\'s how EduSummarize handles 200-page textbooks correctly.',
    emoji: '📄',
    bg: 'linear-gradient(135deg, #22c55e22, #4ade8011)',
    author: 'Engineering Team',
    date: 'Jul 8, 2026',
    readTime: '4 min read',
    content: `One of the most common problems with AI summarization tools is silent truncation. BART, one of the most popular summarization models, has a hard limit of 1,024 tokens — roughly 700 words.

When you upload a 100-page PDF, naive implementations simply discard everything after token 1,024. You get a summary of the first few pages, not the whole document. This is deeply misleading.

EduSummarize solves this with a map-reduce approach. The document is first split into token-safe chunks. Each chunk is summarized independently (the "map" phase). All chunk summaries are then merged and reduced into a final coherent summary (the "reduce" phase).

The result is a summary that faithfully represents the entire document — not just its introduction.`,
  },
  {
    id: 3,
    tag: 'Flashcards',
    title: '5 Science-Backed Reasons to Use Flashcards While Studying',
    desc: 'The testing effect, active recall, and spaced repetition — here\'s the cognitive science behind why flashcards work so well.',
    emoji: '🃏',
    bg: 'linear-gradient(135deg, #fb718522, #f4365611)',
    author: 'Dr. Leo Park',
    date: 'Jul 1, 2026',
    readTime: '6 min read',
    content: `The humble flashcard has survived centuries of educational fads for a simple reason: it works.

1. **The Testing Effect**: Retrieving information strengthens the memory trace far more than re-reading it. Every time you flip a card and recall the answer, you're reinforcing that neural pathway.

2. **Active Recall**: Unlike passive reading, flashcards force your brain to generate an answer — a cognitively demanding task that leads to deeper encoding.

3. **Spaced Repetition**: Review difficult cards more frequently, easy cards less so. This optimizes your study time.

4. **Metacognition**: Flashcards force you to rate your own confidence, building awareness of what you know versus what you think you know.

5. **Chunking**: Breaking large bodies of knowledge into card-sized pieces makes each concept concrete and testable.

EduSummarize auto-generates flashcards from your uploaded documents, applying all five principles automatically.`,
  },
  {
    id: 4,
    tag: 'AI',
    title: 'Ask Your Document Anything: How RAG Powers Smart Study Chat',
    desc: 'Retrieval-Augmented Generation lets you have intelligent conversations with your textbooks. Here\'s the tech behind it.',
    emoji: '💬',
    bg: 'linear-gradient(135deg, #38bdf822, #0ea5e911)',
    author: 'Engineering Team',
    date: 'Jun 25, 2026',
    readTime: '7 min read',
    content: `When you ask EduSummarize "What are the key differences between mitosis and meiosis?" after uploading your biology textbook, something sophisticated happens behind the scenes.

Your question is converted to a vector embedding — a numerical representation capturing its semantic meaning. This embedding is used to search a FAISS vector database containing embeddings of every chunk of your document.

The top-matching chunks are retrieved and fed to the language model as context, alongside your question. The model then generates an answer grounded in your specific document — not its general training data.

This approach, called Retrieval-Augmented Generation (RAG), means the chatbot's answers are always relevant to your specific material. It won't hallucinate facts from other textbooks or confabulate from general knowledge.

The result is a study companion that actually knows what you're studying.`,
  },
];

export default function Blog() {
  const [selected, setSelected] = useState(null);

  if (selected) {
    const post = posts.find(p => p.id === selected);
    return (
      <div>
        <button className="btn btn-ghost" onClick={() => setSelected(null)} style={{ marginBottom: 24 }}>
          ← Back to Blog
        </button>
        <div className="card" style={{ maxWidth: 720, margin: '0 auto' }}>
          <div style={{ fontSize: 64, textAlign: 'center', marginBottom: 20 }}>{post.emoji}</div>
          <div className="badge badge-accent" style={{ marginBottom: 12 }}>{post.tag}</div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 12, lineHeight: 1.3 }}>
            {post.title}
          </h1>
          <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-muted)', marginBottom: 28 }}>
            <span>✍️ {post.author}</span>
            <span>📅 {post.date}</span>
            <span>⏱ {post.readTime}</span>
          </div>
          <hr className="divider" />
          <div style={{ fontSize: 15, lineHeight: 1.8, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
            {post.content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">📰 Blog</h1>
      <p className="page-desc">Insights on AI, learning science, and how to study smarter.</p>

      <div className="blog-grid">
        {posts.map(post => (
          <div key={post.id} className="blog-card" onClick={() => setSelected(post.id)}>
            <div className="blog-card-cover" style={{ background: post.bg }}>
              {post.emoji}
            </div>
            <div className="blog-card-body">
              <div className="blog-card-tag">{post.tag}</div>
              <div className="blog-card-title">{post.title}</div>
              <div className="blog-card-desc">{post.desc}</div>
              <div className="blog-card-meta">
                <span>{post.author}</span>
                <span>{post.readTime}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
