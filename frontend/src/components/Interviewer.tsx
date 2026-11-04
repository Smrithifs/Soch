import { useEffect, useRef, useState } from 'react'
import { cx } from './ui'

/** Original illustrated interviewer avatar ("Ananya"). Mouth animates while speaking; blinks idly. */
export function InterviewerAvatar({ speaking, size = 168 }: { speaking: boolean; size?: number }) {
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <div className={cx('absolute inset-0 rounded-full bg-gradient-to-br from-violet-500/40 to-sky-500/30 blur-xl transition-opacity duration-500', speaking ? 'opacity-100' : 'opacity-40')} />
      <svg viewBox="0 0 200 200" className="relative h-full w-full">
        <defs>
          <clipPath id="iv-c"><circle cx="100" cy="100" r="96" /></clipPath>
          <linearGradient id="iv-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#1e1b4b" /><stop offset="1" stopColor="#0f172a" /></linearGradient>
        </defs>
        <circle cx="100" cy="100" r="96" fill="url(#iv-bg)" stroke="rgba(167,139,250,.5)" strokeWidth="2" />
        <g clipPath="url(#iv-c)">
          {/* hair back */}
          <path d="M42 120 C30 60 60 28 100 28 C140 28 170 60 158 120 L160 190 L40 190 Z" fill="#2b1a12" />
          {/* body / blazer */}
          <path d="M38 200 C42 160 70 146 100 146 C130 146 158 160 162 200 Z" fill="#4338ca" />
          <path d="M84 148 L100 176 L116 148 Z" fill="#e0e7ff" />
          {/* neck */}
          <rect x="88" y="128" width="24" height="24" rx="8" fill="#c68a63" />
          {/* face */}
          <ellipse cx="100" cy="98" rx="38" ry="44" fill="#d89b72" />
          {/* hair front / fringe */}
          <path d="M60 92 C60 56 84 44 104 46 C126 48 142 64 140 92 C130 74 112 64 92 66 C78 68 66 78 60 92 Z" fill="#2b1a12" />
          {/* earrings */}
          <circle cx="62" cy="108" r="3" fill="#fbbf24" /><circle cx="138" cy="108" r="3" fill="#fbbf24" />
          {/* brows */}
          <path d="M77 84 Q86 79 94 83" stroke="#2b1a12" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d="M106 83 Q114 79 123 84" stroke="#2b1a12" strokeWidth="3" fill="none" strokeLinecap="round" />
          {/* eyes (blink) */}
          <g className="iv-blink">
            <ellipse cx="85" cy="95" rx="5" ry="5.5" fill="#1f2937" /><ellipse cx="115" cy="95" rx="5" ry="5.5" fill="#1f2937" />
            <circle cx="86.5" cy="93.5" r="1.4" fill="#fff" /><circle cx="116.5" cy="93.5" r="1.4" fill="#fff" />
          </g>
          {/* nose */}
          <path d="M100 100 Q97 110 101 112" stroke="#b87a55" strokeWidth="2" fill="none" strokeLinecap="round" />
          {/* cheeks */}
          <circle cx="78" cy="112" r="6" fill="#f0a39a" opacity=".35" /><circle cx="122" cy="112" r="6" fill="#f0a39a" opacity=".35" />
          {/* mouth */}
          <g transform="translate(100 123)">
            {speaking
              ? <ellipse rx="9" ry="5" fill="#7f1d1d" className="iv-talk" />
              : <path d="M-10 -1 Q0 7 10 -1" stroke="#7f1d1d" strokeWidth="3" fill="none" strokeLinecap="round" />}
          </g>
        </g>
      </svg>
      <style>{`
        .iv-blink { transform-origin: 100px 95px; animation: ivblink 4.2s infinite; }
        @keyframes ivblink { 0%,94%,100% { transform: scaleY(1) } 96% { transform: scaleY(.1) } }
        .iv-talk { transform-origin: center; animation: ivtalk .22s ease-in-out infinite alternate; }
        @keyframes ivtalk { from { transform: scaleY(.25) } to { transform: scaleY(1.15) } }
      `}</style>
    </div>
  )
}

/** Speech helpers (browser built-ins; no network). */
export function useVoice() {
  const [speaking, setSpeaking] = useState(false)
  const [muted, setMuted] = useState(false)
  const voiceRef = useRef<SpeechSynthesisVoice | null>(null)
  useEffect(() => {
    const pick = () => {
      const vs = window.speechSynthesis?.getVoices() || []
      voiceRef.current = vs.find((v) => /Veena|Isha|Rishi|en-IN/i.test(v.name + v.lang) && /female|Veena|Isha/i.test(v.name)) ||
        vs.find((v) => /Samantha|Karen|Moira|Tessa|Victoria|Google UK English Female|Female/i.test(v.name)) || vs.find((v) => v.lang.startsWith('en')) || null
    }
    pick()
    window.speechSynthesis?.addEventListener?.('voiceschanged', pick)
    return () => { window.speechSynthesis?.cancel() }
  }, [])
  function speak(text: string, onEnd?: () => void) {
    const clean = text.replace(/[*`_#>]/g, '').replace(/\s+/g, ' ').trim()
    if (muted || !window.speechSynthesis) { setSpeaking(true); setTimeout(() => { setSpeaking(false); onEnd?.() }, Math.min(4000, clean.length * 35)); return }
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(clean)
    if (voiceRef.current) u.voice = voiceRef.current
    u.rate = 1.02; u.pitch = 1.05
    u.onstart = () => setSpeaking(true)
    u.onend = u.onerror = () => { setSpeaking(false); onEnd?.() }
    window.speechSynthesis.speak(u)
  }
  function stop() { window.speechSynthesis?.cancel(); setSpeaking(false) }
  return { speak, stop, speaking, muted, setMuted }
}

export function useDictation(onText: (t: string) => void) {
  const [listening, setListening] = useState(false)
  const recRef = useRef<any>(null)
  const SR: any = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  function toggle() {
    if (!SR) return alert('Voice answers need Chrome or Safari.')
    if (listening) { recRef.current?.stop(); return }
    const r = new SR()
    r.lang = 'en-IN'; r.interimResults = true; r.continuous = true
    let finalText = ''
    r.onresult = (e: any) => {
      let interim = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript + ' '
        else interim += e.results[i][0].transcript
      }
      onText((finalText + interim).trim())
    }
    r.onend = () => setListening(false)
    recRef.current = r; r.start(); setListening(true)
  }
  return { listening, toggle, supported: !!SR }
}
