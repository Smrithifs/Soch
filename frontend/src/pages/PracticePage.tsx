import { Bot, Bug, LifeBuoy, MessageSquarePlus, CheckCircle2, ChevronDown, Clipboard, Copy, Layers, Lightbulb, ListTree, Play, RotateCcw, Send, ShieldAlert, Sparkles, Target, XCircle } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { RecallPanel } from '../components/RecallPanel'
import { CodeEditor } from '../components/CodeEditor'
import { Badge, Button, cx, DIFF_TONE, Md, SourceBadge, useToast } from '../components/ui'
import { api, post, put } from '../lib/api'
import { useApp } from '../lib/app'

const MODES = [
  ['explain_problem', 'Explain problem', Sparkles], ['hint', 'Give hint', Lightbulb], ['pattern', 'Identify pattern', Layers], ['failed_approach', 'Explain failed approach', ShieldAlert],
  ['bug', 'Find bug', Bug], ['optimal', 'Optimal solution', Target], ['edge_cases', 'Edge cases', ListTree], ['similar', 'Similar problem', Copy],
] as const
type Msg = { role: 'user' | 'bot'; text: string; title?: string; ctx?: string[]; source?: string }

export function PracticePage() {
  const { slug: routeSlug } = useParams()
  const { profile, bump } = useApp()
  const nav = useNavigate()
  const toast = useToast()
  const [list, setList] = useState<any[]>([])
  const [prob, setProb] = useState<any>(null)
  const [lang, setLang] = useState<'java' | 'python'>(profile?.language === 'Python' ? 'python' : 'java')
  const [code, setCode] = useState('')
  const [stdin, setStdin] = useState('')
  const [out, setOut] = useState<any>(null)
  const [tab, setTab] = useState<'tests' | 'output' | 'input'>('tests')
  const [busy, setBusy] = useState<'' | 'run' | 'submit'>('')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [q, setQ] = useState('')
  const [snipOpen, setSnipOpen] = useState(false)
  const chatEnd = useRef<HTMLDivElement>(null)
  const [sp] = useSearchParams()
  const [side, setSide] = useState<'tutor' | 'recall'>(sp.get('recall') ? 'recall' : 'tutor')
  const [thinking, setThinking] = useState(false)
  const saveT = useRef<any>()

  useEffect(() => { api('/api/problems').then((l) => { setList(l); if (!routeSlug && l[0]) nav(`/app/practice/${l[0].slug}`, { replace: true }) }) }, [])
  useEffect(() => {
    if (!routeSlug) return
    api(`/api/problems/${routeSlug}`).then((p) => {
      setProb(p); setOut(p.last_submission ? { ...p.last_submission, kind: 'submit', restored: true } : null)
      setCode(p.draft?.[lang] ?? p.starter[lang]); setStdin(p.tests[0].input); setMsgs([])
    })
  }, [routeSlug])
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  function edit(v: string) {
    setCode(v)
    clearTimeout(saveT.current)
    saveT.current = setTimeout(() => routeSlug && put(`/api/drafts/${routeSlug}`, { language: lang, code: v }), 600)
  }
  function switchLang(l: 'java' | 'python') { setLang(l); setCode(prob.draft?.[l] ?? prob.starter[l]) }

  async function exec(kind: 'run' | 'submit') {
    setBusy(kind)
    try {
      const r = await post(`/api/${kind}`, { slug: routeSlug, language: lang, code, stdin })
      setOut({ ...r, kind }); setTab(kind === 'submit' ? 'tests' : 'output')
      if (kind === 'submit') {
        bump()
        if (r.status === 'Accepted') toast(`Accepted · ${r.passed}/${r.total} tests · ${r.xp} XP`)
        else if (r.analysis) toast(`${r.status} → recorded as ${r.analysis.category}`, 'err')
        setProb((p: any) => ({ ...p, last_submission: r }))
      }
    } catch (e: any) { toast(e.message, 'err'); setOut({ status: 'Execution unavailable', stderr: e.message, kind }) } finally { setBusy('') }
  }

  async function ask(question: string, mode?: string, label?: string) {
    setMsgs((m) => [...m, { role: 'user', text: label || question }])
    setThinking(true)
    try {
      const r = await post('/api/tutor', { slug: routeSlug, question, code, language: lang, mode })
      setMsgs((m) => [...m, { role: 'bot', text: r.body, title: r.title, ctx: r.context, source: r.source }])
    } catch (e: any) { toast(e.message, 'err') } finally { setThinking(false) }
  }

  const snippets = useMemo(() => Object.entries(prob?.snippets || {}) as [string, string][], [prob])
  if (!prob) return <div className="p-8 text-sm text-slate-500">Loading problem…</div>
  const statusTone = (s: string) => s === 'Accepted' || s === 'Passed' || s === 'Executed' ? 'text-emerald-300' : s === 'Wrong Answer' ? 'text-amber-300' : 'text-rose-300'

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-12 shrink-0 items-center gap-3 border-b border-line px-4">
        <select value={routeSlug} onChange={(e) => nav(`/app/practice/${e.target.value}`)} className="rounded-md border border-line bg-ink-900 px-2 py-1 text-sm">
          {list.map((p) => <option key={p.slug} value={p.slug}>{p.planned ? '★ ' : ''}{p.title}{p.solved ? ' ✓' : ''}</option>)}
        </select>
        <Badge tone={DIFF_TONE[prob.difficulty]}>{prob.difficulty}</Badge>
        {prob.topics.map((t: string) => <Badge key={t}>{t}</Badge>)}
        <span className="ml-auto text-[11px] text-slate-500">Executor: <span className="text-slate-300">{prob.engine}</span> · autosaved</span>
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(280px,1fr)_minmax(420px,1.5fr)_minmax(300px,1fr)]">
        {/* LEFT — problem */}
        <section className="min-h-0 overflow-y-auto border-r border-line p-5">
          <h2 className="text-lg font-semibold text-slate-50">{prob.title}</h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-300">{prob.statement}</p>
          <div className="mt-5 space-y-2">
            {prob.examples.map((e: any, i: number) => (
              <div key={i} className="rounded-lg border border-line bg-ink-950/60 p-3 font-mono text-xs">
                <div><span className="text-slate-500">Input </span><span className="text-slate-200">{e.input}</span></div>
                <div><span className="text-slate-500">Output </span><span className="text-emerald-300">{e.output}</span></div>
                {e.note && <div className="mt-1 font-sans text-slate-500">{e.note}</div>}
              </div>
            ))}
          </div>
          <div className="mt-5 text-[11px] font-medium uppercase tracking-wider text-slate-500">Constraints</div>
          <ul className="mt-1.5 space-y-1 font-mono text-xs text-slate-400">{prob.constraints.map((c: string) => <li key={c}>• {c}</li>)}</ul>
          <div className="mt-5 grid grid-cols-2 gap-2">
            <div className="rounded-lg border border-line p-2.5"><div className="text-[10px] uppercase text-slate-500">Expected time</div><div className="font-mono text-sm text-sky-300">{prob.complexity.time}</div></div>
            <div className="rounded-lg border border-line p-2.5"><div className="text-[10px] uppercase text-slate-500">Expected space</div><div className="font-mono text-sm text-sky-300">{prob.complexity.space}</div></div>
          </div>
          <div className="mt-5 text-[11px] font-medium uppercase tracking-wider text-slate-500">Pattern</div>
          <div className="mt-1 text-sm text-violet-300">{prob.pattern}</div>
          <div className="mt-5 text-[11px] font-medium uppercase tracking-wider text-slate-500">Related problems</div>
          <div className="mt-1.5 flex flex-wrap gap-1.5">{prob.related.map((r: string) => <Badge key={r} tone="slate">{r}</Badge>)}</div>
          <Button size="sm" variant="ghost" className="mt-5" onClick={() => nav(`/app/thinkmap/${routeSlug}`)}>Open ThinkMap</Button>
        </section>

        {/* CENTER — editor */}
        <section className="flex min-h-0 flex-col border-r border-line">
          <div className="flex h-10 shrink-0 items-center gap-2 border-b border-line px-3">
            <select value={lang} onChange={(e) => switchLang(e.target.value as any)} className="rounded border border-line bg-ink-900 px-1.5 py-0.5 text-xs">
              <option value="java">Java 21</option><option value="python">Python 3</option>
            </select>
            {snippets.length > 0 && lang === 'java' && (
              <div className="relative">
                <Button size="sm" variant="subtle" onClick={() => setSnipOpen(!snipOpen)}><Clipboard size={12} />Demo code<ChevronDown size={12} /></Button>
                {snipOpen && (
                  <div className="absolute left-0 top-full z-20 mt-1 w-56 rounded-lg border border-line bg-ink-800 p-1 shadow-xl">
                    {snippets.map(([n, c]) => <button key={n} onClick={() => { edit(c); setSnipOpen(false) }} className="block w-full rounded px-2 py-1.5 text-left text-xs hover:bg-white/[.06]">Paste: {n}</button>)}
                  </div>
                )}
              </div>
            )}
            <div className="ml-auto flex gap-1.5">
              <Button size="sm" variant="subtle" onClick={() => edit(prob.starter[lang])}><RotateCcw size={12} />Reset</Button>
              <Button size="sm" variant="ghost" disabled={!!busy} onClick={() => exec('run')}><Play size={12} />{busy === 'run' ? 'Running…' : 'Run'}</Button>
              <Button size="sm" variant="success" disabled={!!busy} onClick={() => exec('submit')}><Send size={12} />{busy === 'submit' ? 'Judging…' : 'Submit'}</Button>
            </div>
          </div>
          <div className="min-h-0 flex-1"><CodeEditor value={code} onChange={edit} language={lang} /></div>
          <div className="flex h-[38%] shrink-0 flex-col border-t border-line">
            <div className="flex h-9 shrink-0 items-center gap-1 border-b border-line px-2 text-xs">
              {(['tests', 'output', 'input'] as const).map((t) => <button key={t} onClick={() => setTab(t)} className={cx('rounded px-2 py-1 capitalize', tab === t ? 'bg-white/[.07] text-slate-100' : 'text-slate-500 hover:text-slate-300')}>{t === 'input' ? 'Custom input' : t === 'tests' ? 'Test results' : 'Output'}</button>)}
              {out && <span className={cx('ml-auto pr-2 font-medium', statusTone(out.status))}>{out.status}{out.total ? ` · ${out.passed}/${out.total}` : ''}{out.time_ms != null ? ` · ${out.time_ms} ms` : ''}{out.restored ? ' · last submission' : ''}</span>}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-3 font-mono text-xs">
              {tab === 'input' && <textarea className="h-full w-full resize-none rounded-md border border-line bg-ink-950 p-2 text-slate-200 outline-none" value={stdin} onChange={(e) => setStdin(e.target.value)} placeholder="stdin for Run" />}
              {tab === 'output' && (!out ? <div className="text-slate-600">Run your code to see real stdout/stderr.</div> : (
                <div className="space-y-2">
                  {out.kind === 'run' && <div><div className="text-slate-500">stdout</div><pre className="whitespace-pre-wrap text-slate-200">{out.stdout || '(empty)'}</pre></div>}
                  {(out.stderr || out.status === 'Compilation Error') && <div><div className="text-slate-500">stderr</div><pre className="whitespace-pre-wrap text-rose-300">{out.stderr}</pre></div>}
                  {out.kind === 'submit' && !out.stderr && <div className="text-slate-500">See Test results.</div>}
                </div>))}
              {tab === 'tests' && (!out?.tests?.length ? <div className="text-slate-600">{out?.status === 'Compilation Error' ? <pre className="whitespace-pre-wrap text-rose-300">{out.stderr}</pre> : 'Submit to run all configured test cases.'}</div> : (
                <div className="space-y-1.5">
                  {out.analysis && <div className="mb-2 rounded-md border border-amber-400/20 bg-amber-500/[.07] p-2.5 font-sans"><div className="mb-1 text-[11px] font-semibold uppercase text-amber-300">Classified as {out.analysis.category}</div><Md text={out.analysis.explanation} className="!text-xs" /></div>}
                  {out.tests.map((t: any) => (
                    <div key={t.index} className={cx('flex items-start gap-2 rounded-md border px-2.5 py-1.5', t.status === 'Passed' ? 'border-emerald-400/10 bg-emerald-500/[.04]' : 'border-rose-400/20 bg-rose-500/[.06]')}>
                      {t.status === 'Passed' ? <CheckCircle2 size={13} className="mt-0.5 text-emerald-400" /> : <XCircle size={13} className="mt-0.5 text-rose-400" />}
                      <div className="min-w-0 flex-1">
                        <div className="flex gap-3"><span className="text-slate-500">#{t.index + 1}</span><span className="truncate text-slate-200">{t.input.replace('\n', ' | ')}</span><span className="ml-auto text-[10px] text-slate-600">{t.tag} · {t.time_ms}ms</span></div>
                        {t.status !== 'Passed' && <div className="mt-0.5 text-[11px]"><span className="text-slate-500">expected</span> <span className="text-emerald-300">{t.expected}</span> <span className="text-slate-500">actual</span> <span className="text-rose-300">{t.actual || t.status}</span>{t.stderr && <pre className="mt-1 whitespace-pre-wrap text-rose-300/80">{t.stderr.slice(0, 300)}</pre>}</div>}
                      </div>
                    </div>
                  ))}
                </div>))}
            </div>
          </div>
        </section>

        {/* RIGHT — tutor */}
        <section className="flex min-h-0 flex-col">
          <div className="flex h-10 shrink-0 items-center gap-1 border-b border-line px-2 text-sm">
            <button onClick={() => setSide('tutor')} className={cx('flex items-center gap-1.5 rounded-md px-2.5 py-1', side === 'tutor' ? 'bg-white/[.07] text-slate-100' : 'text-slate-500')}><Bot size={14} className="text-indigo-300" />Tutor</button>
            <button onClick={() => setSide('recall')} className={cx('flex items-center gap-1.5 rounded-md px-2.5 py-1', side === 'recall' ? 'bg-white/[.07] text-slate-100' : 'text-slate-500')}><LifeBuoy size={14} className="text-rose-300" />Recall Rescue</button>
            {side === 'tutor' && <button title="New conversation" onClick={async () => { await api(`/api/tutor/${routeSlug}`, { method: 'DELETE' }); setMsgs([]) }} className="ml-auto rounded p-1 text-slate-500 hover:text-slate-200"><MessageSquarePlus size={14} /></button>}
          </div>
          {side === 'recall' ? <RecallPanel key={routeSlug} slug={routeSlug!} autoStart={!!sp.get('recall')} onStart={() => { setCode(prob.starter[lang]); setOut(null); toast('Editor cleared — rebuild it from memory (your old code is still in your history)') }} /> : <>
          <div className="grid shrink-0 grid-cols-2 gap-1.5 border-b border-line p-2.5">
            {MODES.map(([m, label, I]) => <button key={m} onClick={() => ask('', m, label)} className="flex items-center gap-1.5 rounded-md border border-line bg-white/[.02] px-2 py-1.5 text-left text-[11px] text-slate-300 hover:border-indigo-400/40 hover:bg-indigo-500/[.06]"><I size={12} className="text-indigo-300" />{label}</button>)}
          </div>
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
            {msgs.length === 0 && <div className="rounded-lg border border-dashed border-line p-4 text-xs text-slate-500">Ask anything about <b className="text-slate-300">{prob.title}</b> — e.g. “why is my code failing?”, “why do we need a {prob.slug === 'two-sum' ? 'HashMap' : prob.slug === 'valid-parentheses' ? 'stack' : 'running minimum'}?”, “what's the complexity of my code?”</div>}
            {msgs.map((m, i) => m.role === 'user' ? (
              <div key={i} className="ml-8 rounded-lg bg-indigo-500/15 px-3 py-2 text-sm text-indigo-50">{m.text}</div>
            ) : (
              <div key={i} className="fade-in rounded-lg border border-line bg-ink-850 p-3">
                <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-slate-100">{m.title}<SourceBadge source={m.source} /></div>
                <Md text={m.text} />
                {m.ctx && <div className="mt-2 flex flex-wrap gap-1">{m.ctx.map((c) => <span key={c} className="rounded bg-white/[.04] px-1.5 py-0.5 text-[10px] text-slate-500">{c}</span>)}</div>}
              </div>
            ))}
            {thinking && <div className="flex items-center gap-2 text-xs text-slate-500"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />Tutor is reading your code and test results…</div>}
            <div ref={chatEnd} />
          </div>
          <form onSubmit={(e) => { e.preventDefault(); if (q.trim()) { ask(q.trim()); setQ('') } }} className="flex shrink-0 gap-2 border-t border-line p-2.5">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a follow-up…" className="flex-1 rounded-md border border-line bg-ink-950 px-2.5 py-1.5 text-sm outline-none focus:border-indigo-400/50" />
            <Button size="sm" type="submit" disabled={thinking}><Send size={12} /></Button>
          </form>
          </>}
        </section>
      </div>
    </div>
  )
}
