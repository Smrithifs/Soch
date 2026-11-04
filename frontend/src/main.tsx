import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { ToastProvider } from './components/ui'
import { AppProvider, useApp } from './lib/app'
import './index.css'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { CalendarPage } from './pages/CalendarPage'
import { CompanyPage } from './pages/CompanyPage'
import { DashboardPage } from './pages/DashboardPage'
import { InterviewPage } from './pages/InterviewPage'
import { LearningPathPage } from './pages/LearningPathPage'
import { MistakePage } from './pages/MistakePage'
import { MockOAPage } from './pages/MockOAPage'
import { PracticePage } from './pages/PracticePage'
import { RevisionPage } from './pages/RevisionPage'
import { SettingsPage } from './pages/SettingsPage'
import { SignupPage } from './pages/SignupPage'
import { ThinkMapPage } from './pages/ThinkMapPage'
import { MemoryPage } from './pages/MemoryPage'
import { AgentConsolePage } from './pages/AgentConsolePage'

function Gate({ children, need }: { children: React.ReactElement; need: boolean }) {
  const { profile, loading } = useApp()
  if (loading) return <div className="flex h-screen items-center justify-center text-sm text-slate-500">Loading…</div>
  if (need && !profile) return <Navigate to="/" replace />
  return children
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ToastProvider>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Gate need={false}><SignupPage /></Gate>} />
            <Route path="/app" element={<Gate need><Shell /></Gate>}>
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="path" element={<LearningPathPage />} />
              <Route path="practice" element={<PracticePage />} />
              <Route path="practice/:slug" element={<PracticePage />} />
              <Route path="thinkmap" element={<ThinkMapPage />} />
              <Route path="thinkmap/:slug" element={<ThinkMapPage />} />
              <Route path="revision" element={<RevisionPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              <Route path="interview" element={<InterviewPage />} />
              <Route path="mock-oa" element={<MockOAPage />} />
              <Route path="mistakes" element={<MistakePage />} />
              <Route path="company" element={<CompanyPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="memory" element={<MemoryPage />} />
              <Route path="agents" element={<AgentConsolePage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </ToastProvider>
  </React.StrictMode>,
)
