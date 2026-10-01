"""Costruttori di geometria low-poly (coordinate OBJ: x, y su, z). Ogni funzione restituisce (P, F, M):
P lista di punti, F lista di facce (indici locali, antiorari visti dall'esterno), M materiali per faccia."""
import numpy as np, math

class Mesh:
    def __init__(self):
        self.P = []; self.F = []; self.M = []
    def add(self, pts, faces, mats):
        b = len(self.P); self.P += [tuple(map(float, p)) for p in pts]
        self.F += [[b + i for i in f] for f in faces]
        self.M += mats if isinstance(mats, list) else [mats] * len(faces)
        return self
    def extend(self, other):
        return self.add(other.P, other.F, other.M)
    def transform(self, fn):
        self.P = [tuple(p) for p in fn(np.array(self.P))]
        return self
    def to_model(self, m, name, smooth=False, after=None):
        if self.F:
            m.add_faces(name, self.P, self.F, self.M, smooth, after=after)

def box(x0, x1, y0, y1, z0, z1, mat, top=True, bottom=False, mats=None):
    """scatola allineata agli assi; mats opzionale dict per lato: 'top','bottom','xn','xp','zn','zp'"""
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    sides = {'bottom': [0, 1, 2, 3], 'top': [4, 7, 6, 5], 'zn': [0, 4, 5, 1], 'zp': [3, 2, 6, 7], 'xn': [0, 3, 7, 4], 'xp': [1, 5, 6, 2]}
    F = []; M = []
    for k, f in sides.items():
        if k == 'top' and not top: continue
        if k == 'bottom' and not bottom: continue
        F.append(f); M.append((mats or {}).get(k, mat))
    return Mesh().add(P, F, M)

def obox(cx, cz, ux, uz, hl, hw, y0, y1, mat, top=True, mats=None):
    """scatola orientata: centro (cx,cz), asse lungo (ux,uz) unitario, mezza lunghezza hl, mezza larghezza hw"""
    u = np.array([ux, uz]) / math.hypot(ux, uz); v = np.array([-u[1], u[0]])
    c = np.array([cx, cz])
    q = [c - u * hl - v * hw, c + u * hl - v * hw, c + u * hl + v * hw, c - u * hl + v * hw]
    P = [(p[0], y0, p[1]) for p in q] + [(p[0], y1, p[1]) for p in q]
    F = [[4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
    M = [(mats or {}).get('top', mat)] + [mat] * 4
    if not top: F = F[1:]; M = M[1:]
    return Mesh().add(P, F, M)

def wall_segment(a, b, thick, y0, y1, mat, cap=None, cap_h=0.12, cap_over=0.06):
    """muro dritto da a=(x,z) a b=(x,z) con eventuale copertina"""
    a = np.array(a, float); b = np.array(b, float); d = b - a; L = np.linalg.norm(d)
    if L < 1e-6: return Mesh()
    c = (a + b) / 2
    m = obox(c[0], c[1], d[0], d[1], L / 2, thick / 2, y0, y1, mat)
    if cap:
        m.extend(obox(c[0], c[1], d[0], d[1], L / 2 + cap_over, thick / 2 + cap_over, y1, y1 + cap_h, cap))
    return m

def prism(poly, y0, y1, mat, top=True, top_mat=None):
    """prisma verticale da poligono convesso o stellato (x,z) antiorario visto dall'alto"""
    n = len(poly); P = [(p[0], y0, p[1]) for p in poly] + [(p[0], y1, p[1]) for p in poly]
    F = []; M = []
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    if area < 0:   # assicura verso antiorario (x,z)
        poly = poly[::-1]; P = [(p[0], y0, p[1]) for p in poly] + [(p[0], y1, p[1]) for p in poly]
    for i in range(n):
        j = (i + 1) % n
        F.append([i, n + i, n + j, j]); M.append(mat)
    if top:
        F.append(list(range(2 * n - 1, n - 1, -1))); M.append(top_mat or mat)
    return Mesh().add(P, F, M)

def ngon(cx, cz, r, n, y, mat, phase=0.0, up=True):
    P = [(cx + r * math.cos(phase + 2 * math.pi * k / n), y, cz + r * math.sin(phase + 2 * math.pi * k / n)) for k in range(n)]
    f = list(range(n)) if not up else list(range(n))[::-1]
    return Mesh().add(P, [f], [mat])

def column(cx, cz, r, y0, y1, mat, n=8, base=None, cap=None):
    m = Mesh()
    poly = [(cx + r * math.cos(2 * math.pi * k / n + math.pi / n), cz + r * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    hb = 0.0
    if base:
        m.extend(box(cx - r * 1.5, cx + r * 1.5, y0, y0 + 0.2, cz - r * 1.5, cz + r * 1.5, base)); hb = 0.2
    hc = 0.0
    if cap:
        m.extend(box(cx - r * 1.6, cx + r * 1.6, y1 - 0.22, y1, cz - r * 1.6, cz + r * 1.6, cap, top=True)); hc = 0.22
    m.extend(prism(poly, y0 + hb, y1 - hc, mat, top=False))
    return m

def orient_faces_out(mesh, center):
    """non usato: le funzioni costruiscono già facce orientate"""
    return mesh

def arch_face(a, b, y_spring, rise, y_top, n=5, mat='stone_light', offset=(0, 0)):
    """faccia piana (pennacchio) sopra un arco a sesto ribassato fra a e b (punti x,z), da y_spring a y_top.
    Restituisce la faccia rivolta verso il lato sinistro del verso a->b (usare due volte per i due lati)."""
    a = np.array(a, float) + offset; b = np.array(b, float) + offset
    pts = []
    for k in range(n + 1):
        t = k / n; p = a + (b - a) * t
        y = y_spring + rise * math.sin(math.pi * t)
        pts.append((p[0], y, p[1]))
    P = pts + [(b[0], y_top, b[1]), (a[0], y_top, a[1])]
    f = list(range(len(P)))
    return Mesh().add(P, [f], [mat])

def lean_roof(outer, inner, y_out, y_in, mat, trim=None):
    """falda a una pendenza fra due polilinee parallele (outer alto, inner basso) — lista di punti (x,z)"""
    m = Mesh()
    n = len(outer)
    for i in range(n - 1):
        P = [(outer[i][0], y_out, outer[i][1]), (outer[i + 1][0], y_out, outer[i + 1][1]),
             (inner[i + 1][0], y_in, inner[i + 1][1]), (inner[i][0], y_in, inner[i][1])]
        m.add(P, [[0, 3, 2, 1]], [mat])
    return m

def flip(mesh):
    mesh.F = [f[::-1] for f in mesh.F]
    return mesh

def rot_y(P, ang, cx=0.0, cz=0.0):
    """rotazione attorno all'asse verticale (angolo in radianti, positivo = da +X verso -Z guardando dall'alto con Z a destra... usare con coerenza)"""
    P = np.array(P, float).copy(); c, s = math.cos(ang), math.sin(ang)
    x = P[:, 0] - cx; z = P[:, 2] - cz
    P[:, 0] = cx + c * x + s * z; P[:, 2] = cz - s * x + c * z
    return P

def normals(mesh):
    P = np.array(mesh.P); out = []
    for f in mesh.F:
        q = P[f]; n = np.zeros(3)
        for i in range(len(q)):
            a, b = q[i], q[(i + 1) % len(q)]
            n += np.cross(a, b)
        out.append((q.mean(0), n))
    return out

def orient(mesh, want):
    """want(centro, normale) -> True se la faccia è orientata correttamente; altrimenti viene invertita"""
    for k, (c, n) in enumerate(normals(mesh)):
        if not want(c, n):
            mesh.F[k] = mesh.F[k][::-1]
    return mesh
