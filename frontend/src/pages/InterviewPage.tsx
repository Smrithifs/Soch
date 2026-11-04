import { Mic, MicOff, Play, Send, Volume2, VolumeX } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from 'recharts'
import { InterviewerAvatar, useDictation, useVoice } from '../components/Interviewer'
import { Badge, Bar, Button, Card, cx, Md, PageHeader, useToast } from '../components/ui'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'

const NAME = 'Ananya'
const strip = (s: string) => s.replace(/\*\*/g, '')

export function InterviewPage() {
  const { profile, bump } = useApp()
  const [s, setS] = useState<any>(null)
  const [a, setA] = useState('')
  const [busy, setBusy] = useState(false)
  const [notes, setNotes] = useState('')
  const [said, setSaid] = useState('')        // what she's currently saying (typewriter)
  const [typed, setTyped] = useState('')
  const end = useRef<HTMLDivElement>(null)
  const toast = useToast()
  const voice = useVoice()
  const dict = useDictation(setA)

  useEffect(() => { api('/api/interview').then(setS) }, [])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [s?.step, typed])
  // typewriter for the line she's speaking
  useEffect(() => {
    if (!said) return
    setTyped('')
    let i = 0
    const t = setInterval(() => { i += 2; setTyped(said.slice(0, i)); if (i >= said.length) clearInterval(t) }, 28)
    return () => clearInterval(t)
  }, [said])

  function say(text: string) { setSaid(text); voice.speak(strip(text)) }

  async function start() {
    const st = await post('/api/interview/start', {})
    setS(st)
    const first = profile?.name?.split(' ')[0] || 'there'
    say(`Hi ${first}, I'm ${NAME}. I'll be your interviewer today — this is a practice round, so think out loud and don't worry about being perfect. ${st.question}`)
  }
  async function send(e?: React.FormEvent) {
    e?.preventDefault(); if (!a.trim() || busy) return
    if (dict.listening) dict.toggle()
    setBusy(true); voice.stop()
    try {
      const r = await post(`/api/interview/${s.id}/answer`, { answer: a })
      setS(r); setA(''); bump()
      const fb = r.last_feedback
      const react = fb.score >= 8 ? 'Nice, that was clear.' : fb.score >= 5 ? 'Okay, good start.' : "Hmm, let's tighten that up."
      const follow = (fb.feedback.match(/Follow-up:\*\*\s*(.*)$/) || [])[1]
      if (r.status === 'complete') say(`${react} That's the end of our session — thanks! Your overall score is ${r.report.overall} out of 10. Have a look at the feedback report.`)
      else say(`${react} ${follow ? `Quick follow-up to think about: ${follow} ` : ''}Next — ${r.question}`)
    } catch (er: any) { toast(er.message, 'err') } finally { setBusy(false) }
  }
  const r = s?.report

  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <PageHeader title="Interview Simulator" sub="A live practice interview: she asks one question at a time, listens, reacts and grades. Code correctness comes from your real latest submission."
        right={<div className="flex gap-2"><Button variant="ghost" onClick={() => { voice.setMuted(!voice.muted); voice.stop() }}>{voice.muted ? <VolumeX size={14} /> : <Volume2 size={14} />}{voice.muted ? 'Voice off' : 'Voice on'}</Button><Button onClick={start}><Play size={14} />{s ? 'New session' : 'Start interview'}</Button></div>} />

      {!s ? (
        <Card className="flex flex-col items-center p-10 text-center">
          <InterviewerAvatar speaking={false} />
          <div className="mt-4 text-lg font-semibold">{NAME}</div>
          <div className="text-xs text-slate-500">AI interviewer · Senior Software Engineer persona</div>
          <p className="mt-3 max-w-md text-sm text-slate-400">She'll ask 10 questions on today's problem — understanding, approach, brute force, optimisation, complexity, edge cases, code and communication. Answer by typing or with the mic.</p>
          <Button className="mt-5" onClick={start}><Play size={14} />Start interview</Button>
        </Card>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
          <div className="space-y-4">
            {/* stage */}
            <Card className="relative overflow-hidden p-6">
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(30rem_14rem_at_20%_0%,rgba(139,92,246,.14),transparent)]" />
              <div className="relative flex gap-5">
                <div className="flex shrink-0 flex-col items-center">
                  <InterviewerAvatar speaking={voice.speaking} size={132} />
                  <div className="mt-2 text-sm font-semibold">{NAME}</div>
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <span className={cx('h-1.5 w-1.5 rounded-full', voice.speaking ? 'animate-pulse bg-emerald-400' : busy ? 'animate-pulse bg-amber-400' : 'bg-slate-500')} />
                    {voice.speaking ? 'speaking' : busy ? 'thinking…' : dict.listening ? 'listening' : 'waiting for you'}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex items-center gap-2 text-xs text-slate-500"><span className="font-medium text-slate-300">{s.title}</span>· question {Math.min(s.step + 1, s.total)} of {s.total}<div className="ml-auto w-28"><Bar value={(s.step / s.total) * 100} tone="bg-violet-400" /></div></div>
                  {s.dimension && s.status === 'active' && <Badge tone="violet">{s.dimension}</Badge>}
                  <div className="relative mt-2 rounded-2xl rounded-tl-sm border border-violet-400/25 bg-ink-850/90 p-4">
                    <Md text={typed || (s.status === 'active' ? s.question : r?.summary || '')} className="!text-[15px] !leading-relaxed !text-slate-100" />
                    {typed && typed.length < said.length && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-violet-300 align-middle" />}
                  </div>
                </div>
              </div>
              {s.status === 'active' && (
                <form onSubmit={send} className="relative mt-5 flex gap-2">
                  <textarea value={a} onChange={(e) => setA(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) send(e as any) }} rows={2}
                    placeholder={dict.listening ? 'Listening… speak your answer' : 'Answer as you would out loud… (Enter to send)'} className={cx('flex-1 resize-none rounded-xl border bg-ink-950 px-3 py-2 text-sm outline-none', dict.listening ? 'border-rose-400/60' : 'border-line focus:border-violet-400/50')} />
                  {dict.supported && <Button type="button" variant={dict.listening ? 'primary' : 'ghost'} onClick={dict.toggle} title="Answer by voice">{dict.listening ? <MicOff size={14} /> : <Mic size={14} />}</Button>}
                  <Button disabled={busy || !a.trim()}><Send size={13} /></Button>
                </form>
              )}
            </Card>
            {/* transcript */}
            <Card className="max-h-[42vh] overflow-y-auto p-4">
              <div className="mb-2 text-[11px] uppercase tracking-wider text-slate-500">Transcript</div>
              {s.answers.length === 0 && <div className="text-xs text-slate-600">Your answers and her feedback appear here.</div>}
              <div className="space-y-3">
                {s.answers.map((x: any, i: number) => (
                  <div key={i} className="text-sm">
                    <div className="text-[11px] text-violet-300">{NAME} · {x.dimension}</div>
                    <div className="text-slate-400"><Md text={x.question} className="!text-xs !text-slate-400" /></div>
                    <div className="mt-1 ml-6 rounded-lg bg-indigo-500/15 px-3 py-1.5 text-indigo-50">{x.answer}</div>
                    <div className="mt-1 ml-6 flex flex-wrap items-center gap-2 text-xs"><Badge tone={x.score >= 7 ? 'green' : x.score >= 5 ? 'amber' : 'red'}>{x.score}/10</Badge>{x.graded_by && <Badge tone={x.graded_by === 'llm' ? 'violet' : 'slate'}>{x.graded_by === 'llm' ? '✦ agent' : x.graded_by}</Badge>}<Md text={x.feedback} className="!text-xs !text-slate-500" /></div>
                  </div>
                ))}
                <div ref={end} />
              </div>
            </Card>
            <div className="text-[10px] text-slate-600">{s.disclaimer} Voice uses your browser's built-in speech — nothing is recorded or uploaded.</div>
          </div>

          <div className="space-y-4">
            {r ? (
              <>
                <Card className="p-5">
                  <div className="flex items-baseline justify-between"><div className="text-sm font-semibold">Feedback report</div><div className="text-3xl font-semibold tabular-nums text-violet-200">{r.overall}<span className="text-sm text-slate-500">/10</span></div></div>
                  <div className="h-56"><ResponsiveContainer><RadarChart data={Object.entries(r.scores).map(([k, v]) => ({ k: k.replace(' complexity', ' cx').replace('Data structure selection', 'DS choice').replace('Problem understanding', 'Understanding'), v }))}><PolarGrid stroke="#1c2233" /><PolarAngleAxis dataKey="k" tick={{ fill: '#8b93a7', fontSize: 10 }} /><Radar dataKey="v" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.25} /></RadarChart></ResponsiveContainer></div>
                  <p className="text-xs text-slate-400">{r.summary}</p>
                </Card>
                <Card className="p-5 text-sm">
                  <div className="text-xs font-semibold uppercase tracking-wider text-emerald-300">Strengths</div><ul className="mt-1 text-slate-300">{r.strengths.length ? r.strengths.map((x: string) => <li key={x}>• {x} ({r.scores[x]})</li>) : <li className="text-slate-500">None above 7/10 yet</li>}</ul>
                  <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-rose-300">Weaknesses</div><ul className="mt-1 text-slate-300">{r.weaknesses.length ? r.weaknesses.map((x: string) => <li key={x}>• {x} ({r.scores[x]})</li>) : <li className="text-slate-500">None below 5/10</li>}</ul>
                  <div className="mt-3 text-xs font-semibold uppercase tracking-wider text-sky-300">Recommendations</div><ul className="mt-1 space-y-1 text-slate-300">{r.recommendations.map((x: string) => <li key={x}>• {x}</li>)}</ul>
                  {Object.keys(r.improvement_vs_baseline || {}).length > 0 && <><div className="mt-3 text-xs font-semibold uppercase tracking-wider text-amber-300">Change vs baseline</div><div className="mt-1 flex flex-wrap gap-1.5">{Object.entries(r.improvement_vs_baseline).map(([k, v]: any) => <Badge key={k} tone={v > 0 ? 'green' : 'red'}>{k} {v > 0 ? '+' : ''}{v}</Badge>)}</div></>}
                </Card>
                <Card className="p-5">
                  <div className="mb-2 text-xs font-semibold">Your notes on this session</div>
                  <textarea value={notes || r.student_notes || ''} onChange={(e) => setNotes(e.target.value)} rows={3} className="w-full rounded-md border border-line bg-ink-950 p-2 text-sm outline-none" />
                  <Button size="sm" variant="ghost" className="mt-2" onClick={async () => { await post(`/api/interview/${s.id}/feedback`, { notes }); toast('Saved') }}>Save feedback</Button>
                </Card>
              </>
            ) : (
              <Card className="p-5 text-sm text-slate-400"><div className="mb-2 text-sm font-semibold text-slate-200">She's evaluating</div>{['Problem understanding', 'Approach', 'Brute force', 'Optimization', 'Data structure selection', 'Time complexity', 'Space complexity', 'Edge cases', 'Code correctness', 'Communication'].map((d, i) => <div key={d} className={cx('flex items-center justify-between py-0.5 text-xs', i < s.step ? 'text-emerald-300' : i === s.step ? 'text-violet-200' : 'text-slate-500')}><span>{i < s.step ? '✓' : i === s.step ? '→' : '·'} {d}</span>{s.answers[i] && <span className="tabular-nums">{s.answers[i].score}</span>}</div>)}</Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
