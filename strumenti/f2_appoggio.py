"""Fase 2 - appoggio finale.
1) Elementi della fase 1 sotto cui il terreno è cambiato in fase 2 (strade e piazzole nuove, scavi): seguono la nuova
   quota mantenendo lo stesso affondamento di prima; alberi, sassi e siepi finiti su strade o piazze nuove vengono tolti.
2) Case nuove (paese e porto): le parti staccate dal corpo della casa (gradini, panche, botti...) appoggiate al suolo.
Confronto con lo stato finale della fase 1 (stessi indici dei vertici)."""
import numpy as np, collections
from scipy import ndimage
from stato import carica
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[appoggio]', s)

STATO_FASE1 = 'fase1_d.obj.state.pkl'
SOSPESI_PRECEDENTI = 'sospesi_fase2_giro_prova.json'
SALTA = ('Terreno', 'Base_Sezione', 'Acqua', 'Mare', 'Fondale_Esteso')
NATURALI = ('Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Siepi_e_Confini', 'Canneto_Fiume')
STRADE = ('path_dirt', 'street_stone', 'piazza_stone')

def gruppi_bbox(cs, gap=0.03):
    n = len(cs); par = list(range(n))
    def f_(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    lo = np.array([c['lo'] for c in cs]); hi = np.array([c['hi'] for c in cs])
    for i in range(n):
        ov = np.all(lo[i + 1:] - gap <= hi[i], 1) & np.all(lo[i] - gap <= hi[i + 1:], 1)
        for j in np.nonzero(ov)[0]: par[f_(i)] = f_(i + 1 + j)
    g = collections.defaultdict(list)
    for i in range(n): g[f_(i)].append(cs[i])
    return list(g.values())

def fp_min(m, lo, hi, n=3):
    XX, ZZ = np.meshgrid(np.linspace(lo[0], hi[0], n), np.linspace(lo[2], hi[2], n))
    return float(m.height_tri(XX.ravel(), ZZ.ravel()).min())

def run(m):
    m1 = carica(STATO_FASE1); nV1 = len(m1.V)
    di, dj = m1.I0 - m.I0, m1.J0 - m.J0
    H2 = m.H[di:di + m1.H.shape[0], dj:dj + m1.H.shape[1]]
    cambiato = ndimage.binary_dilation(np.abs(H2 - m1.H) > 0.06, iterations=3)
    n1 = np.array(m1.mats + ['<buco>'])[m1.M]
    M2 = m.M[di:di + m1.M.shape[0], dj:dj + m1.M.shape[1]]
    n2 = np.array(m.mats + ['<buco>'])[M2]
    strada_nuova = np.isin(n2, STRADE) & ~np.isin(n1, STRADE)
    def celle(lo, hi):
        i0, j0 = m1.ij(lo[0], lo[2]); i1, j1 = m1.ij(hi[0], hi[2])
        i0 = int(np.clip(np.floor(i0), 0, cambiato.shape[0] - 1)); i1 = int(np.clip(np.ceil(i1), 0, cambiato.shape[0] - 1))
        j0 = int(np.clip(np.floor(j0), 0, cambiato.shape[1] - 1)); j1 = int(np.clip(np.ceil(j1), 0, cambiato.shape[1] - 1))
        return slice(i0, i1 + 1), slice(j0, j1 + 1)
    spost = collections.Counter(); tolti = collections.Counter(); grandi = []
    rem = collections.defaultdict(list)
    for o in list(m.objs):
        nm = o['name']
        if nm in SALTA or not o['faces'] or not m1.has(nm): continue
        cs = m.comps(nm)
        cand = []
        for c in cs:
            if c['verts'].max() >= nV1: continue
            si, sj = celle(c['lo'], c['hi'])
            if cambiato[si, sj].any(): cand.append(c)
        if not cand: continue
        # gruppi: alberi interi; altri oggetti per contatto fra i riquadri (con i vicini)
        lo_c = np.min([c['lo'] for c in cand], 0) - 3; hi_c = np.max([c['hi'] for c in cand], 0) + 3
        vic = [c for c in cs if np.all(c['lo'] <= hi_c) and np.all(c['hi'] >= lo_c) and c['verts'].max() < nV1]
        gr = gruppi_alberi(m, nm, vic) if nm.startswith('Alberi') else gruppi_bbox(vic)
        ids = {id(c) for c in cand}
        naturale = nm.startswith('Alberi') or nm in NATURALI
        for g in gr:
            if not any(id(c) in ids for c in g): continue
            base = min(g, key=lambda c: c['lo'][1])
            y1 = float(m1.V[base['verts'], 1].min()); y2 = float(base['lo'][1])
            g1 = y1 - fp_min(m1, base['lo'], base['hi']); g2 = y2 - fp_min(m, base['lo'], base['hi'])
            delta = g2 - g1
            if abs(delta) < 0.08: continue
            lo = np.min([c['lo'] for c in g], 0); hi = np.max([c['hi'] for c in g], 0)
            ce = (base['lo'] + base['hi']) / 2
            si, sj = celle(np.array([ce[0], 0, ce[2]]), np.array([ce[0], 0, ce[2]]))
            if naturale and strada_nuova[si, sj].any():
                for c in g: rem[nm] += c['faces']
                tolti[nm] += 1; continue
            if max(hi[0] - lo[0], hi[2] - lo[2]) > (8.0 if naturale else 12.0):
                grandi.append('%s (%.0f x %.0f m, %.2f m)' % (nm, hi[0] - lo[0], hi[2] - lo[2], -delta)); continue
            vs = np.unique(np.concatenate([c['verts'] for c in g]))
            m.V[vs, 1] -= delta; spost[nm] += 1
        m.invalidate(nm)
    m.delete(dict(rem))
    log('elementi della fase 1 riallineati al terreno modificato in fase 2: %d (%s)' % (sum(spost.values()), ', '.join('%s %d' % kv for kv in spost.most_common())))
    if tolti: log('alberi/sassi rimasti su strade o piazze nuove, tolti: %d (%s)' % (sum(tolti.values()), ', '.join('%s %d' % kv for kv in tolti.most_common())))
    if grandi: log('ATTENZIONE, elementi grandi con terreno cambiato sotto (lasciati fermi): ' + '; '.join(grandi))
    # 2) parti staccate delle case nuove
    n = 0
    for nm in ('Villaggio_Altopiano_Nuovo', 'Porto_Paese_Nuovo'):
        if not m.has(nm): continue
        for g in gruppi_bbox(m.comps(nm), gap=0.12):
            nf = sum(len(c['faces']) for c in g)
            if nf > 60: continue
            lo = np.min([c['lo'] for c in g], 0); hi = np.max([c['hi'] for c in g], 0)
            gap = lo[1] - fp_min(m, lo, hi)
            if gap > 0.1:
                vs = np.unique(np.concatenate([c['verts'] for c in g])); m.V[vs, 1] -= gap + 0.03; n += 1
        m.invalidate(nm)
    # parti delle case nuove rimaste sospese nel giro di controllo precedente (stessa pipeline, stesse posizioni)
    import json, os
    if os.path.exists(SOSPESI_PRECEDENTI):
        for g in json.load(open(SOSPESI_PRECEDENTI)):
            if not set(g['oggetti']) <= {'Villaggio_Altopiano_Nuovo', 'Porto_Paese_Nuovo'}: continue
            c = np.array(g['centro']); d = np.array(g['dim']); lo = c - d / 2 - 0.05; hi = c + d / 2 + 0.05
            for nm in g['oggetti']:
                sel = [cc for cc in m.comps(nm) if np.all(cc['lo'] >= lo) and np.all(cc['hi'] <= hi)]
                if not sel: continue
                l2 = np.min([cc['lo'] for cc in sel], 0); h2 = np.max([cc['hi'] for cc in sel], 0)
                gap = l2[1] - fp_min(m, l2, h2)
                if gap > 0.05:
                    vs = np.unique(np.concatenate([cc['verts'] for cc in sel])); m.V[vs, 1] -= gap + 0.03; n += 1
                m.invalidate(nm)
    log('case nuove: %d parti staccate (gradini, panche, botti, carretti...) appoggiate al suolo' % n)
    return LOG
