"""
Pure-Python Catmull-Clark subdivision mesh.

SubDMesh provides the geometric foundation for Tier 15B SubD operations.
FreeCAD 1.1.1 has no native SubD kernel, so all operations are implemented
here and exported to FreeCAD via mesh tessellation.

Reference:
  Catmull, E., Clark, J. (1978). Recursively generated B-spline surfaces
  on arbitrary topological meshes. Computer-Aided Design, 10(6), 350-355.
"""

import math


# ── Catmull-Clark kernel ───────────────────────────────────────────────────────

def _cc_step(vertices, faces, creases):
    """One Catmull-Clark iteration. Returns (new_verts, new_faces, new_creases)."""
    n_verts = len(vertices)
    n_faces = len(faces)

    # 1. Face points
    face_pts = []
    for face in faces:
        n = len(face)
        fp = [sum(vertices[vi][c] for vi in face) / n for c in range(3)]
        face_pts.append(fp)

    # 2. Edge → face adjacency
    efm = {}
    for fi, face in enumerate(faces):
        n = len(face)
        for j in range(n):
            e = (min(face[j], face[(j + 1) % n]), max(face[j], face[(j + 1) % n]))
            efm.setdefault(e, []).append(fi)

    edge_list    = sorted(efm.keys())
    edge_to_idx  = {e: i for i, e in enumerate(edge_list)}

    # 3. Edge points
    edge_pts = []
    for e in edge_list:
        vi, vj       = e
        sharpness    = creases.get(e, 0.0)
        mid          = [(vertices[vi][c] + vertices[vj][c]) / 2 for c in range(3)]
        adj          = efm[e]
        if len(adj) >= 2 and sharpness < 1.0:
            fp_avg   = [(face_pts[adj[0]][c] + face_pts[adj[1]][c]) / 2 for c in range(3)]
            smooth   = [(mid[c] + fp_avg[c]) / 2 for c in range(3)]
            ep       = [smooth[c] * (1 - sharpness) + mid[c] * sharpness for c in range(3)]
        else:
            ep       = mid
        edge_pts.append(ep)

    # 4. Updated vertex positions
    vert_edges = [[] for _ in range(n_verts)]
    for e in edge_list:
        vert_edges[e[0]].append(e)
        vert_edges[e[1]].append(e)

    vert_faces = [[] for _ in range(n_verts)]
    for fi, face in enumerate(faces):
        for vi in face:
            vert_faces[vi].append(fi)

    new_verts = []
    for vi in range(n_verts):
        v_edges = vert_edges[vi]
        v_faces = vert_faces[vi]
        n_e     = len(v_edges)

        if n_e == 0:
            new_verts.append(list(vertices[vi]))
            continue

        boundary = [e for e in v_edges if len(efm[e]) == 1]
        creased  = [e for e in v_edges if creases.get(e, 0.0) >= 1.0]

        if len(boundary) >= 2:
            o0   = boundary[0][1] if boundary[0][0] == vi else boundary[0][0]
            o1   = boundary[1][1] if boundary[1][0] == vi else boundary[1][0]
            nv   = [vertices[vi][c] * 0.5
                    + vertices[o0][c] * 0.25
                    + vertices[o1][c] * 0.25
                    for c in range(3)]
        elif len(creased) >= 2:
            o0   = creased[0][1] if creased[0][0] == vi else creased[0][0]
            o1   = creased[1][1] if creased[1][0] == vi else creased[1][0]
            nv   = [vertices[vi][c] * 0.5
                    + vertices[o0][c] * 0.25
                    + vertices[o1][c] * 0.25
                    for c in range(3)]
        else:
            n    = n_e
            Q    = ([sum(face_pts[fi][c] for fi in v_faces) / len(v_faces) for c in range(3)]
                    if v_faces else list(vertices[vi]))
            R    = [sum((vertices[vi][c] + vertices[e[1] if e[0] == vi else e[0]][c]) / 2
                        for e in v_edges) / n
                    for c in range(3)]
            nv   = [Q[c] / n + 2 * R[c] / n + vertices[vi][c] * (n - 3) / n for c in range(3)]

        new_verts.append(nv)

    # 5. New face structure
    fp_offset = n_verts
    ep_offset = n_verts + n_faces
    all_verts = new_verts + face_pts + edge_pts

    new_faces = []
    for fi, face in enumerate(faces):
        n     = len(face)
        fp_vi = fp_offset + fi
        for j in range(n):
            vi       = face[j]
            vj       = face[(j + 1) % n]
            vk       = face[(j - 1) % n]
            e_curr   = (min(vi, vj), max(vi, vj))
            e_prev   = (min(vi, vk), max(vi, vk))
            ep_curr  = ep_offset + edge_to_idx[e_curr]
            ep_prev  = ep_offset + edge_to_idx[e_prev]
            new_faces.append([vi, ep_curr, fp_vi, ep_prev])

    # 6. Propagate creases (sharpness decays by 1 per iteration)
    new_creases = {}
    for e, sharpness in creases.items():
        ns = max(0.0, sharpness - 1.0)
        if ns > 0.0:
            ep_vi = ep_offset + edge_to_idx[e]
            for v in e:
                ne = (min(v, ep_vi), max(v, ep_vi))
                new_creases[ne] = ns

    return all_verts, new_faces, new_creases


# ── Edge-loop walker ───────────────────────────────────────────────────────────

def _find_edge_loop(faces, efm, start_edge):
    """Walk a quad edge loop starting from start_edge. Returns list of edges."""
    def _opposite(face, vi, vj):
        if len(face) != 4:
            return None
        try:
            pi = face.index(vi)
            pj = face.index(vj)
        except ValueError:
            return None
        oi = (pi + 2) % 4
        oj = (pj + 2) % 4
        return (min(face[oi], face[oj]), max(face[oi], face[oj]))

    loop    = [start_edge]
    visited = {start_edge}
    cur     = start_edge

    while True:
        nxt = None
        for fi in efm.get(cur, []):
            opp = _opposite(faces[fi], cur[0], cur[1])
            if opp and opp not in visited:
                nxt = opp
                break
        if nxt is None:
            break
        loop.append(nxt)
        visited.add(nxt)
        cur = nxt
        if cur == start_edge:
            break

    return loop


# ── SubDMesh class ─────────────────────────────────────────────────────────────

class SubDMesh:
    """
    Catmull-Clark subdivision mesh.

    Attributes:
        vertices: list of [x, y, z]
        faces:    list of [v0, v1, ...] (quads preferred; tris work)
        creases:  dict {(vi, vj): sharpness} — sharpness >= 1 is fully sharp
    """

    def __init__(self, vertices, faces, creases=None):
        self.vertices = [list(v) for v in vertices]
        self.faces    = [list(f) for f in faces]
        self.creases  = {(min(a, b), max(a, b)): float(s)
                         for (a, b), s in (creases or {}).items()}

    # ── topology helpers ──────────────────────────────────────────────────────

    def _efm(self):
        efm = {}
        for fi, face in enumerate(self.faces):
            n = len(face)
            for j in range(n):
                e = (min(face[j], face[(j + 1) % n]), max(face[j], face[(j + 1) % n]))
                efm.setdefault(e, []).append(fi)
        return efm

    def face_normal(self, fi):
        """Outward face normal via Newell's method."""
        face = self.faces[fi]
        m    = len(face)
        n    = [0.0, 0.0, 0.0]
        for j in range(m):
            c  = self.vertices[face[j]]
            nx = self.vertices[face[(j + 1) % m]]
            n[0] += (c[1] - nx[1]) * (c[2] + nx[2])
            n[1] += (c[2] - nx[2]) * (c[0] + nx[0])
            n[2] += (c[0] - nx[0]) * (c[1] + nx[1])
        ln = math.sqrt(sum(x**2 for x in n))
        return [x / ln for x in n] if ln > 1e-12 else [0.0, 0.0, 1.0]

    def face_center(self, fi):
        face = self.faces[fi]
        n    = len(face)
        return [sum(self.vertices[vi][c] for vi in face) / n for c in range(3)]

    # ── subdivision ───────────────────────────────────────────────────────────

    def subdivide(self, iterations=1):
        """Apply Catmull-Clark subdivision *iterations* times. Returns self."""
        for _ in range(iterations):
            self.vertices, self.faces, self.creases = _cc_step(
                self.vertices, self.faces, self.creases
            )
        return self

    def copy(self):
        return SubDMesh(
            [list(v) for v in self.vertices],
            [list(f) for f in self.faces],
            dict(self.creases),
        )

    # ── operations ────────────────────────────────────────────────────────────

    def push_pull(self, face_indices, distance):
        """
        Extrude selected faces along their average normal by distance.
        Creates new side quads around the perimeter.
        """
        face_set = set(face_indices)
        efm      = self._efm()

        normals = [self.face_normal(fi) for fi in face_indices]
        avg_n   = [sum(normals[i][c] for i in range(len(normals))) / len(normals)
                   for c in range(3)]
        ln      = math.sqrt(sum(x**2 for x in avg_n))
        if ln > 1e-12:
            avg_n = [x / ln for x in avg_n]

        sel_verts = set(vi for fi in face_indices for vi in self.faces[fi])

        # Duplicate selected vertices at offset position
        vert_map = {}
        for vi in sel_verts:
            nv = len(self.vertices)
            self.vertices.append([self.vertices[vi][c] + avg_n[c] * distance
                                   for c in range(3)])
            vert_map[vi] = nv

        # Boundary edges (in winding order, shared with non-selected face)
        boundary = []
        for fi in face_indices:
            face = self.faces[fi]
            nn   = len(face)
            for j in range(nn):
                vi, vj = face[j], face[(j + 1) % nn]
                e      = (min(vi, vj), max(vi, vj))
                if any(f not in face_set for f in efm.get(e, [])):
                    boundary.append((vi, vj))

        # Remap selected faces
        for fi in face_indices:
            self.faces[fi] = [vert_map[vi] for vi in self.faces[fi]]

        # Side quads: old_vi → old_vj → new_vj → new_vi
        for vi, vj in boundary:
            self.faces.append([vi, vj, vert_map[vj], vert_map[vi]])

        return self

    def insert_loop(self, edge_vi, edge_vj, position=0.5):
        """
        Insert an edge loop at *position* (0–1) along the given edge.
        Works on all-quad meshes; degrades gracefully on mixed meshes.
        """
        e   = (min(edge_vi, edge_vj), max(edge_vi, edge_vj))
        efm = self._efm()
        if e not in efm:
            raise ValueError(f"Edge ({edge_vi}, {edge_vj}) not found in mesh")

        loop   = _find_edge_loop(self.faces, efm, e)

        # Create a new vertex for each edge in the loop
        env = {}  # edge → new_vert_idx
        for le in loop:
            vi, vj = le
            nv     = len(self.vertices)
            self.vertices.append([
                self.vertices[vi][c] * (1 - position) + self.vertices[vj][c] * position
                for c in range(3)
            ])
            env[le] = nv

        # Split each quad containing a loop edge
        new_faces = []
        for fi, face in enumerate(self.faces):
            if len(face) != 4:
                new_faces.append(face)
                continue
            n = len(face)
            loop_js = []
            for j in range(n):
                le = (min(face[j], face[(j + 1) % n]), max(face[j], face[(j + 1) % n]))
                if le in env:
                    loop_js.append((j, le))
            if len(loop_js) == 2:
                j0, le0 = loop_js[0]
                j1, le1 = loop_js[1]
                nv0 = env[le0]
                nv1 = env[le1]
                # Reorder so j0 and j1 are opposite edges (diff of 2 mod 4)
                if (j1 - j0) % 4 != 2:
                    # rotate by 1 and retry
                    face = face[1:] + face[:1]
                    loop_js = [((j - 1) % 4, le) for j, le in loop_js]
                    j0, le0 = loop_js[0]
                    j1, le1 = loop_js[1]
                    nv0 = env[le0]
                    nv1 = env[le1]
                a, b, cc, d = face[j0 % 4], face[(j0 + 1) % 4], face[(j0 + 2) % 4], face[(j0 + 3) % 4]
                new_faces.append([a, nv0, nv1, d])
                new_faces.append([nv0, b, cc, nv1])
            else:
                new_faces.append(face)

        self.faces = new_faces
        return self

    def bevel_edge(self, edge_pairs, size, segments=1):
        """
        Bevel selected edges by offsetting their endpoints by *size* and
        inserting new faces. *edge_pairs* is a list of (vi, vj) tuples.
        *segments* controls how many edge cuts to insert.
        """
        # Normalise to canonical edge keys
        edges = {(min(a, b), max(a, b)) for a, b in edge_pairs}
        for _ in range(segments):
            for e in list(edges):
                try:
                    self.insert_loop(e[0], e[1], size / 2)
                    self.insert_loop(e[0], e[1], 1.0 - size / 2)
                except (ValueError, KeyError):
                    pass
        return self

    def bridge(self, face_indices_a, face_indices_b):
        """
        Connect two face loops with new quad faces.
        Each group must have the same number of faces/edges.
        """
        def _boundary_loop(fi_list):
            efm = self._efm()
            face_set = set(fi_list)
            loop = []
            for fi in fi_list:
                face = self.faces[fi]
                n    = len(face)
                for j in range(n):
                    vi, vj = face[j], face[(j + 1) % n]
                    e      = (min(vi, vj), max(vi, vj))
                    if all(f in face_set for f in efm.get(e, [])):
                        continue  # interior edge
                    loop.append(vi)
            return loop

        loop_a = _boundary_loop(face_indices_a)
        loop_b = _boundary_loop(face_indices_b)
        na, nb = len(loop_a), len(loop_b)
        if na == 0 or nb == 0:
            return self
        n = min(na, nb)
        for i in range(n):
            a0 = loop_a[i % na]
            a1 = loop_a[(i + 1) % na]
            b0 = loop_b[i % nb]
            b1 = loop_b[(i + 1) % nb]
            self.faces.append([a0, a1, b1, b0])
        return self

    def crease(self, edge_pairs, sharpness=1.0):
        """Mark edges as sharp (sharpness >= 1 = fully sharp crease)."""
        for a, b in edge_pairs:
            self.creases[(min(a, b), max(a, b))] = float(sharpness)
        return self

    def symmetry(self, plane="YZ", mode="mirror"):
        """
        Mirror the mesh across a principal plane.
        plane: "YZ" (mirror in X), "XZ" (mirror in Y), "XY" (mirror in Z)
        mode:  "mirror" keeps both halves; "replace" keeps only the mirror
        """
        axis = {"YZ": 0, "XZ": 1, "XY": 2}.get(plane.upper())
        if axis is None:
            raise ValueError(f"plane must be 'YZ', 'XZ', or 'XY', got {plane!r}")

        n_orig  = len(self.vertices)
        mirrored = []
        for v in self.vertices:
            mv = list(v)
            mv[axis] = -mv[axis]
            mirrored.append(mv)

        if mode == "replace":
            self.vertices = mirrored
            return self

        # mode == "mirror": append mirrored vertices and reversed faces
        self.vertices.extend(mirrored)
        for face in list(self.faces):
            # Reverse winding for mirrored faces so normals point outward
            self.faces.append([vi + n_orig for vi in reversed(face)])
        return self

    def soft_select(self, center_vertex, falloff_radius):
        """
        Return a weight dict {vertex_idx: weight} for a soft selection
        centred on *center_vertex* with linear falloff over *falloff_radius*.
        """
        cv = self.vertices[center_vertex]
        weights = {}
        for i, v in enumerate(self.vertices):
            d = math.sqrt(sum((v[c] - cv[c])**2 for c in range(3)))
            if d <= falloff_radius:
                weights[i] = max(0.0, 1.0 - d / falloff_radius)
        return weights

    def sculpt(self, center_point, brush_type, strength, radius):
        """
        Apply a sculpt brush at *center_point*.

        brush_type: "push" | "pull" | "smooth" | "pinch" | "inflate" | "flatten"
        strength:   displacement magnitude in mm
        radius:     brush influence radius in mm
        """
        cx, cy, cz = center_point
        for i, v in enumerate(self.vertices):
            d = math.sqrt((v[0]-cx)**2 + (v[1]-cy)**2 + (v[2]-cz)**2)
            if d > radius:
                continue
            w = (1.0 - d / radius) ** 2  # smooth falloff

            if brush_type == "pull":
                n = [v[c] - center_point[c] for c in range(3)]
                ln = math.sqrt(sum(x**2 for x in n)) or 1.0
                n  = [x / ln for x in n]
                for c in range(3):
                    self.vertices[i][c] += n[c] * strength * w

            elif brush_type == "push":
                n = [center_point[c] - v[c] for c in range(3)]
                ln = math.sqrt(sum(x**2 for x in n)) or 1.0
                n  = [x / ln for x in n]
                for c in range(3):
                    self.vertices[i][c] += n[c] * strength * w

            elif brush_type == "inflate":
                # move along estimated vertex normal (average of face normals)
                vn = [0.0, 0.0, 0.0]
                for fi, face in enumerate(self.faces):
                    if i in face:
                        fn = self.face_normal(fi)
                        for c in range(3):
                            vn[c] += fn[c]
                ln = math.sqrt(sum(x**2 for x in vn)) or 1.0
                for c in range(3):
                    self.vertices[i][c] += vn[c] / ln * strength * w

            elif brush_type == "flatten":
                for c in range(3):
                    self.vertices[i][c] += (center_point[c] - v[c]) * strength * w * 0.3

            elif brush_type == "smooth":
                # average with neighbours
                efm = self._efm()
                nbrs = []
                for e, fis in efm.items():
                    if i in e:
                        nbrs.append(e[1] if e[0] == i else e[0])
                if nbrs:
                    avg = [sum(self.vertices[nb][c] for nb in nbrs) / len(nbrs)
                           for c in range(3)]
                    for c in range(3):
                        self.vertices[i][c] += (avg[c] - v[c]) * strength * w

            elif brush_type == "pinch":
                for c in range(3):
                    self.vertices[i][c] += (center_point[c] - v[c]) * strength * w * 0.5

        return self

    # ── export ────────────────────────────────────────────────────────────────

    def to_part_shape(self):
        """
        Tessellate to a FreeCAD Part.Shape via Mesh module.
        Each face is fan-triangulated.
        """
        import FreeCAD, Part
        import Mesh as MeshModule

        raw_tris = []
        for face in self.faces:
            n = len(face)
            if n < 3:
                continue
            v0 = self.vertices[face[0]]
            for j in range(1, n - 1):
                v1 = self.vertices[face[j]]
                v2 = self.vertices[face[j + 1]]
                raw_tris.append([list(v0), list(v1), list(v2)])

        if not raw_tris:
            raise ValueError("SubDMesh has no faces to tessellate")

        mesh = MeshModule.Mesh(raw_tris)
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh.Topology, 0.05)
        try:
            return Part.makeSolid(shape)
        except Exception:
            return shape

    def to_partikus_shape(self):
        """Wrap to_part_shape() in a PartikusShape with bounding-box anchors."""
        import FreeCAD
        from .core.shape_wrapper import PartikusShape
        from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT

        fc = self.to_part_shape()
        bb = fc.BoundBox
        cx = (bb.XMin + bb.XMax) / 2
        cy = (bb.YMin + bb.YMax) / 2
        cz = (bb.ZMin + bb.ZMax) / 2

        def _V(x, y, z): return FreeCAD.Vector(x, y, z)

        return PartikusShape(
            fc,
            {
                CENTER: _V(cx, cy, cz),
                TOP:    _V(cx, cy, bb.ZMax),
                BOTTOM: _V(cx, cy, bb.ZMin),
                FRONT:  _V(cx, bb.YMax, cz),
                BACK:   _V(cx, bb.YMin, cz),
                RIGHT:  _V(bb.XMax, cy, cz),
                LEFT:   _V(bb.XMin, cy, cz),
            },
            {
                TOP:    _V(0, 0,  1), BOTTOM: _V(0, 0, -1),
                FRONT:  _V(0, 1,  0), BACK:   _V(0, -1, 0),
                RIGHT:  _V(1, 0,  0), LEFT:   _V(-1, 0, 0),
            },
        )

    def __repr__(self):
        return (f"<SubDMesh verts={len(self.vertices)} "
                f"faces={len(self.faces)} "
                f"creases={len(self.creases)}>")


# ── Primitive constructors ────────────────────────────────────────────────────

def cube_mesh(size=10.0):
    """Unit cube SubDMesh — 8 vertices, 6 quad faces."""
    h = size / 2
    verts = [
        [-h, -h, -h], [ h, -h, -h], [ h,  h, -h], [-h,  h, -h],
        [-h, -h,  h], [ h, -h,  h], [ h,  h,  h], [-h,  h,  h],
    ]
    faces = [
        [0, 3, 2, 1],  # bottom
        [4, 5, 6, 7],  # top
        [0, 1, 5, 4],  # front
        [2, 3, 7, 6],  # back
        [0, 4, 7, 3],  # left
        [1, 2, 6, 5],  # right
    ]
    return SubDMesh(verts, faces)


def sphere_mesh(diameter=10.0, seed_subdivisions=2):
    """
    All-quad sphere derived by projecting a subdivided cube onto the sphere.
    seed_subdivisions=2 gives 96 faces (smooth enough for most uses).
    """
    mesh = cube_mesh(size=diameter)
    mesh.subdivide(seed_subdivisions)
    r = diameter / 2
    for i, v in enumerate(mesh.vertices):
        d = math.sqrt(sum(c**2 for c in v))
        if d > 1e-12:
            mesh.vertices[i] = [c * r / d for c in v]
    return mesh


def cylinder_mesh(diameter=10.0, height=20.0, segments=8):
    """N-sided prism SubDMesh with quad sides and triangulated caps."""
    r   = diameter / 2
    h   = height / 2
    seg = max(3, segments)
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append([r * math.cos(a), r * math.sin(a), -h])
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append([r * math.cos(a), r * math.sin(a),  h])
    bc = 2 * seg;  verts.append([0, 0, -h])
    tc = 2 * seg + 1; verts.append([0, 0,  h])

    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([i, j, j + seg, i + seg])
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([bc, j, i])
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([tc, i + seg, j + seg])
    return SubDMesh(verts, faces)


def cone_mesh(base_diameter=10.0, height=20.0, segments=8):
    """Cone SubDMesh — apex at top, circular base."""
    r   = base_diameter / 2
    seg = max(3, segments)
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append([r * math.cos(a), r * math.sin(a), 0.0])
    apex  = seg;     verts.append([0, 0, height])
    bc    = seg + 1; verts.append([0, 0, 0.0])
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([i, j, apex])      # side triangle
    for i in range(seg):
        j = (i + 1) % seg
        faces.append([bc, j, i])        # base cap
    return SubDMesh(verts, faces)


def torus_mesh(major_diameter=20.0, minor_diameter=5.0, major_seg=16, minor_seg=8):
    """Torus SubDMesh — all-quad grid."""
    R    = major_diameter / 2
    r    = minor_diameter / 2
    mj   = max(3, major_seg)
    mn   = max(3, minor_seg)
    verts = []
    for i in range(mj):
        phi = 2 * math.pi * i / mj
        for j in range(mn):
            theta = 2 * math.pi * j / mn
            x = (R + r * math.cos(theta)) * math.cos(phi)
            y = (R + r * math.cos(theta)) * math.sin(phi)
            z = r * math.sin(theta)
            verts.append([x, y, z])

    faces = []
    for i in range(mj):
        ni = (i + 1) % mj
        for j in range(mn):
            nj = (j + 1) % mn
            a = i  * mn + j
            b = i  * mn + nj
            c = ni * mn + nj
            d = ni * mn + j
            faces.append([a, b, c, d])
    return SubDMesh(verts, faces)
