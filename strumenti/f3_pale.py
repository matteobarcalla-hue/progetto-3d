"""Fase 3 - Pale dolomitiche sulla cima della montagna più alta.
La montagna più alta è il massiccio a -X/+Z (spalla a 136-144 m, la cupola rialzata dall'utente arriva a 167,8 m):
la spalla sta all'altezza delle cime delle 15 guglie esistenti (113-149 m), che restano dove sono, davanti.
Sulla cima sorge un massiccio largo a pareti verticali, come le Pale di San Martino. La roccia è costruita a strati
(banchi di 4,5-8 m): un campo di quote fatto di altopiani a pareti ripide viene tagliato a ogni banco; il bordo di
ogni banco diventa una parete verticale, la differenza fra due banchi una cengia (sottile dove la parete è a picco,
larga e erbosa dove il pendio è a gradoni). Così:
- uno zoccolo che copre tutta la cima, con pareti di 25-35 m;
- sopra lo zoccolo l'altopiano e tre pale separate da forcelle: Pala Grande (la più alta, sopra la cupola),
  Cima di Mezzo, Pala del Sud; camini (intagli verticali che si allargano verso l'alto) e torri sul bordo;
- davanti, isolato sulla spalla, il Campanile; ai piedi ghiaioni chiari.
Il punto più alto della mappa è la cima della Pala Grande."""
import numpy as np, math, collections
from scipy import ndimage
from shapely.geometry import Polygon, Point, MultiPolygon, LineString
from shapely.ops import unary_union
import triangle as tr
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[pale]', s)

SPROF = 4.0
# zoccolo: pianta spigolosa sulla cima (x, z); il bordo della mappa è a x = -455,4 e z = 239
ZOCCOLO = dict(nome='Zoccolo delle Pale', cima=166.0, seme=101,
               P=[(-446, 120), (-433, 109), (-411, 111), (-395, 121), (-386, 137), (-391, 151), (-384, 166), (-389, 183),
                  (-392, 199), (-391, 217), (-401, 231), (-418, 235), (-437, 233), (-448, 214), (-444, 186), (-449, 163), (-445, 141)])
# pale sopra lo zoccolo: pianta (macro vertici) e quota delle sommità
PALE = [dict(nome='Pala Grande', cima=187.0, seme=111, torri=0, picco=(-421.0, 213.0, 8.0, 20.0), creste=12.0,
             P=[(-442, 203), (-431, 193), (-410, 195), (-398, 205), (-398, 221), (-411, 231), (-433, 230)]),
        dict(nome='Cima di Mezzo', cima=181.0, seme=121, torri=0, picco=(-433.0, 163.0, 6.0, 14.0), creste=10.0,
             P=[(-444, 152), (-430, 147), (-416, 153), (-411, 168), (-419, 181), (-437, 182), (-445, 170)]),
        dict(nome='Pala del Sud', cima=176.0, seme=131, torri=0, creste=8.0,
             P=[(-441, 122), (-428, 114), (-408, 118), (-399, 129), (-405, 139), (-423, 141), (-438, 136)])]
CAMPANILE = dict(nome='Campanile', c=(-372.0, 141.0), r=5.0, cima=168.0, seme=141)

# ------------------------------------------------------------------ piante con pilastri e camini
def dettaglia(P, rng, scala=1.0, passo=2.5):
    """dai macro vertici una pianta con pilastri (in fuori) e camini (stretti e profondi, in dentro), a spigoli vivi.
    Restituisce (anello Nx2 antiorario, tipo per vertice: 0 liscio, 1 pilastro, 2 camino)"""
    P = np.array(P, float)
    if not Polygon(P).exterior.is_ccw: P = P[::-1]
    pts = []; tipi = []
    n = len(P)
    for k in range(n):
        a = P[k]; b = P[(k + 1) % n]
        L = float(np.linalg.norm(b - a)); u = (b - a) / L; nrm = np.array([u[1], -u[0]])   # fuori (anello antiorario)
        segs = []; t = 1.2 * scala
        segs.append((0.0, t, 0.0, 0))
        while t < L - 1.2 * scala:
            r = rng.random()
            if r < 0.30: w = rng.uniform(1.3, 2.4) * scala; off = -rng.uniform(1.6, 3.2) * scala; ty = 2
            elif r < 0.72: w = rng.uniform(3.0, 6.5) * scala; off = rng.uniform(0.7, 1.9) * scala; ty = 1
            else: w = rng.uniform(1.5, 4.0) * scala; off = rng.uniform(-0.3, 0.3) * scala; ty = 0
            w = min(w, L - 1.2 * scala - t)
            if w < 0.6: break
            segs.append((t, t + w, off, ty)); t += w
        segs.append((t, L, 0.0, 0))
        for (s0, s1, off, ty) in segs:
            m_ = max(1, int(math.ceil((s1 - s0) / passo)))
            for q in range(m_ + 1):
                s = s0 + (s1 - s0) * q / m_
                if s >= L - 1e-6: continue
                pts.append(a + u * s + nrm * off); tipi.append(ty)
    R = np.array(pts); T = np.array(tipi)
    # punti coincidenti consecutivi (passaggi a offset uguale) tolti
    keep = np.ones(len(R), bool)
    for i in range(len(R)):
        if np.linalg.norm(R[i] - R[i - 1]) < 0.05: keep[i] = False
    R = R[keep]; T = T[keep]
    pol = Polygon(R)
    if not pol.is_valid:
        return None
    return R, T

def pianta(P, rng, scala=1.0):
    for _ in range(30):
        r = dettaglia(P, rng, scala)
        if r is not None: return r
    R = np.array(P, float)
    return (R if Polygon(R).exterior.is_ccw else R[::-1]), np.zeros(len(R), int)

def ritaglia(R, T, contenitore):
    """pianta R tagliata dentro il contenitore; i tipi dei vertici rimasti si conservano"""
    pol = Polygon(R).intersection(contenitore)
    if isinstance(pol, MultiPolygon): pol = max(pol.geoms, key=lambda g: g.area)
    if abs(pol.area - Polygon(R).area) < 0.5: return R, T
    R2 = anello_da_poligono(pol)
    T2 = np.zeros(len(R2), int)
    for k, q in enumerate(R2):
        d = np.hypot(R[:, 0] - q[0], R[:, 1] - q[1]); i = int(np.argmin(d))
        if d[i] < 0.05: T2[k] = T[i]
    return R2, T2

def anello_da_poligono(pol):
    R = np.array(pol.exterior.coords)[:-1]
    if not pol.exterior.is_ccw: R = R[::-1]
    return R

# ------------------------------------------------------------------ geometria
class Mesh:
    def __init__(self): self.P = []; self.F = []; self.M = []
    def add(self, pts, mt, su=None, fuori=None):
        """faccia piana; su=True: normale verso l'alto; fuori=(punto, poligono): normale verso l'esterno del poligono"""
        pts = [tuple(map(float, p)) for p in pts]
        q = np.array(pts)
        nrm = np.zeros(3)
        for a, b in zip(q, np.roll(q, -1, 0)):
            nrm += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        if np.linalg.norm(nrm) < 1e-8: return
        if su is not None:
            if (nrm[1] > 0) != su: pts = pts[::-1]
        elif fuori is not None:
            c = q.mean(0); h = np.array([nrm[0], nrm[2]]); h /= np.linalg.norm(h) + 1e-12
            if fuori.contains(Point(c[0] + 0.05 * h[0], c[2] + 0.05 * h[1])): pts = pts[::-1]
        i = len(self.P); self.P.extend(pts); self.F.append(list(range(i, i + len(pts)))); self.M.append(mt)

def pareti(mesh, R, T, y0, y1, rng, mat_fn):
    """pareti verticali dall'anello R (quota y0, scalare) alle quote y1 (scalare o per vertice)"""
    n = len(R); y1 = np.broadcast_to(np.asarray(y1, float), (n,))
    pol = Polygon(R)
    for i in range(n):
        j = (i + 1) % n
        mt = mat_fn(T[i], T[j])
        mesh.add([(R[i, 0], y0, R[i, 1]), (R[j, 0], y0, R[j, 1]), (R[j, 0], y1[j], R[j, 1]), (R[i, 0], y1[i], R[i, 1])], mt, fuori=pol)

def mat_parete(rng):
    def f(ta, tb):
        if ta == 2 and tb == 2: return 'terrain_rock'                  # camini in ombra: più scuri
        r = rng.random()
        return 'tower_stone' if r < 0.18 else ('terrain_rock' if r < 0.24 else 'stone_light')
    return f

def triangola(pol, interni=None, quota_fn=None, mat_fn=None, mesh=None, quota_bordo=None):
    """superficie del poligono (con buchi) triangolata; quota_fn(x, z) per i punti interni, quota_bordo dict per i vertici del bordo"""
    polys = list(pol.geoms) if isinstance(pol, MultiPolygon) else [pol]
    for pg in polys:
        if pg.area < 0.3: continue
        V = []; S = []; holes = []
        def anello(coords):
            c = np.array(coords)[:-1]; b = len(V)
            V.extend(c.tolist())
            S.extend([[b + k, b + (k + 1) % len(c)] for k in range(len(c))])
        anello(pg.exterior.coords)
        for h in pg.interiors:
            anello(h.coords); holes.append(Polygon(h).representative_point().coords[0])
        nb = len(V)
        if interni is not None:
            inner = pg.buffer(-1.2)
            for p in interni:
                if inner.contains(Point(p)): V.append(list(p))
        A = dict(vertices=np.array(V, float), segments=np.array(S, int))
        if holes: A['holes'] = np.array(holes, float)
        try:
            B = tr.triangulate(A, 'p')
        except Exception:
            continue
        VV = B['vertices']
        hh = np.zeros(len(VV))
        for k, p in enumerate(VV):
            key = (round(p[0], 3), round(p[1], 3))
            if quota_bordo is not None and key in quota_bordo: hh[k] = quota_bordo[key]
            else: hh[k] = quota_fn(p[0], p[1], k >= nb)
        for t in B['triangles']:
            cc = VV[t].mean(0)
            if not pg.buffer(0.01).contains(Point(cc)): continue
            mesh.add([(VV[t[q], 0], hh[t[q]], VV[t[q], 1]) for q in range(3)], mat_fn(cc), su=True)

def punti_interni(pol, rng, dmin=4.0, n=400):
    b = pol.bounds; P = []
    for _ in range(n):
        q = (rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3]))
        if all((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 > dmin * dmin for p in P): P.append(q)
    return P

def torre(mesh, pc, rr, yb, ht, rng, mt='stone_light'):
    nn = int(rng.integers(5, 8))
    a0 = np.sort(rng.uniform(0, 2 * np.pi, nn))
    rb = rr * (1 + rng.uniform(-0.2, 0.2, nn))
    B = np.stack([pc[0] + rb * np.cos(a0), pc[1] + rb * np.sin(a0)], 1)
    ym = yb + ht * rng.uniform(0.55, 0.75); yt = yb + ht
    Mid = pc + (B - pc) * rng.uniform(0.75, 0.9) + rng.normal(0, 0.15, (nn, 2))
    Tp = pc + (B - pc) * rng.uniform(0.25, 0.5) + rng.normal(0, 0.15, (nn, 2))
    for R0, R1, y0, y1 in ((B, Mid, yb, ym), (Mid, Tp, ym, yt)):
        pol = Polygon(R0).convex_hull
        for i in range(nn):
            j = (i + 1) % nn
            mesh.add([(R0[i, 0], y0, R0[i, 1]), (R0[j, 0], y0, R0[j, 1]), (R1[j, 0], y1, R1[j, 1]), (R1[i, 0], y1, R1[i, 1])], mt, fuori=pol)
    cc = Tp.mean(0); yp = yt + rng.uniform(0.3, 2.5)
    pol = Polygon(Tp).convex_hull
    for i in range(nn):
        j = (i + 1) % nn
        mesh.add([(Tp[i, 0], yt, Tp[i, 1]), (Tp[j, 0], yt, Tp[j, 1]), (cc[0], yp, cc[1])], mt, fuori=pol)
    return yp

# ------------------------------------------------------------------ ghiaioni
def ghiaioni(m, U, rng, L0=15.0, alza=7.0):
    """coni di ghiaia ai piedi delle pareti: il terreno sale verso la parete (di 2-9 m, di più sotto i camini) e
    scende in 8-25 m; dentro la pianta il terreno non cambia (resta coperto dallo zoccolo)"""
    from matplotlib.path import Path
    X, Z = m.grid_xz(); Xc, Zc = m.cell_xz()
    H0 = m.H.copy()
    polys = list(U.geoms) if isinstance(U, MultiPolygon) else [U]
    ins = np.zeros(X.shape, bool)
    for pg in polys:
        ins |= Path(np.array(pg.exterior.coords)).contains_points(np.stack([X.ravel(), Z.ravel()], 1)).reshape(X.shape)
    d = ndimage.distance_transform_edt(~ins) * 0.9
    cen = np.array(U.centroid.coords[0])
    ang = np.arctan2(Z - cen[1], X - cen[0])
    lobi = np.clip(0.55 + 0.5 * np.maximum(0, np.sin(7 * ang + rng.uniform(0, 6))) + 0.25 * np.sin(13 * ang + rng.uniform(0, 6)), 0.35, 1.3)
    L = L0 * lobi; A = alza * lobi
    lift = np.where((d > 0) & (d < L), A * np.clip(1 - d / L, 0, 1) ** 1.6, 0.0)
    lift = ndimage.gaussian_filter(lift, 1.0)
    lift[ins] = 0.0
    ii, jj = np.indices(lift.shape)
    dbordo = np.minimum.reduce([ii, jj, lift.shape[0] - 1 - ii, lift.shape[1] - 1 - jj])
    lift *= np.clip((dbordo - 3) / 5.0, 0, 1)                           # il bordo della mappa resta com'è (Base_Sezione)
    m.H = H0 + lift
    insc = np.zeros(Xc.shape, bool)
    for pg in polys:
        insc |= Path(np.array(pg.exterior.coords)).contains_points(np.stack([Xc.ravel(), Zc.ravel()], 1)).reshape(Xc.shape)
    liftc = (lift[:-1, :-1] + lift[1:, :-1] + lift[:-1, 1:] + lift[1:, 1:]) / 4
    sel = (liftc > 0.35) & ~insc & (m.M >= 0)
    m.M[sel] = np.where(rng.random(int(sel.sum())) < 0.8, m.mat_index('terrain_gravel'), m.mat_index('stone_light'))
    return int(sel.sum()), float(lift.max()), liftc > 0.2

# ------------------------------------------------------------------ campo delle quote della roccia
RIS = 0.75
def rumore(shape, rng, sigma):
    r = ndimage.gaussian_filter(rng.normal(0, 1, shape), sigma); return r / (r.std() + 1e-9)

def campo(m, rng):
    xs = np.arange(-458.0, -352.0, RIS); zs = np.arange(98.0, 241.0, RIS)
    X, Z = np.meshgrid(xs, zs)                                          # (nz, nx)
    from matplotlib.path import Path
    pts = np.stack([X.ravel(), Z.ravel()], 1)
    n_lento = rumore(X.shape, rng, 14 / RIS); n_medio = rumore(X.shape, rng, 4 / RIS)
    n_cresta = rumore(X.shape, rng, 3.2 / RIS)
    kap = np.clip(7.0 + 4.5 * rumore(X.shape, rng, 10 / RIS), 1.6, 16.0)    # ripidità: bassa = gradoni e cenge larghe
    Fs = []
    info = []
    blocchi = [(ZOCCOLO, 1.0)] + [(p, 0.8) for p in PALE]
    for k, (p, sc) in enumerate(blocchi):
        inside = Path(np.array(p['P'])).contains_points(pts).reshape(X.shape)
        din = ndimage.distance_transform_edt(inside) * RIS; dout = ndimage.distance_transform_edt(~inside) * RIS
        th = rng.uniform(0, 2 * np.pi); c = np.array(p['P']).mean(0)
        tilt = rng.uniform(0.04, 0.10) * ((X - c[0]) * np.cos(th) + (Z - c[1]) * np.sin(th))
        alt = p['cima'] + tilt + 1.6 * n_lento + 0.6 * n_medio + np.minimum(din, 10) * (0.35 if k else 0.12) - (2.5 if k else 0.0)
        if p.get('picco'):                                              # la cima principale un po' più alta, a contorno irregolare
            px, pz, ph, pr = p['picco']
            alt = alt + ph * np.clip(1 - np.hypot(X - px, Z - pz) / (pr * (1 + 0.3 * n_medio)), 0, 1) ** 0.7
        if p.get('creste'):                                             # cresta frastagliata: torri e intagli di 4-10 m
            alt = alt + p['creste'] * np.clip(n_cresta, 0, None) * np.clip(din / 6.0, 0.35, 1.0)
        Fk = np.where(inside, alt, alt - kap * dout - 0.4 * dout ** 1.5)
        Fs.append(Fk)
        info.append((p['nome'], inside))
    # camini: intagli dal bordo verso l'interno, più profondi in alto; ognuno taglia solo il suo blocco
    # (i camini delle pale scendono fino alla cengia dello zoccolo, non dentro lo zoccolo)
    Gs = []
    for p, n_c in [(ZOCCOLO, 16)] + [(q, 6) for q in PALE]:
        G = np.zeros(X.shape)
        P = np.array(p['P'], float); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))]
        for s0 in rng.uniform(0, L[-1], n_c):
            e = int(np.searchsorted(L, s0, 'right') - 1); a = P[e]; b = P[(e + 1) % len(P)]
            u = (b - a) / np.linalg.norm(b - a); q0 = a + u * (s0 - L[e]); nin = np.array([-u[1], u[0]])
            if not Polygon(P).contains(Point(q0 + nin * 1.0)): nin = -nin
            lung = rng.uniform(5, 14); larg = rng.uniform(0.9, 1.8); prof = rng.uniform(30, 60)
            dx = X - q0[0]; dz = Z - q0[1]
            along = dx * nin[0] + dz * nin[1]; lat = -dx * nin[1] + dz * nin[0]
            w = larg * (1 + 0.08 * np.clip(along, 0, None))
            g = prof * np.exp(-(lat / w) ** 2) * np.clip(1 - along / lung, 0, 1) * (along > -6)
            G = np.maximum(G, g)
        Gs.append(G)
    F = np.max([Fk - Gk for Fk, Gk in zip(Fs, Gs)], axis=0)
    G = np.max(Gs, axis=0)
    V = rumore(X.shape, rng, 1.3 / RIS)                                 # venature verticali (stesse a ogni banco)
    B = rumore(X.shape, rng, 4.0 / RIS)
    return xs, zs, X, Z, F, G, V, B, info

def regioni(xs, zs, F, livello, tol=0.7):
    cg = contourpy.contour_generator(xs, zs, F, fill_type='OuterOffset')
    pts, offs = cg.filled(livello, 1e4)
    polys = []
    for P, o in zip(pts, offs):
        rings = [P[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4])
        if not pg.is_valid: pg = pg.buffer(0)
        pg = pg.simplify(tol, preserve_topology=True)
        if pg.area > 3.0: polys.append(pg)
    return unary_union(polys) if polys else Polygon()

def parti(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    return [x for x in getattr(g, 'geoms', []) if isinstance(x, Polygon) and x.area > 2.0]

def pulisci(g, amin=4.0):
    ps = [p for p in parti(g.buffer(0)) if p.area > amin]
    return unary_union(ps) if ps else Polygon()

# ------------------------------------------------------------------ costruzione
def run(m):
    global contourpy
    import contourpy
    mesh = Mesh()
    rng = np.random.default_rng(300)
    xs, zs, X, Z, F, G, Vn, Bn, info = campo(m, rng)
    # banchi
    livelli = [139.0]
    while livelli[-1] < F.max() - 2.0:
        livelli.append(livelli[-1] + rng.uniform(4.5, 8.0))
    R = []
    for L in livelli:
        g = regioni(xs, zs, F, L)
        if R: g = g.intersection(R[-1].buffer(-0.25, join_style=2))
        g = pulisci(g, 22.0)
        if g.is_empty: break
        R.append(g)
    livelli = livelli[:len(R)]
    Fi = lambda x, z: float(ndimage.map_coordinates(F, [[(z - zs[0]) / RIS], [(x - xs[0]) / RIS]], order=1)[0])
    def interp(A):
        return lambda x, z: float(ndimage.map_coordinates(A, [[(z - zs[0]) / RIS], [(x - xs[0]) / RIS]], order=1, mode='nearest')[0])
    Gi = interp(G); Vi = interp(Vn); Bi = interp(Bn)
    U = R[0]
    # ghiaioni attorno alla base (il terreno dentro la roccia non cambia)
    ncel, hmax, ghiaia = ghiaioni(m, U, np.random.default_rng(7))
    # pareti
    nper = collections.Counter()
    for k, Rk in enumerate(R):
        y1 = livelli[k]
        for pg in parti(Rk):
            for ring in [pg.exterior] + list(pg.interiors):
                C = np.array(ring.coords)[:-1]
                if k == 0: y0 = float(m.height(C[:, 0], C[:, 1]).min()) - SPROF
                else: y0 = livelli[k - 1]
                for i in range(len(C)):
                    j = (i + 1) % len(C)
                    mx, mz = (C[i] + C[j]) / 2
                    v = Vi(mx, mz)
                    if Gi(mx, mz) > 6.0: mt = 'terrain_rock'                      # camini in ombra
                    elif v > 2.0: mt = 'stone_dark'                               # colature scure verticali
                    elif v > 1.0: mt = 'tower_stone'
                    elif k <= 1 and Bi(mx, mz) > 0.3: mt = 'terrain_rock'         # piede delle pareti più scuro, a chiazze
                    else: mt = 'stone_light'
                    mesh.add([(C[i, 0], y0, C[i, 1]), (C[j, 0], y0, C[j, 1]), (C[j, 0], y1, C[j, 1]), (C[i, 0], y1, C[i, 1])], mt, fuori=pg)
                    nper[mt] += 1
    # cenge e sommità
    for k, Rk in enumerate(R):
        y = livelli[k]
        sup = Rk.difference(R[k + 1]) if k + 1 < len(R) else Rk
        for pg in parti(sup):
            larga = pg.area / max(pg.length, 1e-6) > 0.9
            ultimo = k + 1 >= len(R)
            def mat(cc, larga=larga, ultimo=ultimo):
                r = rng.random()
                if ultimo or larga: return 'terrain_meadow' if r < 0.4 else ('terrain_gravel' if r < 0.75 else ('moss_stone' if r < 0.85 else 'stone_light'))
                return 'stone_light' if r < 0.6 else 'terrain_gravel'
            def quota(x, z, interno, y=y, ultimo=ultimo):
                if not interno: return y
                if ultimo: return y + float(np.clip(Fi(x, z) - y, 0, 3.5)) * 0.8
                return y + rng.uniform(-0.15, 0.25)
            triangola(pg, punti_interni(pg, rng, 4.0) if (larga or ultimo) else None, quota, mat, mesh)
    # poche torri a punta sul bordo delle sommità (una sulla Cima di Mezzo)
    rt = np.random.default_rng(400)
    torri = []; top_pala = {}
    for p in PALE:
        pol = Polygon(p['P'])
        alti = [(k, pg) for k, Rk in enumerate(R) for pg in parti(Rk) if livelli[k] >= p['cima'] - 8 and pol.intersects(pg)]
        fatte = 0; prove = 0; top_pala[p['nome']] = max([livelli[k] for k, _ in alti] or [0])
        while fatte < p['torri'] and prove < 200 and alti:
            prove += 1
            k, pg = alti[rt.integers(len(alti))]
            if not pol.contains(pg.representative_point()): continue
            rr = rt.uniform(2.6, 4.2)
            q = pg.exterior.interpolate(rt.uniform(0, pg.exterior.length))
            c = pg.representative_point(); d = np.array([c.x - q.x, c.y - q.y]); d /= np.linalg.norm(d) + 1e-9
            pc = np.array([q.x, q.y]) + d * (rr + rt.uniform(0.4, 1.5))
            if not pg.buffer(-0.3).contains(Point(pc).buffer(rr)) or any(np.hypot(*(pc - t)) < 9 for t in torri): continue
            yb = livelli[k] - 0.6
            hh = torre(mesh, pc, rr, yb, rt.uniform(6.0, 9.0), rt); torri.append(pc); fatte += 1
            top_pala[p['nome']] = max(top_pala[p['nome']], hh)
    # Campanile: guglia isolata davanti, con due aghi minori
    c = np.array(CAMPANILE['c'])
    yb = float(m.height(np.array([c[0]]), np.array([c[1]]))[0]) - 3.0
    top_c = torre(mesh, c, CAMPANILE['r'], yb, CAMPANILE['cima'] - yb, rt)
    for dx, dz, rr, hh in ((6.5, 3.0, 2.4, 15.0), (-4.5, 6.5, 2.0, 11.0)):
        q = c + np.array([dx, dz]); y0 = float(m.height(np.array([q[0]]), np.array([q[1]]))[0]) - 2.5
        torre(mesh, q, rr, y0, hh, rt)
    U = unary_union([U, Point(c).buffer(CAMPANILE['r'] + 1.0), Point(c + [6.5, 3.0]).buffer(3.4), Point(c + [-4.5, 6.5]).buffer(3.0)])
    # vertici coincidenti saldati
    Pa = np.round(np.array(mesh.P), 3)
    uniq, inv = np.unique(Pa, axis=0, return_inverse=True)
    inv = inv.ravel()
    F2 = []; M2 = []
    for f, mt in zip(mesh.F, mesh.M):
        g = [int(inv[i]) for i in f]
        g = [v for k, v in enumerate(g) if v != g[k - 1]]
        if len(set(g)) >= 3: F2.append(g); M2.append(mt)
    m.add_faces('Pale_Dolomitiche', uniq.tolist(), F2, M2, False)
    ymax = float(uniq[:, 1].max()); imax = int(np.argmax(uniq[:, 1]))
    # cime: quota massima dentro ogni pianta
    sommita = [(ZOCCOLO['nome'] + ' (cengia grande, quota tipica)', float(np.median([l for l in livelli if l <= ZOCCOLO['cima'] + 4][-1:] or [0])))]
    sommita += [(k, v) for k, v in top_pala.items()] + [(CAMPANILE['nome'], top_c)]
    # alberi, sassi, pareti di roccia vecchie sotto il massiccio, vicino alle pareti e sui ghiaioni
    area = U.buffer(6.0)
    Xc, Zc = m.cell_xz()
    rem = {}; tolti = collections.Counter()
    b = area.bounds
    gx = Xc[ghiaia]; gz = Zc[ghiaia]
    b = (min(b[0], gx.min()), min(b[1], gz.min()), max(b[2], gx.max()), max(b[3], gz.max()))
    for nm in ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Animali'):
        if not m.has(nm): continue
        cs = [c for c in m.comps(nm) if c['hi'][0] > b[0] and c['lo'][0] < b[2] and c['hi'][2] > b[1] and c['lo'][2] < b[3]]
        gr = gruppi_alberi(m, nm, cs) if nm.startswith('Alberi') else [[c] for c in cs]
        fs = []
        for g in gr:
            bb = min(g, key=lambda c: c['lo'][1]); ce = (bb['lo'] + bb['hi']) / 2
            fi, fj = m.ij(ce[0], ce[2]); i = int(np.clip(np.floor(fi), 0, ghiaia.shape[0] - 1)); j = int(np.clip(np.floor(fj), 0, ghiaia.shape[1] - 1))
            if area.contains(Point(ce[0], ce[2])) or ghiaia[i, j]:
                for c in g: fs += c['faces']
                tolti[nm] += 1
        if fs: rem[nm] = fs
    m.delete(rem)
    import pickle
    pickle.dump(U.wkt, open('fase3/pale_impronta.pkl', 'wb'))              # impronta per i controlli del kit
    bx = U.bounds
    log('Pale sulla cima della montagna più alta: massiccio %.0f x %.0f m (%.0f m2 alla base) a %d banchi di roccia (%s m), %d facce; '
        'punto più alto %.1f m in (%.0f, %.0f)' % (bx[2] - bx[0], bx[3] - bx[1], U.area, len(livelli), ', '.join('%.0f' % l for l in livelli),
                                                   len(F2), ymax, uniq[imax, 0], uniq[imax, 2]))
    for nome, hq in sommita:
        log('  %s: fino a %.1f m' % (nome, hq))
    log('ghiaioni: %d celle di ghiaia, terreno rialzato fino a %.1f m ai piedi delle pareti; tolti sotto il massiccio, a meno di 6 m dalle pareti e sui ghiaioni: %s'
        % (ncel, hmax, ', '.join('%s %d' % kv for kv in tolti.most_common())))
    return LOG
