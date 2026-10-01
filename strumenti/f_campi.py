"""Campi dei tre poderi nuovi: strade che li tagliavano, filari interrotti o sollevati, cresta rocciosa, siepi."""
import numpy as np, math, collections
from scipy.cluster.hierarchy import fcluster, linkage
from scipy import ndimage
import ops

LOG = []
def log(s): LOG.append(s); print('[campi]', s)

def fields(m):
    o = m.obj('Poderi_Nuovi'); rows = []
    for c in m.comps('Poderi_Nuovi'):
        ms = collections.Counter(o['mats'][i] for i in c['faces'])
        top = ms.most_common(1)[0][0]; d = c['hi'] - c['lo']
        if top in ('crop_gold', 'crop_green') and max(d[0], d[2]) > 1.0 and d[1] < 1.2 and d[2] < 3 and d[0] < 1.2:
            rows.append(c)
    C = np.array([((c['lo'] + c['hi']) / 2)[[0, 2]] for c in rows])
    lab = fcluster(linkage(C, 'single'), 3.0, 'distance')
    out = []
    for k in range(1, lab.max() + 1):
        segs = [rows[i] for i in np.where(lab == k)[0]]
        if len(segs) < 50: continue
        lo = np.min([s['lo'] for s in segs], 0); hi = np.max([s['hi'] for s in segs], 0)
        mats = collections.Counter()
        for s in segs: mats.update(o['mats'][i] for i in s['faces'])
        out.append(dict(segs=segs, lo=lo, hi=hi, kind=mats.most_common(1)[0][0]))
    return out

def run(m):
    rects = [(f['lo'].copy(), f['hi'].copy()) for f in fields(m)]
    names = lambda: np.array(m.mats + ['<buco>'])[m.M]
    Xc, Zc = m.cell_xz(); X, Z = m.grid_xz()
    tot_lane = tot_fill = tot_move = tot_hedge = 0
    for rlo, rhi in rects:
        # segmenti ricalcolati ad ogni campo (gli indici cambiano dopo le modifiche del campo precedente)
        f = min(fields(m), key=lambda g: np.abs(g['lo'] - rlo).sum() + np.abs(g['hi'] - rhi).sum())
        lo, hi = f['lo'], f['hi']
        x0, x1, z0, z1 = lo[0], hi[0], lo[2], hi[2]
        rect = (Xc >= x0 - 0.3) & (Xc <= x1 + 0.3) & (Zc >= z0 - 0.3) & (Zc <= z1 + 0.3)
        nm = names()
        road_in = rect & (nm == 'path_dirt')
        # materiale del campo = più frequente sotto il campo esclusa la strada
        fm = collections.Counter(nm[rect & ~road_in]).most_common(1)[0][0]
        # righe (linee di filare) per coordinata X
        xs = np.array([((s['lo'] + s['hi']) / 2)[0] for s in f['segs']])
        lines = np.unique(np.round(xs / 0.25) * 0.25)
        # raggruppa linee vicine
        L = [lines[0]]
        for v in lines[1:]:
            if v - L[-1] > 0.6: L.append(v)
        L = np.array(L)
        pitch = np.median(np.diff(L)) if len(L) > 1 else 1.3
        lane_x = None
        if road_in.sum() > 3:
            # ingresso della strada: celle stradali vicino al bordo z0 (lato sinistro)
            entry = road_in & (Zc < z0 + 3.0)
            if entry.sum() == 0: entry = road_in
            ex = Xc[entry].mean()
            # corsia tra due filari più vicina all'ingresso
            mids = (L[:-1] + L[1:]) / 2
            lane_x = float(mids[np.argmin(np.abs(mids - ex))])
        # 1) segmenti nella corsia rimossi
        rem = []
        if lane_x is not None:
            half = max(1.5, pitch * 1.05)
            keep = []
            for s in f['segs']:
                cx = (s['lo'][0] + s['hi'][0]) / 2
                if abs(cx - lane_x) < half: rem += s['faces']
                else: keep.append(s)
            f['segs'] = keep
        # 2) ricucitura dei filari interrotti o accorciati dalla strada: ogni linea riceve tutti i segmenti
        #    del modello di filare completo (stesse posizioni lungo Z), copiando il segmento più vicino della stessa linea
        new_P = []; new_F = []; new_M = []
        o = m.obj('Poderi_Nuovi')
        per_line = {}
        for lx in L:
            per_line[lx] = sorted([s for s in f['segs'] if abs((s['lo'][0] + s['hi'][0]) / 2 - lx) < 0.35], key=lambda s: s['lo'][2])
        full = max(per_line.values(), key=len)
        pattern = [s['lo'][2] for s in full]
        gaps_filled = 0
        for lx, segs in per_line.items():
            if lane_x is not None and abs(lx - lane_x) < max(1.5, pitch * 1.05): continue
            if not segs: continue
            have = np.array([s['lo'][2] for s in segs])
            for zs in pattern:
                if np.min(np.abs(have - zs)) < 0.3: continue
                a = segs[int(np.argmin(np.abs(have - zs)))]
                dz = zs - a['lo'][2]
                rm = {v: i for i, v in enumerate(a['verts'])}
                base = len(new_P)
                new_P += [tuple(m.V[v] + [0, 0, dz]) for v in a['verts']]
                new_F += [[base + rm[v - 1] for v in o['faces'][i]] for i in a['faces']]
                new_M += [o['mats'][i] for i in a['faces']]
                gaps_filled += 1
        if rem: m.delete({'Poderi_Nuovi': rem})
        if new_F: m.add_faces('Poderi_Nuovi', new_P, new_F, new_M, False)
        # 3) terreno del campo: superficie regolare (senza creste né gradini) + materiale del campo
        vin = (X >= x0 - 0.5) & (X <= x1 + 0.5) & (Z >= z0 - 0.5) & (Z <= z1 + 0.5)
        A = np.stack([X[vin], Z[vin], np.ones(vin.sum())], 1)
        coef, *_ = np.linalg.lstsq(A, m.H[vin], rcond=None)
        plane = X * coef[0] + Z * coef[1] + coef[2]
        Hs = ndimage.gaussian_filter(m.H, 3.0)
        target = 0.55 * plane + 0.45 * Hs
        dist = ndimage.distance_transform_edt(~vin) * 0.9
        w = 1 - ops.smoothstep(0, 4.0, dist)
        m.H = m.H * (1 - w) + target * w
        m.M[rect & (m.M >= 0)] = m.mat_index(fm)
        # 4) corsia (carrareccia) dritta tra i filari, collegata alla strada esterna e all'aia
        if lane_x is not None:
            zs0 = z0 - 6.0; zs1 = z1 + 4.0
            nm0 = names()
            yard = (nm0 == 'soil_dark') & (np.abs(Xc - lane_x) < 1.5) & (Zc > z1)
            if yard.any(): zs1 = float(Zc[yard].min()) + 0.5
            pts = [(lane_x, zs0), (lane_x, zs1)]
            hs = [float(m.height(lane_x, zs0)), float(m.height(lane_x, zs1))]
            Pz = np.linspace(zs0, zs1, 20); hz = m.height(np.full(20, lane_x), Pz)
            ops.carve_path(m, [(lane_x, z) for z in Pz], list(hz), width=2.6, shoulder=1.5)
            # vecchia strada fuori dalla corsia dentro il campo -> campo; e il tratto esterno si raccorda
            nm = names()
            old_in = road_in & (np.abs(Xc - lane_x) > 1.6)
            m.M[old_in] = m.mat_index(fm)
            # tratto diagonale residuo fra il bordo del campo e l'aia: torna prato/campo
            gapz = (Zc > z1 + 0.3) & (Zc < zs1 - 0.3) & (Xc > x0 - 2) & (Xc < x1 + 2) & (np.abs(Xc - lane_x) > 1.6) & (names() == 'path_dirt')
            ops.fill_mat_from_neighbors(m, gapz)
            tot_lane += 1
        # 5) filari riappoggiati al terreno
        for c in m.comps('Poderi_Nuovi'):
            ce = (c['lo'] + c['hi']) / 2; d = c['hi'] - c['lo']
            if x0 - 0.5 <= ce[0] <= x1 + 0.5 and z0 - 0.5 <= ce[2] <= z1 + 0.5 and d[1] < 1.2 and max(d[0], d[2]) < 3:
                P = m.V[c['verts']]
                m.V[c['verts'], 1] += ops.footprint_min(m, c['lo'], c['hi'], 3) - c['lo'][1] - 0.03
        m.invalidate('Poderi_Nuovi')
        # 6) rocce, alberi e siepi dentro il campo portati al margine
        for nmo in ('Rocce', 'Alberi', 'Alberi_Nuovi', 'Siepi_e_Confini'):
            if not m.has(nmo): continue
            for c in m.comps(nmo):
                ce = (c['lo'] + c['hi']) / 2
                if x0 <= ce[0] <= x1 and z0 <= ce[2] <= z1:
                    # lato più vicino (in X) fuori dal campo
                    if ce[0] - x0 < x1 - ce[0]: dx = (x0 - 1.2) - ce[0]
                    else: dx = (x1 + 1.2) - ce[0]
                    if nmo == 'Siepi_e_Confini': tot_hedge += 1
                    else: tot_move += 1
                    vs = c['verts']; m.V[vs, 0] += dx
                    lo2 = m.V[vs].min(0); hi2 = m.V[vs].max(0)
                    m.V[vs, 1] += ops.footprint_min(m, lo2, hi2) - lo2[1] - 0.05
            m.invalidate(nmo)
        tot_fill += gaps_filled
        log('campo %s X[%.0f,%.0f] Z[%.0f,%.0f]: corsia %s, segmenti rimossi %d, vuoti ricuciti %d' % (f['kind'], x0, x1, z0, z1, ('a X=%.1f' % lane_x) if lane_x is not None else 'no', len(set(rem)) // 5 if rem else 0, gaps_filled))
    log('totale: %d carrarecce tra i filari al posto delle strade diagonali, %d segmenti di filare ricuciti, %d rocce/alberi e %d elementi di siepe spostati ai margini dei campi' % (tot_lane, tot_fill, tot_move, tot_hedge))
    return LOG
