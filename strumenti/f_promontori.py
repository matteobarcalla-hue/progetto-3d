"""Promontori più realistici: rugosità, cenge, varietà di roccia e massi ai piedi delle pareti."""
import numpy as np, math, collections
from scipy import ndimage
import ops
from occupancy import occupancy, occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[promontori]', s)

def fbm(shape, scales, seed, ridged=False):
    r = np.random.default_rng(seed); out = np.zeros(shape); amp = 1.0; tot = 0
    for s in scales:
        n = ndimage.gaussian_filter(r.normal(size=shape), s / 0.9)
        n /= (np.abs(n).max() + 1e-9)
        if ridged: n = 1 - 2 * np.abs(n)
        out += amp * n; tot += amp; amp *= 0.55
    return out / tot

from f_pareti import ZONES   # stesse zone delle pareti a strati (6 rilievi)

def run(m):
    H0 = m.H.copy()
    X, Z = m.grid_xz(); Xc, Zc = m.cell_xz()
    occ = occupancy_fine(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume'))
    names = np.array(m.mats + ['<buco>'])[m.M]
    prot = occ | np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', 'soil_dark', 'terrain_field', 'crop_green', 'sand', '<buco>'])
    prot = ndimage.binary_dilation(prot, iterations=3)
    pv = np.zeros(m.H.shape, bool)
    pv[:-1, :-1] |= prot; pv[1:, :-1] |= prot; pv[:-1, 1:] |= prot; pv[1:, 1:] |= prot
    free = ndimage.gaussian_filter((~pv).astype(float), 1.2)
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 1.0), 0.9); slope = np.hypot(gx, gz)
    ridged = fbm(m.H.shape, (14, 7, 3.5), 21, ridged=True)
    base = fbm(m.H.shape, (20, 9), 22)
    strata_ph = fbm(m.H.shape, (30,), 23) * 1.2
    tot_cells = 0
    zone_all = np.zeros(m.H.shape)
    for name, x0, x1, z0, z1 in ZONES:
        zone_all = np.maximum(zone_all, ((X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)).astype(float))
    zone_all = ndimage.gaussian_filter(zone_all, 3.0)
    natv = np.zeros(m.H.shape, bool)
    names0 = np.array(m.mats + ['<buco>'])[m.M]
    natc = np.isin(names0, ['terrain_rock', 'stone_dark', 'moss_stone', 'terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_gravel', 'stone_light'])
    for di in (0, 1):
        for dj in (0, 1):
            natv[di:di + natc.shape[0], dj:dj + natc.shape[1]] |= natc
    # 1) sfaccettature: il pendio roccioso diventa un mosaico di piani inclinati (celle di Voronoi di ~8 m)
    rng = np.random.default_rng(24)
    gxs = np.arange(X.min(), X.max(), 8.0); gzs = np.arange(Z.min(), Z.max(), 8.0)
    SX, SZ = np.meshgrid(gxs, gzs, indexing='ij')
    seeds = np.stack([SX.ravel() + rng.uniform(-3, 3, SX.size), SZ.ravel() + rng.uniform(-3, 3, SZ.size)], 1)
    from scipy.spatial import cKDTree
    _, reg = cKDTree(seeds).query(np.stack([X.ravel(), Z.ravel()], 1))
    reg = reg.reshape(X.shape)
    steep_v = np.clip((slope - 0.5) / 0.4, 0, 1)
    sp = ([zz for zz in ZONES if zz[0].startswith('sperone')] + [('nessuno', 1e6, 1e6 + 1, 1e6, 1e6 + 1)])[0]
    forza = 1.0 + 0.7 * ndimage.gaussian_filter(((X >= sp[1]) & (X <= sp[2]) & (Z >= sp[3]) & (Z <= sp[4])).astype(float), 4.0)
    wv = zone_all * free * steep_v * natv * (~pv)
    act = wv > 0.05
    lab = reg[act]; xs = X[act]; zs = Z[act]; hs = m.H[act]
    nreg = len(seeds)
    cnt = np.bincount(lab, minlength=nreg).astype(float)
    def bs(v): return np.bincount(lab, weights=v, minlength=nreg)
    mx, mz, mh = bs(xs) / np.maximum(cnt, 1), bs(zs) / np.maximum(cnt, 1), bs(hs) / np.maximum(cnt, 1)
    dx = xs - mx[lab]; dz = zs - mz[lab]; dh = hs - mh[lab]
    sxx, szz, sxz, sxh, szh = bs(dx * dx), bs(dz * dz), bs(dx * dz), bs(dx * dh), bs(dz * dh)
    det = sxx * szz - sxz ** 2
    ok_r = (cnt >= 12) & (det > 1e-6)
    ga = np.where(ok_r, (sxh * szz - szh * sxz) / np.where(det > 1e-6, det, 1), 0)
    gb = np.where(ok_r, (szh * sxx - sxh * sxz) / np.where(det > 1e-6, det, 1), 0)
    fz = forza[act]
    ga += rng.normal(0, 0.10, nreg); gb += rng.normal(0, 0.10, nreg)
    tn_a = rng.normal(0, 0.07, nreg); tn_b = rng.normal(0, 0.07, nreg)
    plane = mh[lab] + (ga[lab] + tn_a[lab] * (fz - 1) / 0.7) * dx + (gb[lab] + tn_b[lab] * (fz - 1) / 0.7) * dz + rng.normal(0, 0.25, nreg)[lab] * fz
    d = np.clip(plane - hs, -1.4 * fz, 1.4 * fz) * ok_r[lab]
    H1 = m.H.copy(); H1[act] = hs + d * wv[act]
    m.H = H1
    log('sfaccettature rocciose: %d piani di roccia (celle di ~8 m) su %d vertici; spostamento medio %.2f m, massimo %.2f m'
        % (int(ok_r[np.unique(lab)].sum()), int(act.sum()), float(np.abs(d * wv[act]).mean()), float(np.abs(d * wv[act]).max())))
    # 2) rugosità leggera a creste (fino a ~0.4 m) e cenge poco marcate
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 1.0), 0.9); slope = np.hypot(gx, gz)
    for name, x0, x1, z0, z1 in ZONES:
        zone = ((X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)).astype(float)
        zone = ndimage.gaussian_filter(zone, 3.0)
        steep = np.clip((slope - 0.45) / 0.8, 0, 1)
        w = zone * free * steep * natv * (~pv)
        dH = w * (0.75 * ridged + 0.35 * base) * 0.4
        L = 3.2
        q = (m.H + strata_ph * L) / L
        ledge = (q - np.round(q)) * L
        dH += -w * 0.12 * ledge
        m.H = m.H + dH
        tot_cells += int((w > 0.1).sum())
    # 3) materiali di roccia per faccetta (macchie coerenti, non a puntini)
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 0.7), 0.9); slope = np.hypot(gx, gz)
    sc = (slope[:-1, :-1] + slope[1:, :-1] + slope[:-1, 1:] + slope[1:, 1:]) / 4
    regc = reg[:-1, :-1]
    rr = np.random.default_rng(33).random(nreg); rr2 = np.random.default_rng(34).random(nreg)
    fr = rr[regc]; fr2 = rr2[regc]
    edge = ndimage.gaussian_filter(np.random.default_rng(35).normal(size=m.M.shape), 1.0)
    inz = np.zeros(m.M.shape, bool)
    for name, x0, x1, z0, z1 in ZONES:
        inz |= (Xc >= x0) & (Xc <= x1) & (Zc >= z0) & (Zc <= z1)
    names = np.array(m.mats + ['<buco>'])[m.M]
    natural = np.isin(names, ['terrain_rock', 'stone_dark', 'moss_stone', 'terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_gravel', 'stone_light'])
    sel = inz & natural & ~prot & (m.M >= 0)
    cliff = sel & (sc + 0.15 * edge > 0.95)
    m.M[cliff & (fr < 0.55)] = m.mat_index('terrain_rock')
    m.M[cliff & (fr >= 0.55) & (fr < 0.85)] = m.mat_index('stone_dark')
    m.M[cliff & (fr >= 0.85)] = m.mat_index('moss_stone')
    mid = sel & ~cliff & (sc + 0.15 * edge > 0.6)
    m.M[mid & (fr2 < 0.12)] = m.mat_index('terrain_gravel')
    m.M[mid & (fr2 >= 0.12) & (fr2 < 0.24)] = m.mat_index('moss_stone')
    m.M[mid & (fr2 >= 0.24) & (fr2 < 0.36)] = m.mat_index('terrain_rock')
    ledge_c = sel & (sc < 0.35) & ndimage.binary_dilation(cliff, iterations=2) & (fr2 > 0.5)
    m.M[ledge_c] = m.mat_index('terrain_grass')
    log('rugosità leggera e cenge su %d vertici ripidi in %d zone; materiali per faccetta: %d celle di parete (roccia/pietra scura/muschio), %d di pendio (ghiaione/muschio/roccia), %d cenge erbose' % (tot_cells, len(ZONES), int(cliff.sum()), int(mid.sum()), int(ledge_c.sum())))
    # massi ai piedi delle pareti: copie dei massi esistenti (Rocce) in un oggetto nuovo
    rocks = [c for c in m.comps('Rocce') if 20 <= len(c['faces']) <= 80]
    rng = np.random.default_rng(41)
    foot = sel & (sc > 0.25) & (sc < 0.55) & ndimage.binary_dilation(cliff, iterations=3) & ~ndimage.binary_dilation(prot, iterations=2)
    cand = np.argwhere(foot)
    rng.shuffle(cand)
    placed = []; P_all = []; F_all = []; M_all = []
    o = m.obj('Rocce')
    for (i, j) in cand:
        if len(placed) >= 240: break
        x, z = Xc[i, j], Zc[i, j]
        if placed and np.min(np.hypot(np.array(placed)[:, 0] - x, np.array(placed)[:, 1] - z)) < 3.0: continue
        c = rocks[rng.integers(len(rocks))]
        P = m.V[c['verts']].copy(); ce = (P.min(0) + P.max(0)) / 2
        s = rng.uniform(0.7, 1.6); ang = rng.uniform(0, 2 * math.pi)
        loc = (P - ce) * s; ca, sa = math.cos(ang), math.sin(ang)
        loc = np.stack([loc[:, 0] * ca + loc[:, 2] * sa, loc[:, 1], -loc[:, 0] * sa + loc[:, 2] * ca], 1)
        lo = loc.min(0); hi = loc.max(0)
        gy = ops.footprint_min(m, np.array([x + lo[0], 0, z + lo[2]]), np.array([x + hi[0], 0, z + hi[2]]), 3)
        Q = loc + [x, gy - lo[1] - (hi[1] - lo[1]) * 0.3, z]
        rm = {v: k for k, v in enumerate(c['verts'])}; b = len(P_all)
        P_all += [tuple(q) for q in Q]
        F_all += [[b + rm[v - 1] for v in o['faces'][fi]] for fi in c['faces']]
        M_all += [o['mats'][fi] for fi in c['faces']]
        placed.append((x, z))
    if F_all: m.add_faces('Rocce_Promontori', P_all, F_all, M_all, False, after='Rocce')
    log('massi e ghiaioni ai piedi delle pareti: %d copie dei massi esistenti (%d facce, oggetto nuovo Rocce_Promontori)' % (len(placed), len(F_all)))
    # affioramenti rocciosi sui pendii medi (gruppi di 2-4 massi grandi, sepolti per metà)
    cand2 = np.argwhere(sel & (sc > 0.55) & (sc < 1.6) & ~ndimage.binary_dilation(prot, iterations=3))
    rng.shuffle(cand2)
    tp = []
    for nm in ('Alberi', 'Alberi_Nuovi'):
        tp += [((c['lo'][0] + c['hi'][0]) / 2, (c['lo'][2] + c['hi'][2]) / 2) for c in m.comps(nm)]
    from scipy.spatial import cKDTree
    ttree = cKDTree(np.array(tp))
    rocks_lp = [c for c in rocks if len(c['faces']) <= 40] or rocks
    P2 = []; F2 = []; M2 = []; groups = []
    for (i, j) in cand2:
        if len(groups) >= 300: break
        x, z = Xc[i, j], Zc[i, j]
        fzc = float(forza[i, j])
        if groups and np.min(np.hypot(np.array(groups)[:, 0] - x, np.array(groups)[:, 1] - z)) < 11.0 / fzc: continue
        if ttree.query_ball_point((x, z), 2.5): continue
        gxl, gzl = gx[i, j], gz[i, j]; gl = math.hypot(gxl, gzl) + 1e-9
        ux, uz = -gzl / gl, gxl / gl          # lungo la curva di livello
        k = int(rng.integers(2, 5))
        for t in range(k):
            c = rocks_lp[rng.integers(len(rocks_lp))]
            P = m.V[c['verts']].copy(); ce = (P.min(0) + P.max(0)) / 2
            s_ = rng.uniform(1.4, 3.0) * fzc ** 1.5 / max(1e-3, (P.max(0) - P.min(0))[[0, 2]].max())
            ang = rng.uniform(0, 2 * math.pi); ca, sa = math.cos(ang), math.sin(ang)
            loc = (P - ce) * s_ * rng.uniform(1.0, 1.8)
            loc = np.stack([loc[:, 0] * ca + loc[:, 2] * sa, loc[:, 1] * rng.uniform(0.45, 0.7), -loc[:, 0] * sa + loc[:, 2] * ca], 1)
            off = rng.uniform(-2.5, 2.5); px, pz = x + ux * off + rng.uniform(-0.6, 0.6), z + uz * off + rng.uniform(-0.6, 0.6)
            lo = loc.min(0); hi = loc.max(0)
            gy = float(m.height_tri(px, pz))
            Q = loc + [px, gy - lo[1] - (hi[1] - lo[1]) * rng.uniform(0.6, 0.75), pz]
            rm = {v: kk for kk, v in enumerate(c['verts'])}; b0 = len(P2)
            P2 += [tuple(q) for q in Q]
            F2 += [[b0 + rm[v - 1] for v in o['faces'][fi]] for fi in c['faces']]
            mr = 'terrain_rock' if rng.random() < 0.7 else 'stone_dark'
            M2 += [mr for fi in c['faces']]
        groups.append((x, z))
    if F2: m.add_faces('Rocce_Promontori', P2, F2, M2, False)
    log('affioramenti rocciosi sui pendii medi: %d gruppi di massi grandi semi-sepolti (%d facce, stesso oggetto Rocce_Promontori)' % (len(groups), len(F2)))
    n = ops.follow_terrain(m, H0, names=tuple(nm for nm in ops.GROUND_OBJS if nm != 'Rocce_Promontori'))
    log('elementi a terra (alberi, rocce, siepi, animali) riallineati alla nuova quota: %d' % n)
    return LOG
