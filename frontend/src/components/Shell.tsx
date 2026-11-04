import { Activity, BarChart3, Brain, LifeBuoy, Building2, CalendarDays, ChevronsUpDown, Code2, Dna, GitBranch, LayoutDashboard, LogOut, MessagesSquare, Repeat, Route, Settings, Timer } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { post } from '../lib/api'
import { useApp } from '../lib/app'
import { cx } from './ui'
import { AgentDock } from './AgentDock'

const NAV = [
  ['dashboard', 'Dashboard', LayoutDashboard], ['memory', 'Memory & Catch-up', LifeBuoy], ['path', 'My Learning Path', Route], ['practice', 'Practice Arena', Code2], ['thinkmap', 'ThinkMap', GitBranch],
  ['revision', 'Smart Revision', Repeat], ['calendar', 'Calendar', CalendarDays], ['interview', 'Interview Simulator', MessagesSquare], ['mock-oa', 'Mock OA', Timer],
  ['mistakes', 'Mistake DNA', Dna], ['company', 'Company Preparation', Building2], ['analytics', 'Performance Analytics', BarChart3], ['agents', 'Agent Console', Activity], ['settings', 'Settings', Settings],
] as const
export const AVATAR: Record<string, string> = { oa: 'from-sky-400 to-indigo-500', interview: 'from-violet-400 to-fuchsia-500', learning: 'from-emerald-400 to-teal-500' }

export function Shell() {
  const { profile, profiles, refresh, bump } = useApp()
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  if (!profile) return null
  async function switchTo(id: number) { await post('/api/profiles/active', { user_id: id }); setOpen(false); await refresh(); bump(); nav('/app/dashboard') }
  async function logout() { await post('/api/logout'); await refresh(); nav('/') }
  return (
    <div className="flex h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-ink-900/60">
        <div className="flex h-14 items-center gap-2.5 px-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 to-violet-500 text-xs font-bold text-white">S</div>
          <span className="text-sm font-semibold tracking-tight">SOCH</span>
          <span className="ml-auto rounded bg-violet-500/10 px-1.5 py-0.5 text-[10px] text-violet-300">agents</span>
        </div>
        <div className="relative px-3">
          <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-2.5 rounded-lg border border-line bg-white/[.03] p-2 text-left hover:bg-white/[.06]">
            <div className={cx('flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br text-sm font-semibold text-white', AVATAR[profile.track])}>{profile.name[0]}</div>
            <div className="min-w-0 flex-1"><div className="truncate text-sm font-medium">{profile.name}</div><div className="truncate text-[11px] text-slate-500">{profile.track_label}</div></div>
            <ChevronsUpDown size={14} className="text-slate-500" />
          </button>
          {open && (
            <div className="fade-in absolute left-3 right-3 top-full z-30 mt-1 rounded-lg border border-line bg-ink-800 p-1 shadow-2xl">
              <div className="px-2 py-1 text-[10px] uppercase tracking-wider text-slate-500">Switch profile</div>
              {profiles.map((p) => (
                <button key={p.id} onClick={() => switchTo(p.id)} className={cx('flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-white/[.06]', p.id === profile.id && 'bg-white/[.05]')}>
                  <div className={cx('flex h-5 w-5 items-center justify-center rounded bg-gradient-to-br text-[10px] font-semibold text-white', AVATAR[p.track])}>{p.name[0]}</div>
                  <span className="flex-1">{p.name}</span><span className="text-[10px] text-slate-500">{p.track.toUpperCase()}</span>
                </button>
              ))}
              <button onClick={() => nav('/')} className="mt-1 w-full rounded-md border-t border-line px-2 py-1.5 text-left text-xs text-indigo-300 hover:bg-white/[.04]">+ New sign-up</button>
            </div>
          )}
        </div>
        <nav className="mt-3 flex-1 space-y-px overflow-y-auto px-3">
          {NAV.map(([to, label, Icon]) => (
            <NavLink key={to} to={`/app/${to}`} className={({ isActive }) => cx('flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] transition', isActive ? 'bg-indigo-500/10 text-indigo-200' : 'text-slate-400 hover:bg-white/[.04] hover:text-slate-200')}>
              <Icon size={15} />{label}
            </NavLink>
          ))}
        </nav>
        <AgentDock />
        <div className="border-t border-line p-3">
          <div className="mb-2 flex justify-between px-1 text-[11px] text-slate-500"><span>{profile.xp} XP</span><span>🔥 {profile.streak} day streak</span></div>
          <button onClick={logout} className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-[13px] text-slate-400 hover:bg-white/[.04] hover:text-rose-300"><LogOut size={14} />Log out</button>
        </div>
      </aside>
      <main key={`${profile.id}-${profile.time_offset_days}`} className="min-w-0 flex-1 overflow-y-auto"><Outlet /></main>
    </div>
  )
}
