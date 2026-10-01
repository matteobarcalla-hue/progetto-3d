"""Fase 2 - mare fino all'orizzonte: superficie del mare e fondale proseguono per ~2,5 km oltre i bordi del plastico
(lato mare e lati corti verso il mare); schiuma lungo la costa nuova."""
import numpy as np, math
import contourpy

LOG = []
def log(s): LOG.append(s); print('[mare]', s)

Y_MARE = -0.88; Y_FONDO = -9.0; LONTANO = 2600.0

def quads_grid(x0, x1, z0, z1, y, nx, nz):
    xs = np.linspace(x0, x1, nx + 1); zs = np.linspace(z0, z1, nz + 1)
    P = [(x, y, z) for x in xs for z in zs]; F = []
    for i in range(nx):
        for j in range(nz):
            a = i * (nz + 1) + j; b = a + nz + 1
            F.append([a, a + 1, b + 1, b])          # normale verso +Y (verificata sotto)
    return P, F

def up(P, F):
    P = np.array(P)
    for f in F:
        n = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]])
        if n[1] < 0: f.reverse()
    return F

def run(m):
    X, Z = m.grid_xz(); H = m.H
    xmax = float(X[-1, 0]); zmin = float(Z[0, 0]); zmax = float(Z[0, -1])
    # costa sui due bordi laterali (primo vertice in mare dal lato terra)
    def costa_bordo(j):
        h = H[:, j]; k = np.where((h[:-1] > Y_MARE) & (h[1:] <= Y_MARE))[0]
        return float(X[k[-1] + 1, 0]) if len(k) else xmax
    xc_lo, xc_hi = costa_bordo(0), costa_bordo(H.shape[1] - 1)
    # --- superficie del mare
    Pm = []; Fm = []
    def add(P, F, PP, FF):
        b = len(PP); PP.extend(P); FF.extend([[b + v for v in f] for f in up(P, F)])
    add(*quads_grid(xmax, xmax + LONTANO, -LONTANO, LONTANO, Y_MARE, 8, 16), Pm, Fm)            # oltre il lato mare
    add(*quads_grid(xc_lo - 2.0, xmax, -LONTANO, zmin, Y_MARE, 2, 8), Pm, Fm)                  # oltre il bordo -Z
    add(*quads_grid(xc_hi - 2.0, xmax, zmax, LONTANO, Y_MARE, 2, 8), Pm, Fm)                   # oltre il bordo +Z
    # tratto di mare dentro la striscia nuova (-Z): una lastra sotto la costa (il terreno la copre dove è più alto)
    zmare = -193.565
    add(*quads_grid(196.0, xmax, zmin, zmare, Y_MARE, 6, 12), Pm, Fm)
    m.add_faces('Mare', Pm, Fm, 'sea', False)
    # --- fondale oltre i bordi (oggetto nuovo)
    Pf = []; Ff = []
    add(*quads_grid(xmax, xmax + LONTANO, -LONTANO, LONTANO, Y_FONDO, 8, 16), Pf, Ff)
    # raccordo inclinato dal bordo del terreno (che sale verso la costa) al fondale piatto, sui due lati
    for j, sgn, zed in ((0, -1, zmin), (H.shape[1] - 1, 1, zmax)):
        ii = np.where(H[:, j] < -0.3)[0]; ii = ii[X[ii, 0] >= (xc_lo if j == 0 else xc_hi) - 1.0]
        P = []; F = []
        for k, i in enumerate(ii):
            P += [(float(X[i, 0]), float(H[i, j]) - 0.02, zed), (float(X[i, 0]), Y_FONDO, zed + sgn * 45.0)]
            if k: F.append([2 * k - 2, 2 * k, 2 * k + 1, 2 * k - 1])
        if F: add(P, F, Pf, Ff)
        x0 = float(X[ii[0], 0]) if len(ii) else xmax
        if sgn < 0: add(*quads_grid(x0, xmax, -LONTANO, zed - 45.0, Y_FONDO, 1, 6), Pf, Ff)
        else: add(*quads_grid(x0, xmax, zed + 45.0, LONTANO, Y_FONDO, 1, 6), Pf, Ff)
    m.add_faces('Fondale_Esteso', Pf, Ff, 'sand', False, after='Mare')
    # --- schiuma lungo la costa nuova (bolle triangolari come quelle esistenti)
    gen = contourpy.contour_generator(x=X, y=Z, z=H)
    rng = np.random.default_rng(91); P = []; F = []
    for line in gen.lines(Y_MARE + 0.02):
        line = np.asarray(line)
        if line.size == 0: continue
        sel = line[:, 1] < zmare - 0.3
        if sel.sum() < 2: continue
        L = line[sel]
        seg = np.hypot(*np.diff(L, axis=0).T); cum = np.r_[0, np.cumsum(seg)]
        for s in np.arange(0, cum[-1], 0.33):
            x = np.interp(s, cum, L[:, 0]); z = np.interp(s, cum, L[:, 1])
            for row in range(2):
                off = rng.uniform(0.1, 1.6) * (1 + row); r = rng.uniform(0.12, 0.22)
                cx, cz = x + off, z + rng.uniform(-0.15, 0.15)
                a = rng.uniform(0, 2 * math.pi); b = len(P)
                P += [(cx + r * math.cos(a + k * 2.094), Y_MARE + 0.055 + rng.uniform(0, 0.01), cz + r * math.sin(a + k * 2.094)) for k in range(3)]
                F.append([b, b + 1, b + 2])
    if F: m.add_faces('Mare', P, up(P, F), 'foam', False)
    log('superficie del mare prolungata fino a %.1f km oltre il plastico: %d facce nuove (lato mare e lati corti); fondale piatto a %.0f m con raccordi inclinati ai bordi: %d facce (oggetto nuovo Fondale_Esteso)'
        % (LONTANO / 1000, len(Fm), Y_FONDO, len(Ff)))
    log('schiuma lungo la costa nuova: %d bolle' % len(F))
    return LOG
