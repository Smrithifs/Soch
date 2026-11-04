import { Building2, CheckCircle2, Circle, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Bar, Card, cx, DIFF_TONE, Md, PageHeader, SourceBadge } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const ST: any = { strong: ['green', 'strong'], fading: ['amber', 'fading'], forgotten: ['red', 'forgotten'], 'not started': ['slate', 'not started'] }

export function CompanyPage() {
  const { version } = useApp()
  const [d, setD] = useState<any>(null)
  const nav = useNavigate()
  useEffect(() => { setD(null); api('/api/company').then(setD) }, [version])
  if (!d) return <div className="p-8 text-sm text-slate-500">Coach is analysing your fit…</div>
  return (
    <div className="fade-in mx-auto max-w-5xl p-8">
      <PageHeader title={d.company ? `${d.company} preparation` : 'Company preparation'} sub={<>{d.role ? `${d.role} · ` : ''}{d.stage}{d.days_left != null ? ` in ${d.days_left} day${d.days_left === 1 ? '' : 's'}` : ''}</>} />
      <Card className="mb-4 flex gap-3 border-violet-400/25 bg-gradient-to-r from-violet-500/[.07] to-transparent p-5">
        <Sparkles size={16} className="mt-0.5 shrink-0 text-violet-300" />
        <div className="flex-1"><div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-violet-300">Your personal game plan <SourceBadge source={d.brief_source} /></div><Md text={d.brief} className="!text-sm !text-slate-200" /></div>
      </Card>
      <div className="grid gap-4 md:grid-cols-[1fr_1.3fr]">
        <Card className="p-5">
          <div className="flex items-center justify-between"><div className="text-sm font-semibold">Readiness for {d.company || 'target'}</div><span className="text-2xl font-semibold tabular-nums">{d.coverage}%</span></div>
          <div className="mt-2"><Bar value={d.coverage} tone={d.coverage >= 60 ? 'bg-emerald-400' : 'bg-amber-400'} /></div>
          <div className="mt-4 space-y-2">
            {d.focus.map((f: any) => (
              <div key={f.topic} className="flex items-center gap-2 text-sm">
                {f.status === 'strong' ? <CheckCircle2 size={14} className="text-emerald-400" /> : <Circle size={14} className="text-slate-600" />}
                <span className="flex-1 text-slate-200">{f.topic}{f.weak && <span className="ml-1.5 text-[10px] text-amber-300">weak</span>}</span>
                {f.retention != null && <span className="text-[11px] tabular-nums text-slate-500">{f.retention}%</span>}
                <Badge tone={ST[f.status][0]}>{ST[f.status][1]}</Badge>
              </div>
            ))}
          </div>
        </Card>
        <div className="space-y-4">
          <Card className="p-5"><div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-slate-500"><Building2 size={12} />What to expect</div><p className="mt-2 text-sm text-slate-300">{d.format}</p><p className="mt-2 text-xs text-slate-500">{d.other_round}</p></Card>
          <Card className="p-5"><div className="text-[11px] uppercase tracking-wider text-slate-500">Tips</div><ul className="mt-2 space-y-1.5 text-sm text-slate-300">{d.tips.map((t: string) => <li key={t}>• {t}</li>)}</ul></Card>
        </div>
      </div>
      <Card className="mt-4 divide-y divide-line">
        <div className="px-5 py-3 text-sm font-semibold">Practise next for {d.company || 'your target'}</div>
        {d.problems.map((p: any, i: number) => (
          <button key={p.slug} onClick={() => nav(`/app/practice/${p.slug}`)} className="flex w-full items-center gap-3 px-5 py-3 text-left hover:bg-white/[.02]">
            <span className="w-4 text-xs tabular-nums text-slate-500">{i + 1}</span>
            <span className={cx('text-sm font-medium', p.solved && 'text-slate-500')}>{p.title}</span><Badge tone={DIFF_TONE[p.difficulty]}>{p.difficulty}</Badge><Badge>{p.topic}</Badge>{p.solved && <Badge tone="green">solved</Badge>}
            <span className="ml-auto truncate text-xs text-slate-500">{p.why.join(' · ')}</span>
          </button>
        ))}
      </Card>
      <p className="mt-3 text-[11px] text-slate-600">{d.disclaimer}{!d.known && d.company ? ' No stored profile for this company yet — using common patterns.' : ''}</p>
    </div>
  )
}
