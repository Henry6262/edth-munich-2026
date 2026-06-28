import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { Line2 } from 'three/examples/jsm/lines/Line2.js'
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js'
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js'

const MAP_W = 4200
const MAP_H = 3200
const COVERAGE_RESOLUTION = 0.4
const COVERAGE_W = Math.round(MAP_W * COVERAGE_RESOLUTION)
const COVERAGE_H = Math.round(MAP_H * COVERAGE_RESOLUTION)
const CAMERA_MOVE_SPEED = 920
const CAMERA_FAST_MULTIPLIER = 1.8
const MAP_NAV_MARGIN = 180

interface AgentData {
  id: string
  name: string
  color: string
  position: { x: number; y: number; angle: number }
  status: string
}

interface MissionState {
  mission_time: string
  coverage_pct: number
  agents: AgentData[]
  alerts: any[]
  buildings: { id: string; x: number; y: number; w: number; h: number }[]
  roads: [number, number][][]
}

interface AgentView {
  group: THREE.Group
  mixer?: THREE.AnimationMixer
  current: THREE.Vector3
  target: THREE.Vector3
  angle: number
  targetAngle: number
  fov: THREE.Mesh
  trail: Line2
  trailPts: THREE.Vector3[]
  label: THREE.Sprite
  status: string
  ring: THREE.Mesh
  beacon: THREE.Mesh
  baseColor: THREE.Color
}

const BUILDINGS = [
  // central village cluster
  { id: 'B1', x: 1620, y: 1280, w: 280, h: 220 },
  { id: 'B2', x: 2050, y: 1320, w: 300, h: 240 },
  { id: 'B3', x: 1840, y: 1660, w: 320, h: 230 },
  { id: 'B4', x: 1420, y: 1580, w: 270, h: 220 },
  // north industrial yard
  { id: 'B5', x: 1820, y: 420, w: 560, h: 380 },
  // east market / checkpoint
  { id: 'B6', x: 3150, y: 1260, w: 430, h: 320 },
  // west church / observation tower
  { id: 'B7', x: 520, y: 1260, w: 320, h: 340 },
  // south logistics outpost
  { id: 'B8', x: 1950, y: 2520, w: 460, h: 320 },
]

const ROADS: [number, number][][] = [
  [[280, 1560], [3920, 1560]],
  [[2100, 260], [2100, 2980]],
  [[620, 2700], [1600, 1940], [2760, 1220], [3650, 900]],
  [[880, 520], [1400, 1240], [1500, 2220]],
]

const CHARS = ['mert', 'ansem', 'toly', 'gake', 'phoenix']
const TRAIL_LEN = 48
const WORLD_SCALE = 1.0
const HUMAN_HEIGHT = 46
const BUILDING_FOOTPRINT_MULT = 1.75
const BUILDING_HEIGHT_MULT = 1.65

function hexToThree(hex: string) {
  return new THREE.Color(hex)
}

type ScaleMode =
  | { type: 'height'; height: number; minScale?: number; maxScale?: number }
  | { type: 'footprint'; width: number; depth: number; minHeight?: number; maxHeight?: number; minScale?: number; maxScale?: number }

type AssetCategory =
  | 'house'
  | 'large_building'
  | 'industrial'
  | 'tower'
  | 'outpost'
  | 'vehicle'
  | 'heavy_vehicle'
  | 'cover'
  | 'wall'
  | 'street_clutter'
  | 'debris'
  | 'equipment'
  | 'vegetation_low'
  | 'vegetation_mid'
  | 'vegetation_tall'
  | 'terrain'
  | 'excluded'

interface AssetDefinition {
  category: AssetCategory
  mode: ScaleMode
  buildingHeight?: number
}

const ASSET_CATALOG: Record<string, AssetDefinition> = {
  // Buildings
  'ghetto-narco-house.glb': { category: 'house', mode: { type: 'height', height: 255, minScale: 0.2, maxScale: 120 }, buildingHeight: 255 },
  'fuel_house.glb': { category: 'house', mode: { type: 'height', height: 265, minScale: 0.2, maxScale: 120 }, buildingHeight: 265 },
  'elevated_cabin.glb': { category: 'house', mode: { type: 'height', height: 235, minScale: 0.2, maxScale: 120 }, buildingHeight: 235 },
  'modern_building.glb': { category: 'large_building', mode: { type: 'height', height: 330, minScale: 0.2, maxScale: 120 }, buildingHeight: 330 },
  'high_rise_building.glb': { category: 'large_building', mode: { type: 'height', height: 420, minScale: 0.2, maxScale: 120 }, buildingHeight: 420 },
  'Factory_.glb': { category: 'industrial', mode: { type: 'height', height: 360, minScale: 0.2, maxScale: 120 }, buildingHeight: 360 },
  'Containers.glb': { category: 'industrial', mode: { type: 'height', height: 120, minScale: 0.2, maxScale: 120 }, buildingHeight: 120 },
  'Fish-market.glb': { category: 'large_building', mode: { type: 'height', height: 275, minScale: 0.2, maxScale: 120 }, buildingHeight: 275 },
  'old_control_tower.glb': { category: 'tower', mode: { type: 'height', height: 460, minScale: 0.2, maxScale: 120 }, buildingHeight: 460 },
  'junkyard.glb': { category: 'outpost', mode: { type: 'height', height: 220, minScale: 0.2, maxScale: 120 }, buildingHeight: 220 },
  'lab_bunker.glb': { category: 'outpost', mode: { type: 'height', height: 180, minScale: 0.2, maxScale: 120 }, buildingHeight: 180 },
  'haunted_stronghold.glb': { category: 'large_building', mode: { type: 'height', height: 360, minScale: 0.2, maxScale: 120 }, buildingHeight: 360 },
  'strip-club.glb': { category: 'large_building', mode: { type: 'height', height: 280, minScale: 0.2, maxScale: 120 }, buildingHeight: 280 },
  'tropical-bar.glb': { category: 'house', mode: { type: 'height', height: 210, minScale: 0.2, maxScale: 120 }, buildingHeight: 210 },
  'Garden.glb': { category: 'terrain', mode: { type: 'height', height: 70, minScale: 0.2, maxScale: 100 } },

  // Vehicles
  'shot_up_suv.glb': { category: 'vehicle', mode: { type: 'height', height: 72, minScale: 0.25, maxScale: 120 } },
  'narco_truck.glb': { category: 'heavy_vehicle', mode: { type: 'height', height: 96, minScale: 0.25, maxScale: 120 } },
  'big_truck_constrution.glb': { category: 'heavy_vehicle', mode: { type: 'height', height: 112, minScale: 0.25, maxScale: 120 } },
  'crashed_narcoplane.glb': { category: 'excluded', mode: { type: 'height', height: 120, minScale: 0.25, maxScale: 120 } },

  // Cover / street war items
  'concrete_road_block.glb': { category: 'cover', mode: { type: 'height', height: 52, minScale: 0.25, maxScale: 120 } },
  'crate.glb': { category: 'cover', mode: { type: 'height', height: 46, minScale: 0.25, maxScale: 120 } },
  'small_barrels.glb': { category: 'cover', mode: { type: 'height', height: 42, minScale: 0.25, maxScale: 120 } },
  'brick-wall-small.glb': { category: 'wall', mode: { type: 'height', height: 66, minScale: 0.25, maxScale: 120 } },
  'tarp_fence.glb': { category: 'wall', mode: { type: 'height', height: 70, minScale: 0.25, maxScale: 120 } },
  'wallbang_wall.glb': { category: 'wall', mode: { type: 'height', height: 72, minScale: 0.25, maxScale: 120 } },

  // Clutter / equipment / debris
  'destroyed_cinderblock.glb': { category: 'debris', mode: { type: 'height', height: 28, minScale: 0.25, maxScale: 100 } },
  'rope_coil.glb': { category: 'street_clutter', mode: { type: 'height', height: 16, minScale: 0.25, maxScale: 100 } },
  'duffel_cash_ba.glb': { category: 'equipment', mode: { type: 'height', height: 24, minScale: 0.25, maxScale: 100 } },
  'gun_stand.glb': { category: 'equipment', mode: { type: 'height', height: 42, minScale: 0.25, maxScale: 100 } },
  'clay_pots.glb': { category: 'street_clutter', mode: { type: 'height', height: 24, minScale: 0.25, maxScale: 100 } },
  'camp_tent_campfire.glb': { category: 'outpost', mode: { type: 'height', height: 78, minScale: 0.25, maxScale: 120 } },
  'tube.glb': { category: 'excluded', mode: { type: 'height', height: 40, minScale: 0.25, maxScale: 100 } },

  // Vegetation / terrain
  'ground_cover_patch.glb': { category: 'vegetation_low', mode: { type: 'height', height: 22, minScale: 0.25, maxScale: 100 } },
  'grass_bush_low.glb': { category: 'vegetation_low', mode: { type: 'height', height: 26, minScale: 0.25, maxScale: 100 } },
  'ground_fern.glb': { category: 'vegetation_low', mode: { type: 'height', height: 28, minScale: 0.25, maxScale: 100 } },
  'fern_bush.glb': { category: 'vegetation_mid', mode: { type: 'height', height: 42, minScale: 0.25, maxScale: 100 } },
  'boulder_fern_pile.glb': { category: 'terrain', mode: { type: 'height', height: 48, minScale: 0.25, maxScale: 100 } },
  'boulder_mossy.glb': { category: 'terrain', mode: { type: 'height', height: 46, minScale: 0.25, maxScale: 100 } },
  'fallen_hollow_log.glb': { category: 'terrain', mode: { type: 'height', height: 38, minScale: 0.25, maxScale: 100 } },
  'log_stack.glb': { category: 'cover', mode: { type: 'height', height: 44, minScale: 0.25, maxScale: 100 } },
  'rock_circle.glb': { category: 'terrain', mode: { type: 'height', height: 34, minScale: 0.25, maxScale: 100 } },
  'rock_pile_small.glb': { category: 'terrain', mode: { type: 'height', height: 32, minScale: 0.25, maxScale: 100 } },
  'stepping_stones.glb': { category: 'terrain', mode: { type: 'height', height: 16, minScale: 0.25, maxScale: 100 } },

  // Tropical assets excluded from the Ukrainian village pass
  'bamboo_cluster_a.glb': { category: 'excluded', mode: { type: 'height', height: 80, minScale: 0.25, maxScale: 100 } },
  'banana_leaf_plant.glb': { category: 'excluded', mode: { type: 'height', height: 52, minScale: 0.25, maxScale: 100 } },
  'lavender_spikes.glb': { category: 'excluded', mode: { type: 'height', height: 30, minScale: 0.25, maxScale: 100 } },
  'palm_tree_b.glb': { category: 'excluded', mode: { type: 'height', height: 180, minScale: 0.25, maxScale: 100 } },
  'red_tropical_flowers.glb': { category: 'excluded', mode: { type: 'height', height: 28, minScale: 0.25, maxScale: 100 } },
  'yellow_flower_bush.glb': { category: 'excluded', mode: { type: 'height', height: 32, minScale: 0.25, maxScale: 100 } },
  'yucca_spiky.glb': { category: 'excluded', mode: { type: 'height', height: 48, minScale: 0.25, maxScale: 100 } },
}

const SCENE_ASSET_FILES = Object.entries(ASSET_CATALOG)
  .filter(([, asset]) => asset.category !== 'excluded')
  .map(([file]) => file)

function assetUrl(file: string) {
  return `/assets/3d/sin-city/${file}`
}

function assetMode(file: string): ScaleMode {
  return ASSET_CATALOG[file]?.mode ?? { type: 'height', height: 40, minScale: 0.25, maxScale: 100 }
}

function assetBuildingHeight(file: string) {
  const asset = ASSET_CATALOG[file]
  if (asset?.buildingHeight) return asset.buildingHeight
  if (asset?.mode.type === 'height') return asset.mode.height
  return 220
}

interface AssetModel {
  file: string
  model: THREE.Group
}

export class TacticalMap3D {
  private container: HTMLElement
  private scene: THREE.Scene
  private world: THREE.Group
  private camera: THREE.PerspectiveCamera
  private renderer: THREE.WebGLRenderer
  private controls: OrbitControls
  private clock = new THREE.Clock()
  private loader = new GLTFLoader()
  private dracoLoader = new DRACOLoader()
  private agentViews: Record<string, AgentView> = {}
  private mixers: THREE.AnimationMixer[] = []
  private state: MissionState | null = null
  private pollInterval: number | null = null
  private rafId: number | null = null
  private assetCache: Record<string, THREE.Group> = {}
  private coveragePlane?: THREE.Mesh
  private coverageCtx?: CanvasRenderingContext2D
  private coverageTex?: THREE.CanvasTexture
  private pressedKeys = new Set<string>()

  constructor(container: HTMLElement) {
    this.container = container

    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0x6e7a8a)
    this.scene.fog = new THREE.FogExp2(0x8a95a3, 0.00032)

    this.world = new THREE.Group()
    this.world.scale.set(WORLD_SCALE, WORLD_SCALE, WORLD_SCALE)
    this.scene.add(this.world)

    this.camera = new THREE.PerspectiveCamera(56, container.clientWidth / container.clientHeight, 1, 12000)
    this.camera.position.set(1820 * WORLD_SCALE, 760 * WORLD_SCALE, 2360 * WORLD_SCALE)

    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    this.renderer.setSize(container.clientWidth, container.clientHeight)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap
    container.appendChild(this.renderer.domElement)

    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.target.set(1880 * WORLD_SCALE, 0, 1620 * WORLD_SCALE)
    this.controls.enableDamping = true
    this.controls.maxPolarAngle = Math.PI / 2 - 0.05
    this.controls.minDistance = 95 * WORLD_SCALE
    this.controls.maxDistance = 5600 * WORLD_SCALE
    this.controls.panSpeed = 1.4
    this.controls.zoomSpeed = 1.1
    this.controls.rotateSpeed = 0.45

    this.setupLoader()
    this.setupLights()
    this.createGround()
    this.createRoads()
    this.createCoveragePlane()
    this.loadAssets().then(() => this.buildScene())

    window.addEventListener('resize', this.onResize)
    window.addEventListener('keydown', this.onKeyDown)
    window.addEventListener('keyup', this.onKeyUp)
  }

  private onKeyDown = (event: KeyboardEvent) => {
    const key = event.key.toLowerCase()
    if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'shift'].includes(key)) {
      this.pressedKeys.add(key)
      event.preventDefault()
    }
  }

  private onKeyUp = (event: KeyboardEvent) => {
    this.pressedKeys.delete(event.key.toLowerCase())
  }

  private setupLoader() {
    this.dracoLoader.setDecoderPath('/draco/')
    this.loader.setDRACOLoader(this.dracoLoader)
    this.loader.setMeshoptDecoder(MeshoptDecoder)
  }

  private onResize = () => {
    if (!this.container) return
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight)
    Object.values(this.agentViews).forEach((view) => {
      const mat = view.trail.material as LineMaterial
      mat.resolution.set(this.container.clientWidth, this.container.clientHeight)
    })
  }

  private setupLights() {
    const ambient = new THREE.AmbientLight(0xb8c4d0, 0.9)
    this.scene.add(ambient)

    const hemi = new THREE.HemisphereLight(0xcdd9e8, 0x5a5f55, 0.85)
    this.scene.add(hemi)

    const dir = new THREE.DirectionalLight(0xfff5e6, 1.0)
    dir.position.set(400, 900, 300)
    dir.castShadow = true
    dir.shadow.mapSize.set(2048, 2048)
    this.scene.add(dir)

    const rim = new THREE.DirectionalLight(0x9fb0c4, 0.4)
    rim.position.set(-500, 200, -500)
    this.scene.add(rim)

    const fill = new THREE.DirectionalLight(0xd6ccc2, 0.35)
    fill.position.set(500, 100, -500)
    this.scene.add(fill)
  }

  private createGround() {
    const size = 1024
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = size
    const ctx = canvas.getContext('2d')!
    // Ukrainian mud / late-winter dirt base
    ctx.fillStyle = '#4a453d'
    ctx.fillRect(0, 0, size, size)
    // mottled mud patches
    for (let i = 0; i < 8000; i++) {
      const v = 55 + Math.random() * 45
      ctx.fillStyle = `rgba(${v + 10},${v + 5},${v},${0.12 + Math.random() * 0.12})`
      ctx.fillRect(Math.random() * size, Math.random() * size, 3 + Math.random() * 8, 2 + Math.random() * 6)
    }
    // sparse dead grass tufts
    for (let i = 0; i < 1500; i++) {
      const g = 70 + Math.random() * 30
      ctx.fillStyle = `rgba(${g + 15},${g + 20},${g},${0.1 + Math.random() * 0.1})`
      ctx.fillRect(Math.random() * size, Math.random() * size, 2 + Math.random() * 4, 1 + Math.random() * 3)
    }
    // dirt tracks / ruts
    for (let i = 0; i < 10; i++) {
      ctx.strokeStyle = `rgba(55,50,42,${0.08 + Math.random() * 0.08})`
      ctx.lineWidth = 12 + Math.random() * 30
      ctx.beginPath()
      ctx.moveTo(Math.random() * size, Math.random() * size)
      ctx.bezierCurveTo(Math.random() * size, Math.random() * size, Math.random() * size, Math.random() * size, Math.random() * size, Math.random() * size)
      ctx.stroke()
    }
    // puddles
    for (let i = 0; i < 8; i++) {
      ctx.fillStyle = `rgba(90,100,110,${0.15 + Math.random() * 0.1})`
      ctx.beginPath()
      ctx.ellipse(Math.random() * size, Math.random() * size, 20 + Math.random() * 50, 10 + Math.random() * 30, Math.random() * Math.PI, 0, Math.PI * 2)
      ctx.fill()
    }
    // map border
    ctx.strokeStyle = 'rgba(220,230,240,0.15)'
    ctx.lineWidth = 4
    ctx.strokeRect(2, 2, size - 4, size - 4)

    const tex = new THREE.CanvasTexture(canvas)
    tex.wrapS = THREE.RepeatWrapping
    tex.wrapT = THREE.RepeatWrapping
    tex.repeat.set(7, 5)
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(MAP_W, MAP_H),
      new THREE.MeshStandardMaterial({ map: tex, roughness: 1, metalness: 0 })
    )
    ground.rotation.x = -Math.PI / 2
    ground.position.set(MAP_W / 2, -0.2, MAP_H / 2)
    ground.receiveShadow = true
    this.world.add(ground)
  }

  private createRoads() {
    const mat = new THREE.MeshStandardMaterial({
      color: 0x39362f,
      roughness: 1,
      metalness: 0,
      transparent: true,
      opacity: 0.82,
    })

    const makeSegment = (x1: number, z1: number, x2: number, z2: number, width: number) => {
      const dx = x2 - x1
      const dz = z2 - z1
      const len = Math.hypot(dx, dz)
      if (len <= 0) return
      const px = (-dz / len) * width * 0.5
      const pz = (dx / len) * width * 0.5
      const geo = new THREE.BufferGeometry()
      geo.setAttribute(
        'position',
        new THREE.Float32BufferAttribute(
          [
            x1 + px, 0.03, z1 + pz,
            x1 - px, 0.03, z1 - pz,
            x2 + px, 0.03, z2 + pz,
            x2 - px, 0.03, z2 - pz,
          ],
          3
        )
      )
      geo.setIndex([0, 1, 2, 2, 1, 3])
      geo.computeVertexNormals()
      const road = new THREE.Mesh(geo, mat)
      road.receiveShadow = false
      this.world.add(road)
    }

    ROADS.forEach((road, roadIdx) => {
      const width = roadIdx < 2 ? 92 : 68
      for (let i = 0; i < road.length - 1; i++) {
        makeSegment(road[i][0], road[i][1], road[i + 1][0], road[i + 1][1], width)
      }
    })
  }

  private createCoveragePlane() {
    const canvas = document.createElement('canvas')
    canvas.width = COVERAGE_W
    canvas.height = COVERAGE_H
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = 'rgba(0,240,255,0)'
    ctx.fillRect(0, 0, COVERAGE_W, COVERAGE_H)
    this.coverageCtx = ctx
    this.coverageTex = new THREE.CanvasTexture(canvas)
    this.coverageTex.minFilter = THREE.LinearFilter
    this.coverageTex.magFilter = THREE.LinearFilter
    const plane = new THREE.Mesh(
      new THREE.PlaneGeometry(MAP_W, MAP_H),
      new THREE.MeshBasicMaterial({ map: this.coverageTex, transparent: true, opacity: 0.28, depthWrite: false })
    )
    plane.rotation.x = -Math.PI / 2
    plane.position.set(MAP_W / 2, 0.05, MAP_H / 2)
    this.world.add(plane)
    this.coveragePlane = plane
  }

  private drawCoverage(agents: AgentData[]) {
    const ctx = this.coverageCtx
    if (!ctx) return
    // fade
    ctx.fillStyle = 'rgba(10,20,40,0.05)'
    ctx.fillRect(0, 0, COVERAGE_W, COVERAGE_H)
    for (const a of agents) {
      const x = a.position.x * COVERAGE_RESOLUTION
      const y = a.position.y * COVERAGE_RESOLUTION
      const radius = 170 * COVERAGE_RESOLUTION
      const grad = ctx.createRadialGradient(x, y, 0, x, y, radius)
      grad.addColorStop(0, 'rgba(0,240,255,0.16)')
      grad.addColorStop(1, 'rgba(0,240,255,0)')
      ctx.fillStyle = grad
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      ctx.fill()
    }
    if (this.coverageTex) this.coverageTex.needsUpdate = true
  }

  private async loadGltf(url: string): Promise<THREE.Group> {
    if (this.assetCache[url]) return this.assetCache[url].clone()
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (gltf) => {
          const group = gltf.scene
          group.traverse((child) => {
            if ((child as THREE.Mesh).isMesh) {
              child.castShadow = true
              child.receiveShadow = true
            }
          })
          this.assetCache[url] = group
          resolve(group.clone())
        },
        undefined,
        reject
      )
    })
  }

  private objectBox(object: THREE.Object3D) {
    const box = new THREE.Box3().setFromObject(object)
    const size = new THREE.Vector3()
    box.getSize(size)
    return { box, size }
  }

  private normalizeModel(object: THREE.Object3D, mode: ScaleMode) {
    object.scale.set(1, 1, 1)
    const raw = this.objectBox(object)
    const safeX = Math.max(raw.size.x, 0.001)
    const safeY = Math.max(raw.size.y, 0.001)
    const safeZ = Math.max(raw.size.z, 0.001)
    let scale = 1

    if (mode.type === 'height') {
      scale = mode.height / safeY
    } else {
      scale = Math.min(mode.width / safeX, mode.depth / safeZ)
      if (mode.minHeight && safeY * scale < mode.minHeight) scale = mode.minHeight / safeY
      if (mode.maxHeight && safeY * scale > mode.maxHeight) scale = mode.maxHeight / safeY
    }

    scale = THREE.MathUtils.clamp(scale, mode.minScale ?? 0.05, mode.maxScale ?? 120)
    object.scale.setScalar(scale)
    return this.objectBox(object)
  }

  private placeOnGround(object: THREE.Object3D, x: number, z: number, mode: ScaleMode, rot = 0) {
    const { box } = this.normalizeModel(object, mode)
    object.position.set(x, -box.min.y, z)
    object.rotation.y = rot
    return this.objectBox(object)
  }

  private setObjectShadows(object: THREE.Object3D, enabled: boolean) {
    object.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        child.castShadow = enabled
        child.receiveShadow = enabled
      }
    })
  }

  private async loadAssets() {
    const assets = [
      ...SCENE_ASSET_FILES.map(assetUrl),
      // characters
      '/assets/3d/chars/mert/walk.glb',
      '/assets/3d/chars/ansem/walk.glb',
      '/assets/3d/chars/toly/walk.glb',
      '/assets/3d/chars/gake/walk.glb',
      '/assets/3d/chars/phoenix/walk.glb',
    ]
    await Promise.all(assets.map((a) => this.loadGltf(a)))
  }

  private async buildScene() {
    const buildingSpecs = [
      { file: 'ghetto-narco-house.glb', rot: -0.08 },
      { file: 'fuel_house.glb', rot: 0.12 },
      { file: 'elevated_cabin.glb', rot: -0.14 },
      { file: 'ghetto-narco-house.glb', rot: 0.08 },
      { file: 'Factory_.glb', rot: 0.02 },
      { file: 'Fish-market.glb', rot: -0.18 },
      { file: 'old_control_tower.glb', rot: 0.1 },
      { file: 'junkyard.glb', rot: -0.05 },
    ]

    for (let i = 0; i < BUILDINGS.length; i++) {
      const b = BUILDINGS[i]
      const spec = buildingSpecs[i % buildingSpecs.length]
      const standardHeight = assetBuildingHeight(spec.file)
      const cx = b.x + b.w / 2
      const cz = b.y + b.h / 2
      const model = await this.loadGltf(assetUrl(spec.file))
      const placed = this.placeOnGround(
        model,
        cx,
        cz,
        {
          type: 'footprint',
          width: b.w * BUILDING_FOOTPRINT_MULT,
          depth: b.h * BUILDING_FOOTPRINT_MULT,
          minHeight: standardHeight * BUILDING_HEIGHT_MULT * 0.78,
          maxHeight: standardHeight * BUILDING_HEIGHT_MULT,
          minScale: 0.2,
          maxScale: 100,
        },
        spec.rot
      )
      this.world.add(model)

      const canvas = document.createElement('canvas')
      canvas.width = 64
      canvas.height = 28
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = 'rgba(0,0,0,0.45)'
      ctx.roundRect(4, 4, 56, 20, 5)
      ctx.fill()
      ctx.fillStyle = '#fff'
      ctx.font = 'bold 14px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(b.id, 32, 14)
      const tex = new THREE.CanvasTexture(canvas)
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.8 }))
      sprite.position.set(cx, placed.size.y + 14, cz)
      sprite.scale.set(28, 12, 1)
      this.world.add(sprite)
    }

    const loadAll = async (files: string[]): Promise<AssetModel[]> =>
      Promise.all(files.map(async (file) => ({ file, model: await this.loadGltf(assetUrl(file)) })))
    const coverAssets = await loadAll(['crate.glb', 'small_barrels.glb', 'concrete_road_block.glb'])
    const vehicleAssets = await loadAll(['shot_up_suv.glb', 'narco_truck.glb', 'big_truck_constrution.glb'])
    const wallAssets = await loadAll(['brick-wall-small.glb', 'tarp_fence.glb'])
    const debrisAssets = await loadAll(['destroyed_cinderblock.glb', 'rope_coil.glb', 'duffel_cash_ba.glb', 'gun_stand.glb'])
    const lowVegetationAssets = await loadAll(['ground_cover_patch.glb', 'grass_bush_low.glb'])
    const terrainAssets = await loadAll(['log_stack.glb', 'fallen_hollow_log.glb', 'rock_circle.glb', 'rock_pile_small.glb', 'boulder_mossy.glb'])
    const [campAsset] = await loadAll(['camp_tent_campfire.glb'])

    const placeCloned = (asset: AssetModel, x: number, z: number, mode: ScaleMode = assetMode(asset.file), rot = 0, castShadow = false) => {
      const clone = asset.model.clone()
      this.placeOnGround(clone, x, z, mode, rot)
      this.setObjectShadows(clone, castShadow)
      this.world.add(clone)
      return clone
    }

    const buildBarricade = (assets: AssetModel[], x1: number, z1: number, x2: number, z2: number, count: number) => {
      for (let i = 0; i < count; i++) {
        const t = count === 1 ? 0.5 : i / (count - 1)
        const x = x1 + (x2 - x1) * t
        const z = z1 + (z2 - z1) * t
        const rot = Math.atan2(z2 - z1, x2 - x1) + (Math.random() - 0.5) * 0.3
        const asset = assets[Math.floor(Math.random() * assets.length)]
        placeCloned(
          asset,
          x + (Math.random() - 0.5) * 18,
          z + (Math.random() - 0.5) * 18,
          assetMode(asset.file),
          rot,
          false
        )
      }
    }

    buildBarricade(coverAssets, 1260, 1560, 1510, 1560, 5)
    buildBarricade(wallAssets, 1770, 1120, 2320, 1120, 5)
    buildBarricade(coverAssets, 2750, 1480, 3030, 1480, 4)
    buildBarricade(coverAssets, 1920, 2180, 2320, 2180, 5)
    buildBarricade(wallAssets, 1720, 910, 2480, 910, 5)

    placeCloned(vehicleAssets[0], 1290, 1510, undefined, 0.2, true)
    placeCloned(vehicleAssets[1], 2470, 1590, undefined, -0.2, true)
    placeCloned(vehicleAssets[2], 2110, 950, undefined, 1.5, true)
    placeCloned(vehicleAssets[0], 770, 1610, undefined, 2.7, true)

    const placeRandom = (assets: AssetModel[], count: number) => {
      let placed = 0
      let attempts = 0
      while (placed < count && attempts < count * 5) {
        attempts++
        const x = Math.random() * MAP_W
        const z = Math.random() * MAP_H
        const inBuilding = BUILDINGS.some((b) => x > b.x - 100 && x < b.x + b.w + 100 && z > b.y - 100 && z < b.y + b.h + 100)
        if (inBuilding) continue
        const asset = assets[Math.floor(Math.random() * assets.length)]
        placeCloned(asset, x, z, undefined, Math.random() * Math.PI * 2, false)
        placed++
      }
    }

    placeRandom(lowVegetationAssets, 18)
    placeRandom(terrainAssets, 12)
    placeRandom(debrisAssets, 8)
    placeCloned(campAsset, 650, 2660, undefined, -0.4, false)
  }

  private makeFovCone(color: string): THREE.Mesh {
    const geo = new THREE.ConeGeometry(45, 130, 32, 1, true)
    geo.translate(0, 65, 0)
    geo.rotateX(Math.PI / 2)
    geo.rotateY(Math.PI / 2)
    const mat = new THREE.MeshBasicMaterial({
      color: hexToThree(color),
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
    return new THREE.Mesh(geo, mat)
  }

  private makeTrail(color: string): Line2 {
    const geo = new LineGeometry()
    const positions = new Array(TRAIL_LEN * 3).fill(0)
    geo.setPositions(positions)
    const mat = new LineMaterial({
      color: hexToThree(color),
      linewidth: 2.5,
      transparent: true,
      opacity: 0.65,
      dashed: false,
      resolution: new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
    })
    const line = new Line2(geo, mat)
    line.computeLineDistances()
    return line
  }

  private makeLabel(text: string, color: string): THREE.Sprite {
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 48
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = 'rgba(0,0,0,0.55)'
    ctx.roundRect(8, 6, 240, 36, 8)
    ctx.fill()
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.roundRect(8, 6, 240, 36, 8)
    ctx.stroke()
    ctx.fillStyle = '#fff'
    ctx.font = 'bold 22px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, 128, 24)
    const tex = new THREE.CanvasTexture(canvas)
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.9 }))
    sprite.scale.set(45, 8.4, 1)
    return sprite
  }

  private async createAgentView(id: string, charName: string, color: string, name: string): Promise<AgentView> {
    const group = new THREE.Group()
    const gltf = await new Promise<any>((resolve, reject) => {
      this.loader.load(`/assets/3d/chars/${charName}/walk.glb`, resolve, undefined, reject)
    })
    const model = gltf.scene
    this.normalizeModel(model, { type: 'height', height: HUMAN_HEIGHT, minScale: 0.05, maxScale: 80 })
    // place feet on ground
    const scaledBox = new THREE.Box3().setFromObject(model)
    model.position.y = -scaledBox.min.y
    // face +X in our coordinate system
    model.rotation.y = Math.PI / 2
    group.add(model)

    const ringMat = new THREE.MeshBasicMaterial({ color: hexToThree(color), transparent: true, opacity: 0.5, side: THREE.DoubleSide })
    const ring = new THREE.Mesh(new THREE.RingGeometry(14, 18, 32), ringMat)
    ring.rotation.x = -Math.PI / 2
    ring.position.y = 0.3
    group.add(ring)

    const beaconMat = new THREE.MeshBasicMaterial({ color: hexToThree(color), transparent: true, opacity: 0.1 })
    const beacon = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 90, 8), beaconMat)
    beacon.position.y = 45
    group.add(beacon)

    const fov = this.makeFovCone(color)
    this.world.add(fov)

    const trail = this.makeTrail(color)
    this.world.add(trail)

    const label = this.makeLabel(name, color)
    this.world.add(label)

    const mixer = new THREE.AnimationMixer(model)
    if (gltf.animations.length > 0) {
      const action = mixer.clipAction(gltf.animations[0])
      action.play()
    }
    this.mixers.push(mixer)

    this.world.add(group)
    return {
      group,
      mixer,
      current: new THREE.Vector3(),
      target: new THREE.Vector3(),
      angle: 0,
      targetAngle: 0,
      fov,
      trail,
      trailPts: [],
      label,
      status: 'PATROLLING',
      ring,
      beacon,
      baseColor: hexToThree(color),
    }
  }

  private async ensureAgents(agents: AgentData[]) {
    // render only the first 2 agents to reduce clutter / lag
    const toRender = agents.slice(0, 2)
    for (let i = 0; i < toRender.length; i++) {
      const a = toRender[i]
      if (!this.agentViews[a.id]) {
        this.agentViews[a.id] = await this.createAgentView(a.id, CHARS[i % CHARS.length], a.color, a.name)
      }
    }
  }

  private updateTargets(agents: AgentData[]) {
    agents.forEach((a) => {
      const view = this.agentViews[a.id]
      if (!view) return
      view.target.set(a.position.x * WORLD_SCALE, 0, a.position.y * WORLD_SCALE)
      view.targetAngle = -THREE.MathUtils.degToRad(a.position.angle)
      view.status = a.status
    })
  }

  private updateTrail(view: AgentView) {
    view.trailPts.push(view.current.clone())
    if (view.trailPts.length > TRAIL_LEN) view.trailPts.shift()
    const first = view.trailPts[0] ?? view.current
    const positions: number[] = []
    for (let i = 0; i < TRAIL_LEN; i++) {
      const idx = Math.max(0, view.trailPts.length - TRAIL_LEN + i)
      const p = view.trailPts[idx] ?? first
      positions.push(p.x, p.y + 0.3, p.z)
    }
    view.trail.geometry.setPositions(positions)
    view.trail.computeLineDistances()
  }

  private async poll() {
    try {
      const res = await fetch('/api/state')
      const data: MissionState = await res.json()
      this.state = data
      await this.ensureAgents(data.agents)
      this.updateTargets(data.agents)
    } catch (e) {
      console.error('poll failed', e)
    }
  }

  private updateKeyboardNavigation(dt: number) {
    const forward = new THREE.Vector3()
    this.camera.getWorldDirection(forward)
    forward.y = 0
    if (forward.lengthSq() === 0) return
    forward.normalize()

    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize()
    const move = new THREE.Vector3()

    if (this.pressedKeys.has('w') || this.pressedKeys.has('arrowup')) move.add(forward)
    if (this.pressedKeys.has('s') || this.pressedKeys.has('arrowdown')) move.sub(forward)
    if (this.pressedKeys.has('d') || this.pressedKeys.has('arrowright')) move.add(right)
    if (this.pressedKeys.has('a') || this.pressedKeys.has('arrowleft')) move.sub(right)

    if (move.lengthSq() === 0) return
    const speed = CAMERA_MOVE_SPEED * (this.pressedKeys.has('shift') ? CAMERA_FAST_MULTIPLIER : 1)
    move.normalize().multiplyScalar(speed * dt)
    this.camera.position.add(move)
    this.controls.target.add(move)
    this.clampCameraToMap()
  }

  private clampCameraToMap() {
    const minX = -MAP_NAV_MARGIN
    const maxX = MAP_W + MAP_NAV_MARGIN
    const minZ = -MAP_NAV_MARGIN
    const maxZ = MAP_H + MAP_NAV_MARGIN
    const beforeX = this.controls.target.x
    const beforeZ = this.controls.target.z

    this.controls.target.x = THREE.MathUtils.clamp(this.controls.target.x, minX, maxX)
    this.controls.target.z = THREE.MathUtils.clamp(this.controls.target.z, minZ, maxZ)

    this.camera.position.x += this.controls.target.x - beforeX
    this.camera.position.z += this.controls.target.z - beforeZ
    this.camera.position.y = Math.max(this.camera.position.y, 120)
  }

  private frameCount = 0

  start() {
    this.poll()
    this.pollInterval = window.setInterval(() => this.poll(), 500)

    const loop = () => {
      this.rafId = requestAnimationFrame(loop)
      this.frameCount++
      const dt = this.clock.getDelta()

      this.updateKeyboardNavigation(dt)
      this.mixers.forEach((m) => m.update(dt))

      // throttle coverage canvas updates
      if (this.state?.agents && this.frameCount % 4 === 0) this.drawCoverage(this.state.agents)

      Object.values(this.agentViews).forEach((view) => {
        view.current.lerp(view.target, 0.1)
        view.group.position.copy(view.current)

        let diff = view.targetAngle - view.angle
        while (diff > Math.PI) diff -= Math.PI * 2
        while (diff < -Math.PI) diff += Math.PI * 2
        view.angle += diff * 0.12
        view.group.rotation.y = -view.angle

        view.fov.rotation.y = -view.angle
        view.fov.position.copy(view.current)
        view.fov.position.y = 1.5

        view.label.position.set(view.current.x, 110, view.current.z)
        view.label.position.y += Math.sin(this.clock.elapsedTime * 2 + view.current.x) * 0.8

        const isThreat = view.status === 'THREAT'
        const isHold = view.status === 'HOLD'
        const pulse = (Math.sin(this.clock.elapsedTime * 6) + 1) * 0.5
        const statusColor = isThreat ? new THREE.Color('#ff0044') : isHold ? new THREE.Color('#f5e600') : view.baseColor
        ;(view.fov.material as THREE.MeshBasicMaterial).color.copy(statusColor)
        ;(view.ring.material as THREE.MeshBasicMaterial).color.copy(statusColor)
        ;(view.beacon.material as THREE.MeshBasicMaterial).color.copy(statusColor)
        ;(view.fov.material as THREE.MeshBasicMaterial).opacity = isThreat ? 0.25 + pulse * 0.2 : 0.16
        ;(view.ring.material as THREE.MeshBasicMaterial).opacity = isThreat ? 0.6 + pulse * 0.4 : 0.5
        ;(view.beacon.material as THREE.MeshBasicMaterial).opacity = isThreat ? 0.15 + pulse * 0.15 : 0.1

        this.updateTrail(view)
      })

      this.controls.update()
      this.clampCameraToMap()
      this.renderer.render(this.scene, this.camera)
    }
    loop()
  }

  dispose() {
    window.removeEventListener('resize', this.onResize)
    window.removeEventListener('keydown', this.onKeyDown)
    window.removeEventListener('keyup', this.onKeyUp)
    if (this.pollInterval) clearInterval(this.pollInterval)
    if (this.rafId) cancelAnimationFrame(this.rafId)
    this.controls.dispose()
    this.renderer.dispose()
    this.container.removeChild(this.renderer.domElement)
  }
}
