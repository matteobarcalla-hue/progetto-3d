"""Fase 2 - torre del mago: scalinata ripida scavata nella roccia che sale dalla strada del canyon fino a una grotta
aperta nella rupe sotto la torre (il suo ingresso: portale ad arco, porta di legno con bande di ferro, lanterne);
fuori dalla torre, sulla spianata vicino alla porta, un calderone sul fuoco, un tavolo con ampolle e libro,
legna con una scopa, uno sgabello, cristalli.
Ai piedi un ponticello di legno attraversa il fiume e una scaletta scende alla strada sulla riva opposta.
Tracciato delle rampe scelto con una ricerca sul terreno reale: 4 rampe, pendenze 0.68-0.73, scavo massimo 2.6 m."""
import numpy as np, math
from scipy import ndimage
import ops
import animali_gen as G
from occupancy import occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[mago]', s)

# piede (riva del fiume, davanti al ponticello che porta alla strada), tre svolte, arrivo sul pianerottolo della grotta
PUNTI = [(-228.2, -137.0), (-241.0, -147.5), (-232.0, -153.5), (-242.5, -159.5), (-234.6, -163.4)]
XB, ZW, ZE = -227.6, -135.4, -126.6       # ponticello sul fiume: asse x, testata ovest (lato scala) e est (lato strada)
PIEDE = [(-229.4, -134.9), (-226.4, -134.9), (-226.4, -138.0), (-229.4, -138.0)]
GX, ZB, GY = -230.0, -165.95, 72.2        # bocca della grotta: centro x, piano z (guarda verso +Z), pavimento
RW, HS = 1.2, 1.5                          # semilarghezza dell'apertura e altezza dei piedritti
PIANEROTTOLO = [(-234.9, -166.05), (-225.3, -166.05), (-225.3, -162.3), (-234.9, -162.3)]
CALDERONE = (-224.55, -172.75)             # spianata della torre, 4 m dalla porta (lato +X)
LARGH = 1.5                                # larghezza dei gradini
CORRIDOIO = 3.4                            # fascia (m) attorno alla scala libera da alberi (usata anche da f2_alberi)

class Mesh:
    def __init__(self): self.P = []; self.F = []; self.M = []
    def add(self, VF, mat, flip=False):
        V, F = VF; b = len(self.P); self.P += [tuple(map(float, v)) for v in V]
        mats = mat if isinstance(mat, list) else [mat] * len(F)
        self.F += [[b + i for i in (f[::-1] if flip else f)] for f in F]; self.M += mats
    def quad(self, q, mat, want):
        """quadrilatero (o poligono) orientato con la normale verso 'want' (vettore 3d)"""
        Q = np.array(q, float); n = np.zeros(3)
        for t in range(len(Q)): n += np.cross(Q[t], Q[(t + 1) % len(Q)])
        f = list(range(len(Q)))
        if np.dot(n, want) < 0: f = f[::-1]
        b = len(self.P); self.P += [tuple(map(float, v)) for v in Q]; self.F.append([b + i for i in f]); self.M.append(mat)

def blocco(c, u, w, d, h0, h1, faces=('top', 'front', 'back', 'left', 'right')):
    """parallelepipedo con base orizzontale: c=(x,z) centro, u=direzione (lunghezza w), larghezza d, quote h0..h1"""
    u = np.array(u, float); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]])
    c = np.array(c, float)
    corners = [c - u * w / 2 - v * d / 2, c + u * w / 2 - v * d / 2, c + u * w / 2 + v * d / 2, c - u * w / 2 + v * d / 2]
    P = [(p[0], h0, p[1]) for p in corners] + [(p[0], h1, p[1]) for p in corners]
    F = {'top': [4, 5, 6, 7], 'bottom': [3, 2, 1, 0], 'back': [0, 1, 5, 4], 'right': [1, 2, 6, 5], 'front': [2, 3, 7, 6], 'left': [3, 0, 4, 7]}
    Pa = np.array(P); cen = Pa.mean(0); out = []
    for f in [F[k] for k in faces]:
        q = Pa[f]; n = np.cross(q[1] - q[0], q[2] - q[0])
        out.append(f if np.dot(n, q.mean(0) - cen) >= 0 else f[::-1])
    return P, out

def box3(c, U, V, W, hu, hv, hw, jit=0.0, rng=None):
    """parallelepipedo orientato (assi U, V, W qualsiasi), facce verso l'esterno; jit = irregolarità dei vertici"""
    c = np.asarray(c, float); U, V, W = [np.asarray(a, float) / np.linalg.norm(a) for a in (U, V, W)]
    P = []
    for su in (-1, 1):
        for sv in (-1, 1):
            for sw in (-1, 1):
                p = c + su * hu * U + sv * hv * V + sw * hw * W
                if jit and rng is not None: p = p + rng.uniform(-jit, jit, 3)
                P.append(p)
    F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    Pa = np.array(P); cen = Pa.mean(0); out = []
    for f in F:
        q = Pa[f]; n = np.cross(q[1] - q[0], q[2] - q[0]) + np.cross(q[2] - q[0], q[3] - q[0])
        out.append(f if np.dot(n, q.mean(0) - cen) >= 0 else f[::-1])
    return P, out

_ICO = None
def sasso(c, sx, sy, sz, rng, piatto=0.55):
    """sasso low-poly: icosaedro irregolare (inviluppo convesso, 20 triangoli circa), base appiattita"""
    global _ICO
    from scipy.spatial import ConvexHull
    if _ICO is None:
        t = (1 + 5 ** 0.5) / 2
        _ICO = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float) / math.sqrt(1 + t * t)
    P = _ICO * rng.uniform(0.78, 1.05, (12, 1)) + rng.normal(0, 0.06, (12, 3))
    P[:, 1] = np.maximum(P[:, 1], -piatto)
    P = P * [sx, sy, sz] + np.asarray(c, float)
    h = ConvexHull(P); cen = P.mean(0); F = []
    for sm in h.simplices:
        q = P[sm]; nrm = np.cross(q[1] - q[0], q[2] - q[0])
        F.append(list(sm) if np.dot(nrm, q.mean(0) - cen) >= 0 else list(sm[::-1]))
    return P, F

def quota(m, H, x, z):
    Hs = m.H; m.H = H
    try: return m.height(x, z)
    finally: m.H = Hs

def lanterna(S, x, y, z, braccio=None):
    """lanterna di ferro con luce (palo se braccio è None, altrimenti staffa dal punto braccio)"""
    if braccio is None:
        S.add(G.loft([(x, y - 0.05, z), (x, y + 1.75, z)], [0.045, 0.04], [0.045, 0.04], n=5), 'iron_dark')
        yl = y + 1.75
    else:
        S.add(G.loft([braccio, (x, y + 0.25, z)], [0.03, 0.03], [0.03, 0.03], n=4, up=(0, 1, 0)), 'iron_dark')
        yl = y
    S.add(blocco((x, z), (1, 0), 0.24, 0.24, yl - 0.02, yl + 0.26), 'fire_glow')
    S.add(blocco((x, z), (1, 0), 0.32, 0.32, yl + 0.26, yl + 0.33), 'iron_dark')
    S.add(G.cone((x, yl + 0.33, z), (x, yl + 0.5, z), 0.16, n=4), 'iron_dark')

def run(m):
    rng = np.random.default_rng(131)
    Xg, Zg = m.grid_xz(); Xc, Zc = m.cell_xz()
    pts = [np.array(p, float) for p in PUNTI]
    H_prima = m.H.copy()
    # --- 1) quote: piede alla quota della strada, svolte poco sotto il terreno, arrivo al pavimento della grotta
    # quota dell'impalcato del ponticello: sopra la riva ovest e almeno 0.85 m sopra l'acqua
    Wv = m.V[np.unique(np.concatenate([np.array(f) - 1 for f in m.obj('Acqua')['faces']]))]
    acq = Wv[(np.abs(Wv[:, 0] - XB) < 1.2) & (Wv[:, 2] > ZW) & (Wv[:, 2] < ZE), 1]
    y_acqua = float(acq.max()) if len(acq) else float(m.height(XB, (ZW + ZE) / 2))
    yd = round(max(float(m.height(*PUNTI[0])) + 0.05, y_acqua + 0.7), 2)
    ys = [yd] + [float(m.height(*p)) - 0.4 for p in PUNTI[1:-1]] + [GY]
    fl = []                                          # rampe: (a, b, y0, y1, u, L, n_a_monte)
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]; u = b - a; L = float(np.linalg.norm(u)); u = u / L
        n = np.array([-u[1], u[0]])
        ss = np.linspace(1.0, L - 1.0, 8); cc = a + np.outer(ss, u)
        dpos = m.height(cc[:, 0] + n[0] * 2.2, cc[:, 1] + n[1] * 2.2) - m.height(cc[:, 0] - n[0] * 2.2, cc[:, 1] - n[1] * 2.2)
        nup = n if dpos.mean() > 0 else -n
        fl.append((a, b, ys[k], ys[k + 1], u, L, nup))
    # --- 2) solco della scala: nucleo piano sotto i gradini, taglio a monte, sostegno a valle (strade esistenti intatte)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    sc_ = np.isin(nomi, ['path_dirt', 'street_stone'])
    strada_v = np.zeros(m.H.shape, bool)
    for di in (0, 1):
        for dj in (0, 1):
            strada_v[di:di + sc_.shape[0], dj:dj + sc_.shape[1]] |= sc_
    for k, (a, b, y0, y1, u, L, nup) in enumerate(fl):
        d, t, Ls = ops.dist_to_polyline(Xg, Zg, [tuple(a), tuple(b)])
        yy = y0 + (y1 - y0) * np.clip(t / L, 0, 1)
        side = (Xg - a[0]) * nup[0] + (Zg - a[1]) * nup[1]          # >0 a monte
        avanti = ((Xg - a[0]) * u[0] + (Zg - a[1]) * u[1]) > (-0.2 if k == 0 else -9)
        libero_v = ~strada_v & avanti
        core = (d < 1.6) & libero_v
        m.H = np.where(core, yy - 0.3, m.H)
        band = (d >= 1.6) & (d < 3.2) & libero_v
        m.H = np.where(band & (side > 0), np.minimum(m.H, yy + 0.9 + (d - 1.6) * 2.2), m.H)
        m.H = np.where(band & (side <= 0), np.maximum(m.H, yy - 0.3 - (d - 1.6) * 1.6), m.H)
    for p, yl in zip(pts[1:-1], ys[1:-1]):                          # pianerottoli alle svolte
        sq = np.hypot(Xg - p[0], Zg - p[1]) < 1.7
        m.H = np.where(sq, yl - 0.3, m.H)
    # --- 3) piede: piazzola verso la strada; pianerottolo e parete della grotta
    u0 = fl[0][4]; pie = PIEDE
    ops.flatten_pad(m, pie, ys[0] - 0.02, blend=0.9)
    ops.flatten_pad(m, PIANEROTTOLO, GY, blend=0.8)
    lat = 1 - ops.smoothstep(3.6, 5.2, np.abs(Xg - GX))
    for zr, hgt in ((-166.9, GY + 4.5), (-167.8, GY + 5.0)):
        row = np.abs(Zg - zr) < 0.3
        m.H = np.where(row & (lat > 0), m.H * (1 - lat) + np.maximum(m.H, hgt) * lat, m.H)
    # l'ultima rampa non deve essere coperta dal raccordo del pianerottolo
    a, b, y0, y1, u, L, nup = fl[-1]
    d, t, _ = ops.dist_to_polyline(Xg, Zg, [tuple(a), tuple(b)])
    yy = y0 + (y1 - y0) * np.clip(t / L, 0, 1)
    m.H = np.where((d < 1.1) & (t < L - 0.4), np.minimum(m.H, yy - 0.3), m.H)
    # fasce di taglio e di sostegno smussate (la griglia di 0.9 m le farebbe a scalini)
    dg, _, _ = ops.dist_to_polyline(Xg, Zg, [tuple(p) for p in PUNTI])
    dentro = ops.verts_in_poly(m, PIANEROTTOLO) | ops.verts_in_poly(m, pie)
    for p in pts[1:-1]: dentro |= np.hypot(Xg - p[0], Zg - p[1]) < 1.8
    liscio = ndimage.gaussian_filter(m.H, 0.8)
    fascia = (dg > 1.75) & (dg < 3.9) & ~strada_v & ~dentro
    m.H = np.where(fascia, liscio, m.H)
    # --- 4) materiali
    dl, _, _ = ops.dist_to_polyline(Xc, Zc, [tuple(p) for p in PUNTI])
    ok = (m.M >= 0) & ~sc_
    m.M[ok & (dl < 3.2)] = m.mat_index('terrain_rock'); m.M[ok & (dl < 1.6)] = m.mat_index('stone_dark')
    m.M[ok & ops.cells_in_poly(m, PIANEROTTOLO)] = m.mat_index('path_dirt')
    m.M[ok & ops.cells_in_poly(m, pie)] = m.mat_index('path_dirt')
    parete = ok & (np.abs(Xc - GX) < 4.5) & (Zc < -166.05) & (Zc > -168.3)
    m.M[parete] = m.mat_index('stone_dark')
    # --- 5) via alberi, sassi e fasce di roccia dal corridoio della scala, dalla grotta, dal piede e dal ponticello
    #        (per gruppi: un albero è tronco + chioma, si toglie o si sposta intero)
    zone = [(np.min(np.array(z_)[:, 0]) - 2.0, np.max(np.array(z_)[:, 0]) + 2.0, np.min(np.array(z_)[:, 1]) - 2.0, np.max(np.array(z_)[:, 1]) + 2.0)
            for z_ in (PIANEROTTOLO, pie, [(XB - 1.2, ZW), (XB + 1.2, ZE + 4.6)])]
    AREA = (-254.0, -214.0, -174.0, -114.0)
    def gruppi_area(nm):
        cs = [c for c in m.comps(nm) if not (c['hi'][0] < AREA[0] or c['lo'][0] > AREA[1] or c['hi'][2] < AREA[2] or c['lo'][2] > AREA[3])]
        n = len(cs)
        if n == 0: return []
        par = list(range(n))
        def f_(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        lo = np.array([c['lo'] for c in cs]); hi = np.array([c['hi'] for c in cs])
        if nm.startswith('Alberi'):
            from alberi_util import gruppi_alberi
            return gruppi_alberi(m, nm, cs)
        else:
            for i in range(n):
                ov = np.all(lo[i + 1:] - 0.02 <= hi[i], 1) & np.all(lo[i] - 0.02 <= hi[i + 1:], 1)
                for j in np.nonzero(ov)[0]: par[f_(i)] = f_(i + 1 + j)
        g = {}
        for i in range(n): g.setdefault(f_(i), []).append(cs[i])
        return list(g.values())
    TOGLIBILI = ('Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Siepi_e_Confini')
    rem = {}; nrem = {}
    for nm in [o['name'] for o in m.objs]:
        if nm in ('Terreno', 'Base_Sezione', 'Acqua', 'Mare') or not m.obj(nm)['faces']: continue
        if not (nm.startswith('Alberi') or nm in TOGLIBILI): continue
        fs = []; ng = 0
        for gr in gruppi_area(nm):
            hit = False
            for c in gr:
                V = m.V[c['verts']]
                dv, _, _ = ops.dist_to_polyline(V[:, 0], V[:, 2], PUNTI)
                ce = (c['lo'] + c['hi']) / 2
                dc, _, _ = ops.dist_to_polyline(np.array([ce[0]]), np.array([ce[2]]), PUNTI)
                inz = any(((V[:, 0] > x0) & (V[:, 0] < x1) & (V[:, 2] > z0) & (V[:, 2] < z1)).any() for (x0, x1, z0, z1) in zone)
                parete_v = ((np.abs(V[:, 0] - GX) < 4.0) & (V[:, 2] < -166.0) & (V[:, 2] > -168.5) & (V[:, 1] < GY + 5.5)).any()
                if dv.min() < 3.0 or dc[0] < CORRIDOIO or inz or parete_v: hit = True; break
            if hit:
                for c in gr: fs += c['faces']
                ng += 1
        if fs: rem[nm] = fs; nrem[nm] = (ng, len(fs))
    m.delete(rem)
    # ciò che resta dove il terreno è cambiato: riappoggio verticale; piccole rocce finite sul pianerottolo spostate di lato
    x0z, x1z = min(p[0] for p in PIANEROTTOLO) - 0.6, max(p[0] for p in PIANEROTTOLO) + 0.6
    z0z, z1z = min(p[1] for p in PIANEROTTOLO) - 2.6, max(p[1] for p in PIANEROTTOLO) + 0.6
    def in_zona(lo, hi):
        return hi[0] > x0z and lo[0] < x1z and hi[2] > z0z and lo[2] < z1z
    def fp(H, lo, hi):
        XX, ZZ = np.meshgrid(np.linspace(lo[0], hi[0], 5), np.linspace(lo[2], hi[2], 5))
        return float(quota(m, H, XX.ravel(), ZZ.ravel()).min())
    nres = 0; spost = []
    for nm in [o['name'] for o in m.objs]:
        if nm in ('Terreno', 'Base_Sezione', 'Acqua', 'Mare') or not m.obj(nm)['faces']: continue
        for gr in gruppi_area(nm):
            lo = np.min([c['lo'] for c in gr], 0); hi = np.max([c['hi'] for c in gr], 0)
            base = min(gr, key=lambda c: c['lo'][1])
            b0 = fp(H_prima, base['lo'], base['hi']); dy = fp(m.H, base['lo'], base['hi']) - b0
            if abs(dy) < 0.12: continue
            vs = np.unique(np.concatenate([c['verts'] for c in gr]))
            if max(hi[0] - lo[0], hi[2] - lo[2]) > 6.0:
                log('ATTENZIONE: %s, elemento grande (%.0f x %.0f m) con terreno cambiato di %.2f m sotto l\'impronta: lasciato fermo'
                    % (nm, hi[0] - lo[0], hi[2] - lo[2], dy)); continue
            mats = set(m.obj(nm)['mats'][f] for c in gr for f in c['faces'])
            roccia = mats <= {'moss_stone', 'terrain_rock', 'stone_dark', 'stone_light'} and sum(len(c['faces']) for c in gr) <= 60
            if roccia and in_zona(lo, hi):
                fatto = False
                for rr in np.arange(0.5, 6.01, 0.5):
                    for a_ in np.linspace(0, 2 * math.pi, 16, endpoint=False):
                        dx, dz = rr * math.cos(a_), rr * math.sin(a_)
                        lo2 = lo + [dx, 0, dz]; hi2 = hi + [dx, 0, dz]
                        if in_zona(lo2, hi2): continue
                        XX, ZZ = np.meshgrid(np.linspace(lo2[0], hi2[0], 5), np.linspace(lo2[2], hi2[2], 5))
                        h1 = m.height(XX.ravel(), ZZ.ravel()); h0 = quota(m, H_prima, XX.ravel(), ZZ.ravel())
                        if np.abs(h1 - h0).max() > 0.05 or h1.max() - h1.min() > 1.2: continue
                        dd, _, _ = ops.dist_to_polyline(XX.ravel(), ZZ.ravel(), PUNTI)
                        if dd.min() < 3.5: continue
                        m.V[vs, 0] += dx; m.V[vs, 2] += dz
                        m.V[vs, 1] += float(h1.min()) - b0
                        spost.append('%s (%.1f m)' % (nm, rr)); fatto = True; break
                    if fatto: break
                if fatto: continue
            m.V[vs, 1] += dy; nres += 1
        m.invalidate(nm)
    if spost: log('piccole rocce spostate fuori dal pianerottolo della grotta: ' + ', '.join(spost))
    if nres: log('%d elementi (alberi, sassi) riappoggiati dove il terreno è stato scavato o raccordato' % nres)
    # --- 6) gradini, pianerottoli, pareti scavate e parapetti di roccia, lanterne
    S = Mesh(); nst = 0; rises = []
    for k, (a, b, y0, y1, u, L, nup) in enumerate(fl):
        n = max(3, int(math.ceil((y1 - y0) / 0.2))); r = (y1 - y0) / n; tr = L / n; rises.append((r, tr))
        for i in range(n):
            c = a + u * tr * (i + 0.5)
            S.add(blocco(c, u, tr + 0.03, LARGH, y0 + i * r - 0.35, y0 + (i + 1) * r), 'tower_stone')
            nst += 1
        # pareti: taglio verticale a monte con coronamento, parapetto di roccia a valle
        s_a = 0.6 if k == 0 else 1.3
        s_b = L - (0.4 if k == len(fl) - 1 else 1.3)
        N = max(3, int((s_b - s_a) / 0.9) + 1); ss = np.linspace(s_a, s_b, N)
        cc = a + np.outer(ss, u); yy = y0 + (y1 - y0) * ss / L; yt = yy + r * 0.5
        o1 = cc + nup * (LARGH / 2 + 0.03)
        hc = m.height(cc[:, 0] + nup[0] * 2.1, cc[:, 1] + nup[1] * 2.1)
        ht = np.clip(hc + 0.05, yt + 0.9, yt + 3.2) + rng.uniform(-0.12, 0.12, N)
        o2 = cc + nup * 3.3; h2 = m.height(o2[:, 0], o2[:, 1]) - 0.08
        dn = -nup
        i1 = cc + dn * (LARGH / 2 + 0.03); i2 = cc + dn * (LARGH / 2 + 0.47)
        hp = yt + 0.5 + rng.uniform(-0.08, 0.1, N)
        want_in = np.array([-nup[0], 0, -nup[1]])
        for j in range(N - 1):
            # parete a monte (verso la scala) e coronamento (verso l'alto)
            S.quad([(o1[j, 0], yt[j] - 0.45, o1[j, 1]), (o1[j + 1, 0], yt[j + 1] - 0.45, o1[j + 1, 1]),
                    (o1[j + 1, 0], ht[j + 1], o1[j + 1, 1]), (o1[j, 0], ht[j], o1[j, 1])], 'stone_dark', want_in)
            S.quad([(o1[j, 0], ht[j], o1[j, 1]), (o1[j + 1, 0], ht[j + 1], o1[j + 1, 1]),
                    (o2[j + 1, 0], h2[j + 1], o2[j + 1, 1]), (o2[j, 0], h2[j], o2[j, 1])], 'terrain_rock', np.array([0, 1.0, 0]))
            # parapetto a valle: faccia interna, cima, faccia esterna (fino dentro il sostegno)
            S.quad([(i1[j, 0], yt[j] - 0.3, i1[j, 1]), (i1[j + 1, 0], yt[j + 1] - 0.3, i1[j + 1, 1]),
                    (i1[j + 1, 0], hp[j + 1], i1[j + 1, 1]), (i1[j, 0], hp[j], i1[j, 1])], 'terrain_rock', -want_in)
            S.quad([(i1[j, 0], hp[j], i1[j, 1]), (i1[j + 1, 0], hp[j + 1], i1[j + 1, 1]),
                    (i2[j + 1, 0], hp[j + 1] - 0.05, i2[j + 1, 1]), (i2[j, 0], hp[j] - 0.05, i2[j, 1])], 'terrain_rock', np.array([0, 1.0, 0]))
            S.quad([(i2[j, 0], hp[j] - 0.05, i2[j, 1]), (i2[j + 1, 0], hp[j + 1] - 0.05, i2[j + 1, 1]),
                    (i2[j + 1, 0], yy[j + 1] - 1.5, i2[j + 1, 1]), (i2[j, 0], yy[j] - 1.5, i2[j, 1])], 'terrain_rock', -want_in)
        for j, sg in ((0, -1), (N - 1, 1)):          # testate del parapetto
            S.quad([(i1[j, 0], yt[j] - 0.3, i1[j, 1]), (i1[j, 0], hp[j], i1[j, 1]), (i2[j, 0], hp[j] - 0.05, i2[j, 1]),
                    (i2[j, 0], yy[j] - 1.5, i2[j, 1])], 'terrain_rock', np.array([u[0] * sg, 0, u[1] * sg]))
    for k in range(1, len(pts) - 1):                 # pianerottoli alle svolte, con lanterna sul lato a valle
        p, yl = pts[k], ys[k]
        ud = fl[k - 1][4] + fl[k][4]
        ud = ud / np.linalg.norm(ud) if np.linalg.norm(ud) > 1e-3 else fl[k][4]
        S.add(blocco(tuple(p), tuple(ud), 2.3, 2.3, yl - 0.5, yl), 'tower_stone')
        dn = -(fl[k - 1][6] + fl[k][6]); dn = dn / (np.linalg.norm(dn) + 1e-9)
        q = p + dn * 0.9
        lanterna(S, q[0], yl, q[1])
    lanterna(S, XB - 1.45, ys[0] - 0.02, ZW - 1.0)                 # lanterna al piede, accanto al ponticello
    m.add_faces('Torre_Mago_Scala', S.P, S.F, S.M, False, after='Torre_Mago')
    # --- 6b) ponticello di legno sul fiume, testate di pietra, scaletta fino alla strada, cartello
    Pn = Mesh(); zc_ = (ZW + ZE) / 2; mezza = (ZE - ZW) / 2
    for sx in (-0.6, 0.6):                           # travi
        Pn.add(box3((XB + sx, yd - 0.18, zc_), (0, 0, 1), (0, 1, 0), (1, 0, 0), mezza + 0.45, 0.11, 0.08), 'trunk_brown')
    zz = np.arange(ZW - 0.3, ZE + 0.3 - 0.01, 0.3)
    for k, z_ in enumerate(zz):                      # assi dell'impalcato
        Pn.add(box3((XB, yd - 0.035 + rng.uniform(-0.008, 0.008), z_ + 0.15), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.8, 0.035, 0.135), 'wood_trim' if k % 3 else 'fence_wood')
    yb = float(m.height(XB, zc_)) - 0.4              # pila in mezzo al fiume
    for sx in (-0.6, 0.6):
        Pn.add(box3((XB + sx, (yb + yd - 0.29) / 2, zc_), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.09, (yd - 0.29 - yb) / 2, 0.09), 'trunk_brown')
    Pn.add(box3((XB, yd - 0.35, zc_), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.78, 0.06, 0.08), 'trunk_brown')
    for sx in (-0.82, 0.82):                         # parapetti
        for z_ in np.linspace(ZW - 0.2, ZE + 0.2, 7):
            Pn.add(box3((XB + sx, yd + 0.45, z_), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.05, 0.5, 0.05), 'trunk_brown')
        Pn.add(box3((XB + sx, yd + 0.93, zc_), (0, 0, 1), (0, 1, 0), (1, 0, 0), mezza + 0.25, 0.04, 0.045), 'wood_trim')
        Pn.add(box3((XB + sx, yd + 0.5, zc_), (0, 0, 1), (0, 1, 0), (1, 0, 0), mezza + 0.25, 0.03, 0.03), 'wood_trim')
    for zt, hz in ((ZW - 0.35, 0.55), (ZE + 0.15, 0.35)):     # testate di pietra
        XX, ZZ = np.meshgrid(np.linspace(XB - 1.0, XB + 1.0, 4), np.linspace(zt - hz, zt + hz, 3))
        y_b = float(m.height(XX.ravel(), ZZ.ravel()).min()) - 0.4
        Pn.add(box3((XB, (y_b + yd - 0.07) / 2, zt), (1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0, (yd - 0.07 - y_b) / 2, hz, 0.04, rng), 'stone_dark')
    # scaletta sulla riva est fino alla strada
    k = 0; z_s = ZE + 0.5; top = yd - 0.07
    while True:
        k += 1; top_k = yd - 0.07 - 0.2 * k; zk = z_s + (k - 0.5) * 0.3
        th = float(m.height(XB, zk))
        if top_k < th + 0.05 or k > 20: break
        XX = np.array([XB - 0.7, XB + 0.7, XB, XB]); ZZ = np.array([zk, zk, zk - 0.15, zk + 0.15])
        y_b = float(m.height(XX, ZZ).min()) - 0.3
        Pn.add(blocco((XB, zk), (0, 1), 0.31, 1.4, y_b, top_k), 'tower_stone')
    n_sc = k - 1; z_fine = z_s + n_sc * 0.3
    lanterna(Pn, XB - 0.95, yd - 0.07, ZE + 0.2)
    q2 = (XB + 1.25, z_fine + 0.2); hq = float(m.height(*q2))      # cartello verso la torre, dove arriva la strada
    Pn.add(blocco(q2, (1, 0), 0.12, 0.12, hq - 0.1, hq + 1.5), 'wood_trim')
    Pn.add(blocco(q2, (0, 1), 0.7, 0.06, hq + 1.05, hq + 1.4), 'wood_trim')
    Pn.add(blocco((q2[0] - 0.035, q2[1]), (0, 1), 0.5, 0.02, hq + 1.12, hq + 1.33), 'magic_violet')
    m.add_faces('Torre_Mago_Ponticello', Pn.P, Pn.F, Pn.M, False, after='Torre_Mago')
    # --- 7) grotta: portale ad arco di conci, porta arretrata, rocce attorno, lanterne, cristalli
    Gm = Mesh(); zc = ZB + 0.35; hw = 0.72
    Gm.quad([(GX - RW, GY - 0.02, ZB + 0.01)] + [(GX + RW * math.cos(math.pi - math.pi * k / 12), GY + HS + RW * math.sin(math.pi - math.pi * k / 12), ZB + 0.01) for k in range(13)] +
            [(GX + RW, GY - 0.02, ZB + 0.01)], 'cave_dark', np.array([0, 0, 1.0]))
    rd, hd = 0.62, 1.42                              # porta ad arco
    Gm.quad([(GX - rd, GY, ZB + 0.04)] + [(GX + rd * math.cos(math.pi - math.pi * k / 8), GY + hd + rd * math.sin(math.pi - math.pi * k / 8), ZB + 0.04) for k in range(9)] +
            [(GX + rd, GY, ZB + 0.04)], 'wood_trim', np.array([0, 0, 1.0]))
    for hy in (0.45, 1.25):
        Gm.add(box3((GX, GY + hy, ZB + 0.07), (1, 0, 0), (0, 1, 0), (0, 0, 1), rd - 0.02, 0.045, 0.025), 'iron_dark')
    Gm.add(box3((GX + 0.36, GY + 0.98, ZB + 0.1), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.06, 0.06, 0.04), 'bronze')
    Gm.add(box3((GX, GY + hd + 0.25, ZB + 0.08), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.14, 0.1, 0.03), 'iron_dark')
    rc = RW + 0.36
    for k in range(9):                               # conci dell'arco nel piano verticale della bocca
        a = math.pi * (k + 0.5) / 9
        R_ = np.array([math.cos(a), math.sin(a), 0.0]); T_ = np.array([-math.sin(a), math.cos(a), 0.0])
        cen = np.array([GX, GY + HS, zc]) + R_ * rc
        chiave = k == 4
        Gm.add(box3(cen, T_, R_, (0, 0, 1), math.pi * rc / 18 * (1.02 if chiave else 0.93), 0.42 if chiave else 0.36, hw + (0.06 if chiave else 0.0), 0.03, rng),
               'stone_light' if chiave else ('stone_dark' if k % 2 else 'terrain_rock'))
    for sx in (-1, 1):                               # piedritti
        for (h0, h1) in ((GY - 0.15, GY + 0.74), (GY + 0.76, GY + HS + 0.02)):
            Gm.add(box3((GX + sx * rc, (h0 + h1) / 2, zc), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.36, (h1 - h0) / 2, hw, 0.03, rng),
                   'terrain_rock' if h0 < GY else 'stone_dark')
    gem_y = GY + HS + rc + 0.42
    Gm.add(G.cone((GX, gem_y - 0.05, zc + hw + 0.08), (GX, gem_y + 0.3, zc + hw + 0.12), 0.13, n=4), 'magic_violet')
    for (dx, dy, dz, sx_, sy_, sz_, mt) in ((-RW - 1.45, 0.75, 0.1, 0.62, 0.95, 0.8, 'terrain_rock'), (RW + 1.5, 0.6, 0.15, 0.7, 0.8, 0.85, 'stone_dark'),
                                            (-1.5, 3.75, -0.25, 1.0, 0.65, 0.75, 'moss_stone'), (1.7, 3.55, -0.2, 0.95, 0.7, 0.7, 'terrain_rock'),
                                            (0.1, 4.25, -0.45, 1.2, 0.6, 0.7, 'stone_dark')):
        Gm.add(sasso((GX + dx, GY + dy, ZB + dz), sx_ * 1.15, sy_ * 1.1, sz_ * 1.1, rng), mt)
    for sx in (-1, 1):
        bx = GX + sx * (rc + 0.95)
        lanterna(Gm, bx, GY + 2.05, ZB + 1.25, braccio=(GX + sx * (rc + 0.3), GY + 2.3, ZB + 0.9))
    for k in range(4):                               # cristalli sul pianerottolo, a destra della bocca
        b0 = (GX + 3.7 + rng.uniform(-0.4, 0.4), GY - 0.05, ZB + 1.3 + rng.uniform(-0.3, 0.5))
        tip = (b0[0] + rng.uniform(-0.25, 0.25), b0[1] + rng.uniform(0.5, 1.1), b0[2] + rng.uniform(-0.2, 0.2))
        Gm.add(G.cone(b0, tip, rng.uniform(0.1, 0.17), n=5), 'crystal_teal' if k % 3 else 'magic_violet')
    m.add_faces('Torre_Mago_Grotta', Gm.P, Gm.F, Gm.M, False, after='Torre_Mago')
    # --- 8) fuori dalla torre: calderone e dettagli (posti verificati liberi e piani)
    occ = occupancy_fine(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Animali', 'Canneto_Fiume'), with_mats=False)
    names = np.array(m.mats + ['<buco>'])[m.M]
    gxh, gzh = np.gradient(m.H, 0.9); sl = np.hypot(gxh, gzh); sc = (sl[:-1, :-1] + sl[1:, :-1] + sl[:-1, 1:] + sl[1:, 1:]) / 4
    libero = ndimage.distance_transform_edt(~(occ | (sc > 0.5) | (names == 'path_dirt'))) * 0.9
    def libero_in(x, z):
        i, j = [int(v) for v in m.ij(x, z)]
        return libero[i, j]
    def posto(centro, r, dmin=0.0, dmax=5.0, lontano_da=()):
        for dd in np.arange(dmin, dmax + 0.01, 0.3):
            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
                px, pz = centro[0] + dd * math.cos(a), centro[1] + dd * math.sin(a)
                if libero_in(px, pz) >= r and all(math.hypot(px - q[0], pz - q[1]) > q[2] for q in lontano_da):
                    return (px, pz)
        return None
    D = Mesh(); dett = []
    pc = posto(CALDERONE, 1.2)
    if pc:
        cx, cz = pc; y0 = float(m.height(np.array([cx - 0.8, cx + 0.8, cx, cx]), np.array([cz, cz, cz - 0.8, cz + 0.8])).min())
        for k in range(3):                           # treppiede
            a = 2 * math.pi * k / 3 + 0.3; lx, lz = cx + 0.66 * math.cos(a), cz + 0.66 * math.sin(a)
            D.add(G.loft([(lx, y0 - 0.08, lz), (cx + 0.12 * math.cos(a), y0 + 1.55, cz + 0.12 * math.sin(a))], [0.035, 0.03], [0.035, 0.03], n=4), 'iron_dark')
        D.add(G.loft([(cx, y0 + 1.5, cz), (cx, y0 + 1.25, cz)], [0.02, 0.02], [0.02, 0.02], n=4), 'iron_dark')
        prof = [(0.0, 0.18), (0.08, 0.36), (0.25, 0.5), (0.48, 0.55), (0.68, 0.5), (0.78, 0.44), (0.84, 0.48)]
        path = [(cx, y0 + 0.42 + h, cz) for h, r in prof]
        D.add(G.loft(path, [r for h, r in prof], [r for h, r in prof], n=12, up=(1, 0, 0), caps=(True, False)), 'iron_dark')
        D.add(([(cx + 0.43 * math.cos(2 * math.pi * k / 12), y0 + 0.42 + 0.76, cz + 0.43 * math.sin(2 * math.pi * k / 12)) for k in range(12)][::-1], [list(range(12))]), 'crystal_teal')
        for k in range(4):                           # bolle
            a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.05, 0.28)
            b0 = (cx + rr * math.cos(a), y0 + 1.17, cz + rr * math.sin(a))
            D.add(G.cone(b0, (b0[0], b0[1] + rng.uniform(0.08, 0.16), b0[2]), rng.uniform(0.05, 0.09), n=4), 'crystal_teal')
        for k in range(6):                           # fuoco
            a = rng.uniform(0, 2 * math.pi); r_ = rng.uniform(0.0, 0.28)
            b = (cx + r_ * math.cos(a), y0 + 0.03, cz + r_ * math.sin(a))
            D.add(G.cone(b, (b[0] + rng.uniform(-0.05, 0.05), b[1] + rng.uniform(0.25, 0.42), b[2]), rng.uniform(0.08, 0.13), n=4), 'fire_glow' if k % 2 else 'ember')
        for k in range(5):                           # ceppi a raggiera
            a = 2 * math.pi * k / 5 + rng.uniform(-0.2, 0.2)
            D.add(G.loft([(cx + 0.12 * math.cos(a), y0 + 0.07, cz + 0.12 * math.sin(a)), (cx + 0.6 * math.cos(a), y0 + 0.05, cz + 0.6 * math.sin(a))],
                         [0.065, 0.06], [0.065, 0.06], n=5, up=(0, 1, 0)), 'ember' if k % 2 else 'trunk_brown')
        for k in range(9):                           # pietre del focolare
            a = 2 * math.pi * k / 9
            D.add(box3((cx + 0.78 * math.cos(a), y0 + 0.05, cz + 0.78 * math.sin(a)), (math.cos(a), 0, math.sin(a)), (0, 1, 0), (-math.sin(a), 0, math.cos(a)), 0.11, 0.09, 0.14, 0.02, rng), 'stone_dark')
        dett.append('calderone su treppiede con pozione luminosa, fuoco e focolare di pietre in (%.1f, %.1f)' % (cx, cz))
        # tavolo con ampolle e libro, sgabello
        pt = posto((cx, cz), 1.0, 2.0, 3.2)
        if pt:
            tx, tz = pt; ut = (-(tz - cz), tx - cx)
            yt = float(m.height(tx, tz))
            D.add(blocco((tx, tz), ut, 1.4, 0.7, yt + 0.72, yt + 0.8), 'wood_trim')
            un = np.array(ut) / np.linalg.norm(ut); vn = np.array([-un[1], un[0]])
            for (ox, oz) in ((-0.6, -0.27), (0.6, -0.27), (-0.6, 0.27), (0.6, 0.27)):
                q = np.array([tx, tz]) + un * ox + vn * oz
                D.add(blocco(tuple(q), ut, 0.08, 0.08, yt - 0.05, yt + 0.72, ('front', 'back', 'left', 'right')), 'wood_trim')
            for k, mt in enumerate(('magic_violet', 'crystal_teal', 'flag_red', 'crystal_teal', 'magic_violet')):
                q = np.array([tx, tz]) + un * (-0.55 + 0.17 * k) + vn * rng.uniform(-0.15, 0.12); hh = rng.uniform(0.18, 0.3)
                D.add(G.loft([(q[0], yt + 0.8, q[1]), (q[0], yt + 0.8 + hh * 0.6, q[1]), (q[0], yt + 0.8 + hh * 0.75, q[1]), (q[0], yt + 0.8 + hh, q[1])],
                             [0.065, 0.06, 0.025, 0.025], [0.065, 0.06, 0.025, 0.025], n=6, up=(1, 0, 0)), mt)
            q = np.array([tx, tz]) + un * 0.38
            D.add(blocco(tuple(q), ut, 0.46, 0.34, yt + 0.79, yt + 0.81, ('top', 'front', 'back', 'left', 'right')), 'flag_red')
            D.add(blocco(tuple(q), ut, 0.42, 0.3, yt + 0.81, yt + 0.85, ('top', 'front', 'back', 'left', 'right')), 'wool_white')
            q = np.array([tx, tz]) + vn * 0.75 * (1 if libero_in(*(np.array([tx, tz]) + vn * 0.75)) > 0.3 else -1)
            D.add(blocco(tuple(q), ut, 0.36, 0.36, yt + 0.42, yt + 0.48), 'wood_trim')
            for (ox, oz) in ((-0.13, -0.13), (0.13, -0.13), (-0.13, 0.13), (0.13, 0.13)):
                qq = q + un * ox + vn * oz
                D.add(blocco(tuple(qq), ut, 0.05, 0.05, yt - 0.05, yt + 0.42, ('front', 'back', 'left', 'right')), 'wood_trim')
            dett.append('tavolo con 5 ampolle e libro aperto, sgabello')
        # catasta di legna con scopa appoggiata
        pl = posto((cx, cz), 0.9, 1.9, 3.2, lontano_da=((pt[0], pt[1], 1.9),) if pt else ())
        if pl:
            lx, lz = pl; yl = float(m.height(lx, lz)); ul = np.array([lx - cx, lz - cz]); ul /= np.linalg.norm(ul); vl = np.array([-ul[1], ul[0]])
            for k in range(6):
                row = 0 if k < 3 else 1; col = k % 3 if k < 3 else (k - 3) % 2
                q = np.array([lx, lz]) + ul * ((col - 1) * 0.22 + (0.11 if row else 0))
                yy_ = yl + 0.1 + row * 0.19
                D.add(G.loft([(q[0] - vl[0] * 0.45, yy_, q[1] - vl[1] * 0.45), (q[0] + vl[0] * 0.45, yy_, q[1] + vl[1] * 0.45)], [0.1, 0.1], [0.1, 0.1], n=6, up=(0, 1, 0)), 'trunk_brown')
            bs = np.array([lx, lz]) + vl * 0.7
            D.add(G.loft([(bs[0] + ul[0] * 0.45, yl + 1.45, bs[1] + ul[1] * 0.45), (bs[0], yl + 0.35, bs[1])], [0.025, 0.025], [0.025, 0.025], n=4), 'trunk_brown')
            D.add(G.cone((bs[0], yl + 0.38, bs[1]), (bs[0] - ul[0] * 0.08, yl - 0.02, bs[1] - ul[1] * 0.08), 0.13, n=6), 'hay')
            dett.append('catasta di legna con scopa')
        nc = 0
        for k in range(4):                           # cristalli che spuntano dal terreno
            q = posto((cx + 2.4 * math.cos(k * 1.7), cz + 2.4 * math.sin(k * 1.7)), 0.5, 0.0, 1.5,
                      lontano_da=((cx, cz, 1.3),) + (((pt[0], pt[1], 1.2),) if pt else ()) + (((pl[0], pl[1], 1.0),) if pl else ()))
            if not q: continue
            b0 = (q[0], float(m.height(*q)) - 0.05, q[1])
            D.add(G.cone(b0, (b0[0] + rng.uniform(-0.1, 0.1), b0[1] + rng.uniform(0.45, 0.8), b0[2]), 0.12, n=5), 'crystal_teal' if k % 2 else 'magic_violet')
            nc += 1
        dett.append('%d cristalli' % nc)
        m.add_faces('Torre_Mago_Dettagli', D.P, D.F, D.M, False, after='Torre_Mago')
    Ltot = sum(f[5] for f in fl)
    log('scala ripida scavata nella roccia dalla riva del fiume ai piedi della rupe (quota %.1f, collegata alla strada dal ponticello) alla grotta sotto la torre (quota %.1f): %d rampe di %s m, %d pianerottoli di svolta, %d gradini (alzata %s m, pedata %s m), pendenza media %.0f%% (%.0f gradi)'
        % (ys[0], ys[-1], len(fl), ' + '.join('%.1f' % f[5] for f in fl), len(fl) - 1, nst, '/'.join('%.2f' % r for r, t in rises), '/'.join('%.2f' % t for r, t in rises),
           100 * (ys[-1] - ys[0]) / Ltot, math.degrees(math.atan((ys[-1] - ys[0]) / Ltot))))
    log('il solco: parete tagliata a monte e parapetto di roccia a valle lungo le rampe; 4 lanterne su palo (oggetto nuovo Torre_Mago_Scala, %d facce)' % len(S.F))
    log('ai piedi: ponticello di legno di %.1f m sul fiume (impalcato a quota %.2f, %.2f m sopra l\'acqua), con pila centrale, parapetti e testate di pietra; scaletta di %d gradini fino alla strada sulla riva est, lanterna e cartello (oggetto nuovo Torre_Mago_Ponticello, %d facce)'
        % (ZE - ZW, yd, yd - y_acqua, n_sc, len(Pn.F)))
    log('grotta d\'ingresso nella rupe sotto la torre (apertura %.1f x %.1f m, pavimento a quota %.1f, 7.4 m sotto la spianata): portale ad arco di 9 conci con chiave chiara e gemma viola, piedritti, porta ad arco con bande di ferro arretrata nel buio, rocce di raccordo, 2 lanterne a staffa, cristalli (oggetto nuovo Torre_Mago_Grotta, %d facce)'
        % (2 * RW, HS + RW, GY, len(Gm.F)))
    log('fuori dalla torre: %s (oggetto nuovo Torre_Mago_Dettagli, %d facce)' % ('; '.join(dett) if dett else 'nessun posto libero trovato', len(D.F)))
    log('tolti dal corridoio della scala, dalla grotta e dal ponticello: ' + (', '.join('%s %d (%d facce)' % (k, v[0], v[1]) for k, v in nrem.items()) if nrem else 'niente'))
    return LOG
