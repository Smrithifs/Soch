import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { api, Profile } from './api'

type Ctx = { profile: Profile | null; profiles: Profile[]; loading: boolean; refresh: () => Promise<void>; version: number; bump: () => void }
const AppCtx = createContext<Ctx>({} as Ctx)

export function AppProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)
  const refresh = useCallback(async () => {
    try {
      const d = await api<{ active_id: number | null; profiles: Profile[] }>('/api/profiles')
      setProfiles(d.profiles)
      setProfile(d.profiles.find((p) => p.id === d.active_id) || null)
    } finally { setLoading(false) }
  }, [])
  useEffect(() => { refresh() }, [refresh])
  const bump = useCallback(() => { setVersion((v) => v + 1); refresh() }, [refresh])
  return <AppCtx.Provider value={{ profile, profiles, loading, refresh, version, bump }}>{children}</AppCtx.Provider>
}
export const useApp = () => useContext(AppCtx)
