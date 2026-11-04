import { Brain, Check, Eye, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Badge, Button, Card, cx, PageHeader } from '../components/ui'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'

export function RevisionPage() {
  const [cards, setCards] = useState<any[]>([])
  const [idx, setIdx] = useState(0)
  const [pick, setPick] = useState<number | null>(null)
  const [res, setRes] = useState<any>(null)
  const [sp] = useSearchParams()
  const { bump } = useApp()
  const load = () => api('/api/revisions').then((c) => {
    setCards(c)
    const want = sp.get('card')
    const i = want ? c.findIndex((x: any) => x.key === want) : -1
    setIdx(i >= 0 ? i : 0)
  })
  useEffect(() => { load() }, [])
  const card = cards[idx]

  async function answer(revealed = false) {
    const r = await post(`/api/revisions/${card.id}/answer`, { choice: revealed ? null : pick, revealed })
    setRes(r); bump()
  }
  function next() { setRes(null); setPick(null); api('/api/revisions').then((c) => { setCards(c); setIdx(0) }) }

  return (
    <div className="fade-in mx-auto max-w-5xl p-8">
      <PageHeader title="Smart Revision" sub="Spaced repetition with concept cards and 'predict the output' code cards: missed cards return in 10 minutes; consecutive correct answers stretch the interval 1 → 3 → 7 → 14 → 30 days." />
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        {card ? (
          <Card key={card.id} className="fade-in p-6">
            <div className="mb-4 flex items-center gap-2"><Badge tone="violet">{card.topic}</Badge><Badge>{card.concept}</Badge>{card.type === 'code' && <Badge tone="blue">predict the output</Badge>}{card.priority_reasons?.map((r: string) => <Badge key={r} tone="amber">{r}</Badge>)}</div>
            <div className="flex gap-3"><Brain size={18} className="mt-0.5 shrink-0 text-violet-300" /><h2 className="text-lg font-medium leading-snug text-slate-50">{card.question.replace(/`/g, '')}</h2></div>
            {card.code && <pre className="mt-4 overflow-x-auto rounded-lg border border-line bg-ink-950 p-4 font-mono text-[13px] leading-relaxed text-sky-100">{card.code}</pre>}
            <div className="mt-5 space-y-2">
              {card.options.map((o: string, i: number) => {
                const correct = res && res.card.answer === i, wrong = res && pick === i && !res.correct
                return (
                  <button key={i} disabled={!!res} onClick={() => setPick(i)} className={cx('flex w-full items-center gap-3 rounded-lg border px-4 py-2.5 text-left text-sm transition', correct ? 'border-emerald-400/50 bg-emerald-500/10' : wrong ? 'border-rose-400/50 bg-rose-500/10' : pick === i ? 'border-indigo-400/60 bg-indigo-500/10' : 'border-line hover:bg-white/[.03]')}>
                    <span className="flex h-5 w-5 items-center justify-center rounded border border-line text-[10px] text-slate-500">{'ABCD'[i]}</span>{o}
                    {correct && <Check size={14} className="ml-auto text-emerald-400" />}{wrong && <X size={14} className="ml-auto text-rose-400" />}
                  </button>
                )
              })}
            </div>
            {res ? (
              <div className="fade-in mt-5 rounded-lg border border-line bg-ink-950/60 p-4">
                <div className={cx('text-sm font-semibold', res.correct ? 'text-emerald-300' : 'text-rose-300')}>{res.correct ? 'Correct' : 'Not quite — recorded in Mistake DNA'}</div>
                <p className="mt-1 text-sm text-slate-300">{res.card.explanation}</p>
                <div className="mt-2 text-xs text-slate-500">Next review in <b className="text-slate-300">{res.next_due_in}</b></div>
                <Button className="mt-3" size="sm" onClick={next}>Next card</Button>
              </div>
            ) : (
              <div className="mt-5 flex gap-2"><Button disabled={pick === null} onClick={() => answer()}>Check answer</Button><Button variant="subtle" onClick={() => answer(true)}><Eye size={13} />Reveal (counts as miss)</Button></div>
            )}
          </Card>
        ) : <Card className="p-6 text-sm text-slate-500">No cards yet.</Card>}
        <Card className="p-5">
          <div className="mb-3 text-sm font-semibold">Queue (priority order)</div>
          <div className="space-y-1">
            {cards.map((c, i) => (
              <button key={c.id} onClick={() => { setIdx(i); setRes(null); setPick(null) }} className={cx('flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs', i === idx ? 'bg-white/[.06]' : 'hover:bg-white/[.03]')}>
                <span className="text-slate-300">{c.type === 'code' && <span className="mr-1 text-sky-400">{'</>'}</span>}{c.concept}</span>
                <span className="flex items-center gap-2 tabular-nums text-slate-500">{c.attempts ? `${c.correct}/${c.attempts}` : 'new'}<Badge tone={c.last_result === 'wrong' ? 'red' : c.due ? 'violet' : 'green'}>{c.last_result === 'wrong' ? 'missed' : c.due ? 'due' : `${c.interval_days}d`}</Badge></span>
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
