import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { TacticalMap3D } from './components/TacticalMap3D'

const COLORS = ['#00f0ff', '#f5e600', '#ff2a6d', '#05ffa1', '#9d4edd']

interface Agent {
  id: string
  name: string
  status: string
  color: string
  position: { x: number; y: number; angle: number }
}

interface MissionState {
  mission_time: string
  coverage_pct: number
  agents: Agent[]
  alerts: { type: string; agent: string; location: string; detail?: string }[]
  challenge_goals?: {
    ats: {
      name: string
      title: string
      phase: string
      explore_threshold: number
      surveil_threshold: number
      explore_pct: number
      surveil_pct: number
      achieved: boolean
    }
    se3: {
      name: string
      title: string
      track: string
      status: string
      changes_detected: number
      achieved: boolean
    }
  }
}

function GoalRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: 11, color: 'rgba(255,255,255,0.56)' }}>
      <span>{label}</span>
      <strong style={{ color: '#fff', fontWeight: 800 }}>{value}</strong>
    </div>
  )
}

function GoalCard({
  name,
  title,
  state,
  achieved,
  children,
}: {
  name: string
  title: string
  state: string
  achieved: boolean
  children: ReactNode
}) {
  return (
    <div
      style={{
        border: `1px solid ${achieved ? 'rgba(5,255,161,0.45)' : 'rgba(0,240,255,0.18)'}`,
        background: 'rgba(10,15,31,0.58)',
        padding: '10px 12px',
        borderRadius: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 5 }}>
        <span style={{ color: '#00f0ff', fontWeight: 900, fontSize: 11, letterSpacing: 1.1 }}>{name}</span>
        <span style={{ color: achieved ? '#05ffa1' : '#f5e600', fontWeight: 900, fontSize: 10, letterSpacing: 0.8 }}>
          {achieved ? 'ACHIEVED' : state}
        </span>
      </div>
      <div style={{ fontSize: 12, fontWeight: 800, lineHeight: 1.25, marginBottom: 8 }}>{title}</div>
      <div style={{ display: 'grid', gap: 5 }}>{children}</div>
    </div>
  )
}

function App() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<TacticalMap3D | null>(null)
  const [state, setState] = useState<MissionState | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    mapRef.current = new TacticalMap3D(containerRef.current)
    mapRef.current.start()

    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/state')
        const data = await res.json()
        setState(data)
      } catch (e) {
        console.error('state poll failed', e)
      }
    }, 500)

    return () => {
      clearInterval(interval)
      mapRef.current?.dispose()
      mapRef.current = null
    }
  }, [])

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', overflow: 'hidden', background: '#0a0f1f' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      <div
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          padding: '14px 18px',
          borderRadius: 12,
          background: 'rgba(10,15,31,0.75)',
          border: '1px solid rgba(0,240,255,0.25)',
          color: '#fff',
          fontFamily: 'Inter, system-ui, sans-serif',
          backdropFilter: 'blur(6px)',
          width: 318,
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 1.5, color: '#00f0ff', marginBottom: 8 }}>SCOUT C2 · TACTICAL</div>
        <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>MISSION: MUNICH</div>
        <div style={{ fontSize: 13, opacity: 0.8, marginBottom: 12 }}>
          T+ {state?.mission_time ?? '--:--'} · COVERAGE {state?.coverage_pct?.toFixed?.(1) ?? '0.0'}%
        </div>

        <div style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
          {state?.challenge_goals?.ats && (
            <GoalCard
              name={state.challenge_goals.ats.name}
              title={state.challenge_goals.ats.title}
              state={state.challenge_goals.ats.phase}
              achieved={state.challenge_goals.ats.achieved}
            >
              <GoalRow
                label="Explore"
                value={`${state.challenge_goals.ats.explore_pct.toFixed(1)} / ${state.challenge_goals.ats.explore_threshold}%`}
              />
              <GoalRow
                label="Surveil"
                value={`${state.challenge_goals.ats.surveil_pct.toFixed(1)} / ${state.challenge_goals.ats.surveil_threshold}%`}
              />
            </GoalCard>
          )}
          {state?.challenge_goals?.se3 && (
            <GoalCard
              name={state.challenge_goals.se3.name}
              title={state.challenge_goals.se3.title}
              state={state.challenge_goals.se3.status}
              achieved={state.challenge_goals.se3.achieved}
            >
              <GoalRow label="Layer" value="3D map intelligence" />
              <GoalRow label="Changes" value={String(state.challenge_goals.se3.changes_detected)} />
            </GoalCard>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: 12 }}>
          {state?.agents?.map((a, i) => (
            <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: a.color || COLORS[i % COLORS.length],
                  boxShadow: `0 0 8px ${a.color || COLORS[i % COLORS.length]}`,
                }}
              />
              <span style={{ opacity: 0.85 }}>{a.name}</span>
              <span style={{ opacity: 0.5, fontSize: 10 }}>{a.status}</span>
            </div>
          ))}
        </div>

        {state?.alerts?.length ? (
          <div style={{ marginTop: 12, display: 'grid', gap: 6 }}>
            {state.alerts.slice(0, 2).map((alert, idx) => (
              <div
                key={`${alert.type}-${alert.agent}-${idx}`}
                style={{
                  borderLeft: `3px solid ${alert.type === 'CHANGE' ? '#f5e600' : '#ff2a6d'}`,
                  background: 'rgba(255,255,255,0.06)',
                  padding: '7px 9px',
                  borderRadius: 5,
                  fontSize: 11,
                }}
              >
                <strong>{alert.type}</strong> · {alert.agent} @ {alert.location}
                {alert.detail ? <div style={{ color: 'rgba(255,255,255,0.62)', marginTop: 2 }}>{alert.detail}</div> : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          padding: '10px 14px',
          borderRadius: 8,
          background: 'rgba(10,15,31,0.7)',
          border: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.5)',
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: 11,
          pointerEvents: 'none',
        }}
      >
        WASD / Arrows move · Scroll zoom · Left-drag rotate · Right-drag pan
      </div>
    </div>
  )
}

export default App
