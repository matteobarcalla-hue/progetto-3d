"""Fase 2 - estensione della mappa: +150 m sul lato dell'altopiano (-Z) e +150 m sul lato corto della cascata (-X).
Il terreno nuovo continua quello del bordo (raccordo con larghezza irregolare, niente linee dritte) e diventa:
montagna rocciosa, valle, canyon con il fiume che risale; sul lato dell'altopiano un pianoro fra monti e mare.
Rifà le fasce laterali del plastico (Base_Sezione) sui nuovi bordi."""
import numpy as np, math, collections
from scipy import ndimage
import ops

LOG = []
def log(s): LOG.append(s); print('[estensione]', s)

P = 167                         # celle aggiunte per lato (150.3 m)

def fbm(shape, scales, seed, ridged=False):
    r = np.random.default_rng(seed); out = np.zeros(shape); amp = 1.0; tot = 0
    for s in scales:
        n = ndimage.gaussian_filter(r.normal(size=shape), s / 0.9, mode='reflect'); n /= (np.abs(n).max() + 1e-9)
        if ridged: n = 1 - 2 * np.abs(n)
        out += amp * n; tot += amp; amp *= 0.55
    return out / tot

def noise(shape, scale, rng):
    n = ndimage.gaussian_filter(rng.normal(size=shape), scale / 0.9, mode='reflect')
    return n / (3.0 * n.std() + 1e-9)            # circa in [-1, 1]

def rmf(shape, scales, seed, offset=1.0, gain=2.2):
    """ridged multifractal (Musgrave): creste affilate e valli, valori ~[0, 1]"""
    rng = np.random.default_rng(seed)
    sig = (offset - np.abs(noise(shape, scales[0], rng))) ** 2
    res = sig.copy(); amp = 1.0; tot = 1.0
    for sc in scales[1:]:
        w = np.clip(sig * gain, 0, 1); amp *= 0.5
        sig = (offset - np.abs(noise(shape, sc, rng))) ** 2 * w
        res += sig * amp; tot += amp
    res /= tot
    lo, hi = np.percentile(res, 2), np.percentile(res, 99.5)
    return np.clip((res - lo) / (hi - lo), 0, 1)

def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def costa(z):
    """linea di costa nel tratto nuovo (x in funzione di z, z <= -193)"""
    s = np.maximum(0.0, -193.0 - z)
    return 230.4 + 7.0 * np.sin(s / 34.0) - 0.04 * s + 3.0 * np.sin(s / 11.0) * sstep(10, 40, s)

def fiume_centro(x):
    """asse del fiume che risale nel canyon nuovo (x <= -305): z e quota dell'acqua"""
    s = np.maximum(0.0, -305.1 - x)
    z = -165.8 - 0.10 * s + 8.0 * np.sin(s / 26.0) * sstep(0, 25, s)
    y = 61.8 + 0.105 * s + 0.6 * np.sin(s / 9.0) * sstep(0, 20, s)
    return z, y

def run(m):
    NI0, NJ0 = m.H.shape
    H0 = m.H; M0 = m.M
    # --- 1) griglia allargata
    H = np.full((NI0 + P, NJ0 + P), np.nan); H[P:, P:] = H0
    M = np.full((NI0 - 1 + P, NJ0 - 1 + P), -1, int); M[P:, P:] = M0
    m.I0 -= P; m.J0 -= P
    m.H = H; m.M = M
    X, Z = m.grid_xz()
    xs0, zs0 = X[P, 0], Z[0, P]                      # bordo del terreno originale (-305.1, -193.0)
    old = np.zeros(H.shape, bool); old[P:, P:] = True
    dx = np.maximum(0, xs0 - X); dz = np.maximum(0, zs0 - Z); d = np.hypot(dx, dz)
    # --- 2) estrusione del bordo con lisciatura crescente (niente copie di dettagli fini)
    ii = np.clip(np.arange(H.shape[0]) - P, 0, NI0 - 1); jj = np.clip(np.arange(H.shape[1]) - P, 0, NJ0 - 1)
    E = H0[np.ix_(ii, jj)]
    levels = [0, 3, 8, 16, 30]
    Es = [E] + [ndimage.gaussian_filter(E, s / 0.9, mode='nearest') for s in levels[1:]]
    sig = np.clip(d * 0.35, 0, 30)
    Ef = np.zeros_like(E)
    for k in range(len(levels) - 1):
        a, b = levels[k], levels[k + 1]
        t = np.clip((sig - a) / (b - a), 0, 1) * ((sig >= a) & (sig <= b))
        sel = (sig >= a) & (sig <= b)
        Ef[sel] = (Es[k] * (1 - t) + Es[k + 1] * t)[sel]
    Ef[sig >= levels[-1]] = Es[-1][sig >= levels[-1]]
    # --- 3) forme nuove disegnate: massicci, creste, valli di drenaggio, valle e pianoro
    rr0 = np.random.default_rng(100)
    # deformazione del dominio per creste non regolari
    wx = fbm(H.shape, (50, 20), 106) * 18.0; wz = fbm(H.shape, (50, 20), 107) * 18.0
    Xw, Zw = X + wx, Z + wz
    ridged = fbm(H.shape, (60, 30, 15, 7), 101, ridged=True)
    soft = fbm(H.shape, (60, 25), 102)
    detail = fbm(H.shape, (12, 6, 3), 103)
    # maschera dei monti: dove ci sono massicci (macchie larghe) e lontano dal pianoro e dalla valle
    MASSICCI = [(-210, -290, 1.0, 70), (-60, -300, 1.0, 65), (55, -318, 0.85, 55), (150, -332, 0.7, 45),
                (-400, -245, 1.0, 75), (-390, -120, 0.8, 55), (-410, 120, 0.9, 70), (-380, 205, 0.85, 55),
                (-430, 55, 0.5, 40), (-455, -330, 0.9, 70)]
    mg = np.zeros(H.shape)
    for (cx, cz, A, r) in MASSICCI:
        mg = np.maximum(mg, A * np.exp(-((Xw - cx) ** 2 + (Zw - cz) ** 2) / (2 * r * r)))
    R = rmf(H.shape, (140, 70, 35, 17, 8), 110)
    mtn = mg * (18 + 75 * R) + 8 * mg
    mmask = sstep(0.15, 0.5, mg)
    # valli di drenaggio verso la mappa sul lato altopiano e valle grande sul lato cascata
    for (vx, wv, dep) in ((-130, 16, 18), (10, 14, 16)):
        vxz = vx + 10 * np.sin((Z + 193) / 23.0)
        mtn -= dep * np.exp(-((X - vxz) ** 2) / (2 * wv ** 2)) * sstep(-195, -215, Z)
    vz = 8 + 6 * np.sin((X + 305) / 31.0)
    vall = np.exp(-((Z - vz) ** 2) / (2 * 30 ** 2)) * (X < xs0 + 1)
    mtn = mtn * (1 - 0.9 * vall)
    floor_v = Ef + 0.13 * dx                       # fondovalle che sale piano verso -X
    D = Ef + np.maximum(mtn, 0) * sstep(0, 70, d) + 0.10 * dx * (1 - vall)
    D = np.where(vall > 0.2, D * (1 - vall) + np.minimum(D, floor_v + 3 * soft) * vall, D)
    D = np.where(D > 150, 150 + (D - 150) * 0.45, D)
    # pianoro del villaggio (~39 m) fra i monti e il mare, discesa alla scogliera
    xc = costa(Z)
    w_pian = sstep(98, 118, X) * (1 - sstep(-268, -252, Z)) * (Z < zs0 + 1)
    plateau = 39.0 + 0.8 * soft
    desc = np.interp(np.clip(xc - X, 0, 60), [0, 10, 18, 40, 60], [-0.9, 22.0, 30.0, 37.5, 39.0])
    pz = np.where(X > xc - 60, desc, plateau)
    wp = w_pian * sstep(0, 25, dz)
    D = D * (1 - wp) + pz * wp
    # scogliere sul mare oltre il pianoro: le montagne finiscono a picco sulla costa
    cliff = (Z < zs0) & (X > xc - 25) & (wp < 0.5)
    D = np.where(cliff, np.minimum(D, np.interp(np.clip(xc - X, 0, 25), [0, 4, 25], [-0.9, 18, 300])), D)
    # mare oltre la costa nuova: fondale che scende a -9
    sea = sstep(-0.5, 3.0, X - xc) * sstep(0, 25, dz)
    seab = -0.9 - np.clip(X - xc, 0, 40) * 0.35
    D = np.where(sea > 0, D * (1 - sea) + np.maximum(seab, -9.0) * sea, D)
    # --- 4) raccordo con larghezza irregolare (35-60 m) e dettaglio
    L = 35 + 25 * (0.5 + 0.5 * soft)
    w = sstep(0, 1, d / L)
    Hn = (1 - w) * Ef + w * D
    nat = ~(sea > 0.5)
    Hn = Hn + detail * (0.8 + 1.6 * mmask) * sstep(0, 45, d) * nat * (1 - 0.8 * wp)
    # --- 5) canyon con il fiume che risale
    zc, yr = fiume_centro(X)
    dc = np.abs(Z - zc)
    inx = (X < xs0 + 0.5)
    prof = np.where(dc < 2.6, yr - 0.7, np.where(dc < 3.4, yr - 0.7 + (dc - 2.6) / 0.8 * 0.75,
            np.where(dc < 4.4, yr + 0.05, np.where(dc < 6.5, yr + 0.05 + (dc - 4.4) * 0.55, yr + 1.2 + (dc - 6.5) * 2.1))))
    canyon = inx & (prof < Hn)
    wc = sstep(0, 6, xs0 - X)                         # vicino al bordo vecchio comanda l'estrusione (già col fiume)
    Hn = np.where(canyon, Hn * (1 - wc) + prof * wc, Hn)
    # sentiero lungo il fiume: ripiano a +1.5 m sulla sponda destra (verso +Z)
    H[~old] = Hn[~old]
    m.H = H; m.M = M
    # --- 6) materiali delle celle nuove (a macchie, come la tavolozza esistente)
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 0.7), 0.9); sl = np.hypot(gx, gz)
    sc = (sl[:-1, :-1] + sl[1:, :-1] + sl[:-1, 1:] + sl[1:, 1:]) / 4
    hc = (m.H[:-1, :-1] + m.H[1:, :-1] + m.H[:-1, 1:] + m.H[1:, 1:]) / 4
    Xc, Zc = m.cell_xz()
    newc = np.ones(M.shape, bool); newc[P:, P:] = False
    rr = np.random.default_rng(104)
    # macchie organiche (rumore liscio a 15-30 m) per scegliere le varianti
    v1 = 0.5 + 0.5 * fbm(M.shape, (22, 9), 108) / 0.6; v2 = 0.5 + 0.5 * fbm(M.shape, (16, 7), 109) / 0.6
    v1 = np.clip(v1, 0, 1); v2 = np.clip(v2, 0, 1)
    edge = ndimage.gaussian_filter(rr.normal(size=M.shape), 1.0)
    forest = fbm(M.shape, (30, 12), 105) + 0.1 * edge
    idx = m.mat_index
    out = np.full(M.shape, idx('terrain_grass'))
    s_ = sc + 0.12 * edge
    out[(s_ <= 0.55) & (v1 < 0.45)] = idx('terrain_meadow')
    out[(s_ <= 0.8) & (forest > -0.15) & (hc > 8) & (hc < 125)] = idx('terrain_forest')
    alp = (hc > 140) & (s_ <= 0.55)
    out[alp & (v2 < 0.5)] = idx('terrain_gravel'); out[alp & (v2 >= 0.5) & (v2 < 0.75)] = idx('moss_stone')
    mid = (s_ > 0.55) & (s_ <= 0.95) & ~((s_ <= 0.8) & (forest > -0.15) & (hc > 8) & (hc < 125))
    out[mid] = idx('terrain_meadow')
    out[mid & (v2 < 0.3)] = idx('terrain_gravel'); out[mid & (v2 >= 0.3) & (v2 < 0.5)] = idx('moss_stone'); out[mid & (v2 >= 0.5) & (v2 < 0.7)] = idx('terrain_rock')
    cl = s_ > 0.95
    out[cl & (v1 < 0.55)] = idx('terrain_rock'); out[cl & (v1 >= 0.55) & (v1 < 0.85)] = idx('stone_dark'); out[cl & (v1 >= 0.85)] = idx('moss_stone')
    # pianoro: prato e prato fiorito
    pianoro = (Xc > 105) & (Xc < costa(Zc) - 12) & (Zc < -193) & (Zc > -262) & (s_ < 0.35)
    out[pianoro] = np.where(v1[pianoro] < 0.5, idx('terrain_grass'), idx('terrain_meadow'))
    # mare e spiaggia
    out[hc < -4.5] = np.where(v2[hc < -4.5] < 0.82, idx('sand'), idx('stone_dark'))
    out[(hc >= -4.5) & (hc < 1.2) & (Xc > 150)] = idx('sand')
    # canyon: letto, strisce d'argilla, sponde
    zcc, yrc = fiume_centro(Xc); dcc = np.abs(Zc - zcc); cx = Xc < xs0
    out[cx & (dcc < 3.3)] = idx('soil_dark')
    out[cx & (dcc >= 3.3) & (dcc < 4.5)] = idx('terrain_clay')
    out[cx & (dcc >= 4.5) & (dcc < 6.3)] = np.where(v1[cx & (dcc >= 4.5) & (dcc < 6.3)] < 0.5, idx('terrain_gravel'), idx('moss_stone'))
    M[newc] = out[newc]
    # bordo del raccordo: i materiali delle prime celle nuove riprendono quelli del bordo vecchio a macchie (niente linea)
    near = newc & (ndimage.distance_transform_edt(newc) < 4 + 3 * (v1 > 0.5))
    ic = np.clip(np.arange(M.shape[0]) - P, 0, M0.shape[0] - 1); jc = np.clip(np.arange(M.shape[1]) - P, 0, M0.shape[1] - 1)
    Mext = M0[np.ix_(ic, jc)]
    ok_ext = np.isin(np.array(m.mats + ['<buco>'])[Mext], ['terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_rock', 'stone_dark', 'moss_stone', 'terrain_gravel', 'sand'])
    M[near & ok_ext] = Mext[near & ok_ext]
    m.M = M
    log('griglia del terreno da %dx%d a %dx%d vertici: X %.1f..%.1f, Z %.1f..%.1f; celle nuove %d (%.0f m²)'
        % (NI0, NJ0, H.shape[0], H.shape[1], X.min(), X.max(), Z.min(), Z.max(), int(newc.sum()), newc.sum() * 0.81))
    nh = H[~old]
    log('quote nuove: min %.1f, max %.1f m; raccordo con il bordo largo 35-60 m (irregolare); canyon del fiume lungo %.0f m dalla quota %.1f a %.1f'
        % (nh.min(), nh.max(), xs0 - X.min(), fiume_centro(np.array([xs0]))[1][0], fiume_centro(np.array([X.min()]))[1][0]))
    cnt = collections.Counter(np.array(m.mats + ['<buco>'])[M[newc]])
    log('materiali delle celle nuove: ' + ', '.join('%s %d' % kv for kv in cnt.most_common(10)))
    acqua_fiume(m, xs0, X.min())
    fasce(m, xs0, zs0)
    return LOG

def acqua_fiume(m, xs0, xmin):
    """superficie dell'acqua nel canyon nuovo: nastro di quad a 3 punti per sezione"""
    xs = np.arange(xs0 + 1.3, xmin - 0.01, -1.8)
    if xs[-1] > xmin + 0.01: xs = np.r_[xs, xmin]
    zc, yr = fiume_centro(xs)
    Pts = []; F = []
    for k, (x, z, y) in enumerate(zip(xs, zc, yr)):
        Pts += [(x, y, z - 3.4), (x, y, z), (x, y, z + 3.4)]
        if k:
            b = 3 * (k - 1)
            F += [[b, b + 3, b + 4, b + 1], [b + 1, b + 4, b + 5, b + 2]]
    # normali verso l'alto
    Pa = np.array(Pts)
    for f in F:
        q = Pa[f]; n = np.cross(q[1] - q[0], q[2] - q[0])
        if n[1] < 0: f.reverse()
    m.add_faces('Acqua', Pts, F, 'water', False)
    log('acqua del fiume nel canyon nuovo: %d facce (largh. 6.8 m, pendenza media 10.5%%)' % len(F))

def fasce(m, xs0, zs0):
    """fasce laterali del plastico: tolgo quelle dei bordi interni e del lato mare, le rifaccio sui bordi nuovi"""
    b = m.obj('Base_Sezione'); V = m.V
    keep = []; rem = 0
    xmax = 271.8
    for f, mt, sm in zip(b['faces'], b['mats'], b['smooth']):
        Q = V[np.array(f) - 1]
        on_x0 = np.all(np.abs(Q[:, 0] - xs0) < 0.01); on_z0 = np.all(np.abs(Q[:, 2] - zs0) < 0.01)
        on_xm = np.all(np.abs(Q[:, 0] - xmax) < 0.01)
        sea_side = np.all(Q[:, 0] > 243.0) and np.all(np.abs(Q[:, 2] - 239.0) < 0.01)
        if on_x0 or on_z0 or on_xm or sea_side or mt == 'water_deep':
            rem += 1; continue
        keep.append((f, mt, sm))
    b['faces'] = [k[0] for k in keep]; b['mats'] = [k[1] for k in keep]; b['smooth'] = [k[2] for k in keep]
    m.invalidate('Base_Sezione')
    X, Z = m.grid_xz(); H = m.H
    Pts = []; F = []; Mt = []
    def edge(ptsx, ptsz, hs, out):
        for k in range(len(hs) - 1):
            x0, z0, h0 = ptsx[k], ptsz[k], hs[k]; x1, z1, h1 = ptsx[k + 1], ptsz[k + 1], hs[k + 1]
            if h0 < -0.85 and h1 < -0.85: continue           # tratto di mare: niente fascia (il mare continua)
            base = len(Pts)
            Pts.extend([(x0, h0, z0), (x1, h1, z1), (x1, h1 - 2.5, z1), (x0, h0 - 2.5, z0), (x1, -14.0, z1), (x0, -14.0, z0)])
            for f, mt in (([0, 1, 2, 3], 'soil_dark'), ([3, 2, 4, 5], 'stone_dark')):
                q = np.array([Pts[base + i] for i in f]); n = np.cross(q[1] - q[0], q[2] - q[0])
                ff = [base + i for i in f]
                if np.dot(n, out) < 0: ff = ff[::-1]
                F.append(ff); Mt.append(mt)
    # bordo -X nuovo (tutta la lunghezza), bordo -Z nuovo, bordo +Z prolungato verso -X
    edge(X[0, :], Z[0, :], H[0, :], np.array([-1.0, 0, 0]))
    edge(X[:, 0], Z[:, 0], H[:, 0], np.array([0, 0, -1.0]))
    jl = H.shape[1] - 1
    edge(X[:P + 1, jl], Z[:P + 1, jl], H[:P + 1, jl], np.array([0, 0, 1.0]))
    m.add_faces('Base_Sezione', Pts, F, Mt, False)
    log('fasce laterali del plastico: %d facce tolte (bordi diventati interni e lato mare), %d nuove sui bordi nuovi' % (rem, len(F)))
