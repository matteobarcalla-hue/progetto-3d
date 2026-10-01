"""Podere inglobato dallo sperone della rocca: spostato in blocco in una radura piana ai piedi della rocca."""
import numpy as np, math, collections
import ops, geo

LOG = []
def log(s): LOG.append(s); print('[podere]', s)

OLD_C = np.array([116.05, -23.1])     # centro casa
NEW_C = np.array([139.0, 8.0])

def run(m):
    names = ('Poderi', 'Poderi_Dettagli', 'Dettagli_Poderi')
    def pick(lo, hi):
        c = (lo + hi) / 2
        if not (102 <= c[0] <= 126 and -37 <= c[2] <= -11): return False
        return lo[1] > 12.5
    sel = m.select(pick, names=names)
    # recinzioni della stessa proprietà lungo il pendio (pali e traverse), anche sotto quota 12.5
    fen = m.select(lambda lo, hi: 102 <= (lo[0] + hi[0]) / 2 <= 125.5 and -37 <= (lo[2] + hi[2]) / 2 <= -11 and lo[1] > 8.0, names=('Poderi',))
    for k, v in fen.items():
        o = m.obj(k); v = [i for i in v if o['mats'][i] == 'fence_wood']
        sel[k] = sorted(set(sel.get(k, [])) | set(v))
    well = m.select(lambda lo, hi: 118 <= (lo[0] + hi[0]) / 2 <= 122 and -31.5 <= (lo[2] + hi[2]) / 2 <= -28.5 and lo[1] > 9.5, names=('Poderi',))
    for k, v in well.items(): sel[k] = sorted(set(sel.get(k, [])) | set(v))
    nf = sum(len(v) for v in sel.values())
    log('podere selezionato: %d facce (casa, davanzali, bucato, pagliaio, orto, pozzo, recinti)' % nf)
    # casa (con dettagli entro 1.5 m) vs elementi dell'aia
    house_box = (np.array([110.3 - 1.5, -27.7 - 1.5]), np.array([121.8 + 1.5, -18.5 + 1.5]))
    house = {}; yard = {}
    for nm, fs in sel.items():
        o = m.obj(nm)
        for c in m.comps(nm):
            if not set(c['faces']) & set(fs): continue
            ce = (c['lo'] + c['hi']) / 2
            inside = house_box[0][0] <= ce[0] <= house_box[1][0] and house_box[0][1] <= ce[2] <= house_box[1][1] and c['lo'][1] > 23.5
            (house if inside else yard).setdefault(nm, []).extend([i for i in c['faces'] if i in set(fs)])
    # radura: alberi e rocce spostati ai margini (fuori da un'area 26x26 m)
    x0, x1, z0, z1 = NEW_C[0] - 13, NEW_C[0] + 14, NEW_C[1] - 11, NEW_C[1] + 13
    moved = 0
    for nm in ('Alberi', 'Alberi_Nuovi', 'Rocce'):
        # albero = gruppo di componenti vicine (tronco+chiome): sposto per gruppi
        cs = m.comps(nm)
        cen = np.array([((c['lo'] + c['hi']) / 2)[[0, 2]] for c in cs]) if cs else np.zeros((0, 2))
        inside = [(k, c) for k, c in enumerate(cs) if x0 <= cen[k][0] <= x1 and z0 <= cen[k][1] <= z1]
        if not inside: continue
        from scipy.cluster.hierarchy import fcluster, linkage
        P = np.array([cen[k] for k, _ in inside])
        lab = fcluster(linkage(P, 'single'), 1.2, 'distance') if len(P) > 1 else np.array([1])
        rng = np.random.default_rng(7)
        for g in range(1, lab.max() + 1):
            grp = [inside[i][1] for i in range(len(inside)) if lab[i] == g]
            gc = np.mean([((c['lo'] + c['hi']) / 2)[[0, 2]] for c in grp], 0)
            # spinta radiale fuori dal rettangolo, verso il lato più vicino
            dxs = [gc[0] - x0, x1 - gc[0], gc[1] - z0, z1 - gc[1]]; k = int(np.argmin(dxs))
            off = np.zeros(2)
            if k == 0: off[0] = -(dxs[0] + 1.5 + rng.uniform(0, 3))
            if k == 1: off[0] = (dxs[1] + 1.5 + rng.uniform(0, 3))
            if k == 2: off[1] = -(dxs[2] + 1.5 + rng.uniform(0, 3))
            if k == 3: off[1] = (dxs[3] + 1.5 + rng.uniform(0, 3))
            vs = np.unique(np.concatenate([c['verts'] for c in grp]))
            m.V[vs, 0] += off[0]; m.V[vs, 2] += off[1]
            lo = m.V[vs].min(0); hi = m.V[vs].max(0)
            m.V[vs, 1] += ops.footprint_min(m, lo, hi) - lo[1] - 0.05
            moved += 1
        m.invalidate(nm)
    log('radura: %d alberi/rocce spostati ai margini' % moved)
    # piazzola della casa e aia: terreno spianato dolcemente
    def tf(P):
        P = geo.rot_y(P, math.pi, OLD_C[0], OLD_C[1])
        P[:, 0] += NEW_C[0] - OLD_C[0]; P[:, 2] += NEW_C[1] - OLD_C[1]
        return P
    m.transform(house, tf)
    m.transform(yard, tf)
    hv = m.sel_verts(house); P = m.V[hv]; lo = P.min(0); hi = P.max(0)
    # piazzola alla quota più bassa sotto l'impronta
    base = ops.footprint_min(m, lo, hi, 9)
    pad = [(lo[0] - 1.2, lo[2] - 1.2), (hi[0] + 1.2, lo[2] - 1.2), (hi[0] + 1.2, hi[2] + 1.2), (lo[0] - 1.2, hi[2] + 1.2)]
    ops.flatten_pad(m, pad, base, blend=3.5)
    # la casa: base originale 24.3 (zoccolo interrato ~0.2 m come in origine)
    m.V[hv, 1] += base - 0.2 - lo[1]
    for nm in house: m.invalidate(nm)
    # elementi dell'aia riappoggiati uno per uno (il recinto segue il terreno palo per palo)
    n = 0
    for nm, fs in yard.items():
        fs = set(fs)
        for c in m.comps(nm):
            if not set(c['faces']) & fs: continue
            lo2, hi2 = m.V[c['verts']].min(0), m.V[c['verts']].max(0)
            if max(hi2[0] - lo2[0], hi2[2] - lo2[2]) > 4.0:
                # traverse lunghe: ogni vertice segue il terreno mantenendo la propria altezza relativa (0.5-1.1 m)
                V = m.V[c['verts']]
                rel = V[:, 1] - lo2[1]
                m.V[c['verts'], 1] = m.height(V[:, 0], V[:, 2]) + 0.55 + rel
            else:
                m.V[c['verts'], 1] += ops.footprint_min(m, lo2, hi2) - lo2[1] - 0.04
            n += 1
        m.invalidate(nm)
    # recinto: pali e traverse del vecchio recinto seguivano il pendio del vecchio sito; il recinto viene rifatto
    # (stesso materiale, stesso tipo: pali + due traverse) attorno alla nuova aia
    nrem = 0
    for grp in (yard, house):
      for nm in list(grp.keys()):
        o = m.obj(nm); yf = set(grp[nm]); rem = []
        for c in m.comps(nm):
            if not set(c['faces']) & yf: continue
            if set(o['mats'][i] for i in c['faces']) == {'fence_wood'}:
                rem += c['faces']
        if rem:
            # indici delle facce cambiano dopo la cancellazione: ricalcolo le liste per nome
            keep_y = [i for i in yard.get(nm, []) if i not in set(rem)]
            keep_h = [i for i in house.get(nm, []) if i not in set(rem)]
            m.delete({nm: rem}); nrem += len(rem)
            shift = np.searchsorted(np.array(sorted(rem)), np.array(keep_y), side='left') if keep_y else []
            yard[nm] = list(np.array(keep_y) - shift) if keep_y else []
            shift = np.searchsorted(np.array(sorted(rem)), np.array(keep_h), side='left') if keep_h else []
            house[nm] = list(np.array(keep_h) - shift) if keep_h else []
    # bbox di casa + aia
    allv = []
    for nm, fs in list(house.items()) + list(yard.items()):
        if fs: allv.append(m.sel_verts({nm: []}) if False else None)
    xs = []; zs = []
    for c in []: pass
    bx0, bx1, bz0, bz1 = lo[0] - 2.5, hi[0] + 4.5, lo[2] - 3.5, hi[2] + 5.5
    corners = [(bx1 - 4.0, bz0), (bx0, bz0), (bx0, bz1), (bx1, bz1), (bx1, bz0 + 4.0)]   # varco d'ingresso nell'angolo verso il sentiero
    fence = geo.Mesh(); npost = 0
    for k in range(len(corners) - 1):
        a_ = np.array(corners[k]); b_ = np.array(corners[k + 1]); Ls = np.linalg.norm(b_ - a_)
        n = max(1, int(round(Ls / 2.4)))
        pts = [a_ + (b_ - a_) * t for t in np.linspace(0, 1, n + 1)]
        for p in (pts if k == 0 else pts[1:]):
            gy = float(m.height(p[0], p[1])); npost += 1
            fence.extend(geo.box(p[0] - 0.08, p[0] + 0.08, gy - 0.15, gy + 1.15, p[1] - 0.08, p[1] + 0.08, 'fence_wood'))
        for p, q in zip(pts[:-1], pts[1:]):
            for hgt in (0.5, 0.95):
                ya, yb = float(m.height(*p)) + hgt, float(m.height(*q)) + hgt
                d = q - p; L2 = np.linalg.norm(d); u = d / L2; nn = np.array([-u[1], u[0]]) * 0.035
                P8 = [(p[0] - nn[0], ya, p[1] - nn[1]), (q[0] - nn[0], yb, q[1] - nn[1]), (q[0] + nn[0], yb, q[1] + nn[1]), (p[0] + nn[0], ya, p[1] + nn[1])]
                P8 += [(x, y + 0.1, z) for x, y, z in P8]
                f = geo.Mesh().add(P8, [[0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0], [4, 7, 6, 5]], 'fence_wood')
                c0 = np.array([(p[0] + q[0]) / 2, (ya + yb) / 2 + 0.05, (p[1] + q[1]) / 2])
                geo.orient(f, lambda cc, nv, c0=c0: np.dot(nv, cc - c0) >= 0)
                fence.extend(f)
    fence.to_model(m, 'Poderi'); m.invalidate('Poderi')
    log('recinto dell\'aia rifatto: %d facce del vecchio recinto sul pendio sostituite da %d pali con doppia traversa' % (nrem, npost))
    # orto: patch di terra (terrain_clay) già nel blocco; terreno sotto l'aia a prato/terra battuta
    Xc, Zc = m.cell_xz()
    yard_cells = (Xc > lo[0] - 1.0) & (Xc < hi[0] + 1.0) & (Zc > lo[2] - 1.0) & (Zc < hi[2] + 1.0)
    m.M[yard_cells & (m.M >= 0)] = m.mat_index('path_dirt')
    log('casa spostata da (116.1, -23.1, quota 24.3) a (%.1f, %.1f, quota %.1f) ruotata di 180°; %d elementi dell\'aia riappoggiati' % (NEW_C[0], NEW_C[1], base - 0.2, n))
    # vecchio sito: celle di terra battuta dell'aia tornano roccia/prato dai vicini
    old = (Xc > 103) & (Xc < 126) & (Zc > -37) & (Zc < -11)
    old &= np.isin(np.array(m.mats + ['<buco>'])[m.M], ['path_dirt', 'terrain_clay', 'soil_dark'])
    ops.fill_mat_from_neighbors(m, old, exclude=('path_dirt', 'terrain_clay', 'soil_dark'))
    # sentiero dall'aia alla strada più vicina
    names_ = np.array(m.mats + ['<buco>'])[m.M]
    road = (names_ == 'path_dirt') & ~yard_cells
    d = np.hypot(Xc - NEW_C[0], Zc - NEW_C[1]); d[~road] = 1e9
    i, j = np.unravel_index(np.argmin(d), d.shape)
    tgt = (Xc[i, j], Zc[i, j])
    start = (NEW_C[0] + (hi[0] - lo[0]) / 2 + 1.0, NEW_C[1])
    hs = [float(m.height(*start)), float(m.height(*tgt))]
    L = math.hypot(tgt[0] - start[0], tgt[1] - start[1])
    ops.carve_path(m, [start, tgt], hs, width=2.2, shoulder=2.0)
    log('sentiero di accesso di %.0f m fino alla strada a (%.0f, %.0f)' % (L, tgt[0], tgt[1]))
    return LOG
