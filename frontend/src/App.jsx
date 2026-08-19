import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3002'

/* ────────────────────────────────────────────────────────────────────
 * Mascot — a tiny inline SVG bunny with expressive eyes.
 * Used in two sizes: 56px (header) and 110px (upload screen).
 * ──────────────────────────────────────────────────────────────────── */
function Mascot({ small = false, mood = 'happy' }) {
  return (
    <svg
      className={small ? 'mascot small' : 'mascot'}
      viewBox="0 0 120 120"
      role="img"
      aria-label="Kahani bunny mascot"
    >
      <defs>
        <linearGradient id="bodyG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFE0EC" />
          <stop offset="1" stopColor="#E2D6FF" />
        </linearGradient>
      </defs>

      {/* Ears */}
      <ellipse cx="44" cy="22" rx="8" ry="20" fill="url(#bodyG)" />
      <ellipse cx="44" cy="22" rx="3.5" ry="14" fill="#FFD6E7" />
      <ellipse cx="76" cy="22" rx="8" ry="20" fill="url(#bodyG)" />
      <ellipse cx="76" cy="22" rx="3.5" ry="14" fill="#FFD6E7" />

      {/* Head */}
      <circle cx="60" cy="62" r="34" fill="url(#bodyG)" />

      {/* Cheeks */}
      <circle cx="42" cy="72" r="6" fill="#FFD6E7" opacity="0.7" />
      <circle cx="78" cy="72" r="6" fill="#FFD6E7" opacity="0.7" />

      {/* Eyes */}
      {mood === 'happy' && (
        <>
          <circle cx="50" cy="58" r="4" fill="#3a2a3a" />
          <circle cx="70" cy="58" r="4" fill="#3a2a3a" />
          <circle cx="51.5" cy="56.5" r="1.5" fill="white" />
          <circle cx="71.5" cy="56.5" r="1.5" fill="white" />
        </>
      )}
      {mood === 'thinking' && (
        <>
          <path d="M46 58 Q50 54 54 58" stroke="#3a2a3a" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d="M66 58 Q70 54 74 58" stroke="#3a2a3a" strokeWidth="3" fill="none" strokeLinecap="round" />
        </>
      )}

      {/* Nose */}
      <ellipse cx="60" cy="70" rx="2.5" ry="1.8" fill="#a78bd9" />

      {/* Mouth */}
      <path d="M60 72 Q60 78 56 78" stroke="#3a2a3a" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M60 72 Q60 78 64 78" stroke="#3a2a3a" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  )
}

/* ────────────────────────────────────────────────────────────────────
 * Upload screen
 * ──────────────────────────────────────────────────────────────────── */
function UploadScreen({ onStoryLoaded }) {
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [pastedText, setPastedText] = useState('')
  const [mode, setMode] = useState('upload') // 'upload' | 'paste'

  const submitFile = async (file) => {
    setError(null)
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: fd })
      if (!res.ok) {
        const j = await res.json().catch(() => ({}))
        throw new Error(j.detail || `Upload failed (${res.status})`)
      }
      const tokens = await res.json()
      onStoryLoaded({ tokens, filename: file.name })
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const submitText = async () => {
    if (!pastedText.trim()) return
    setError(null)
    setBusy(true)
    try {
      const res = await fetch(`${API_BASE}/api/tokenize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pastedText }),
      })
      if (!res.ok) {
        const j = await res.json().catch(() => ({}))
        throw new Error(j.detail || `Tokenize failed (${res.status})`)
      }
      const tokens = await res.json()
      onStoryLoaded({ tokens, filename: 'Pasted story' })
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) submitFile(file)
  }

  return (
    <div className="screen">
      <div className="upload-card">
        <div className="mascot-row">
          <Mascot mood="happy" />
        </div>
        <h1>Kahani</h1>
        <p className="subtitle">
          Upload a story and watch it come alive with signs! <br />
          Read along with the bunny — every word gets its own sign video.
        </p>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 20 }}>
          <button
            className="alt-toggle"
            style={{ background: mode === 'upload' ? '#f3edff' : 'none', borderColor: mode === 'upload' ? '#a78bd9' : '#c7c2e0' }}
            onClick={() => setMode('upload')}
          >
            Upload file
          </button>
          <button
            className="alt-toggle"
            style={{ background: mode === 'paste' ? '#f3edff' : 'none', borderColor: mode === 'paste' ? '#a78bd9' : '#c7c2e0' }}
            onClick={() => setMode('paste')}
          >
            Paste text
          </button>
        </div>

        {mode === 'upload' ? (
          <div className="upload-area">
            <div
              className={'drop-zone' + (dragOver ? ' dragover' : '')}
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <div className="big-emoji">📖</div>
              <p><strong>Drag a story file here</strong></p>
              <p>or</p>
              <label className="file-picker-button">
                Choose a file
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.docx"
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) submitFile(f)
                  }}
                />
              </label>
              <p style={{ marginTop: 14, fontSize: 13 }}>.txt · .pdf · .docx</p>
            </div>
          </div>
        ) : (
          <div className="text-paste-area">
            <textarea
              placeholder="Paste your story here…"
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              rows={8}
            />
            <div style={{ marginTop: 14 }}>
              <button
                className="file-picker-button"
                disabled={!pastedText.trim() || busy}
                onClick={submitText}
                style={{ opacity: !pastedText.trim() || busy ? 0.5 : 1 }}
              >
                {busy ? 'Reading…' : 'Read to me!'}
              </button>
            </div>
          </div>
        )}

        {busy && <p style={{ marginTop: 12, color: '#a78bd9' }}>Getting the story ready…</p>}
        {error && <div className="error-banner">⚠️ {error}</div>}
      </div>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────
 * Preview screen — word inventory + start / change story
 * ──────────────────────────────────────────────────────────────────── */
function PreviewScreen({ story, onPlay, onChange }) {
  const { tokens, filename } = story
  const stats = useMemo(() => {
    const signs = tokens.filter((t) => !t.is_fingerspelling).length
    const fs = tokens.length - signs
    return { total: tokens.length, signs, fingerspell: fs }
  }, [tokens])

  const fsPct = stats.total === 0 ? 0 : Math.round((stats.fingerspell / stats.total) * 100)

  return (
    <div className="screen">
      <div className="preview-card">
        <h2>Ready to read: <em style={{ color: '#3a2a3a' }}>{filename}</em></h2>
        <div className="preview-summary">
          <span className="summary-pill">{stats.total} words</span>
          <span className="summary-pill good">{stats.signs} have sign videos</span>
          <span className={'summary-pill ' + (fsPct > 60 ? 'warn' : '')}>
            {stats.fingerspell} will be fingerspelled
          </span>
        </div>

        <div className="preview-words">
          {tokens.map((t, i) => (
            <span
              key={i}
              className={'preview-word ' + (t.is_fingerspelling ? 'fingerspell' : 'has-sign')}
              title={t.is_fingerspelling ? 'Will be fingerspelled letter by letter' : 'Has a sign video'}
            >
              {t.display_word}
            </span>
          ))}
        </div>

        <div className="preview-actions">
          <button className="big-button play" onClick={onPlay}>
            ▶ Play story
          </button>
          <button className="alt-toggle" onClick={onChange}>
            Pick a different story
          </button>
        </div>
      </div>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────
 * Playback screen — the core experience.
 *
 * Sync strategy (per the spec): a single SpeechSynthesisUtterance drives
 * word-by-word timing via its onboundary event. We map charIndex back to
 * a token index by walking the original display text and matching each
 * token's display_word to a substring. That same token index drives both
 * the text-highlight and the video swap. One event → one update → no
 * drift between the three channels.
 *
 * When a token has no sign_video, we fall back to fingerspelling: split
 * the lemma into letters and queue the per-letter clips from
 * /static/signs/_letters/<letter>.mp4 in sequence. The active letter
 * gets a highlighted chip below the video.
 *
 * Speed toggle changes utterance.rate (0.8 = slow, 1.0 = normal).
 * ──────────────────────────────────────────────────────────────────── */
function PlaybackScreen({ story, onExit }) {
  const { tokens } = story

  const [activeIdx, setActiveIdx] = useState(-1)
  const [activeLetter, setActiveLetter] = useState(0)
  const [letterSequence, setLetterSequence] = useState([]) // for fingerspell mode
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1.0)

  const videoRef = useRef(null)
  const utteranceRef = useRef(null)
  const cancelledRef = useRef(false)

  // Build the source string the browser will speak. We use the
  // display_word joined by spaces — exactly the same order as the
  // tokens array, so onboundary → token index mapping is deterministic.
  const sourceText = useMemo(() => tokens.map((t) => t.display_word).join(' '), [tokens])

  // Pre-compute the cumulative character offset of each token within
  // sourceText. This lets us map SpeechSynthesisEvent.charIndex back to
  // a token index in O(1).
  const tokenOffsets = useMemo(() => {
    const offsets = []
    let pos = 0
    for (const t of tokens) {
      offsets.push(pos)
      pos += t.display_word.length + 1 // +1 for the space separator
    }
    return offsets
  }, [tokens])

  const findTokenIdx = useCallback(
    (charIndex) => {
      // Binary search for the token whose [start, end) range contains charIndex.
      let lo = 0
      let hi = tokens.length - 1
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1
        if (tokenOffsets[mid] <= charIndex) lo = mid
        else hi = mid - 1
      }
      return lo
    },
    [tokens, tokenOffsets]
  )

  // Update which video is shown based on the active token.
  useEffect(() => {
    if (activeIdx < 0 || activeIdx >= tokens.length) return
    const tok = tokens[activeIdx]
    if (tok.is_fingerspelling) {
      // Build the letter clip sequence from the lemma.
      const letters = tok.lemma.toLowerCase().split('').filter((c) => /[a-z]/.test(c))
      setLetterSequence(letters)
      setActiveLetter(0)
    } else {
      setLetterSequence([])
    }
  }, [activeIdx, tokens])

  // When the active letter changes (within a fingerspelling word),
  // point the video at that letter's clip and restart playback.
  useEffect(() => {
    if (letterSequence.length === 0) return
    const v = videoRef.current
    if (!v) return
    const src = `/static/signs/_letters/${letterSequence[activeLetter]}.mp4`
    v.src = src
    v.loop = true
    v.play().catch(() => {})
  }, [letterSequence, activeLetter])

  // Advance to next letter when the current letter clip ends.
  const onLetterVideoEnded = () => {
    if (letterSequence.length === 0) return
    if (activeLetter < letterSequence.length - 1) {
      setActiveLetter((i) => i + 1)
    } else {
      // Restart the whole word so fingerspelling loops while the
      // utterance is still talking.
      setActiveLetter(0)
    }
  }

  const playFromStart = useCallback(() => {
    if (!('speechSynthesis' in window)) {
      alert('Sorry — your browser does not support speech synthesis.')
      return
    }
    cancelledRef.current = false
    setActiveIdx(0)
    setPlaying(true)

    // Cancel anything in flight first.
    window.speechSynthesis.cancel()

    const u = new SpeechSynthesisUtterance(sourceText)
    u.rate = speed
    u.pitch = 1.05 // a touch higher for kids
    u.lang = 'en-US'
    u.onboundary = (e) => {
      if (cancelledRef.current) return
      // Some engines fire onboundary with charName='sentence' instead
      // of useful charIndex — guard.
      if (typeof e.charIndex !== 'number' || e.charIndex < 0) return
      const idx = findTokenIdx(e.charIndex)
      if (idx !== activeIdxRef.current) {
        activeIdxRef.current = idx
        setActiveIdx(idx)
      }
    }
    u.onend = () => {
      if (cancelledRef.current) return
      setPlaying(false)
      setActiveIdx(-1)
    }
    u.onerror = () => {
      setPlaying(false)
      setActiveIdx(-1)
    }

    utteranceRef.current = u
    activeIdxRef.current = 0
    window.speechSynthesis.speak(u)
  }, [sourceText, speed, findTokenIdx])

  // Mirror activeIdx into a ref so the onboundary closure sees the
  // latest value without re-binding the utterance on every keystroke.
  const activeIdxRef = useRef(-1)
  useEffect(() => {
    activeIdxRef.current = activeIdx
  }, [activeIdx])

  const pause = () => {
    cancelledRef.current = true
    window.speechSynthesis.cancel()
    setPlaying(false)
  }

  const restart = () => {
    cancelledRef.current = true
    window.speechSynthesis.cancel()
    // Reset video.
    const v = videoRef.current
    if (v) {
      v.pause()
      v.removeAttribute('src')
      v.load()
    }
    setActiveIdx(-1)
    setActiveLetter(0)
    setLetterSequence([])
    // Kick off a fresh play after a tick so React state settles.
    setTimeout(playFromStart, 60)
  }

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      cancelledRef.current = true
      window.speechSynthesis.cancel()
    }
  }, [])

  const activeToken = activeIdx >= 0 ? tokens[activeIdx] : null
  const currentVideoSrc = (() => {
    if (!activeToken) return null
    if (activeToken.is_fingerspelling) {
      const letter = letterSequence[activeLetter] || letterSequence[0]
      return letter ? `/static/signs/_letters/${letter}.mp4` : null
    }
    return activeToken.sign_video
  })()

  return (
    <div className="screen">
      <div className="playback">
        <div className="text-panel">
          <div className="text-flow">
            {tokens.map((t, i) => {
              const isActive = i === activeIdx
              const isPast = activeIdx > i && activeIdx !== -1
              return (
                <span
                  key={i}
                  className={
                    'word ' +
                    (isActive ? 'active ' : '') +
                    (t.is_fingerspelling ? 'fingerspell' : 'sign-hit')
                  }
                  style={{ opacity: isPast ? 0.55 : 1 }}
                >
                  {t.display_word}
                </span>
              )
            })}
          </div>

          <div className="controls">
            {!playing ? (
              <button className="big-button play" onClick={playFromStart}>
                ▶ Play
              </button>
            ) : (
              <button className="big-button" onClick={pause}>
                ⏸ Pause
              </button>
            )}
            <button className="big-button restart" onClick={restart}>
              ↻ Restart
            </button>
            <div className="speed-toggle" role="group" aria-label="Speed">
              <button className={speed <= 0.85 ? 'active' : ''} onClick={() => setSpeed(0.8)}>
                Slow
              </button>
              <button className={speed > 0.85 ? 'active' : ''} onClick={() => setSpeed(1.0)}>
                Normal
              </button>
            </div>
            <button className="alt-toggle" onClick={onExit}>
              New story
            </button>
          </div>
        </div>

        <div className="video-panel">
          <div className="video-frame">
            {currentVideoSrc ? (
              <video
                ref={videoRef}
                key={currentVideoSrc}
                autoPlay
                muted
                playsInline
                onEnded={onLetterVideoEnded}
              >
                <source src={currentVideoSrc} type="video/mp4" />
              </video>
            ) : (
              <div style={{ textAlign: 'center', color: '#a78bd9' }}>
                <Mascot small mood="thinking" />
                <p style={{ marginTop: 12, fontWeight: 600 }}>Press Play to begin</p>
              </div>
            )}
          </div>
          {activeToken && (
            <div className="video-caption">
              <strong>{activeToken.display_word}</strong>
              {activeToken.is_fingerspelling
                ? 'Fingerspelling…'
                : activeToken.sign_video
                ? 'Sign video'
                : ''}
              {letterSequence.length > 0 && (
                <div className="letter-row">
                  {letterSequence.map((ch, i) => (
                    <span key={i} className={'letter-chip ' + (i === activeLetter ? 'active' : '')}>
                      {ch.toUpperCase()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────────
 * App shell
 * ──────────────────────────────────────────────────────────────────── */
export default function App() {
  const [story, setStory] = useState(null) // { tokens, filename } | null
  const [screen, setScreen] = useState('upload') // 'upload' | 'preview' | 'play'

  const onStoryLoaded = (s) => {
    setStory(s)
    setScreen('preview')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand-mark" aria-hidden="true">🐰</div>
        <div className="brand">Kahani</div>
        <div style={{ marginLeft: 'auto', color: '#a78bd9', fontWeight: 600 }}>
          Story time with signs
        </div>
      </header>

      {screen === 'upload' && <UploadScreen onStoryLoaded={onStoryLoaded} />}
      {screen === 'preview' && story && (
        <PreviewScreen
          story={story}
          onPlay={() => setScreen('play')}
          onChange={() => {
            setStory(null)
            setScreen('upload')
          }}
        />
      )}
      {screen === 'play' && story && (
        <PlaybackScreen
          story={story}
          onExit={() => {
            setStory(null)
            setScreen('upload')
          }}
        />
      )}

      <footer className="app-footer">
        Sign clips courtesy of the <a href="https://zenodo.org/records/4010759" target="_blank" rel="noreferrer">INCLUDE dataset</a>{' '}
        (Sridhar et al., ACM MM 2020) — licensed{' '}
        <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC-BY-4.0</a>.
        <br />
        Kahani prototype · local dev only
      </footer>
    </div>
  )
}