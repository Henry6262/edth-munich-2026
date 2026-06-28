# 3D Asset Scale Catalog

SCOUT C2 `/3d` uses category-based model scaling in `frontend/src/components/TacticalMap3D.ts`.

Do not place GLB assets with arbitrary `scale.set(...)` values. Add or edit the asset in
`ASSET_CATALOG`, then place it through `placeOnGround` / `placeCloned`.

## Scale Rules

| Category | Intended Use | Target Size Rule |
|---|---|---|
| `house` | small village houses | building footprint + 235-265 height before global building multiplier |
| `large_building` | market, club, larger structures | building footprint + 275-420 height before global building multiplier |
| `industrial` | factory, containers | industrial footprint + 120-360 height before global building multiplier |
| `tower` | observation / church-like tower | 460 height before global building multiplier |
| `outpost` | junkyard, bunker, camp | 78-220 height depending on asset |
| `vehicle` | SUV / car | 72 height |
| `heavy_vehicle` | trucks / construction vehicles | 96-112 height |
| `cover` | crates, barrels, road blocks, logs | 44-52 height |
| `wall` | fences, brick walls | 66-72 height |
| `street_clutter` | pots, rope, small scene detail | 16-24 height |
| `debris` | cinderblocks / rubble | 28 height |
| `equipment` | bags, gun stand, mission gear | 24-42 height |
| `vegetation_low` | grass / ground cover | 22-28 height |
| `vegetation_mid` | bushes / ferns | 42 height |
| `terrain` | rocks / logs / low terrain detail | 16-48 height |
| `excluded` | wrong-biome or weird assets | preloaded/placed only if intentionally re-enabled |

## Current Global Multipliers

| Constant | Value | Purpose |
|---|---:|---|
| `HUMAN_HEIGHT` | `46` | operator/agent rig height |
| `BUILDING_FOOTPRINT_MULT` | `1.75` | makes buildings read as map anchors |
| `BUILDING_HEIGHT_MULT` | `1.65` | makes buildings dominate humans and cars |

## Asset Categories

The source of truth is `ASSET_CATALOG`. Current important examples:

- Houses: `ghetto-narco-house.glb`, `fuel_house.glb`, `elevated_cabin.glb`
- Large buildings: `modern_building.glb`, `high_rise_building.glb`, `Fish-market.glb`, `strip-club.glb`
- Industrial: `Factory_.glb`, `Containers.glb`
- Tower: `old_control_tower.glb`
- Vehicles: `shot_up_suv.glb`, `narco_truck.glb`, `big_truck_constrution.glb`
- Cover/walls: `crate.glb`, `small_barrels.glb`, `concrete_road_block.glb`, `brick-wall-small.glb`, `tarp_fence.glb`
- Excluded from the Ukrainian village pass: tropical plants, `tube.glb`, `crashed_narcoplane.glb`
