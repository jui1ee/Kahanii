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
  const [speed, setSpeed] = useState(0.8)   // kid-friendly default; user can hit Normal for 1.0×

  const videoRef = useRef(null)
  const utteranceRef = useRef(null)
  const cancelledRef = useRef(false)
  const gapTimerRef = useRef(null)

  // Kid-friendly default: each spoken unit (single letter for fingerspell
  // words, whole word for sign-video) gets exactly UNIT_DURATION_MS of
  // stage time. Audio starts at t=0; a setTimeout fires at UNIT_DURATION_MS
  // to start the next unit. We deliberately do NOT wait for the audio
  // utterance's onend or the <video> element's onended — both can fail to
  // fire reliably, and either way the timer gives a predictable cadence.
  const UNIT_DURATION_MS = 1350

  // Post-roll hold after the last unit speaks. Without this, the final
  // word/letter is shown for its full UNIT_DURATION_MS but then resets
  // immediately, which feels abrupt on short stories ("night" alone gets
  // its last letter cut off mid-gesture). Hold the last active state for
  // this many ms before clearing.
  const POST_ROLL_MS = 700

  // For each token, build a "spoken surface".
  //   - sign_video token: surface = display_word.
  //   - fingerspell token: surface = uppercased letters separated by ". "
  //     with a trailing ".", e.g. "T. H. E.". The trailing "." forces the
  //     TTS engine to insert a brief pause between letters.
  // We no longer need per-letter charIndex spans — the new playback walks
  // spokenUnits and speaks each unit (letter or whole word) as its own
  // utterance with an explicit gap between them.
  const spokenSegments = useMemo(() => {
    return tokens.map((t, idx) => {
      if (!t.is_fingerspelling) {
        return { tokenIdx: idx, kind: 'word', surface: t.display_word }
      }
      const chars = t.display_word
        .toLowerCase()
        .split('')
        .filter((c) => /[a-z0-9]/.test(c))
      if (chars.length === 0) {
        return { tokenIdx: idx, kind: 'word', surface: t.display_word }
      }
      const surface = chars
        .map((ch) => ch.toUpperCase())
        .reduce((acc, ch, i) => acc + (i === 0 ? '' : '. ') + ch, '') + '.'
      return { tokenIdx: idx, kind: 'letters', surface, letters: chars.map((c) => c.toUpperCase()) }
    })
  }, [tokens])

  // Flatten spokenSegments into one entry per spoken unit. Each unit is
  // either a single letter/digit (for fingerspelled tokens) or a whole
  // word (for sign_video tokens). playFromStart walks this list and speaks
  // each unit with an explicit gap between them.
  const spokenUnits = useMemo(() => {
    const units = []
    for (const seg of spokenSegments) {
      if (seg.kind === 'word') {
        units.push({ tokenIdx: seg.tokenIdx, letterIdx: 0, surface: seg.surface })
      } else {
        for (let li = 0; li < seg.letters.length; li++) {
          units.push({
            tokenIdx: seg.tokenIdx,
            letterIdx: li,
            surface: seg.letters[li],
          })
        }
      }
    }
    return units
  }, [spokenSegments])

  // Update which video is shown based on the active token.
  useEffect(() => {
    if (activeIdx < 0 || activeIdx >= tokens.length) return
    const tok = tokens[activeIdx]
    if (tok.is_fingerspelling) {
      // Build the per-character clip sequence from the display word.
      // Each entry is { char, kind: 'letter' | 'digit' } so the renderer
      // can pick the right clip folder for letters vs digits.
      const seq = tok.display_word
        .toLowerCase()
        .split('')
        .map((c) => {
          if (/[a-z]/.test(c)) return { char: c, kind: 'letter' }
          if (/[0-9]/.test(c)) return { char: c, kind: 'digit' }
          return null
        })
        .filter(Boolean)
      setLetterSequence(seq)
      setActiveLetter(0)
    } else {
      setLetterSequence([])
    }
  }, [activeIdx, tokens])

  // When the active character changes (within a fingerspelling word),
  // point the video at that letter's clip and restart playback. The
  // explicit [currentVideoSrc] hook below handles sign-video tokens
  // (where letterSequence is empty).
  useEffect(() => {
    if (letterSequence.length === 0) return
    const v = videoRef.current
    if (!v) return
    const item = letterSequence[activeLetter]
    const folder = item.kind === 'digit' ? '_digits' : '_letters'
    const src = `/static/signs/${folder}/${item.char}.mp4`
    v.src = src
    v.loop = true
    v.play().catch(() => {})
  }, [letterSequence, activeLetter])

  // Advance is driven by SpeechSynthesisUtterance.onboundary (audio is the
// timeline). The video element just loops the current letter's clip.

  const playFromStart = useCallback(() => {
    if (!('speechSynthesis' in window)) {
      alert('Sorry — your browser does not support speech synthesis.')
      return
    }
    cancelledRef.current = false
    if (gapTimerRef.current) {
      clearTimeout(gapTimerRef.current)
      gapTimerRef.current = null
    }
    setActiveIdx(-1)
    setActiveLetter(0)
    setLetterSequence([])
    setPlaying(true)

    // Cancel anything in flight first.
    window.speechSynthesis.cancel()

    // Walk spokenUnits sequentially. Each unit gets exactly UNIT_DURATION_MS
    // of stage time: at t=0 we speak the surface (a letter/digit for
    // fingerspell tokens, the whole word for sign-video); a setTimeout
    // at t=UNIT_DURATION_MS advances to the next unit. Audio and video
    // do NOT gate the advance — they've been unreliable in browsers
    // (especially for short utterances and same-clip repeated units).
    // The <video> element is driven by separate effects/handlers and
    // simply shows whatever clip corresponds to the active unit at any
    // given moment.
    const speakUnit = (idx) => {
      if (cancelledRef.current) return
      if (idx >= spokenUnits.length) {
        // End of story: don't reset immediately — hold the last active
        // word/letter for POST_ROLL_MS so the user actually sees it.
        gapTimerRef.current = setTimeout(() => {
          gapTimerRef.current = null
          if (cancelledRef.current) return
          setPlaying(false)
          setActiveIdx(-1)
          setActiveLetter(0)
          setLetterSequence([])
          utteranceRef.current = null
        }, POST_ROLL_MS)
        return
      }
      const unit = spokenUnits[idx]
      const u = new SpeechSynthesisUtterance(unit.surface)
      u.rate = speed
      u.pitch = 1.05
      u.lang = 'en-US'
      u.onstart = () => {
        if (cancelledRef.current) return
        activeStateRef.current = { tokenIdx: unit.tokenIdx, letterIdx: unit.letterIdx }
        setActiveIdx(unit.tokenIdx)
        setActiveLetter(unit.letterIdx)
      }
      u.onerror = () => {
        if (cancelledRef.current) return
        setPlaying(false)
        setActiveIdx(-1)
        setActiveLetter(0)
        setLetterSequence([])
      }
      utteranceRef.current = u
      window.speechSynthesis.speak(u)
      // Schedule the advance. We rely on this timer alone — not on
      // u.onend or <video>.onEnded — because those have been the source
      // of stuck-state bugs in repeated same-clip units and short
      // utterances.
      gapTimerRef.current = setTimeout(() => {
        gapTimerRef.current = null
        speakUnit(idx + 1)
      }, UNIT_DURATION_MS)
    }

    speakUnit(0)
  }, [spokenUnits, speed])

  // Mirror the active (tokenIdx, letterIdx) into a ref. Kept for any future
  // async callback that needs the latest value without re-binding.
  const activeStateRef = useRef({ tokenIdx: -1, letterIdx: 0 })

  const pause = () => {
    cancelledRef.current = true
    window.speechSynthesis.cancel()
    if (gapTimerRef.current) {
      clearTimeout(gapTimerRef.current)
      gapTimerRef.current = null
    }
    setPlaying(false)
  }

  const restart = () => {
    cancelledRef.current = true
    window.speechSynthesis.cancel()
    if (gapTimerRef.current) {
      clearTimeout(gapTimerRef.current)
      gapTimerRef.current = null
    }
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
      if (gapTimerRef.current) {
        clearTimeout(gapTimerRef.current)
        gapTimerRef.current = null
      }
    }
  }, [])

  const activeToken = activeIdx >= 0 ? tokens[activeIdx] : null
  const currentVideoSrc = (() => {
    if (!activeToken) return null
    if (activeToken.is_fingerspelling) {
      const item = letterSequence[activeLetter] || letterSequence[0]
      if (!item) return null
      const folder = item.kind === 'digit' ? '_digits' : '_letters'
      return `/static/signs/${folder}/${item.char}.mp4`
    }
    return activeToken.sign_video
  })()

  // Explicit src+play hook for sign-video tokens (and any token whose
  // currentVideoSrc just changed). Force the video element to load the
  // new clip and start playing. We .load() before .play() to make sure
  // the browser actually fetches the media — relying on autoPlay +
  // <source src> alone is unreliable when an element persists across
  // many unit transitions.
  useEffect(() => {
    const v = videoRef.current
    if (!v || !currentVideoSrc) return
    // Always reset and reload. Cheap for matching src (browser no-ops
    // fetch); critical for a fresh src on a persistent element.
    v.src = currentVideoSrc
    v.currentTime = 0
    v.load()
    v.play().catch(() => {})
  }, [currentVideoSrc])

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
                autoPlay
                muted
                playsInline
                preload="auto"
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
                  {letterSequence.map((item, i) => (
                    <span
                      key={i}
                      className={
                        'letter-chip ' +
                        (i === activeLetter ? 'active ' : '') +
                        (item.kind === 'digit' ? 'digit' : 'letter')
                      }
                    >
                      {item.kind === 'digit' ? item.char : item.char.toUpperCase()}
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