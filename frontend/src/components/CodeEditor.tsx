import Editor, { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'

// Bundle Monaco locally (no CDN) so the editor works offline.
;(self as any).MonacoEnvironment = { getWorker: () => new editorWorker() }
loader.config({ monaco })
monaco.editor.defineTheme('soch', {
  base: 'vs-dark', inherit: true,
  rules: [{ token: 'keyword', foreground: 'a78bfa' }, { token: 'string', foreground: '86efac' }, { token: 'number', foreground: 'fbbf24' }, { token: 'comment', foreground: '5b6478', fontStyle: 'italic' }],
  colors: { 'editor.background': '#07090f', 'editor.lineHighlightBackground': '#0f1320', 'editorLineNumber.foreground': '#2f374d', 'editorLineNumber.activeForeground': '#8b93a7', 'editor.selectionBackground': '#312e8180', 'editorGutter.background': '#07090f' },
})

export function CodeEditor({ value, onChange, language, height = '100%' }: { value: string; onChange: (v: string) => void; language: string; height?: string }) {
  return (
    <Editor height={height} language={language} theme="soch" value={value} onChange={(v) => onChange(v ?? '')}
      options={{ fontSize: 13, fontFamily: 'JetBrains Mono, monospace', fontLigatures: true, minimap: { enabled: false }, scrollBeyondLastLine: false, padding: { top: 12 }, tabSize: 4, renderLineHighlight: 'all', smoothScrolling: true, automaticLayout: true }} />
  )
}
