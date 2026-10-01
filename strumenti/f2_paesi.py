"""Fase 2 - il paese dell'altopiano si allarga nel pianoro nuovo fra monti e mare; il porto diventa un paesino di case
portuali. Le case sono copie (ruotate) di quelle esistenti dello stesso luogo, su piazzole spianate, lungo strade nuove."""
import numpy as np, math, collections
from scipy import ndimage
import scipy.sparse as sp, scipy.sparse.csgraph as cg
import ops
from occupancy import occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[paesi]', s)

def gruppi_case(m, nm, gap=0.35):
    o = m.obj(nm); cs = m.comps(nm)
    lo = np.array([c['lo'] for c in cs]); hi = np.array([c['hi'] for c in cs]); n = len(cs)
    rows = []; cols = []
    for a in range(n):
        ov = np.all(lo[a] - gap <= hi, 1) & np.all(lo - gap <= hi[a], 1); ov[:a + 1] = False
        for b in np.nonzero(ov)[0]: rows.append(a); cols.append(b)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    k, g = cg.connected_components(A, directed=False)
    out = []
    for gi in range(k):
        mem = [cs[i] for i in np.where(g == gi)[0]]
        L = np.min([c['lo'] for c in mem], 0); Hh = np.max([c['hi'] for c in mem], 0); d = Hh - L
        nf = sum(len(c['faces']) for c in mem)
        if not (4.0 <= max(d[0], d[2]) <= 8.0 and 6.5 <= d[1] <= 12.5 and 200 <= nf <= 600): continue
        mats = collections.Counter(o['mats'][f] for c in mem for f in c['faces'])
        if not any(k_.startswith('wall_') for k_ in mats): continue
        vs = np.unique(np.concatenate([c['verts'] for c in mem])); rm = {v: i for i, v in enumerate(vs)}
        P = m.V[vs].copy()
        F = []; M = []
        for c in mem:
            for f in c['faces']:
                F.append([rm[v - 1] for v in o['faces'][f]]); M.append(o['mats'][f])
        # orientamento proprio della casa: direzioni delle pareti (normali orizzontali dei muri, angolo modulo 90 gradi)
        angs = []; wts = []
        for f, mt in zip(F, M):
            if not mt.startswith('wall_'): continue
            q = P[f]; nrm = np.cross(q[1] - q[0], q[2] - q[0]); ln = np.linalg.norm(nrm)
            if ln < 1e-9 or abs(nrm[1]) / ln > 0.2: continue
            angs.append(math.atan2(nrm[2], nrm[0]) * 4); wts.append(ln)
        phi = math.atan2(np.average(np.sin(angs), weights=wts), np.average(np.cos(angs), weights=wts)) / 4 if angs else 0.0
        c0, s0 = math.cos(-phi), math.sin(-phi)
        P = np.stack([P[:, 0] * c0 - P[:, 2] * s0, P[:, 1], P[:, 0] * s0 + P[:, 2] * c0], 1)
        L2 = P.min(0); H2 = P.max(0); d = H2 - L2
        base = np.array([(L2[0] + H2[0]) / 2, L2[1], (L2[2] + H2[2]) / 2])
        P = P - base
        # lato della porta: legno vicino a terra sulle pareti verticali
        acc = np.zeros(2)
        for f, mt in zip(F, M):
            if mt != 'wood_trim': continue
            q = P[f]; c = q.mean(0)
            if c[1] > 2.3: continue
            nrm = np.cross(q[1] - q[0], q[2] - q[0]); ln = np.linalg.norm(nrm)
            if ln < 1e-9 or abs(nrm[1]) / ln > 0.3: continue
            acc += np.array([c[0], c[2]])
        if np.linalg.norm(acc) > 0.5:
            front = np.array([np.sign(acc[0]), 0.0]) if abs(acc[0]) >= abs(acc[1]) else np.array([0.0, np.sign(acc[1])])
        else:   # porta non riconosciuta: la facciata lunga verso la strada
            front = np.array([0.0, 1.0]) if d[0] >= d[2] else np.array([1.0, 0.0])
        out.append(dict(P=P, F=F, M=M, nf=nf, dim=d, front=front, src=nm))
    return out

def posa(m, t, x, z, dirz, obj, occ, vietati, rng, pad_extra=1.0, max_dislivello=3.0):
    """casa t con la porta verso la direzione dirz (vettore x,z); controlla impronta libera; spiana e posa"""
    f = t['front'] if t['front'] is not None else np.array([1.0, 0.0])
    a_t = math.atan2(f[1], f[0]); a_d = math.atan2(dirz[1], dirz[0]); th = a_d - a_t
    c_, s_ = math.cos(th), math.sin(th)
    P = t['P']
    Pr = np.stack([P[:, 0] * c_ - P[:, 2] * s_, P[:, 1], P[:, 0] * s_ + P[:, 2] * c_], 1)
    lo = Pr.min(0); hi = Pr.max(0)
    poly = [(x + lo[0] - pad_extra, z + lo[2] - pad_extra), (x + hi[0] + pad_extra, z + lo[2] - pad_extra),
            (x + hi[0] + pad_extra, z + hi[2] + pad_extra), (x + lo[0] - pad_extra, z + hi[2] + pad_extra)]
    cells = ops.cells_in_poly(m, poly)
    if (cells & (occ | vietati)).any(): return None
    xs = np.linspace(x + lo[0], x + hi[0], 6); zs = np.linspace(z + lo[2], z + hi[2], 6)
    XX, ZZ = np.meshgrid(xs, zs); hh = m.height(XX.ravel(), ZZ.ravel())
    if hh.max() - hh.min() > max_dislivello: return None
    y = float(np.median(hh))
    ops.flatten_pad(m, poly, y, blend=2.5)
    Q = Pr + [x, y - 0.05, z]
    m.add_faces(obj, Q.tolist(), t['F'], t['M'], False)
    occ |= ndimage.binary_dilation(cells, iterations=1)
    return poly

def strada(m, pts, width=3.0, mat='path_dirt', max_grade=0.10):
    P, _ = __import__('f_porte').resample(pts, 1.0)
    h = ndimage.uniform_filter1d(m.height(P[:, 0], P[:, 1]), 9, mode='nearest')
    for i in range(1, len(h)): h[i] = np.clip(h[i], h[i - 1] - max_grade, h[i - 1] + max_grade)
    ops.carve_path(m, [tuple(p) for p in P], list(h), width=width, shoulder=2.0, mat=mat)
    return P

def run(m):
    rng = np.random.default_rng(121)
    case_v = gruppi_case(m, 'Villaggio_Altopiano')
    case_p = gruppi_case(m, 'Porto') + gruppi_case(m, 'Borgo_Basso')
    log('modelli di casa: %d dal villaggio dell\'altopiano, %d dal porto e dal borgo basso (porta riconosciuta su %d)'
        % (len(case_v), len(case_p), sum(t['front'] is not None for t in case_v + case_p)))
    occ = occupancy_fine(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume'), with_mats=False)
    occ = ndimage.binary_dilation(occ, iterations=1)
    names = lambda: np.array(m.mats + ['<buco>'])[m.M]
    # ---------------- paese dell'altopiano: strade nuove nel pianoro
    s1 = strada(m, [(141.0, -190.5), (141.5, -205), (141.0, -220), (140.0, -233)], width=3.0)
    s2 = strada(m, [(108.0, -213.0), (125, -214.5), (141.0, -214.0), (158, -213.0), (176, -214.5), (194.0, -216.0)], width=2.6)
    pz = [(133.5, -233.5), (147.0, -233.5), (147.0, -246.0), (133.5, -246.0)]
    yp = float(np.median(m.height(np.array([p[0] for p in pz]), np.array([p[1] for p in pz]))))
    ops.flatten_pad(m, pz, yp, blend=3.0)
    m.M[ops.cells_in_poly(m, pz)] = m.mat_index('piazza_stone')
    vietati = np.isin(names(), ['path_dirt', 'street_stone', 'piazza_stone', 'terrain_field', 'crop_green', 'crop_gold', 'sand', '<buco>'])
    # lotti: (x, z, direzione della porta)
    lotti = [(134.0, -199.5, (1, 0)), (148.5, -200.0, (-1, 0)), (134.5, -226.5, (1, 0)), (148.0, -225.0, (-1, 0)),
             (117.0, -207.0, (0, -1)), (128.0, -221.0, (0, 1)), (160.0, -206.5, (0, -1)), (171.0, -221.5, (0, 1)),
             (184.0, -207.5, (0, -1)), (187.0, -223.0, (0, 1)), (130.0, -253.0, (0, 1)), (151.0, -253.5, (0, 1)),
             (115.0, -224.0, (0, 1)), (162.0, -222.0, (0, 1))]
    nv = 0; posati = []
    order = rng.permutation(len(case_v))
    for k, (x, z, d) in enumerate(lotti):
        for tries in range(len(case_v)):
            t = case_v[order[(k + tries) % len(case_v)]]
            pl = posa(m, t, x, z, np.array(d, float), 'Villaggio_Altopiano_Nuovo', occ, vietati, rng)
            if pl is not None:
                nv += 1; posati.append(pl); break
    # pozzo al centro della piazzetta: copia del pozzo del chiostro della rocca (stessi pezzi e materiali)
    pz_c = (140.25, -239.75)
    sel = m.select(lambda lo, hi: abs((lo[0] + hi[0]) / 2 - 70.5) < 1.6 and abs((lo[2] + hi[2]) / 2 - 20.8) < 1.6 and lo[1] > 33.0 and hi[1] < 38.0, names=('Rocca',))
    npz = sum(len(v) for v in sel.values())
    if npz:
        Pw = m.V[m.sel_verts(sel)]; lo_w = Pw.min(0); hi_w = Pw.max(0); cw = (lo_w + hi_w) / 2
        yb = float(m.height(np.array([pz_c[0] - 1, pz_c[0] + 1, pz_c[0], pz_c[0]]), np.array([pz_c[1], pz_c[1], pz_c[1] - 1, pz_c[1] + 1])).min())
        d = np.array([pz_c[0] - cw[0], yb - lo_w[1] - 0.04, pz_c[1] - cw[2]])
        m.copy_sel(sel, lambda P: P + d, target='Villaggio_Altopiano_Nuovo')
    log('paese dell\'altopiano allargato nel pianoro nuovo: %d case, strada principale di %.0f m, traversa di %.0f m, piazzetta 13 x 12 m con pozzo al centro (copia del pozzo del chiostro, %d facce) (oggetto nuovo Villaggio_Altopiano_Nuovo)'
        % (nv, len(s1), len(s2), npz))
    # ---------------- porto: case portuali sul fronte del molo e lungo la strada del porto
    vietati = np.isin(names(), ['path_dirt', 'street_stone', 'piazza_stone', 'terrain_field', 'crop_green', 'crop_gold', 'terrain_clay', '<buco>'])
    vietati |= m.H[:-1, :-1] < 0.6
    s3 = strada(m, [(203.0, 4.0), (204.5, 15.0), (205.5, 26.0), (205.0, 37.0)], width=2.6, mat='street_stone', max_grade=0.12)
    s4 = strada(m, [(190.0, -24.0), (189.0, -34.0), (188.5, -42.0)], width=2.4, mat='street_stone', max_grade=0.12)
    lotti_p = [(201.0, -31.5, (1, 0)), (199.5, 10.0, (1, 0)), (200.5, 19.5, (1, 0)), (201.0, 29.0, (1, 0)), (210.0, 21.0, (-1, 0)),
               (210.5, 31.5, (-1, 0)), (183.5, -30.0, (1, 0)), (183.0, -38.5, (1, 0)), (195.0, -33.0, (-1, 0)), (199.0, 38.5, (1, 0)),
               (180.5, 27.0, (1, 0)), (189.0, 22.0, (1, 0))]
    npo = 0
    order = rng.permutation(len(case_p))
    for k, (x, z, d) in enumerate(lotti_p):
        for tries in range(len(case_p)):
            t = case_p[order[(k + tries) % len(case_p)]]
            pl = posa(m, t, x, z, np.array(d, float), 'Porto_Paese_Nuovo', occ, vietati, rng, pad_extra=0.8, max_dislivello=4.0)
            if pl is not None:
                npo += 1; posati.append(pl); break
    log('porto diventato paesino: %d case portuali nuove sul fronte del molo e lungo la strada, 2 vicoli lastricati (oggetto nuovo Porto_Paese_Nuovo)' % npo)
    # alberi, sassi e siepi rimasti dentro le impronte delle case nuove o sulle strade nuove: tolti interi
    from matplotlib.path import Path
    from alberi_util import gruppi_alberi
    paths = [Path(np.array(pl)) for pl in posati]
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    su_strada = np.isin(nomi, ['path_dirt', 'street_stone', 'piazza_stone'])
    zone_lav = [(100, 200, -260, -186), (172, 222, -50, 45)]
    rem = {}; nt = collections.Counter()
    for nm in ('Alberi', 'Alberi_Nuovi', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini'):
        if not m.has(nm): continue
        cs = [c for c in m.comps(nm) if any(x0 <= (c['lo'][0] + c['hi'][0]) / 2 <= x1 and z0 <= (c['lo'][2] + c['hi'][2]) / 2 <= z1 for x0, x1, z0, z1 in zone_lav)]
        gr = gruppi_alberi(m, nm, cs) if nm.startswith('Alberi') else [[c] for c in cs]
        fs = []
        for g in gr:
            b = min(g, key=lambda c: c['lo'][1]); ce = (b['lo'] + b['hi']) / 2
            i, j = [int(v) for v in m.ij(ce[0], ce[2])]
            if any(pa.contains_point((ce[0], ce[2])) for pa in paths) or su_strada[i, j]:
                for c in g: fs += c['faces']
                nt[nm] += 1
        if fs: rem[nm] = fs
    m.delete(rem)
    if nt: log('tolti perché dentro le case nuove o sulle strade nuove: ' + ', '.join('%s %d' % kv for kv in nt.items()))
    return LOG
