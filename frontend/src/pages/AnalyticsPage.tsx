import { useEffect, useState } from 'react'
import { Bar as RBar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, PageHeader, Stat } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const tt = { contentStyle: { background: '#0f1320', border: '1px solid rgba(148,163,184,.15)', borderRadius: 8, fontSize: 12 }, cursor: { fill: 'rgba(148,163,184,.06)' } }
const ax = { tick: { fill: '#64748b', fontSize: 11 }, axisLine: false, tickLine: false }

export function AnalyticsPage() {
  const { version } = useApp()
  const [d, setD] = useState<any>(null)
  useEffect(() => { api('/api/analytics').then(setD) }, [version])
  if (!d) return null
  const mistakes = Object.entries(d.mistakes).map(([k, v]) => ({ k, v }))
  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <PageHeader title="Performance Analytics" sub="Computed from your stored submissions, revisions and interviews — no estimates." />
      <div className="grid gap-4 md:grid-cols-5">
        <Stat label="Readiness" value={`${d.progress.readiness}%`} accent="text-indigo-300" />
        <Stat label="XP" value={d.xp} /><Stat label="Streak" value={`${d.streak}d`} />
        <Stat label="Submissions" value={d.submissions.total} hint={`${d.submissions.Accepted || 0} accepted`} />
        <Stat label="Revision accuracy" value={`${d.progress.revision_accuracy}%`} hint={`${d.progress.revision_attempts} attempts`} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card className="p-5"><div className="mb-3 text-sm font-semibold">XP — last 7 days</div><div className="h-52"><ResponsiveContainer><BarChart data={d.weekly}><CartesianGrid stroke="#1c2233" vertical={false} /><XAxis dataKey="day" {...ax} /><YAxis {...ax} width={30} /><Tooltip {...tt} /><RBar dataKey="xp" fill="#818cf8" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></Card>
        <Card className="p-5"><div className="mb-3 text-sm font-semibold">Topic mastery</div><div className="h-52"><ResponsiveContainer><BarChart data={d.mastery} layout="vertical"><XAxis type="number" domain={[0, 100]} {...ax} /><YAxis type="category" dataKey="topic" width={110} {...ax} /><Tooltip {...tt} /><RBar dataKey="mastery" radius={[0, 4, 4, 0]}>{d.mastery.map((m: any) => <Cell key={m.topic} fill={m.status === 'revise' ? '#fbbf24' : m.status === 'current' ? '#818cf8' : '#34d399'} />)}</RBar></BarChart></ResponsiveContainer></div></Card>
        <Card className="p-5"><div className="mb-3 text-sm font-semibold">Accuracy by topic (submissions)</div>{d.topic_accuracy.length ? <div className="h-44"><ResponsiveContainer><BarChart data={d.topic_accuracy}><CartesianGrid stroke="#1c2233" vertical={false} /><XAxis dataKey="topic" {...ax} /><YAxis domain={[0, 100]} {...ax} width={30} /><Tooltip {...tt} /><RBar dataKey="accuracy" fill="#34d399" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div> : <div className="text-xs text-slate-500">No submissions yet.</div>}</Card>
        <Card className="p-5"><div className="mb-3 text-sm font-semibold">Mistakes by category</div>{mistakes.length ? <div className="h-44"><ResponsiveContainer><BarChart data={mistakes}><XAxis dataKey="k" {...ax} interval={0} tick={{ fill: '#64748b', fontSize: 10 }} /><YAxis allowDecimals={false} {...ax} width={24} /><Tooltip {...tt} /><RBar dataKey="v" fill="#fb7185" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div> : <div className="text-xs text-slate-500">No mistakes recorded.</div>}</Card>
        {d.interviews.length > 0 && <Card className="p-5 lg:col-span-2"><div className="mb-3 text-sm font-semibold">Interview scores over time</div><div className="h-44"><ResponsiveContainer><LineChart data={d.interviews.map((i: any, n: number) => ({ n: i.baseline ? 'baseline' : `mock ${n}`, overall: i.overall, comm: i.scores?.Communication, time: i.scores?.['Time complexity'] }))}><CartesianGrid stroke="#1c2233" /><XAxis dataKey="n" {...ax} /><YAxis domain={[0, 10]} {...ax} width={24} /><Tooltip {...tt} /><Line dataKey="overall" stroke="#a78bfa" strokeWidth={2} /><Line dataKey="comm" stroke="#fbbf24" /><Line dataKey="time" stroke="#38bdf8" /></LineChart></ResponsiveContainer></div></Card>}
      </div>
    </div>
  )
}
