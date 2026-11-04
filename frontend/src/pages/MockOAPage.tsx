import { AlertTriangle, ArrowRight, CheckCircle2, Flag, Play, Timer, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CodeEditor } from '../components/CodeEditor'
import { Badge, Button, Card, cx, DIFF_TONE, Md, PageHeader, SourceBadge, useToast } from '../components/ui'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'

export function MockOAPage() {
  const { profile, bump } = useApp()
  const toast = useToast()
  const nav = useNavigate()
  const [probs, setProbs] = useState<any[]>([])
  const [active, setActive] = useState(0)
  const [code, setCode] = useState<Record<string, string>>({})
  const [runOut, setRunOut] = useState<Record<string, any>>({})
  const [left, setLeft] = useState<number | null>(null)
  const [busy, setBusy] = useState<'' | 'run' | 'finish'>('')
  const [report, setReport] = useState<any>(null)
  const [confirm, setConfirm] = useState(false)
  const timer = useRef<any>()
  const n = Math.min(4, Math.max(2, profile?.questions_expected || 2))
  const total = n * 25 * 60

  async function start() {
    const plan = await api('/api/plan/today')
    let slugs: string[] = plan.tasks.filter((t: any) => t.kind === 'problem').map((t: any) => t.ref)
    const comp = await api('/api/company')
    slugs = [...slugs, ...comp.problems.map((p: any) => p.slug)].filter((s, i, a) => a.indexOf(s) === i).slice(0, n)
    const ps = await Promise.all(slugs.map((s) => api(`/api/problems/${s}`)))
    setProbs(ps); setCode(Object.fromEntries(ps.map((p) => [p.slug, p.starter.java]))); setRunOut({}); setReport(null); setActive(0); setLeft(total)
    clearInterval(timer.current)
    timer.current = setInterval(() => setLeft((l) => (l && l > 0 ? l - 1 : 0)), 1000)
  }
  useEffect(() => () => clearInterval(timer.current), [])
  useEffect(() => { if (left === 0 && probs.length && !report && busy !== 'finish') { toast('Time is up — submitting your OA', 'err'); finish() } }, [left])

  async function runSample() {
    const p = probs[active]; setBusy('run')
    try { const r = await post('/api/run', { slug: p.slug, language: 'java', code: code[p.slug], stdin: p.tests[0].input }); setRunOut((x) => ({ ...x, [p.slug]: r })) }
    catch (e: any) { toast(e.message, 'err') } finally { setBusy('') }
  }
  async function finish() {
    setConfirm(false); setBusy('finish'); clearInterval(timer.current)
    try {
      const r = await post('/api/mockoa/finish', { items: probs.map((p) => ({ slug: p.slug, code: code[p.slug] })), seconds_used: total - (left ?? 0) })
      setReport(r); bump()
    } catch (e: any) { toast(e.message, 'err') } finally { setBusy('') }
  }
  const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  const edited = (p: any) => code[p.slug] && code[p.slug].trim() !== p.starter.java.trim()

  if (report) return (
    <div className="fade-in mx-auto max-w-5xl p-8">
      <PageHeader title="Mock OA — Review" sub={`${report.solved}/${report.total_questions} solved · ${report.minutes_used} min used · every verdict from real test execution`}
        right={<Button onClick={start}><Timer size={14} />Take another</Button>} />
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-5"><div className="text-[11px] uppercase tracking-wider text-slate-500">Score</div><div className={cx('mt-1 text-4xl font-semibold tabular-nums', report.score >= 70 ? 'text-emerald-300' : report.score >= 40 ? 'text-amber-300' : 'text-rose-300')}>{report.score}%</div><div className="text-xs text-slate-500">of all test cases passed</div></Card>
        <Card className="p-5 md:col-span-2 border-violet-400/30">
          <div className="flex items-center gap-2 text-sm font-semibold"><Flag size={14} className="text-violet-300" />Added to your roadmap</div>
          {report.weak_topics.length ? <>
            <p className="mt-1 text-xs text-slate-400">These topics are now marked <b className="text-amber-300">needs revision</b>, prioritised in your daily plan, and these cards are due now:</p>
            <div className="mt-2 flex flex-wrap gap-1.5">{report.weak_topics.map((t: string) => <Badge key={t} tone="amber">{t}</Badge>)}{report.roadmap_update.revision_cards_due.map((c: string) => <Badge key={c} tone="violet">{c}</Badge>)}</div>
            <div className="mt-3 flex gap-2"><Button size="sm" onClick={() => nav('/app/dashboard')}>See updated plan<ArrowRight size={12} /></Button><Button size="sm" variant="ghost" onClick={() => nav('/app/path')}>Roadmap</Button></div>
          </> : <p className="mt-1 text-xs text-slate-400">No weak areas found — great run. Your plan stays as is.</p>}
        </Card>
      </div>
      <div className="mt-4 space-y-3">
        {report.reviews.map((r: any, i: number) => (
          <Card key={r.slug} className={cx('p-5', r.status === 'Accepted' ? 'border-emerald-400/20' : 'border-rose-400/20')}>
            <div className="flex flex-wrap items-center gap-2">
              {r.status === 'Accepted' ? <CheckCircle2 size={16} className="text-emerald-400" /> : r.status === 'Not attempted' ? <AlertTriangle size={16} className="text-amber-400" /> : <XCircle size={16} className="text-rose-400" />}
              <span className="font-semibold">Q{i + 1}. {r.title}</span><Badge tone={DIFF_TONE[r.difficulty]}>{r.difficulty}</Badge><Badge>{r.topic}</Badge>
              <span className="ml-auto text-sm tabular-nums text-slate-300">{r.passed}/{r.total} tests</span><SourceBadge source={r.review.source} />
            </div>
            <div className="mt-1 text-sm text-slate-200">{r.review.verdict}</div>
            {r.first_failure && <div className="mt-2 inline-flex flex-wrap gap-3 rounded-md border border-line bg-ink-950/60 px-2.5 py-1 font-mono text-[11px]"><span className="text-slate-500">failing input</span>{r.first_failure.input}<span className="text-slate-500">expected</span><span className="text-emerald-300">{r.first_failure.expected}</span><span className="text-slate-500">yours</span><span className="text-rose-300">{r.first_failure.actual || r.first_failure.status}</span></div>}
            <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
              {r.review.what_went_wrong && <div><div className="text-[11px] font-semibold uppercase tracking-wider text-rose-300">Where it went wrong</div><Md text={r.review.what_went_wrong} className="mt-1 !text-xs" /></div>}
              {r.review.what_went_well && <div><div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-300">What went well</div><Md text={r.review.what_went_well} className="mt-1 !text-xs" /></div>}
              {r.review.fix && <div><div className="text-[11px] font-semibold uppercase tracking-wider text-sky-300">How to fix</div><Md text={r.review.fix} className="mt-1 !text-xs" /></div>}
            </div>
            <div className="mt-3 flex items-center gap-3 border-t border-line pt-3 text-xs text-slate-500">
              <span>Your complexity: <b className="text-slate-300">{r.time}</b> time · <b className="text-slate-300">{r.space}</b> space</span>
              {r.review.concept_gap && <span>Revise: <b className="text-amber-300">{r.review.concept_gap}</b></span>}
              <Button size="sm" variant="ghost" className="ml-auto" onClick={() => nav(`/app/practice/${r.slug}`)}>Practise this</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )

  return (
    <div className="fade-in flex h-full flex-col p-8">
      <PageHeader title="Mock OA" sub={`${n} questions · ${n * 25} minutes · Java · one final submission, then a full review`} right={<Button onClick={start}><Timer size={14} />{probs.length ? 'Restart' : 'Start mock OA'}</Button>} />
      {!probs.length ? <Card className="p-10 text-center text-sm text-slate-400">Timed like a real OA: write all answers, use <b>Run sample</b> to check the example, then <b>Finish & submit</b> once. You get a per-question review and your weak topics go straight into your roadmap.</Card> : (
        <Card className="flex min-h-[560px] flex-1 flex-col overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line px-3 py-2">
            {probs.map((p, i) => <button key={p.slug} onClick={() => setActive(i)} className={cx('flex items-center gap-1.5 rounded-md px-3 py-1 text-xs', i === active ? 'bg-white/[.08] text-slate-100' : 'text-slate-400')}><span className={cx('h-1.5 w-1.5 rounded-full', edited(p) ? 'bg-sky-400' : 'bg-slate-600')} />Q{i + 1}. {p.title}</button>)}
            <span className={cx('ml-auto font-mono text-sm tabular-nums', (left ?? 0) < 300 ? 'text-rose-300' : 'text-slate-200')}>{mmss(left ?? 0)}</span>
            <Button size="sm" variant="ghost" disabled={!!busy} onClick={runSample}><Play size={12} />{busy === 'run' ? 'Running…' : 'Run sample'}</Button>
            <Button size="sm" variant="success" disabled={!!busy} onClick={() => setConfirm(true)}><Flag size={12} />{busy === 'finish' ? 'Grading all…' : 'Finish & submit'}</Button>
          </div>
          <div className="grid min-h-0 flex-1 grid-cols-[1fr_1.6fr]">
            <div className="overflow-y-auto border-r border-line p-4 text-sm text-slate-300">
              <div className="flex items-center gap-2 font-semibold text-slate-100">{probs[active].title}<Badge tone={DIFF_TONE[probs[active].difficulty]}>{probs[active].difficulty}</Badge></div>
              <p className="mt-2">{probs[active].statement}</p>
              {probs[active].examples.map((e: any, i: number) => <div key={i} className="mt-2 rounded border border-line p-2 font-mono text-xs">{e.input} → {e.output}</div>)}
              {runOut[probs[active].slug] && <div className="mt-4 rounded-md border border-line bg-ink-950/60 p-2.5 font-mono text-xs"><div className="text-slate-500">sample input: {probs[active].tests[0].input.replace('\n', ' | ')}</div><div className="mt-1 text-slate-500">expected <span className="text-emerald-300">{probs[active].tests[0].expected}</span></div><div className="text-slate-500">your output <span className={runOut[probs[active].slug].stdout?.trim() === probs[active].tests[0].expected ? 'text-emerald-300' : 'text-rose-300'}>{runOut[probs[active].slug].stdout?.trim() || runOut[probs[active].slug].status}</span></div>{runOut[probs[active].slug].stderr && <pre className="mt-1 whitespace-pre-wrap text-rose-300">{runOut[probs[active].slug].stderr.slice(0, 400)}</pre>}</div>}
              <p className="mt-4 text-[11px] text-slate-500">Hidden tests are only run on final submission — like a real OA.</p>
            </div>
            <CodeEditor language="java" value={code[probs[active].slug]} onChange={(v) => setCode((c) => ({ ...c, [probs[active].slug]: v }))} />
          </div>
        </Card>
      )}
      {confirm && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setConfirm(false)}>
          <Card className="fade-in w-96 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="text-base font-semibold">Submit your OA?</div>
            <p className="mt-1 text-sm text-slate-400">This is final. {probs.filter((p) => !edited(p)).length ? `${probs.filter((p) => !edited(p)).length} question(s) are still untouched.` : 'All questions have code.'}</p>
            <div className="mt-4 flex justify-end gap-2"><Button variant="subtle" onClick={() => setConfirm(false)}>Keep working</Button><Button variant="success" onClick={finish}>Submit all</Button></div>
          </Card>
        </div>
      )}
    </div>
  )
}
