import { CheckCircle2, Circle, Lock, PlayCircle, RotateCcw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge, Bar, Card, cx, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const ST: Record<string, [any, string, string]> = {
  done: [CheckCircle2, 'text-emerald-400', 'mastered'], current: [PlayCircle, 'text-indigo-300', 'current'], revise: [RotateCcw, 'text-amber-300', 'needs revision'],
  available: [Circle, 'text-slate-400', 'unlocked'], locked: [Lock, 'text-slate-600', 'locked'],
}

export function LearningPathPage() {
  const { profile, version } = useApp()
  const [c, setC] = useState<any[]>([])
  const [next, setNext] = useState<any>(null)
  useEffect(() => { api('/api/curriculum').then(setC); api('/api/dashboard').then((d) => setNext(d.next_problem)) }, [version])
  const weeks = Math.max(...c.map((x) => x.week_end), 1)
  return (
    <div className="fade-in mx-auto max-w-5xl p-8">
      <PageHeader title="My Learning Path" sub={profile?.track === 'learning' ? `${profile.months_available}-month roadmap · prerequisites are enforced; a topic unlocks once its prerequisites reach 50% mastery.` : 'Topic mastery across the full DSA roadmap (your track focuses on the highlighted topics).'} />
      {next && <Card className="mb-4 flex items-center gap-3 p-4 text-sm"><Badge tone="green">Next</Badge><b>{next.title}</b><span className="text-slate-400">— {next.reason}</span></Card>}
      <Card className="divide-y divide-line">
        {c.map((t) => {
          const [I, tone, label] = ST[t.status]
          return (
            <div key={t.topic} className={cx('grid grid-cols-[24px_1.2fr_1.5fr_1fr_80px] items-center gap-4 px-5 py-3', t.status === 'current' && 'bg-indigo-500/[.05]')}>
              <I size={16} className={tone} />
              <div><div className="text-sm font-medium text-slate-100">{t.topic}</div><div className="text-[11px] text-slate-500">{t.prerequisites.length ? `needs ${t.prerequisites.join(', ')}` : 'no prerequisites'}</div></div>
              <div className="relative h-5 rounded bg-white/[.03]"><div className={cx('absolute inset-y-1 rounded', t.status === 'current' ? 'bg-indigo-400/60' : t.status === 'done' ? 'bg-emerald-500/40' : 'bg-white/10')} style={{ left: `${((t.week_start - 1) / weeks) * 100}%`, width: `${Math.max(3, ((t.week_end - t.week_start + 1) / weeks) * 100)}%` }} /></div>
              <div><div className="mb-1 flex justify-between text-[11px]"><span className="text-slate-500">mastery</span><span className="tabular-nums text-slate-300">{t.mastery}%</span></div><Bar value={t.mastery} tone={t.status === 'revise' ? 'bg-amber-400' : 'bg-emerald-400'} /></div>
              <div className={cx('text-right text-[11px]', tone)}>{label}<div className="text-slate-600">wk {t.week_start}–{t.week_end}</div></div>
            </div>
          )
        })}
      </Card>
    </div>
  )
}
