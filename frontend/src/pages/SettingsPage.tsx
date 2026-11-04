import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, PageHeader, useToast } from '../components/ui'
import { post, put } from '../lib/api'
import { useApp } from '../lib/app'

export function SettingsPage() {
  const { profile, refresh, bump } = useApp()
  const [m, setM] = useState(profile?.daily_minutes || 20)
  const [lang, setLang] = useState(profile?.language || 'Java')
  const toast = useToast()
  const nav = useNavigate()
  if (!profile) return null
  return (
    <div className="fade-in mx-auto max-w-3xl p-8">
      <PageHeader title="Settings" />
      <Card className="space-y-4 p-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <label>Daily minutes<input type="number" min={5} max={240} value={m} onChange={(e) => setM(+e.target.value)} className="mt-1 w-full rounded-md border border-line bg-ink-950 px-2 py-1.5" /></label>
          <label>Language<select value={lang} onChange={(e) => setLang(e.target.value)} className="mt-1 w-full rounded-md border border-line bg-ink-950 px-2 py-1.5"><option>Java</option><option>Python</option></select></label>
        </div>
        <Button onClick={async () => { await put('/api/profiles/active', { daily_minutes: m, language: lang }); bump(); toast('Saved — plan regenerated') }}>Save & regenerate plan</Button>
      </Card>
      <Card className="mt-4 p-6">
        <div className="text-sm font-semibold">Profile</div>
        <pre className="mt-2 overflow-x-auto rounded-md bg-ink-950 p-3 font-mono text-[11px] text-slate-400">{JSON.stringify({ name: profile.name, track: profile.track_label, company: profile.company, role: profile.role, days_left: profile.days_left, level: profile.level, starting_topic: profile.starting_topic, revise_topics: profile.revise_topics }, null, 2)}</pre>
      </Card>
      <Card className="mt-4 border-rose-400/20 p-6">
        <div className="text-sm font-semibold text-rose-200">Reset demo</div>
        <p className="mt-1 text-xs text-slate-400">Drops all data and restores the original Smrithi, Dhanya and Vismaya profiles.</p>
        <Button variant="ghost" className="mt-3 border-rose-400/30 text-rose-200" onClick={async () => { if (!confirm('Reset all demo data?')) return; await post('/api/demo/reset'); await refresh(); bump(); toast('Demo restored'); nav('/') }}>Reset demo data</Button>
      </Card>
    </div>
  )
}
