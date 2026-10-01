"""Fase 2 - alberi: stessa densità del nucleo originale della mappa
1) nelle aree nuove (lato altopiano e lato cascata), con specie secondo quota e vicinanza al mare;
2) nelle zone aggiunte dalle espansioni precedenti (poderi laterali, striscia bassa) dove erano più radi.
Gli alberi sono copie dei modelli già presenti (Alberi, Alberi_Nuovi), ruotate e scalate."""
import numpy as np, math, collections
from scipy import ndimage
from scipy.spatial import cKDTree
import scipy.sparse as sp, scipy.sparse.csgraph as cg
from occupancy import occupancy_fine

LOG = []
def log(s): LOG.append(s); print('[alberi]', s)

TIPI = ('conifer', 'tree_dark', 'tree_green', 'tree_light', 'tree_olive', 'tree_autumn', 'hedge')
# densità del nucleo originale (alberi per m2) per materiale del suolo, misurate sul modello
DENS = {'terrain_forest': 0.110, 'terrain_grass': 0.035, 'terrain_meadow': 0.035, 'terrain_rock': 0.026,
        'stone_dark': 0.015, 'moss_stone': 0.037, 'terrain_gravel': 0.029}
RISERVE = [(-229.0, -168.0, 16.0)]          # (x, z, raggio): attorno alla scala della torre del mago

def gruppi(m):
    """alberi esistenti come gruppi tronco + chiome (alberi_util), solo parti collegate"""
    from alberi_util import gruppi_alberi, collegati
    out = []; scartate = 0
    for nm in ('Alberi', 'Alberi_Nuovi'):
        if not m.has(nm): continue
        for g in gruppi_alberi(m, nm):
            ok, via = collegati(m, g, nm=nm)
            scartate += len(via)
            out.append((nm, ok))
    log('alberi esistenti riconosciuti: %d (parti staccate escluse dai modelli: %d)' % (len(out), scartate))
    return out

def libreria(m, gr):
    lib = collections.defaultdict(list)
    for nm, mem in gr:
        o = m.obj(nm)
        mats = collections.Counter(o['mats'][f] for c in mem for f in c['faces'])
        crown = [k for k in mats if k != 'trunk_brown']
        if not crown: continue
        tipo = max(crown, key=lambda k: mats[k])
        if tipo not in TIPI: continue
        lo = np.min([c['lo'] for c in mem], 0); hi = np.max([c['hi'] for c in mem], 0)
        h = hi[1] - lo[1]; nf = sum(len(c['faces']) for c in mem)
        if tipo == 'hedge':
            if not (0.5 < h < 2.2) or not (12 <= nf <= 40): continue
        elif not (2.5 < h < 8.5) or not (18 <= nf <= 75) or 'trunk_brown' not in mats:
            continue
        low = min(mem, key=lambda c: c['lo'][1])
        base = np.array([(low['lo'][0] + low['hi'][0]) / 2, lo[1], (low['lo'][2] + low['hi'][2]) / 2])
        vs = np.unique(np.concatenate([c['verts'] for c in mem])); rm = {v: i for i, v in enumerate(vs)}
        faces = []; fm = []
        for c in mem:
            for f in c['faces']:
                faces.append([rm[v - 1] for v in o['faces'][f]]); fm.append(o['mats'][f])
        P = m.V[vs] - base
        # il tronco entra di 30 cm nella chioma: nei modelli originali a volte la chioma lo sfiora appena
        tv = np.unique([v for f, mt in zip(faces, fm) if mt == 'trunk_brown' for v in f])
        if len(tv) and tipo != 'hedge':
            top = P[tv, 1].max(); alti = tv[P[tv, 1] > top - 0.02]
            P[alti, 1] += 0.3
        lib[tipo].append(dict(P=P, F=faces, M=fm, nf=nf))
    for t in lib:
        lib[t] = sorted(lib[t], key=lambda d: d['nf'])[:40]
    return lib

def scegli_tipo(rng, h, x, z, mat):
    if mat in ('terrain_meadow', 'terrain_grass') and rng.random() < 0.07: return 'hedge'
    if rng.random() < 0.07: return 'tree_autumn'
    pc = float(np.clip((h - 35) / 75, 0.08, 0.9))
    if x > 140 and h < 48 and rng.random() < 0.45: return 'tree_olive'
    if rng.random() < pc: return 'conifer'
    return ('tree_dark', 'tree_green', 'tree_light')[int(rng.integers(3))]

def run(m):
    gr = gruppi(m)
    lib = libreria(m, gr)
    log('modelli di albero ricavati da quelli esistenti: ' + ', '.join('%s %d (%.0f facce medie)' % (t, len(v), np.mean([d['nf'] for d in v])) for t, v in lib.items()))
    names = np.array(m.mats + ['<buco>'])[m.M]
    Xc, Zc = m.cell_xz()
    occ = occupancy_fine(m, extra_exclude=('Alberi', 'Alberi_Nuovi', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Animali', 'Canneto_Fiume'))
    occ = ndimage.binary_dilation(occ, iterations=1)
    gx, gz = np.gradient(m.H, 0.9); sl = np.hypot(gx, gz)
    sc = (sl[:-1, :-1] + sl[1:, :-1] + sl[:-1, 1:] + sl[1:, 1:]) / 4
    hc = (m.H[:-1, :-1] + m.H[1:, :-1] + m.H[:-1, 1:] + m.H[1:, 1:]) / 4
    # alberi esistenti (per la distanza minima)
    ex = []
    for nm, mem in gr:
        lo = np.min([c['lo'] for c in mem], 0); hi = np.max([c['hi'] for c in mem], 0)
        ex.append(((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2))
    ex = np.array(ex)
    # zone: aree nuove (fase 2) e zone delle espansioni precedenti
    nuove = (Xc < -305.1) | (Zc < -193.0)
    vecchie = ((Zc > 179) | (Xc < -225)) & ~nuove
    # densità attuale nelle zone vecchie per materiale (per aggiungere solo la differenza)
    ti, tj = m.ij(ex[:, 0], ex[:, 1]); ti = np.clip(ti.astype(int), 0, names.shape[0] - 1); tj = np.clip(tj.astype(int), 0, names.shape[1] - 1)
    tmat = names[ti, tj]; tin = vecchie[ti, tj]
    target = np.zeros(names.shape)
    deficit = {}
    for mt, d0 in DENS.items():
        sel = names == mt
        target[sel & nuove] = d0
        a = (sel & vecchie).sum() * 0.81
        if a > 0:
            cur = ((tmat == mt) & tin).sum() / a
            deficit[mt] = max(0.0, d0 - cur)
            target[sel & vecchie] = deficit[mt]
    # esclusioni
    vietati = np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', 'sand', 'terrain_clay', 'soil_dark', 'terrain_field', 'crop_green', 'crop_gold', '<buco>'])
    target[vietati | occ | (sc > 1.15) | (hc < 0.3)] = 0
    pian = (Xc > 105) & (Xc < 215) & (Zc < -193) & (Zc > -264)        # pianoro del paese nuovo: quasi libero
    target[pian] *= 0.12
    porto = (Xc > 175) & (Xc < 230) & (Zc > -95) & (Zc < 45)
    target[porto] *= 0.2
    for (rx, rz, rr_) in RISERVE:
        target[np.hypot(Xc - rx, Zc - rz) < rr_] = 0
    # niente alberi nuovi sulla scala della torre del mago, sul ponticello e davanti alla grotta
    import f2_mago, ops
    dsc, _, _ = ops.dist_to_polyline(Xc, Zc, f2_mago.PUNTI)
    target[dsc < f2_mago.CORRIDOIO + 0.6] = 0
    target[(np.abs(Xc - f2_mago.XB) < 3.0) & (Zc > f2_mago.ZW - 2.5) & (Zc < f2_mago.ZE + 6.0)] = 0
    rng = np.random.default_rng(81)
    lam = target * 0.81
    cnt = rng.poisson(lam)
    ci, cj = np.nonzero(cnt)
    pts = []
    for i, j in zip(ci, cj):
        for _ in range(cnt[i, j]):
            pts.append((Xc[i, j] + rng.uniform(-0.45, 0.45), Zc[i, j] + rng.uniform(-0.45, 0.45), i, j))
    order = rng.permutation(len(pts))
    # griglia di hash per la distanza minima
    cell = 2.0; grid = collections.defaultdict(list)
    for (x, z) in ex: grid[(int(x // cell), int(z // cell))].append((x, z))
    P_all = {'n': [], 'v': []}; outs = {'Alberi_Aree_Nuove': ([], [], []), 'Alberi_Infittimento': ([], [], [])}
    nt = collections.Counter(); placed = collections.Counter()
    for k in order:
        x, z, i, j = pts[k]
        mt = names[i, j]; dmin = 1.7 if mt == 'terrain_forest' else 2.6
        gxk, gzk = int(x // cell), int(z // cell); ok = True
        for a in (gxk - 2, gxk - 1, gxk, gxk + 1, gxk + 2):
            for b in (gzk - 2, gzk - 1, gzk, gzk + 1, gzk + 2):
                for (px, pz) in grid.get((a, b), ()):
                    if (px - x) ** 2 + (pz - z) ** 2 < dmin * dmin: ok = False; break
                if not ok: break
            if not ok: break
        if not ok: continue
        h = float(hc[i, j]); tipo = scegli_tipo(rng, h, x, z, mt)
        if tipo not in lib or not lib[tipo]: tipo = 'conifer'
        t = lib[tipo][int(rng.integers(len(lib[tipo])))]
        s = rng.uniform(0.85, 1.2) if tipo != 'hedge' else rng.uniform(0.8, 1.3)
        th = rng.uniform(0, 2 * math.pi); c_, s_ = math.cos(th), math.sin(th)
        Pl = t['P'] * s
        Pr = np.stack([Pl[:, 0] * c_ + Pl[:, 2] * s_, Pl[:, 1], -Pl[:, 0] * s_ + Pl[:, 2] * c_], 1)
        ring = np.array([[0, 0], [0.4, 0], [-0.4, 0], [0, 0.4], [0, -0.4]])
        y = float(m.height_tri(x + ring[:, 0], z + ring[:, 1]).min()) - 0.06
        Q = Pr + [x, y, z]
        dest = 'Alberi_Aree_Nuove' if nuove[i, j] else 'Alberi_Infittimento'
        Pd, Fd, Md = outs[dest]; b0 = len(Pd)
        Pd.extend(Q.tolist()); Fd.extend([[b0 + v for v in f] for f in t['F']]); Md.extend(t['M'])
        grid[(gxk, gzk)].append((x, z)); nt[tipo] += 1; placed[dest] += 1
    for dest, (Pd, Fd, Md) in outs.items():
        if Fd: m.add_faces(dest, Pd, Fd, Md, False, after='Alberi_Nuovi')
    log('alberi nelle aree nuove: %d (%d facce, oggetto nuovo Alberi_Aree_Nuove)' % (placed['Alberi_Aree_Nuove'], len(outs['Alberi_Aree_Nuove'][1])))
    log('infittimento nelle zone delle espansioni precedenti (poderi laterali, striscia bassa): %d alberi (%d facce, oggetto nuovo Alberi_Infittimento)' % (placed['Alberi_Infittimento'], len(outs['Alberi_Infittimento'][1])))
    log('densità di riferimento del nucleo originale (alberi/m2): ' + ', '.join('%s %.3f' % kv for kv in DENS.items()) + '; mancanze nelle zone vecchie: ' + ', '.join('%s %.3f' % kv for kv in deficit.items()))
    log('specie piantate: ' + ', '.join('%s %d' % kv for kv in nt.most_common()))
    return LOG
