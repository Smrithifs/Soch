import { ArrowRight, Dna } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, Card, cx, Md, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const GROUPS: [string, string, string][] = [
  ['conceptual', 'Conceptual misunderstanding', 'bg-violet-400'], ['pattern', 'Pattern recognition', 'bg-sky-400'], ['logic', 'Logic errors', 'bg-rose-400'],
  ['implementation', 'Implementation errors', 'bg-orange-400'], ['complexity', 'Complexity errors', 'bg-amber-400'], ['edge', 'Edge-case errors', 'bg-pink-400'], ['communication', 'Communication issues', 'bg-teal-400'],
]

export function MistakePage() {
  const [d, setD] = useState<any>(null)
  const [f, setF] = useState<string | null>(null)
  const { version } = useApp()
  const nav = useNavigate()
  useEffect(() => { api('/api/mistakes').then(setD) }, [version])
  if (!d) return null
  const list = d.mistakes.filter((m: any) => !f || m.group === f)
  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <PageHeader title="Mistake DNA" sub="Every mistake links back to its problem, explanation, topic, revision card and the next problem to attempt." />
      <div className="grid grid-cols-7 gap-2">
        {GROUPS.map(([k, label, tone]) => (
          <button key={k} onClick={() => setF(f === k ? null : k)} className={cx('card p-3 text-left transition', f === k ? 'border-indigo-400/50' : 'hover:border-slate-600')}>
            <div className={cx('mb-2 h-1 w-8 rounded-full', tone)} />
            <div className="text-2xl font-semibold tabular-nums">{d.groups[k] || 0}</div>
            <div className="text-[11px] leading-tight text-slate-400">{label}</div>
          </button>
        ))}
      </div>
      <div className="mt-5 space-y-3">
        {list.length === 0 && <Card className="p-8 text-center text-sm text-slate-500"><Dna className="mx-auto mb-2 text-slate-600" />No mistakes recorded{f ? ' in this group' : ''} yet. They appear automatically from real submissions, revision answers and mock interviews.</Card>}
        {list.map((m: any) => (
          <Card key={m.id} className="fade-in p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={cx('h-2 w-2 rounded-full', GROUPS.find((g) => g[0] === m.group)?.[2])} />
              <span className="text-sm font-semibold text-slate-100">{m.category}</span>
              <Badge tone={m.status === 'open' ? 'red' : m.status === 'improving' ? 'amber' : 'green'}>{m.status}</Badge>
              <Badge>{m.source === 'seed-baseline' ? 'demo baseline' : m.source}</Badge>
              <span className="ml-auto text-[11px] text-slate-500">{new Date(m.created_at + 'Z').toLocaleString()}</span>
            </div>
            <div className="mt-1 text-sm text-slate-300">{m.title}</div>
            <Md text={m.explanation} className="mt-2 !text-xs" />
            {m.evidence?.input != null && <div className="mt-2 inline-flex gap-3 rounded-md border border-line bg-ink-950/60 px-2.5 py-1 font-mono text-[11px]"><span className="text-slate-500">input</span>{m.evidence.input}<span className="text-slate-500">expected</span><span className="text-emerald-300">{m.evidence.expected}</span><span className="text-slate-500">actual</span><span className="text-rose-300">{m.evidence.actual}</span></div>}
            {m.evidence?.latest_score != null && <div className="mt-2 text-[11px] text-amber-200">Baseline {m.evidence.baseline_score}/10 → latest mock {m.evidence.latest_score}/10</div>}
            <div className="mt-3 grid gap-2 border-t border-line pt-3 text-xs sm:grid-cols-4">
              <div><div className="text-slate-500">Problem</div><button className="text-sky-300 hover:underline" onClick={() => nav(`/app/practice/${m.slug}`)}>{m.problem}</button></div>
              <div><div className="text-slate-500">Topic</div><div className="text-slate-300">{m.topic}</div></div>
              <div><div className="text-slate-500">Revision activity</div><button className="text-violet-300 hover:underline" onClick={() => nav(`/app/revision?card=${m.revision_card}`)}>{m.revision_concept || '—'}</button></div>
              <div><div className="text-slate-500">Next problem</div>{m.next_problem ? <Button size="sm" variant="subtle" className="!h-auto !px-0 text-emerald-300" onClick={() => nav(`/app/practice/${m.next_problem}`)}>{m.next_problem_title}<ArrowRight size={11} /></Button> : '—'}</div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
