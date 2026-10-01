"""Riordino del compartimento della rocca."""
import numpy as np, math, collections
import geo, ops
from geo import Mesh

LOG = []
def log(s): LOG.append(s); print('[rocca]', s)

def sel_center(m, names, test):
    return m.select(lambda lo, hi: test((lo + hi) / 2, lo, hi), names=names)

def count(sel): return sum(len(v) for v in sel.values())

def dy_for(m, sel, dx, dz):
    """differenza di quota minima del terreno sotto l'impronta fra posizione nuova e vecchia"""
    vs = m.sel_verts(sel); P = m.V[vs]
    lo = P.min(0); hi = P.max(0)
    old = ops.footprint_min(m, lo, hi, 7)
    new = ops.footprint_min(m, lo + [dx, 0, dz], hi + [dx, 0, dz], 7)
    return new - old

def ribbon(m, pts, width, y_off, mat, name='Strade_Borgo', step=0.9):
    """nastro di pavimentazione che segue il terreno lungo la polilinea"""
    P = np.array(pts, float)
    # ricampiona
    L = np.r_[0, np.cumsum(np.hypot(*(P[1:] - P[:-1]).T))]
    t = np.linspace(0, L[-1], max(2, int(L[-1] / step) + 1))
    x = np.interp(t, L, P[:, 0]); z = np.interp(t, L, P[:, 1])
    d = np.gradient(np.stack([x, z], 1), axis=0); d /= np.linalg.norm(d, axis=1)[:, None]
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    Lp = np.stack([x, z], 1) + nrm * width / 2; Rp = np.stack([x, z], 1) - nrm * width / 2
    pts3 = []
    for a in list(Lp) + list(Rp):
        pts3.append((a[0], float(m.height(a[0], a[1])) + y_off, a[1]))
    n = len(x); F = []
    for i in range(n - 1):
        F.append([i, i + 1, n + i + 1, n + i])
    me = Mesh().add(pts3, F, mat)
    geo.orient(me, lambda c, nn: nn[1] > 0)
    me.to_model(m, name)
    return len(F)

def disc(m, cx, cz, r, n, y_off, mat, name='Strade_Borgo'):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    P = [(cx, float(m.height(cx, cz)) + y_off, cz)] + [(p[0], float(m.height(p[0], p[1])) + y_off, p[1]) for p in pts]
    F = [[0, 1 + k, 1 + (k + 1) % n] for k in range(n)]
    me = Mesh().add(P, F, mat); geo.orient(me, lambda c, nn: nn[1] > 0); me.to_model(m, name)

# ---------------------------------------------------------------- chiostro nuovo
def extract_unit(m):
    """modulo d'arcata dal vecchio chiostro: colonna + capitello + conci fra le colonne 65.55 e 66.85 (lato Z=5.05)"""
    o = m.obj('Chiostro'); P = []; F = []; M = []
    for c in m.comps('Chiostro'):
        ce = (c['lo'] + c['hi']) / 2
        if abs(ce[2] - 5.05) < 0.05 and ((abs(ce[0] - 65.55) < 0.05 and c['lo'][1] < 37.2) or (65.7 < ce[0] < 66.7 and c['lo'][1] > 37.2)):
            for i in c['faces']:
                idx = np.array(o['faces'][i]) - 1
                b = len(P); P += [tuple(m.V[v] - [65.55, 34.28, 5.05]) for v in idx]
                F.append(list(range(b, b + len(idx)))); M.append(o['mats'][i])
    return np.array(P), F, M

def place_unit(unit, x, y, z, ang, sx=1.0):
    P, F, M = unit; Q = P.copy(); Q[:, 0] *= np.where(np.abs(Q[:, 0]) > 0.3, sx, 1.0)
    c, s = math.cos(ang), math.sin(ang)
    R = np.stack([Q[:, 0] * c - Q[:, 2] * s, Q[:, 1], Q[:, 0] * s + Q[:, 2] * c], 1) + [x, y, z]
    return Mesh().add(R, F, M)

def build_cloister(m, x0, x1, z0, z1, door_x, unit):
    base = ops.footprint_min(m, np.array([x0, 0, z0]), np.array([x1, 0, z1]), 9)
    y0 = base; T = 0.5; HW = 5.6; DEP = 3.0
    me = Mesh()
    W = x1 - x0; D = z1 - z0
    door_w, door_h = 1.7, 2.7
    segs = [((x0, z0), (door_x - door_w / 2, z0)), ((door_x + door_w / 2, z0), (x1, z0)),
            ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))]
    for a, b in segs:
        a = np.array(a); b = np.array(b); d = b - a; L = np.linalg.norm(d); u = d / L
        nin = np.array([-u[1], u[0]])
        c = (a + b) / 2 + nin * T / 2
        me.extend(geo.obox(c[0], c[1], u[0], u[1], L / 2, T / 2, y0 - 0.6, y0 + HW, 'wall_plaster'))
        me.extend(geo.obox(c[0] - nin[0] * 0.05, c[1] - nin[1] * 0.05, u[0], u[1], L / 2, T / 2 + 0.05, y0 - 0.6, y0 + 0.45, 'wall_stone'))
    me.extend(geo.obox(door_x, z0 + T / 2, 1, 0, door_w / 2, T / 2, y0 + door_h, y0 + HW, 'wall_plaster', top=False))
    for sx in (-1, 1):
        xa = door_x + sx * door_w / 2
        me.extend(geo.box(min(xa, xa + sx * 0.18), max(xa, xa + sx * 0.18), y0, y0 + door_h, z0 - 0.06, z0 + 0.02, 'stone_light'))
    me.extend(geo.box(door_x - door_w / 2 - 0.18, door_x + door_w / 2 + 0.18, y0 + door_h, y0 + door_h + 0.25, z0 - 0.06, z0 + 0.02, 'stone_light'))
    me.extend(geo.box(door_x - door_w / 2, door_x + door_w / 2, y0 - 0.02, y0 + 0.12, z0 - 0.35, z0 + T, 'stone_light'))
    # finestrelle alte sui lati esterni
    win = []
    for k in range(4):
        x = x0 + 2.2 + k * (W - 4.4) / 3
        if abs(x - door_x) > 1.8: win.append(('z0', x))
        win.append(('z1', x))
    for k in range(4):
        z = z0 + 2.2 + k * (D - 4.4) / 3
        win += [('x0', z), ('x1', z)]
    for side, s in win:
        yb, yt = y0 + 2.9, y0 + 3.9
        if side == 'z0': me.extend(geo.box(s - 0.22, s + 0.22, yb, yt, z0 - 0.03, z0, 'window_dark', top=False)); me.extend(geo.box(s - 0.3, s + 0.3, yb - 0.1, yb, z0 - 0.12, z0, 'stone_light'))
        if side == 'z1': me.extend(geo.box(s - 0.22, s + 0.22, yb, yt, z1, z1 + 0.03, 'window_dark', top=False)); me.extend(geo.box(s - 0.3, s + 0.3, yb - 0.1, yb, z1, z1 + 0.12, 'stone_light'))
        if side == 'x0': me.extend(geo.box(x0 - 0.03, x0, yb, yt, s - 0.22, s + 0.22, 'window_dark', top=False)); me.extend(geo.box(x0 - 0.12, x0, yb - 0.1, yb, s - 0.3, s + 0.3, 'stone_light'))
        if side == 'x1': me.extend(geo.box(x1, x1 + 0.03, yb, yt, s - 0.22, s + 0.22, 'window_dark', top=False)); me.extend(geo.box(x1, x1 + 0.12, yb - 0.1, yb, s - 0.3, s + 0.3, 'stone_light'))
    # colonnato con il modulo d'arcata del vecchio chiostro
    ci0, ci1, cz0, cz1 = x0 + T + DEP, x1 - T - DEP, z0 + T + DEP, z1 - T - DEP
    yf = y0 + 0.12                     # piano del portico
    corners = [(ci0, cz0), (ci1, cz0), (ci1, cz1), (ci0, cz1)]
    nb = 6
    y_band0, y_band1 = yf + 3.64, yf + 4.35
    for k in range(4):
        A = np.array(corners[k]); B = np.array(corners[(k + 1) % 4]); L = np.linalg.norm(B - A); u = (B - A) / L
        ang = math.atan2(u[1], u[0]); s = L / nb
        nrm = np.array([-u[1], u[0]])
        me.extend(geo.box(A[0] - 0.32, A[0] + 0.32, y0 - 0.2, y_band0, A[1] - 0.32, A[1] + 0.32, 'stone_light'))
        for i in range(nb):
            p = A + u * s * i
            un = place_unit(unit, p[0], yf, p[1], ang, sx=s / 1.3)
            if i == 0:   # il primo modulo parte dal pilastro d'angolo: tolgo colonna e capitello
                keep = [j for j, f in enumerate(un.F) if np.array(un.P)[f][:, 1].min() > yf + 3.0]
                un = Mesh().add(un.P, [un.F[j] for j in keep], [un.M[j] for j in keep])
            me.extend(un)
            # pennacchi sopra gli archi (due lati)
            a2 = p + u * 0.24; b2 = p + u * (s - 0.24)
            for sgn in (-1, 1):
                f = geo.arch_face(a2, b2, yf + 3.12, 0.52, y_band0, n=6, mat='wall_plaster', offset=nrm * sgn * 0.2)
                geo.orient(f, lambda c, nn, w=nrm * sgn: nn[0] * w[0] + nn[2] * w[1] > 0)
                me.extend(f)
        # fascia (architrave) sopra l'arcata e cornice
        c = (A + B) / 2
        me.extend(geo.obox(c[0], c[1], u[0], u[1], L / 2 + 0.3, 0.21, y_band0, y_band1, 'wall_plaster'))
        me.extend(geo.obox(c[0], c[1], u[0], u[1], L / 2 + 0.36, 0.27, y_band1 - 0.12, y_band1, 'stone_light'))
    # tetto: falda unica per lato dal colmo sul filo esterno del muro verso il cortile (4 trapezi), in coppi
    ov = 0.45
    yo = y0 + HW + 0.02; yi = y_band1 + 0.03
    slope = (yo - yi) / (T + DEP)
    yi2 = yi - slope * ov
    O = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    I = [(ci0 + ov, cz0 + ov), (ci1 - ov, cz0 + ov), (ci1 - ov, cz1 - ov), (ci0 + ov, cz1 - ov)]
    for k in range(4):
        o0, o1 = O[k], O[(k + 1) % 4]; i0, i1 = I[k], I[(k + 1) % 4]
        f = Mesh().add([(o0[0], yo, o0[1]), (o1[0], yo, o1[1]), (i1[0], yi2, i1[1]), (i0[0], yi2, i0[1])], [[0, 1, 2, 3]], 'roof_terracotta')
        geo.orient(f, lambda c, nn: nn[1] > 0); me.extend(f)
        f = Mesh().add([(o0[0], yo - 0.1, o0[1]), (o1[0], yo - 0.1, o1[1]), (i1[0], yi2 - 0.1, i1[1]), (i0[0], yi2 - 0.1, i0[1])], [[0, 1, 2, 3]], 'wood_trim')
        geo.orient(f, lambda c, nn: nn[1] < 0); me.extend(f)
        d = np.array(i1) - np.array(i0); L = np.linalg.norm(d); cc = (np.array(i0) + np.array(i1)) / 2
        me.extend(geo.obox(cc[0], cc[1], d[0], d[1], L / 2, 0.05, yi2 - 0.2, yi2 - 0.02, 'wood_trim'))
        # cornicione in pietra sul filo esterno
        d = np.array(o1) - np.array(o0); L = np.linalg.norm(d); u = d / L; nout = np.array([u[1], -u[0]])
        cc = (np.array(o0) + np.array(o1)) / 2 + nout * 0.09
        me.extend(geo.obox(cc[0], cc[1], d[0], d[1], L / 2 + 0.18, 0.12, yo - 0.3, yo + 0.04, 'stone_light'))
    # pavimento del portico e cordolo verso il cortile
    ring_o = [(x0 + T, z0 + T), (x1 - T, z0 + T), (x1 - T, z1 - T), (x0 + T, z1 - T)]
    for k in range(4):
        a0, a1 = ring_o[k], ring_o[(k + 1) % 4]; b0, b1 = corners[k], corners[(k + 1) % 4]
        f = Mesh().add([(a0[0], yf, a0[1]), (a1[0], yf, a1[1]), (b1[0], yf, b1[1]), (b0[0], yf, b0[1])], [[0, 1, 2, 3]], 'piazza_stone')
        geo.orient(f, lambda c, nn: nn[1] > 0); me.extend(f)
        b0, b1 = np.array(b0), np.array(b1); d = b1 - b0; L = np.linalg.norm(d); c = (b0 + b1) / 2
        me.extend(geo.obox(c[0], c[1], d[0], d[1], L / 2, 0.22, y0 - 0.25, yf + 0.02, 'stone_light'))
    me.to_model(m, 'Chiostro')
    log('Chiostro nuovo: %.1f x %.1f m, muro esterno %.2f m, portico profondo %.1f m, cortile %.1f x %.1f m, %d facce' % (W, D, T, DEP, ci1 - ci0, cz1 - cz0, len(me.F)))
    return dict(y0=y0, yf=yf, court=(ci0, ci1, cz0, cz1), door=(door_x, z0))

# ---------------------------------------------------------------- recinto del cimitero
def build_enclosure(m, poly, gate, y_floor):
    """muretto con copertina lungo il poligono chiuso; gate=(a,b) punti del varco sul primo lato che lo contiene"""
    me = Mesh()
    n = len(poly)
    for i in range(n):
        a = np.array(poly[i], float); b = np.array(poly[(i + 1) % n], float)
        pieces = [(a, b)]
        ga, gb = np.array(gate[0]), np.array(gate[1])
        # varco se il segmento contiene i punti del cancello
        d = b - a; L = np.linalg.norm(d); u = d / L
        ta = np.dot(ga - a, u); tb = np.dot(gb - a, u)
        off = abs(np.cross(np.r_[u, 0], np.r_[ga - a, 0])[2])
        if off < 0.3 and 0 < ta < L and 0 < tb < L:
            t0, t1 = sorted([ta, tb])
            pieces = [(a, a + u * t0), (a + u * t1, b)]
        for p, q in pieces:
            me.extend(geo.wall_segment(p, q, 0.4, y_floor - 0.4, y_floor + 0.95, 'wall_stone', cap='stone_light', cap_h=0.1, cap_over=0.05))
    me.to_model(m, 'Cimitero')

def floor_poly(m, poly, y, mat, name):
    c = np.mean(poly, 0)
    P = [(c[0], y, c[1])] + [(p[0], y, p[1]) for p in poly]
    n = len(poly)
    F = [[0, 1 + k, 1 + (k + 1) % n] for k in range(n)]
    me = Mesh().add(P, F, mat); geo.orient(me, lambda cc, nn: nn[1] > 0); me.to_model(m, name)

def point_in_poly(p, poly, margin=0.0):
    from matplotlib.path import Path
    return Path(np.array(poly)).contains_point(p, radius=-margin)

# ---------------------------------------------------------------- principale
def run(m):
    R = ('Rocca', 'Dettagli_Rocca')
    # 1) blocchi
    mastio = sel_center(m, R, lambda c, lo, hi: (76 <= c[0] <= 104 and -5 <= c[2] <= 25) or (88.5 <= c[0] <= 91.5 and 18 <= c[2] <= 28.2))
    casa = sel_center(m, R, lambda c, lo, hi: 61 <= c[0] <= 70 and 21.5 <= c[2] <= 31)
    pozzo = sel_center(m, R, lambda c, lo, hi: 77 <= c[0] <= 80 and 26 <= c[2] <= 30)
    log('selezionati: mastio %d facce, casa %d, pozzo %d' % (count(mastio), count(casa), count(pozzo)))
    # mensole sospese del mastio (cubi aperti a quota 65.2-66.1)
    o = m.obj('Rocca'); mens = []
    for c in m.comps('Rocca'):
        if len(c['faces']) == 5 and abs(c['lo'][1] - 65.24) < 0.05 and abs(c['hi'][1] - 66.12) < 0.08:
            ce = (c['lo'] + c['hi']) / 2
            dt = min(math.hypot(ce[0] - tx, ce[2] - tz) for tx, tz in ((81.0, 0.9), (98.9, 0.9), (98.9, 18.8), (81.0, 18.8)))
            inside = 80.9 < ce[0] < 99.0 and 0.8 < ce[2] < 18.9
            if 3.6 < dt < 6.0 and not inside:
                mens.append(c)
    log('mensole sospese trovate: %d' % len(mens))
    # 2) sposta il mastio di 6 m verso sinistra (-Z)
    DZ = -6.0
    m.translate(mastio, (0, 0, DZ))
    # 3) riposiziona le mensole: appoggiate al fusto delle torri angolari (r=2.7) sotto l'anello
    towers = [(81.0, 0.9 + DZ), (98.9, 0.9 + DZ), (98.9, 18.8 + DZ), (81.0, 18.8 + DZ)]
    keep_c = np.array([89.95, 9.85 + DZ])
    by_t = collections.defaultdict(list)
    for c in mens:
        ce = ((c['lo'] + c['hi']) / 2)
        k = int(np.argmin([math.hypot(ce[0] - t[0], ce[2] - t[1]) for t in towers])); by_t[k].append(c)
    for k, cs in by_t.items():
        t = np.array(towers[k]); out = t - keep_c; base_ang = math.atan2(out[1], out[0])
        angs = [base_ang + math.radians(a) for a in (-112.5, -37.5, 37.5, 112.5)][:len(cs)]
        for c, ang in zip(cs, angs):
            vs = c['verts']; P = m.V[vs]; ce = P.mean(0)
            # direzione del lato aperto: asse con facce mancanti -> la metto verso la torre
            loc = P - ce
            # ruota attorno a Y in modo che l'asse locale +X punti radialmente
            r = 2.7 + 0.43
            tgt = np.array([t[0] + r * math.cos(ang), ce[1], t[1] + r * math.sin(ang)])
            ca, sa = math.cos(-ang), math.sin(-ang)
            rot = np.stack([loc[:, 0] * ca + loc[:, 2] * sa, loc[:, 1], -loc[:, 0] * sa + loc[:, 2] * ca], 1)
            m.V[vs] = tgt + rot
        m.invalidate('Rocca')
    # 4) casa grigia in basso a sinistra (porta verso +X)
    dxh, dzh = 0.0, -27.0
    m.translate(casa, (dxh, dy_for(m, casa, dxh, dzh), dzh))
    # 5) pozzo al centro della corte
    dxp, dzp = 70.5 - 78.5, 21.0 - 28.2
    Pp = m.V[m.sel_verts(pozzo)]; lo_p, hi_p = Pp.min(0), Pp.max(0)
    y_new = ops.footprint_min(m, lo_p + [dxp, 0, dzp], hi_p + [dxp, 0, dzp], 7)
    m.translate(pozzo, (dxp, y_new - lo_p[1] - 0.04, dzp))      # base del pozzo appoggiata (4 cm nel terreno)
    # 6) foglie/fiori autunnali dentro la nuova impronta del mastio
    fog = m.select(lambda lo, hi: 82 <= (lo[0] + hi[0]) / 2 <= 86 and -5 <= (lo[2] + hi[2]) / 2 <= -3, names=('Alberi',))
    m.translate(fog, (-11.0, 0, -5.0))
    # 7) cappella + cimitero: rotazione -90° attorno al centro del cimitero e traslazione
    CX, CZ = 95.1, -7.5; NX, NZ = 86.0, 34.6
    cim_all = m.select(lambda lo, hi: True, names=('Cimitero', 'Oratorio', 'Dettagli_Oratorio'))
    # muri e pavimento vecchi del cimitero: facce singole grandi o box di muro -> da rifare
    oc = m.obj('Cimitero'); walls = []
    for c in m.comps('Cimitero'):
        d = c['hi'] - c['lo']; mats = set(oc['mats'][i] for i in c['faces'])
        if (max(d[0], d[2]) > 1.2 and mats <= {'wall_stone', 'stone_light', 'terrain_gravel'}):
            walls += c['faces']
    m.delete({'Cimitero': walls})
    log('recinto e pavimento vecchi del cimitero rimossi: %d facce (ricostruiti sotto)' % len(walls))
    cim_all = m.select(lambda lo, hi: True, names=('Cimitero', 'Oratorio', 'Dettagli_Oratorio'))
    y_old = 33.9
    def tf(P):
        P = geo.rot_y(P, -math.pi / 2, CX, CZ)
        P[:, 0] += NX - CX; P[:, 2] += NZ - CZ
        return P
    m.transform(cim_all, tf)
    # quota: pavimento nuovo
    poly = [(79.0, 26.2), (93.0, 26.2), (93.0, 35.6), (89.2, 40.6), (79.0, 40.6)]
    ymin = min(float(m.height(p[0], p[1])) for p in poly)
    xs = np.linspace(79, 93, 12); zs = np.linspace(26.2, 40.6, 12)
    X, Z = np.meshgrid(xs, zs); yfl = float(m.height(X.ravel(), Z.ravel()).min())
    m.translate(cim_all, (0, yfl - y_old, 0))
    # elementi fuori dal nuovo recinto (angolo tagliato verso le mura): ricollocati in posti liberi
    units = []
    for nm in ('Cimitero',):
        for c in m.comps(nm):
            ce = (c['lo'] + c['hi']) / 2
            if not point_in_poly((ce[0], ce[2]), poly, 0.45):
                units.append((nm, c))
    # raggruppa per vicinanza (tomba = lapide+croce+fiori)
    moved = 0
    if units:
        cen = np.array([((c['lo'] + c['hi']) / 2)[[0, 2]] for _, c in units])
        from scipy.cluster.hierarchy import fcluster, linkage
        lab = fcluster(linkage(cen, 'single'), 0.9, 'distance') if len(cen) > 1 else np.array([1])
        # posti liberi: griglia nella fascia libera fra cappella e cancello e lungo il muro destro
        slots = [(x, z) for x in np.arange(86.2, 92.4, 1.5) for z in np.arange(30.0, 35.0, 1.6)]
        occ = []
        for c in m.comps('Cimitero'):
            ce = (c['lo'] + c['hi']) / 2
            if point_in_poly((ce[0], ce[2]), poly, 0.45): occ.append(ce[[0, 2]])
        occ = np.array(occ) if occ else np.zeros((0, 2))
        free = [s for s in slots if len(occ) == 0 or np.min(np.hypot(occ[:, 0] - s[0], occ[:, 1] - s[1])) > 1.0]
        for k in range(1, lab.max() + 1):
            grp = [units[i] for i in range(len(units)) if lab[i] == k]
            gc = np.mean([((c['lo'] + c['hi']) / 2)[[0, 2]] for _, c in grp], 0)
            if not free: break
            s = free.pop(0)
            for nm, c in grp:
                m.V[c['verts'], 0] += s[0] - gc[0]; m.V[c['verts'], 2] += s[1] - gc[1]
            moved += 1
        m.invalidate('Cimitero')
    log('cimitero: %d gruppi di elementi ricollocati dentro il nuovo recinto' % moved)
    build_enclosure(m, poly, ((88.4, 26.2), (90.6, 26.2)), yfl)
    floor_poly(m, poly, yfl + 0.02, 'terrain_gravel', 'Cimitero')
    # 8) vecchio chiostro: conservo fontana e albero, il resto è ricostruito
    och = m.obj('Chiostro'); keep = []; drop = []
    for c in m.comps('Chiostro'):
        ce = (c['lo'] + c['hi']) / 2; mats = set(och['mats'][i] for i in c['faces'])
        if (abs(ce[0] - 67.5) < 1.2 and abs(ce[2] - 7.0) < 1.2 and c['lo'][1] > 34.3 and not mats <= {'stone_light'} ) or \
           (abs(ce[0] - 67.5) < 0.1 and abs(ce[2] - 7.0) < 0.1 and 'stone_light' in mats and c['hi'][1] < 35.3 and c['lo'][1] > 34.3) or 'tree_green' in mats:
            keep += c['faces']
        else:
            drop += c['faces']
    unit = extract_unit(m)
    log('modulo d\'arcata estratto dal vecchio chiostro: %d facce' % len(unit[1]))
    nf_old = len(och['faces'])
    m.delete({'Chiostro': drop})
    fontana_albero = {'Chiostro': list(range(len(m.obj('Chiostro')['faces'])))}
    log('chiostro vecchio: %d facce, conservate fontana e albero (%d facce)' % (nf_old, len(keep)))
    X0, X1, Z0, Z1 = 61.5, 76.5, 24.0, 39.0
    info = build_cloister(m, X0, X1, Z0, Z1, door_x=69.0, unit=unit)
    ci0, ci1, cz0, cz1 = info['court']
    ccx, ccz = (ci0 + ci1) / 2, (cz0 + cz1) / 2
    # fontana al centro del cortile, albero in un angolo
    och = m.obj('Chiostro')
    fa = [i for i in fontana_albero['Chiostro']]
    tree = [i for i in fa if och['mats'][i] == 'tree_green']
    fon = [i for i in fa if och['mats'][i] != 'tree_green']
    def move_faces(idx, tx, tz):
        vs = np.unique(np.concatenate([np.array(och['faces'][i]) - 1 for i in idx]))
        P = m.V[vs]; lo = P.min(0); hi = P.max(0); c = (lo + hi) / 2
        dy = ops.footprint_min(m, lo + [tx - c[0], 0, tz - c[2]], hi + [tx - c[0], 0, tz - c[2]]) - lo[1] + 0.0
        m.V[vs] += [tx - c[0], 0, tz - c[2]]
        return vs
    vs_f = move_faces(fon, ccx, ccz)
    # la base della fontana appoggiata al cortile
    m.V[vs_f, 1] += info['y0'] - m.V[vs_f, 1].min() - 0.05
    vs_t = move_faces(tree, 73.2, -7.5)
    gy = float(m.height(73.2, -7.5))
    m.V[vs_t, 1] += gy + 1.25 - m.V[vs_t, 1].min()
    tc = m.V[vs_t].mean(0)
    geo.box(tc[0] - 0.12, tc[0] + 0.12, gy - 0.1, gy + 1.45, tc[2] - 0.12, tc[2] + 0.12, 'trunk_brown').to_model(m, 'Chiostro')
    m.invalidate('Chiostro')
    # 9) giardino della rocca: le 4 aiuole nei quadranti del cortile del chiostro (hortus conclusus attorno al pozzo)
    beds = np.array([(89.3, 30.0), (89.3, 34.3), (91.7, 28.8), (91.7, 33.0)])
    tg = [(ccx - 2.45, ccz - 2.45), (ccx - 2.45, ccz + 2.45), (ccx + 2.45, ccz - 2.45), (ccx + 2.45, ccz + 2.45)]
    groups = collections.defaultdict(list)
    for c in m.comps('Giardino_Rocca'):
        ce = ((c['lo'] + c['hi']) / 2)[[0, 2]]
        groups[int(np.argmin(np.hypot(*(beds - ce).T)))] += c['faces']
    for k, fs in groups.items():
        G = {'Giardino_Rocca': fs}; vs = m.sel_verts(G); P = m.V[vs]; gc = (P.min(0) + P.max(0)) / 2
        m.V[vs] += [tg[k][0] - gc[0], info['yf'] + 0.01 - P[:, 1].min(), tg[k][1] - gc[2]]
    m.invalidate('Giardino_Rocca')
    log('giardino: %d aiuole spostate nei quadranti del cortile' % len(groups))
    # 10) pavimentazioni: tolgo i pezzi vecchi nella rocca e traccio i nuovi percorsi
    old = m.select(lambda lo, hi: 56 <= (lo[0] + hi[0]) / 2 <= 104 and -18 <= (lo[2] + hi[2]) / 2 <= 46, names=('Strade_Borgo',))
    m.delete(old)
    n = 0
    n += ribbon(m, [(56.8, 16.2), (63, 17.2), (70.5, 18.4), (78, 19.9), (85, 21.2), (89.9, 22.4)], 2.6, 0.04, 'street_stone')
    n += ribbon(m, [(69.0, 19.0), (69.0, 23.6)], 1.8, 0.05, 'street_stone')
    n += ribbon(m, [(89.9, 22.4), (89.5, 25.9)], 1.8, 0.05, 'street_stone')
    n += ribbon(m, [(64.5, 17.3), (70.0, 8.0), (70.6, 1.0)], 1.6, 0.05, 'street_stone')
    disc(m, 70.5, 21.0, 3.2, 10, 0.03, 'piazza_stone')
    log('pavimentazioni della rocca rifatte: %d tratti di nastro + piazzetta del pozzo' % n)
    # 11) terreno: cortile del chiostro a prato, piazzola sotto chiostro e cappella
    Xc, Zc = m.cell_xz()
    court = (Xc > ci0 + 0.2) & (Xc < ci1 - 0.2) & (Zc > cz0 + 0.2) & (Zc < cz1 - 0.2)
    m.M[court] = m.mat_index('terrain_grass')
    ops.flatten_pad(m, [(X0 - 0.3, Z0 - 0.3), (X1 + 0.3, Z0 - 0.3), (X1 + 0.3, Z1 + 0.3), (X0 - 0.3, Z1 + 0.3)], info['y0'], blend=2.0)
    ops.flatten_pad(m, poly, yfl, blend=2.0)
    return LOG
