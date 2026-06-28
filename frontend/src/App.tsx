import { useEffect, useRef, useState } from 'react'
import { TacticalMap3D } from './components/TacticalMap3D'

const COLORS = ['#00f0ff', '#f5e600', '#ff2a6d', '#05ffa1', '#9d4edd']

interface Agent {
  id: string
  name: string
  status: string
  position: { x: number; y: number; angle: number }
}

interface MissionState {
  mission_time: string
  coverage_pct: number
  agents: Agent[]
  alerts: any[]
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
          minWidth: 220,
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 1.5, color: '#00f0ff', marginBottom: 8 }}>SCOUT C2 · TACTICAL</div>
        <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>MISSION: MUNICH</div>
        <div style={{ fontSize: 13, opacity: 0.8, marginBottom: 12 }}>
          T+ {state?.mission_time ?? '--:--'} · COVERAGE {state?.coverage_pct?.toFixed?.(1) ?? '0.0'}%
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: 12 }}>
          {state?.agents?.map((a, i) => (
            <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: COLORS[i % COLORS.length],
                  boxShadow: `0 0 8px ${COLORS[i % COLORS.length]}`,
                }}
              />
              <span style={{ opacity: 0.85 }}>{a.name}</span>
              <span style={{ opacity: 0.5, fontSize: 10 }}>{a.status}</span>
            </div>
          ))}
        </div>
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
