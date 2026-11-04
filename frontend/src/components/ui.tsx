import { createContext, ReactNode, useCallback, useContext, useState } from 'react'

export function cx(...c: (string | false | null | undefined)[]) { return c.filter(Boolean).join(' ') }

export function Card({ className, children, ...r }: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cx('card', className)} {...r}>{children}</div>
}

type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' | 'subtle' | 'success'; size?: 'sm' | 'md' }
export function Button({ variant = 'primary', size = 'md', className, ...r }: BtnProps) {
  const v = {
    primary: 'bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_0_1px_rgba(129,140,248,.4),0_8px_24px_-8px_rgba(99,102,241,.6)]',
    success: 'bg-emerald-500 text-emerald-950 hover:bg-emerald-400',
    ghost: 'border border-line bg-white/[.03] text-slate-200 hover:bg-white/[.07]',
    subtle: 'text-slate-400 hover:text-slate-100 hover:bg-white/[.05]',
  }[variant]
  const s = size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-9 px-3.5 text-sm'
  return <button className={cx('inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-40', v, s, className)} {...r} />
}

export function Badge({ tone = 'slate', children, className }: { tone?: 'slate' | 'blue' | 'violet' | 'green' | 'amber' | 'red'; children: ReactNode; className?: string }) {
  const t = {
    slate: 'bg-white/[.06] text-slate-300 ring-white/10', blue: 'bg-sky-500/10 text-sky-300 ring-sky-400/20', violet: 'bg-violet-500/10 text-violet-300 ring-violet-400/20',
    green: 'bg-emerald-500/10 text-emerald-300 ring-emerald-400/20', amber: 'bg-amber-500/10 text-amber-300 ring-amber-400/20', red: 'bg-rose-500/10 text-rose-300 ring-rose-400/20',
  }[tone]
  return <span className={cx('inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset', t, className)}>{children}</span>
}

export const inputClass = 'w-full rounded-lg border border-line bg-ink-950/60 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-indigo-400/60 focus:ring-2 focus:ring-indigo-500/20'

export function PageHeader({ title, sub, right }: { title: string; sub?: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-50">{title}</h1>
        {sub && <p className="mt-1 text-sm text-slate-400">{sub}</p>}
      </div>
      {right}
    </div>
  )
}

export function Stat({ label, value, hint, accent = 'text-slate-50' }: { label: string; value: ReactNode; hint?: ReactNode; accent?: string }) {
  return (
    <Card className="p-4">
      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</div>
      <div className={cx('mt-1.5 text-2xl font-semibold tabular-nums', accent)}>{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </Card>
  )
}

export function Ring({ value, size = 88, label, color = '#818cf8' }: { value: number; size?: number; label?: string; color?: string }) {
  const r = size / 2 - 7, c = 2 * Math.PI * r
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(148,163,184,.12)" strokeWidth="6" fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth="6" fill="none" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(100, value) / 100)} style={{ transition: 'stroke-dashoffset .6s' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-lg font-semibold tabular-nums text-slate-50">{value}%</div>
        {label && <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>}
      </div>
    </div>
  )
}

export function Bar({ value, tone = 'bg-indigo-400' }: { value: number; tone?: string }) {
  return <div className="h-1.5 overflow-hidden rounded-full bg-white/[.06]"><div className={cx('h-full rounded-full transition-all duration-500', tone)} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>
}

/** Minimal, safe markdown: code fences, inline code, bold, italic, bullets, quotes. */
export function Md({ text, className }: { text: string; className?: string }) {
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const inline = (s: string) => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s.,;:)]|$)/g, '$1<em>$2</em>').replace(/(^|\W)_([^_]+)_(\W|$)/g, '$1<em>$2</em>$3')
  const out: string[] = []
  const blocks = text.split(/```/)
  blocks.forEach((b, i) => {
    if (i % 2) { out.push(`<pre><code>${esc(b.replace(/^\w*\n/, ''))}</code></pre>`); return }
    let list = false
    for (const line of b.split('\n')) {
      const li = line.match(/^\s*[-•]\s+(.*)/)
      if (li) { if (!list) { out.push('<ul>'); list = true } out.push(`<li>${inline(li[1])}</li>`); continue }
      if (list) { out.push('</ul>'); list = false }
      if (line.startsWith('> ')) out.push(`<blockquote>${inline(line.slice(2))}</blockquote>`)
      else if (line.trim()) out.push(`<p>${inline(line)}</p>`)
    }
    if (list) out.push('</ul>')
  })
  return <div className={cx('md text-sm leading-relaxed text-slate-300', className)} dangerouslySetInnerHTML={{ __html: out.join('') }} />
}

// ---------------------------------------------------------------- toast
const ToastCtx = createContext<(m: string, t?: 'ok' | 'err') => void>(() => {})
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<{ id: number; m: string; t: string }[]>([])
  const push = useCallback((m: string, t: 'ok' | 'err' = 'ok') => {
    const id = Date.now() + Math.random()
    setItems((x) => [...x, { id, m, t }])
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 3500)
  }, [])
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {items.map((i) => (
          <div key={i.id} className={cx('fade-in rounded-lg border px-3.5 py-2.5 text-sm shadow-xl backdrop-blur', i.t === 'err' ? 'border-rose-400/30 bg-rose-950/80 text-rose-100' : 'border-emerald-400/30 bg-emerald-950/80 text-emerald-100')}>{i.m}</div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}
export const useToast = () => useContext(ToastCtx)

export const DIFF_TONE: Record<string, 'green' | 'amber' | 'red'> = { Easy: 'green', Medium: 'amber', Hard: 'red' }

export function SourceBadge({ source, model }: { source?: string; model?: string }) {
  if (!source) return null
  return source === 'llm'
    ? <Badge tone="violet">✦ agent{model ? ` · ${model}` : ''}</Badge>
    : <Badge tone="slate" className="opacity-80">offline rules</Badge>
}
