"""Modelli di casa per i borghi: gruppi di componenti (casa + dettagli anche se stanno in un altro oggetto) presi dagli
edifici esistenti, portati in un sistema locale: centro dell'impronta dei muri in (0,0), base a y=0, porta verso +Z locale."""
import numpy as np, math, collections
import scipy.sparse as sp, scipy.sparse.csgraph as cg

FONTI = [('Borgo_Basso', 'Dettagli_Borgo_Basso'), ('Villaggio_Altopiano', None), ('Porto', None), ('Borgo_Alto', 'Dettagli_Borgo_Alto')]

def _gruppi(m, nomi, gap=0.3):
    cs = []
    for nm in nomi:
        if nm and m.has(nm):
            for c in m.comps(nm): cs.append((nm, c))
    n = len(cs)
    lo = np.array([c['lo'] for _, c in cs]); hi = np.array([c['hi'] for _, c in cs])
    rows = []; cols = []
    for a in range(n):
        ov = np.all(lo[a] - gap <= hi, 1) & np.all(lo - gap <= hi[a], 1); ov[:a + 1] = False
        for b in np.nonzero(ov)[0]: rows.append(a); cols.append(b)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    k, g = cg.connected_components(A, directed=False)
    return [[cs[i] for i in np.where(g == gi)[0]] for gi in range(k)]

def _angolo_muri(P, F, M):
    angs = []; wts = []
    for f, mt in zip(F, M):
        if not mt.startswith('wall_'): continue
        q = P[f]; nrm = np.cross(q[1] - q[0], q[2] - q[0]); ln = np.linalg.norm(nrm)
        if ln < 1e-9 or abs(nrm[1]) / ln > 0.2: continue
        angs.append(math.atan2(nrm[2], nrm[0]) * 4); wts.append(ln)
    if not angs: return 0.0
    return math.atan2(np.average(np.sin(angs), weights=wts), np.average(np.cos(angs), weights=wts)) / 4

def rot_y(P, th):
    c, s = math.cos(th), math.sin(th)
    return np.stack([P[:, 0] * c - P[:, 2] * s, P[:, 1], P[:, 0] * s + P[:, 2] * c], 1)

def solo_collegate(P, F, M, soglia=0.12):
    """parti del modello collegate al corpo (catena di contatti <= soglia): le parti staccate dei modelli originali
    (per esempio un'imposta o un'insegna che non tocca il muro) non vengono copiate"""
    from components import components
    lab = components([np.array(f) for f in F])
    k = lab.max() + 1
    if k == 1: return P, F, M, 0
    gruppi = [np.nonzero(lab == i)[0] for i in range(k)]
    tri = []
    for g in gruppi:
        T = []
        for fi in g:
            q = P[F[fi]]
            for j in range(1, len(q) - 1): T.append((q[0], q[j], q[j + 1]))
        tri.append(np.array(T))
    verts = [P[np.unique(np.concatenate([F[fi] for fi in g]))] for g in gruppi]
    lo = np.array([v.min(0) for v in verts]); hi = np.array([v.max(0) for v in verts])
    from alberi_util import _dist_punti_triangoli, _dentro
    muri = [sum(M[fi].startswith('wall_') for fi in g) for g in gruppi]
    base = int(np.argmax(muri)) if max(muri) > 0 else int(np.argmax([len(g) for g in gruppi]))   # il corpo: il pezzo con più muri
    vis = {base}; fr = [base]
    while fr:
        a = fr.pop()
        for b in range(k):
            if b in vis: continue
            if np.any(lo[a] - soglia > hi[b]) or np.any(lo[b] - soglia > hi[a]): continue
            ok = _dentro(verts[b], verts[a]) or _dentro(verts[a], verts[b]) or \
                 _dist_punti_triangoli(verts[b], tri[a]) <= soglia or _dist_punti_triangoli(verts[a], tri[b]) <= soglia
            if ok: vis.add(b); fr.append(b)
    # anche le parti a terra (gradini, botti) restano: poggiano sul suolo come nel modello
    y0 = P[:, 1].min()
    for b in range(k):
        if b not in vis and lo[b][1] - y0 < 0.15: vis.add(b)
    tenere = np.zeros(len(F), bool)
    for b in vis: tenere[gruppi[b]] = True
    F2 = [f for f, t in zip(F, tenere) if t]; M2 = [mm for mm, t in zip(M, tenere) if t]
    usati = np.unique(np.concatenate(F2)); rm = np.full(len(P), -1); rm[usati] = np.arange(len(usati))
    return P[usati], [list(rm[f]) for f in F2], M2, k - len(vis)

staccate = [0]

def estrai(m, escludi_centri=(), fonti=FONTI, hmin=6.0, hmax=13.5, lmin=3.5, lmax=13.5):
    out = []
    for nomi in fonti:
        if not m.has(nomi[0]): continue
        for g in _gruppi(m, nomi):
            principali = [c for nm, c in g if nm == nomi[0]]
            if not principali: continue
            L = np.min([c['lo'] for _, c in g], 0); H = np.max([c['hi'] for _, c in g], 0); d = H - L
            nf = sum(len(c['faces']) for _, c in g)
            if not (lmin <= max(d[0], d[2]) <= lmax and hmin <= d[1] <= hmax and nf >= 120): continue
            Ps = []; F = []; M = []; base = 0
            for nm, c in g:
                o = m.obj(nm)
                vs = c['verts']; rm = {v: i + base for i, v in enumerate(vs)}
                Ps.append(m.V[vs])
                for f in c['faces']:
                    F.append([rm[v - 1] for v in o['faces'][f]]); M.append(o['mats'][f])
                base += len(vs)
            P = np.concatenate(Ps)
            if not any(mt.startswith('wall_') for mt in M): continue
            # (le parti staccate dei modelli si tolgono alla fine con il controllo degli elementi sospesi)
            if any(mt in ('fence_wood', 'vine', 'crop_green', 'hay') for mt in M) and sum(mt in ('fence_wood', 'vine', 'hay') for mt in M) > 0.15 * len(M):
                continue                                                  # cortili, stalle: non sono case di borgo
            centro0 = (L + H) / 2
            if any(abs(centro0[0] - cx) < 2 and abs(centro0[2] - cz) < 2 for cx, cz in escludi_centri): continue
            phi = _angolo_muri(P, F, M)
            P = rot_y(P, -phi)
            # corpo: muri
            wv = np.unique(np.concatenate([F[i] for i, mt in enumerate(M) if mt.startswith('wall_')]))
            bl = P[wv].min(0); bh = P[wv].max(0)
            c0 = np.array([(bl[0] + bh[0]) / 2, P[:, 1].min(), (bl[2] + bh[2]) / 2])
            P = P - c0; bl = bl - c0; bh = bh - c0
            # porta: legno (o scuro) vicino a terra sulle pareti verticali; altrimenti il lato con più finestre
            def lati(materiali, ymax):
                acc = collections.Counter()
                for f, mt in zip(F, M):
                    if mt not in materiali: continue
                    q = P[f]; c = q.mean(0)
                    if c[1] > ymax: continue
                    nrm = np.cross(q[1] - q[0], q[2] - q[0]); ln = np.linalg.norm(nrm)
                    if ln < 1e-9 or abs(nrm[1]) / ln > 0.3: continue
                    dist = {'+x': abs(c[0] - bh[0]), '-x': abs(c[0] - bl[0]), '+z': abs(c[2] - bh[2]), '-z': abs(c[2] - bl[2])}
                    s_ = min(dist, key=dist.get)
                    if dist[s_] < 0.6: acc[s_] += ln
                return acc
            acc = lati(('wood_trim',), 2.6); porta = True
            if not acc: acc = lati(('wood_trim', 'window_dark', 'iron_dark'), 3.0)
            if not acc: acc = lati(('window_dark',), 99.0); porta = False
            lato = acc.most_common(1)[0][0] if acc else None
            if lato is None: continue
            th = {'+z': 0.0, '-z': math.pi, '+x': -math.pi / 2, '-x': math.pi / 2}[lato]
            # ruoto in modo che la porta guardi +Z locale
            th2 = {'+z': 0.0, '-z': math.pi, '+x': math.pi / 2, '-x': -math.pi / 2}[lato]
            P = rot_y(P, th2)
            wv_P = P[wv]; bl = wv_P.min(0); bh = wv_P.max(0)
            lo = P.min(0); hi = P.max(0)
            sporg = dict(sx=bl[0] - lo[0], dx=hi[0] - bh[0], retro=bl[2] - lo[2], fronte=hi[2] - bh[2])
            out.append(dict(P=P, F=F, M=M, nf=len(F), larg=bh[0] - bl[0], prof=bh[2] - bl[2], alt=hi[1], corpo=(bl, bh), tutto=(lo, hi),
                            sporg=sporg, fonte=nomi[0], porta=porta, centro=(float(centro0[0]), float(centro0[2]))))
    return out
