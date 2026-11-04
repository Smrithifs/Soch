import { Background, Controls, Edge, Handle, MarkerType, Node, Position, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { CheckCircle2, ChevronDown, Circle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Bar, cx, Md, PageHeader } from '../components/ui'
import { api, put } from '../lib/api'

function StepNode({ data }: any) {
  return (
    <div onClick={data.onToggle} className={cx('w-64 cursor-pointer rounded-xl border bg-ink-850 shadow-lg transition', data.done ? 'border-emerald-400/40' : data.open ? 'border-indigo-400/50' : 'border-line hover:border-slate-500')}>
      <Handle type="target" position={Position.Top} className="!border-0 !bg-slate-600" />
      <div className="flex items-center gap-2 px-3 py-2.5">
        <span className="flex h-5 w-5 items-center justify-center rounded bg-white/[.06] text-[10px] font-semibold text-slate-400">{data.i}</span>
        <span className="flex-1 text-[13px] font-medium text-slate-100">{data.title}</span>
        <ChevronDown size={13} className={cx('text-slate-500 transition', data.open && 'rotate-180')} />
      </div>
      {data.open && (
        <div className="nodrag border-t border-line px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
          <Md text={data.body} className="!text-xs" />
          <button onClick={data.onDone} className={cx('mt-2 flex items-center gap-1.5 text-[11px] font-medium', data.done ? 'text-emerald-300' : 'text-slate-400 hover:text-emerald-300')}>
            {data.done ? <CheckCircle2 size={12} /> : <Circle size={12} />}{data.done ? 'Completed' : 'Mark step complete'}
          </button>
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!border-0 !bg-slate-600" />
    </div>
  )
}
const nodeTypes = { step: StepNode }

export function ThinkMapPage() {
  const { slug } = useParams()
  const nav = useNavigate()
  const [list, setList] = useState<any[]>([])
  const [d, setD] = useState<any>(null)
  const [open, setOpen] = useState<string[]>(['n1'])
  useEffect(() => { api('/api/problems').then((l) => { setList(l); if (!slug) nav(`/app/thinkmap/${l[0].slug}`, { replace: true }) }) }, [])
  useEffect(() => { if (slug) api(`/api/thinkmap/${slug}`).then(setD) }, [slug])

  async function toggleDone(id: string) {
    const completed = d.completed.includes(id) ? d.completed.filter((x: string) => x !== id) : [...d.completed, id]
    setD({ ...d, completed })
    await put(`/api/thinkmap/${slug}`, { completed })
  }
  const { nodes, edges } = useMemo(() => {
    if (!d) return { nodes: [], edges: [] }
    const pos = [[0, 0], [300, 0], [600, 0], [600, 150], [300, 150], [0, 150], [0, 300], [300, 300], [600, 300], [300, 450]]
    const nodes: Node[] = d.nodes.map((n: any, i: number) => ({
      id: n.id, type: 'step', position: { x: pos[i][0], y: pos[i][1] + (open.includes(n.id) ? 0 : 0) },
      data: { ...n, i: i + 1, open: open.includes(n.id), done: d.completed.includes(n.id), onToggle: () => setOpen((o) => o.includes(n.id) ? o.filter((x) => x !== n.id) : [...o, n.id]), onDone: () => toggleDone(n.id) },
    }))
    const edges: Edge[] = d.nodes.slice(1).map((n: any, i: number) => ({ id: `e${i}`, source: d.nodes[i].id, target: n.id, animated: !d.completed.includes(n.id), style: { stroke: d.completed.includes(d.nodes[i].id) ? '#34d399' : '#475569' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' } }))
    return { nodes, edges }
  }, [d, open])

  return (
    <div className="flex h-full flex-col p-8">
      <PageHeader title="ThinkMap" sub="A visual problem-solving workflow. Click a node to expand; mark steps complete — progress is saved per student."
        right={<select value={slug} onChange={(e) => nav(`/app/thinkmap/${e.target.value}`)} className="rounded-md border border-line bg-ink-900 px-2 py-1.5 text-sm">{list.map((p) => <option key={p.slug} value={p.slug}>{p.title}</option>)}</select>} />
      {d && <div className="mb-3 flex items-center gap-3 text-xs text-slate-400"><span>{d.completed.length}/10 steps</span><div className="w-48"><Bar value={d.completed.length * 10} tone="bg-emerald-400" /></div></div>}
      <div className="card min-h-[520px] flex-1 overflow-hidden">
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView minZoom={0.3} maxZoom={1.8} colorMode="dark" proOptions={{ hideAttribution: true }}>
          <Background color="#1c2233" gap={20} /><Controls />
        </ReactFlow>
      </div>
    </div>
  )
}
