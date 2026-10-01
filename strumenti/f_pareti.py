"""Pareti rocciose a strati: lastre di roccia low-poly incastrate nelle pareti ripide dei promontori e dei rilievi.
Le lastre seguono le curve di livello (strati orizzontali ondulati), sporgono 0.3-0.9 m e sono incassate 1.4-2 m nella roccia."""
import numpy as np, math, collections
from scipy import ndimage
from scipy.spatial import cKDTree
import contourpy
from occupancy import occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[pareti]', s)

ZONES = [('promontorio sul mare (alto a sinistra)', 170, 275, -216, -85),
         ('sperone della rocca e fianchi della fortezza', -110, 140, -85, 90),
         ('montagna della miniera e vetta', -306, -125, 25, 240),
         ('collina del teatro e scogliere (alto a destra)', 165, 275, 95, 240),
         ('scogliere sul mare fra porto e teatro', 185, 275, -85, 95),
         ('montagne della cascata e del canyon', -306, -125, -216, 25)]
NATURAL = ('terrain_rock', 'stone_dark', 'moss_stone', 'terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_gravel', 'stone_light')
SOGLIA_PENDENZA = 1.7      # pendenza minima delle pareti con strati (1.7 = ~60 gradi)
SALTO_STRATI = 22          # percentuale di strati saltati per zona
BANDS = (('terrain_rock', 0.62), ('stone_dark', 0.32), ('stone_light', 0.02), ('moss_stone', 0.04))

def fbm(shape, scales, seed):
    r = np.random.default_rng(seed); out = np.zeros(shape); amp = 1.0; tot = 0
    for s in scales:
        n = ndimage.gaussian_filter(r.normal(size=shape), s / 0.9); n /= (np.abs(n).max() + 1e-9)
        out += amp * n; tot += amp; amp *= 0.55
    return out / tot

def band_mat(level, x, z, rng):
    h = hash((int(level), int(math.floor(x / 35.0)), int(math.floor(z / 35.0)))) % 1000 / 1000.0
    acc = 0
    for name, w in BANDS:
        acc += w
        if h < acc: base = name; break
    else: base = BANDS[0][0]
    if rng.random() < 0.15:
        base = BANDS[rng.integers(len(BANDS))][0]
    return base

def run(m):
    X, Z = m.grid_xz(); Xc, Zc = m.cell_xz()
    occ = occupancy_fine(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume'))
    names = np.array(m.mats + ['<buco>'])[m.M]
    prot = occ | np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', 'soil_dark', 'terrain_field', 'crop_green', 'sand', 'terrain_clay', '<buco>'])
    prot = ndimage.binary_dilation(prot, iterations=2)
    natural_c = np.isin(names, NATURAL)
    # celle -> vertici
    pv = np.zeros(m.H.shape, bool); nv = np.zeros(m.H.shape, bool)
    for di in (0, 1):
        for dj in (0, 1):
            pv[di:di + prot.shape[0], dj:dj + prot.shape[1]] |= prot
            nv[di:di + prot.shape[0], dj:dj + prot.shape[1]] |= natural_c
    zone = np.zeros(m.H.shape)
    for _, x0, x1, z0, z1 in ZONES:
        zone = np.maximum(zone, ((X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)).astype(float))
    zsoft = ndimage.gaussian_filter(zone, 6.0) * zone
    Hs = ndimage.gaussian_filter(m.H, 0.8)
    gx, gz = np.gradient(Hs, 0.9); slope = np.hypot(gx, gz)
    spz = ([zz for zz in ZONES if zz[0].startswith('sperone')] + [('nessuno', 1e6, 1e6 + 1, 1e6, 1e6 + 1)])[0]
    in_sp = (X >= spz[1]) & (X <= spz[2]) & (Z >= spz[3]) & (Z <= spz[4])
    ok = (zone > 0) & (slope > np.where(in_sp, 1.05, SOGLIA_PENDENZA)) & ~pv & nv & (m.H > -0.6)
    ok = ndimage.binary_opening(ok, iterations=1)
    hb = 1.6 + 0.5 * (fbm(m.H.shape, (40,), 51) + 1)            # altezza degli strati 1.6-2.6 m
    # strati inclinati (immersione di 6-12 gradi, direzione diversa per zona), raccordati fra le zone
    rz = np.random.default_rng(53); num = np.zeros(m.H.shape); den = np.zeros(m.H.shape) + 1e-6
    for _, x0, x1, z0, z1 in ZONES:
        wz = ndimage.gaussian_filter(((X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)).astype(float), 10.0 / 0.9)
        az = rz.uniform(0, 2 * math.pi); tg = math.tan(math.radians(rz.uniform(6, 12)))
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        num += wz * tg * ((X - cx) * math.cos(az) + (Z - cz) * math.sin(az)); den += wz
    dip = num / den
    phase = 2.5 * fbm(m.H.shape, (25, 12), 52)                   # ondulazione degli strati
    q = np.ma.masked_array((m.H + phase + dip) / hb, mask=~ok)
    gen = contourpy.contour_generator(x=X, y=Z, z=q, line_type='Separate')
    # alberi (per non infilzarli)
    tp = []
    for nm in ('Alberi', 'Alberi_Nuovi', 'Salice', 'Quercia_Gigante'):
        if m.has(nm):
            tp += [((c['lo'][0] + c['hi'][0]) / 2, (c['lo'][2] + c['hi'][2]) / 2) for c in m.comps(nm)]
    ttree = cKDTree(np.array(tp)) if tp else None
    rng = np.random.default_rng(61)
    P_all = []; F_all = []; M_all = []
    stats = collections.Counter()
    def cell_prot(x, z):
        i, j = m.ij(x, z); i = np.clip(np.floor(i).astype(int), 0, prot.shape[0] - 1); j = np.clip(np.floor(j).astype(int), 0, prot.shape[1] - 1)
        return prot[i, j]
    def sample(A, x, z):
        i, j = m.ij(x, z); i = np.clip(np.round(i).astype(int), 0, A.shape[0] - 1); j = np.clip(np.round(j).astype(int), 0, A.shape[1] - 1)
        return A[i, j]
    def noise1(n, k, seed):
        r = np.random.default_rng(seed); v = ndimage.gaussian_filter1d(r.normal(size=n + 8), k, mode='nearest')[4:4 + n]
        return v / (np.abs(v).max() + 1e-9)
    def emit(st, mat, top):
        """st: lista di stazioni (5 vertici ciascuna: bb, bt, ft, fm, fb) -> fascia continua con testate"""
        S = np.array(st, float); ns = len(st); base = len(P_all)
        P_all.extend(S.reshape(-1, 3).tolist())
        L = [([5 * i + 1, 5 * i + 6, 5 * i + 7, 5 * i + 2], top, i) for i in range(ns - 1)]
        for i in range(ns - 1):
            L += [([5 * i + 2, 5 * i + 7, 5 * i + 8, 5 * i + 3], mat, i), ([5 * i + 3, 5 * i + 8, 5 * i + 9, 5 * i + 4], mat, i),
                  ([5 * i + 4, 5 * i + 9, 5 * i + 5, 5 * i + 0], mat, i), ([5 * i + 0, 5 * i + 5, 5 * i + 6, 5 * i + 1], mat, i)]
        d_ = S[-1].mean(0) - S[0].mean(0)
        L += [([0, 1, 2, 3, 4], mat, -1), ([5 * (ns - 1) + k for k in range(4, -1, -1)], mat, -2)]
        Pl = S.reshape(-1, 3)
        for f, mt, i in L:
            Q = Pl[f]; nn = np.zeros(3)
            for t in range(len(Q)): nn += np.cross(Q[t], Q[(t + 1) % len(Q)])
            if i >= 0: ref = Q.mean(0) - (S[i].mean(0) + S[i + 1].mean(0)) / 2
            else: ref = -d_ if i == -1 else d_
            if np.dot(nn, ref) < 0: f = f[::-1]
            F_all.append([base + v for v in f]); M_all.append(mt)
    kmin = int(np.floor(q.min())); kmax = int(np.ceil(q.max()))
    seed = 1000
    for level in range(kmin, kmax + 1):
        for line in gen.lines(level):
            if len(line) < 2: continue
            seg = np.hypot(*np.diff(line, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1]
            if L < 3.0: continue
            ns = max(2, int(L / 1.7) + 1)
            sv = np.linspace(0, L, ns) + np.r_[0, rng.uniform(-0.35, 0.35, ns - 2), 0]
            Px = np.interp(sv, cum, line[:, 0]); Pz = np.interp(sv, cum, line[:, 1])
            Py = m.height_tri(Px, Pz)
            seed += 1
            pn = noise1(ns, 2.0, seed); hn = noise1(ns, 3.0, seed + 7919)
            # tangenti e normali verso valle
            T = np.gradient(np.stack([Px, Pz], 1), axis=0); T /= (np.linalg.norm(T, axis=1)[:, None] + 1e-9)
            N = np.stack([-T[:, 1], T[:, 0]], 1)
            gxs = sample(gx, Px, Pz); gzs = sample(gz, Px, Pz)
            flip = (N[:, 0] * gxs + N[:, 1] * gzs) > 0
            N[flip] *= -1
            i = 0
            while i < ns - 1:
                run = int(rng.integers(2, 6))          # 2-5 segmenti (3.4-8.5 m)
                j = min(ns - 1, i + run)
                x0, z0 = Px[i], Pz[i]
                sl = float(sample(slope, x0, z0)); zs = float(sample(zsoft, x0, z0))
                reg = hash((level, int(x0 // 35), int(z0 // 35))) % 100
                skip = 0.12 if sl > 1.5 else (0.3 if sl > 1.1 else 0.5)
                if reg < SALTO_STRATI or rng.random() < skip or rng.random() > zs:
                    stats['saltate'] += 1; i = j + (0 if rng.random() < 0.5 else 1); continue
                hbl = float(sample(hb, x0, z0)); h0 = hbl * rng.uniform(0.55, 0.95)
                p0 = rng.uniform(0.35, 0.8); ap = rng.uniform(0.1, 0.3); d = rng.uniform(1.4, 2.0)
                if sample(in_sp, x0, z0): p0 += 0.35; h0 *= 1.2; d += 0.6
                dy = rng.uniform(-0.25, 0.25); ridge = rng.uniform(0.06, 0.25); cham = rng.uniform(0.08, 0.25)
                st = []; bad = None
                for k in range(i, j + 1):
                    E = np.array([Px[k], Pz[k]]); n = N[k]; yE = Py[k] + dy
                    h = h0 * (1 + 0.15 * hn[k]); p = max(0.05, p0 + ap * pn[k])
                    bb = E - d * n
                    q5 = [(bb[0], yE - h, bb[1]), (bb[0], yE + 0.05, bb[1]),
                          (E[0] + (p - cham) * n[0], yE - 0.06, E[1] + (p - cham) * n[1]),
                          (E[0] + (p + ridge) * n[0], yE - h * 0.45, E[1] + (p + ridge) * n[1]),
                          (E[0] + p * n[0], yE - h, E[1] + p * n[1])]
                    Q = np.array(q5)
                    if Q[1, 1] > m.height_tri(Q[1, 0], Q[1, 2]) - 0.1: bad = 'retro scoperto'
                    elif np.any(cell_prot(Q[:, 0], Q[:, 2])): bad = 'zona protetta'
                    elif ttree is not None and ttree.query_ball_point(E, 0.9): bad = 'albero vicino'
                    if bad: break
                    st.append(q5)
                if bad: stats[bad] += 1
                if len(st) >= 2:
                    bm = band_mat(level, x0, z0, rng)
                    top = bm
                    if sl < 1.6:
                        r_ = rng.random(); top = 'moss_stone' if r_ < 0.35 else ('terrain_grass' if r_ < 0.45 else bm)
                    emit(st, bm, top); stats['lastre'] += 1; stats['mat_' + bm] += 1
                i = j + (0 if rng.random() < 0.5 else 1)
    if F_all:
        m.add_faces('Pareti_Rocciose', P_all, F_all, M_all, False, after='Rocce')
    log('pareti a strati: %d fasce di roccia (%d facce, %d vertici) incastrate nelle pareti ripide di %d zone; oggetto nuovo Pareti_Rocciose'
        % (stats['lastre'], len(F_all), len(P_all), len(ZONES)))
    log('materiali delle lastre: ' + ', '.join('%s %d' % (k[4:], v) for k, v in sorted(stats.items()) if k.startswith('mat_'))
        + '; scartate: %d retro non incassato, %d vicino a strade/edifici, %d vicino ad alberi' % (stats['retro scoperto'], stats['zona protetta'], stats['albero vicino']))
    return LOG
