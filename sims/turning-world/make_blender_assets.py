"""Blender asset generator for The Turning World (run headless):

  /Applications/Blender.app/Contents/MacOS/Blender --background \
      --python sims/turning-world/make_blender_assets.py

Renders, into sims/turning-world/assets/:
  terra_<region>.png  - seven 3D isometric terrain plates, 1536x768,
                        transparent, camera locked to the sim's 2:1
                        projection so the page's SVG buildings align
  hero_globe.png      - a 3D globe with extruded continents, Moon and
                        satellite, for the page header

This is the one place the site's no-dependency rule is deliberately bent
(prompter's request: "prioritize coolness over following rules") — the
outputs are plain PNGs; the page still loads no external code.
"""

import bpy
import bmesh
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
os.makedirs(OUT, exist_ok=True)

TERRA = {
  'britain': ["wwwwwwwwwwww","wwggfggwwwww","wgggggggwwww","wggfggggdgww",
              "wggggdggggww","wwgggggggdww","wwgdggggggww","wwwggggdggww",
              "wwgggwwggggw","wwggwwwwggww","wwwwwwwwwwww","wwwwwwwwwwww"],
  'levant':  ["aaaaaaaaadaa","aadaaaaaaaaa","aaaaadaaaaaa","waaaaaaaadaa",
              "wwaaadgggaaa","wwaaaggdgaaa","waaaadggaaaa","waaaaaaaaaaa",
              "wwaaaaadaaaa","waaadaaaaaaa","waaaaaaaadaa","aaaaaaaaaaaa"],
  'china':   ["ggggffgggggg","ggdggggdgggg","ggggdwwggggg","gdggwwwdgggg",
              "ggdwwgggdggg","ggwwdgggggfg","gwwggdgdgggg","gwgdgggggdgg",
              "wwgggdgggggg","wggdggggdggg","ggggggdggggg","gggdgggggggg"],
  'mysore':  ["gggffggggggg","ggffgggdgggg","gffggdgggggg","ggggggggdggg",
              "ggdggfgggggg","gggggffgdggg","gdgggffggggg","ggggggggggfg",
              "ggdggggdgggg","gggggdgggggg","ggfgggggdggg","gggggggggggg"],
  'europe':  ["ggggffffgggg","ggdggffggggg","gggggggggdgg","gdgggdgggggg",
              "ggggggggdggg","ggdgdggggggg","gggggggdgggg","ggfggggggggd",
              "gfgggdgggggg","ggggggggdggg","gdggggdggggg","gggggggggggg"],
  'america': ["ffffffgggggw","fffggggdggww","ffgggggggwww","fgdgggdggggw",
              "ggggggggggww","gfgggdgggwww","ggggggggggww","gdggggdggggw",
              "gggfgggggwww","ggggggggwwww","gfggdggggwww","ggggggggggww"],
  'steppe':  ["ssssssssssss","ssssssssssss","ssdsssssssss","ssssssssssss",
              "sssssssdssss","ssssssssssss","ssssssssssss","sdssssssssss",
              "ssssssssssss","ssssssssdsss","ssssssssssss","ssssssssssss"],
}
COLORS = {   # sRGB 0-1, matched to the site's light palette but juicier in 3D
  'g': (0.55, 0.62, 0.35), 'f': (0.55, 0.62, 0.35),
  'a': (0.82, 0.70, 0.46), 's': (0.80, 0.70, 0.48),
  'd': (0.76, 0.58, 0.25), 'w': (0.38, 0.53, 0.60),
}
TREE_GREEN = (0.30, 0.44, 0.24)
TRUNK = (0.42, 0.36, 0.28)
DARK_COLORS = {
  'g': (0.150, 0.185, 0.105), 'f': (0.150, 0.185, 0.105),
  'a': (0.260, 0.215, 0.130), 's': (0.250, 0.215, 0.140),
  'd': (0.280, 0.205, 0.080), 'w': (0.085, 0.125, 0.160),
}
DARK_TREE = (0.10, 0.16, 0.09)
DARK_TRUNK = (0.16, 0.13, 0.10)

LAND = [  # [lon,lat] low-poly coastlines (same data as the page)
 [[-168,66],[-140,70],[-125,71],[-110,72],[-95,72],[-80,73],[-70,62],[-55,52],
  [-65,45],[-70,42],[-75,38],[-80,32],[-81,25],[-90,29],[-97,26],[-97,20],
  [-105,20],[-110,23],[-115,30],[-124,40],[-125,49],[-140,60],[-155,58]],
 [[-77,8],[-60,10],[-52,4],[-45,-2],[-35,-8],[-39,-18],[-48,-28],[-55,-35],
  [-62,-40],[-65,-47],[-68,-55],[-72,-50],[-75,-40],[-78,-30],[-81,-15],[-79,-5]],
 [[-17,15],[-10,30],[0,36],[10,37],[20,32],[32,31],[35,25],[43,11],[51,10],
  [48,2],[40,-5],[40,-15],[35,-22],[30,-30],[20,-35],[15,-28],[12,-18],[9,-5],
  [0,5],[-10,5]],
 [[-10,37],[0,44],[-2,48],[8,54],[8,57],[18,56],[22,60],[28,60],[30,70],[45,68],
  [60,70],[75,73],[95,77],[115,74],[130,72],[150,70],[170,67],[179,65],[170,60],
  [158,61],[156,52],[141,53],[135,44],[126,39],[122,31],[115,23],[108,12],[104,2],
  [99,7],[94,16],[90,22],[85,20],[80,13],[77,7],[73,18],[68,24],[60,25],[57,20],
  [52,14],[45,13],[43,17],[39,20],[35,29],[27,37],[23,36],[15,38],[5,38]],
 [[-5,50],[-6,53],[-4,58],[-1,57],[1,52]],
 [[130,31],[133,34],[137,35],[141,39],[142,43],[139,41],[135,35],[131,32]],
 [[95,5],[105,0],[115,-3],[118,2],[110,5],[100,6]],
 [[114,-22],[122,-18],[132,-12],[142,-11],[147,-19],[153,-27],[150,-37],[140,-38],
  [131,-32],[122,-34],[114,-33],[113,-26]],
 [[-45,60],[-52,65],[-55,70],[-40,77],[-25,73],[-33,67]],
]


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    # pick whichever EEVEE this Blender ships
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    return sc


def mat(name, rgb, rough=0.9, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    return m


def add_cube(x, y, z, sx, sy, sz, material):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    ob = bpy.context.object
    ob.scale = (sx, sy, sz)
    ob.data.materials.append(material)
    # soft bevel so edges catch light
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = 0.04
    bev.segments = 2
    return ob


def lights():
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.object
    sun.data.energy = 1.7
    sun.data.angle = math.radians(12)          # soft shadows
    # light from the upper-left of the final image (matches SVG shading)
    sun.rotation_euler = (math.radians(50), math.radians(-18), math.radians(-30))
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    fill = bpy.context.object
    fill.data.energy = 0.45
    fill.data.angle = math.radians(60)
    fill.rotation_euler = (math.radians(30), math.radians(25), math.radians(140))
    world = bpy.data.worlds.new('w')
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.32
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)


def iso_camera(grid=12):
    """Orthographic camera locked to the page's 2:1 isometric projection.
    Plan-space u = x - y spans ±grid ⇒ camera width 2·grid/√2; 2:1 follows
    from the 60° pitch."""
    cx, cy = (grid - 1) / 2.0, -(grid - 1) / 2.0
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = (2 * grid) / math.sqrt(2)   # exact horizontal fit
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    d = 40
    cam.location = (cx + d * math.sin(math.radians(45)) * math.sin(math.radians(60)),
                    cy - d * math.cos(math.radians(45)) * math.sin(math.radians(60)),
                    d * math.cos(math.radians(60)))
    bpy.context.scene.camera = cam



# ---------------- landmark modelling helpers (all primitives) ----------------
def _box(x, y, z, sx, sy, sz, m):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    ob = bpy.context.object
    ob.scale = (sx, sy, sz)
    ob.data.materials.append(m)
    return ob

def _cyl(x, y, z, r, depth, m, rt=None, vertices=24):
    if rt is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth,
                                            location=(x, y, z), vertices=vertices)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=rt, depth=depth,
                                        location=(x, y, z), vertices=vertices)
    ob = bpy.context.object
    ob.data.materials.append(m)
    return ob

def _dome(x, y, z, r, m, squash=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z),
                                         segments=24, ring_count=16)
    ob = bpy.context.object
    ob.scale = (1, 1, squash)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob

def _cone(x, y, z, r, depth, m, vertices=24):
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=depth, location=(x, y, z),
                                    vertices=vertices)
    ob = bpy.context.object
    ob.data.materials.append(m)
    return ob

WHITE = (0.93, 0.90, 0.84)
STONE = (0.78, 0.72, 0.60)
GREYST = (0.62, 0.60, 0.55)
BRONZE = (0.55, 0.30, 0.20)
VERDI = (0.35, 0.58, 0.50)
DOMET = (0.55, 0.68, 0.62)

def lm_taj(cx, cy):
    m = mat('lm_white', WHITE, rough=.6)
    _box(cx, cy, 0.14, 0.75, 0.75, 0.06, m)                        # plinth
    _box(cx, cy, 0.42, 0.42, 0.42, 0.26, m)                        # hall
    _dome(cx, cy, 0.86, 0.30, m, squash=1.15)                      # onion dome
    _cone(cx, cy, 1.24, 0.045, 0.16, mat('lm_gold', (0.8, 0.62, 0.25), rough=.4))
    for dx, dy in ((-.34, -.34), (-.34, .34), (.34, -.34), (.34, .34)):
        _cyl(cx + dx, cy + dy, 0.32, 0.045, 0.28, m)               # chhatri posts
        _dome(cx + dx, cy + dy, 0.50, 0.09, m)
    for dx, dy in ((-.72, -.72), (-.72, .72), (.72, -.72), (.72, .72)):
        _cyl(cx + dx, cy + dy, 0.28, 0.05, 0.55, m, rt=0.035)      # minarets
        _dome(cx + dx, cy + dy, 0.585, 0.065, m)

def lm_bigben(cx, cy):
    m = mat('lm_stone', STONE, rough=.8)
    _box(cx, cy, 0.55, 0.14, 0.14, 0.55, m)                        # shaft
    _box(cx, cy, 1.18, 0.17, 0.17, 0.10, m)                        # clock stage
    f = mat('lm_face', (0.95, 0.94, 0.88), rough=.4)
    for dx, dy, rx, ry in ((0.171, 0, 0.01, 0.09), (-0.171, 0, 0.01, 0.09),
                           (0, 0.171, 0.09, 0.01), (0, -0.171, 0.09, 0.01)):
        _box(cx + dx, cy + dy, 1.18, rx, ry, 0.09, f)              # clock faces
    _cone(cx, cy, 1.42, 0.13, 0.28, m)                             # spire
    _cone(cx, cy, 1.60, 0.02, 0.10, mat('lm_gold', (0.8, 0.62, 0.25), rough=.4))

def lm_notredame(cx, cy):
    m = mat('lm_grey', GREYST, rough=.85)
    _box(cx - 0.22, cy - 0.28, 0.42, 0.14, 0.14, 0.42, m)          # west towers
    _box(cx - 0.22, cy + 0.28, 0.42, 0.14, 0.14, 0.42, m)
    _box(cx + 0.12, cy, 0.26, 0.42, 0.20, 0.26, m)                 # nave
    bpy.ops.mesh.primitive_cube_add(location=(cx + 0.12, cy, 0.60))
    roofob = bpy.context.object
    roofob.scale = (0.42, 0.14, 0.10)
    roofob.rotation_euler = (math.radians(45), 0, 0)
    roofob.data.materials.append(m)
    _cone(cx + 0.05, cy, 0.86, 0.035, 0.34, m)                     # fleche
    _cyl(cx - 0.365, cy, 0.42, 0.055, 0.012, mat('lm_gold', (0.8, 0.62, 0.25), rough=.4),
         vertices=20)                                              # rose window

def lm_mosque(cx, cy):
    m = mat('lm_ivory', (0.88, 0.83, 0.70), rough=.7)
    _box(cx, cy, 0.16, 0.55, 0.4, 0.16, m)                         # prayer hall
    _dome(cx, cy, 0.40, 0.22, mat('lm_dome', DOMET, rough=.5), squash=1.0)
    _cyl(cx + 0.62, cy - 0.25, 0.5, 0.045, 1.0, m)                 # minaret
    _dome(cx + 0.62, cy - 0.25, 1.03, 0.07, mat('lm_dome', DOMET, rough=.5))

def lm_pagoda(cx, cy):
    m = mat('lm_bronze', BRONZE, rough=.75)
    z = 0.0
    for i, (r, h) in enumerate([(0.30, 0.18), (0.26, 0.16), (0.22, 0.15),
                                (0.18, 0.14), (0.14, 0.13)]):
        _cyl(cx, cy, z + h / 2, r * 0.72, h, m, vertices=8)
        _cone(cx, cy, z + h + 0.025, r, 0.09, m, vertices=8)
        z += h + 0.05
    _cone(cx, cy, z + 0.10, 0.02, 0.22, mat('lm_gold', (0.8, 0.62, 0.25), rough=.4))

def lm_liberty(cx, cy):
    p = mat('lm_ped', STONE, rough=.85)
    v = mat('lm_verdi', VERDI, rough=.7)
    _box(cx, cy, 0.22, 0.22, 0.22, 0.22, p)                        # pedestal
    _cyl(cx, cy, 0.72, 0.13, 0.56, v, rt=0.07)                     # robe
    _dome(cx, cy, 1.04, 0.07, v)                                   # head
    for k in range(5):
        a = math.radians(-60 + k * 30)
        _cone(cx + 0.09 * math.cos(a), cy, 1.13 + 0.05 * math.sin(a) * 0,
              0.012, 0.09, v, vertices=6)                          # crown
    arm = _cyl(cx + 0.10, cy + 0.08, 1.22, 0.025, 0.42, v)
    arm.rotation_euler = (math.radians(18), math.radians(-12), 0)
    _cone(cx + 0.16, cy + 0.13, 1.47, 0.05, 0.10,
          mat('lm_flame', (0.85, 0.55, 0.20), rough=.4))           # torch

def lm_yurts(cx, cy):
    m = mat('lm_felt', (0.85, 0.80, 0.70), rough=.9)
    for dx, dy, r in ((0, 0, 0.28), (0.75, 0.55, 0.20)):
        _cyl(cx + dx, cy + dy, 0.10, r, 0.20, m)
        _dome(cx + dx, cy + dy, 0.20, r, m, squash=0.62)

LANDMARKS = {
  'britain': (lm_bigben,   2.85, 5.25),
  'europe':  (lm_notredame,2.95, 6.15),
  'china':   (lm_pagoda,   2.95, 7.75),
  'levant':  (lm_mosque,   3.75, 7.85),
  'mysore':  (lm_taj,      3.55, 7.75),
  'america': (lm_liberty,  7.95, 2.95),
  'steppe':  (lm_yurts,    3.75, 6.85),
}

def render_region(key, rows, colors=COLORS, tree=TREE_GREEN, trunk=TRUNK, suffix=''):
    sc = reset_scene()
    sc.render.resolution_x = 1536
    sc.render.resolution_y = 768
    lights()
    iso_camera(12)
    m_by = {c: mat('m_' + c + suffix, colors[c]) for c in colors}
    m_by['w'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.15
    m_tree = mat('m_tree' + suffix, tree)
    m_trunk = mat('m_trunk' + suffix, trunk)
    for ty in range(12):
        for tx in range(12):
            ch = rows[ty][tx]
            h = 0.10 if ch != 'w' else 0.02
            add_cube(tx, -ty, h / 2, 0.5, 0.5, h / 2, m_by[ch])
            if ch == 'f':
                for dx, dy, s in ((0, 0, 1.0), (-0.28, 0.22, 0.7)):
                    bpy.ops.mesh.primitive_cylinder_add(
                        radius=0.035 * s, depth=0.16 * s,
                        location=(tx + dx, -ty + dy, 0.09 + 0.08 * s))
                    tr = bpy.context.object
                    tr.data.materials.append(m_trunk)
                    bpy.ops.mesh.primitive_cone_add(
                        radius1=0.16 * s, depth=0.34 * s,
                        location=(tx + dx, -ty + dy, 0.17 + 0.17 * s))
                    co = bpy.context.object
                    co.data.materials.append(m_tree)
    if key in LANDMARKS:
        fn, lx, ly = LANDMARKS[key]
        fn(lx, -ly)
    sc.render.filepath = os.path.join(OUT, f'terra_{key}{suffix}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', key)


def lonlat_inside(lon, lat):
    for poly in LAND:
        inside = False
        n = len(poly)
        for k in range(n):
            x1, y1 = poly[k]
            x2, y2 = poly[(k + 1) % n]
            if (y1 > lat) != (y2 > lat):
                xin = x1 + (lat - y1) / (y2 - y1) * (x2 - x1)
                if xin > lon:
                    inside = not inside
        if inside:
            return True
    return False


def render_hero():
    import mathutils
    sc = reset_scene()
    sc.render.resolution_x = 1760
    sc.render.resolution_y = 990
    # ocean
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0)
    ocean = bpy.context.object
    bpy.ops.object.shade_smooth()
    ocean.data.materials.append(mat('sea', (0.42, 0.56, 0.62), rough=0.3))
    # land: dense sphere, keep only faces whose centre is on land, shell it
    bpy.ops.mesh.primitive_uv_sphere_add(segments=256, ring_count=128, radius=1.008)
    land = bpy.context.object
    me = land.data
    bm = bmesh.new()
    bm.from_mesh(me)
    doomed = []
    for f in bm.faces:
        c = f.calc_center_median()
        lat = math.degrees(math.asin(max(-1, min(1, c.z / c.length))))
        lon = math.degrees(math.atan2(c.y, c.x))
        if not lonlat_inside(lon, lat):
            doomed.append(f)
    bmesh.ops.delete(bm, geom=doomed, context='FACES')
    bm.to_mesh(me)
    bm.free()
    land.data.materials.append(mat('landm', (0.76, 0.68, 0.50), rough=0.85))
    sol = land.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = 0.02
    sol.offset = 1
    bpy.ops.object.shade_smooth()
    # equator hint
    bpy.ops.mesh.primitive_torus_add(major_radius=1.004, minor_radius=0.0022)
    bpy.context.object.data.materials.append(mat('ring', (0.62, 0.58, 0.50), rough=.6))
    # Moon
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(1.15, -1.55, 1.05))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(mat('moon', (0.70, 0.68, 0.63), rough=.95))
    # satellite orbit ring + satellite (accent colour)
    eul = mathutils.Euler((math.radians(62), 0, math.radians(24)))
    bpy.ops.mesh.primitive_torus_add(major_radius=1.42, minor_radius=0.0045,
                                     rotation=eul[:])
    bpy.context.object.data.materials.append(mat('orb', (0.72, 0.34, 0.20), rough=.5))
    pt = mathutils.Vector((1.42 * math.cos(0.9), 1.42 * math.sin(0.9), 0))
    pt.rotate(eul)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=pt[:])
    bpy.context.object.data.materials.append(mat('sat', (0.72, 0.34, 0.20)))
    # camera aimed with a tracking constraint (Europe/Levant hemisphere)
    bpy.ops.object.empty_add(location=(0, 0, 0.05))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(5.3, 3.9, 2.7))
    cam = bpy.context.object
    cam.data.lens = 50
    tc = cam.constraints.new('TRACK_TO')
    tc.target = target
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    bpy.context.scene.camera = cam
    lights()
    sc.render.filepath = os.path.join(OUT, 'hero_globe.png')
    bpy.ops.render.render(write_still=True)
    print('rendered hero')


for key, rows in TERRA.items():
    render_region(key, rows)
    render_region(key, rows, DARK_COLORS, DARK_TREE, DARK_TRUNK, '_dark')
render_hero()
print('all assets done ->', OUT)
