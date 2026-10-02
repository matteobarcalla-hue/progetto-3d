"""Fase 3 - stato di partenza dal .blend dell'utente (castello sul mare.blend).
- Oggetti della mappa presi dal .blend (vertici in coordinate OBJ, facce, materiali, smussatura): conservano tutte le modifiche fatte a mano.
- Terreno: il .blend è stato scolpito (vertici spostati anche in orizzontale). La griglia di 0,9 m viene ricampionata sulla
  superficie scolpita (quota esatta della superficie del .blend in ogni nodo); i materiali restano quelli delle celle.
- Fasce laterali del plastico (Base_Sezione) riadattate ai bordi rialzati dalla scultura.
- Animali (fermi, nascosti dal kit): la mesh nel .blend era ruotata di 90 gradi attorno a X; rimessa diritta.
- Cube (cubo predefinito di Blender, non fa parte della mappa) e le luci della scena non entrano nell'OBJ."""
import sys, pickle, numpy as np
from scipy import ndimage
from stato import carica

LOG = []
def log(s): LOG.append(s); print('[base]', s)

def costruisci(stato_fase2='fase2_h.obj.state.pkl', blend_pkl='fase3/blend_mesh.pkl', terr='fase3/terreno_blend.npz'):
    m = carica(stato_fase2)
    B = pickle.load(open(blend_pkl, 'rb'))
    mtl = set()
    for l in open('castello_mappa_estesa.mtl'):
        if l.startswith('newmtl'): mtl.add(l.split()[1])
    Vs = []; base = 0; nuovi = []
    strani = set()
    for o in m.objs:
        nm = o['name']
        if nm == 'Terreno' or not o['faces']:
            nuovi.append(dict(name=nm, faces=[], mats=[], smooth=[])); continue
        b = B[nm]
        P = b['V'].copy()
        if nm == 'Animali' and P[:, 2].max() < 0 and P[:, 1].min() < -50:
            P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)      # (x, z, -y) -> (x, y, z)
            log('Animali: mesh ruotata di 90 gradi nel .blend, rimessa diritta (bbox y %.1f..%.1f)' % (P[:, 1].min(), P[:, 1].max()))
        names = []
        for mn in b['mats']:
            if mn is None: names.append('stone_dark'); strani.add('None'); continue
            k = mn.split('.')[0] if mn not in mtl and mn.split('.')[0] in mtl else mn
            if k not in mtl: strani.add(mn)
            names.append(k)
        F = [[int(v) + base + 1 for v in b['lv'][a:a + n]] for a, n in zip(b['ls'], b['lt'])]
        nuovi.append(dict(name=nm, faces=F, mats=[names[i] for i in b['mi']], smooth=[bool(s) for s in b['sm']]))
        Vs.append(P); base += len(P)
    if strani: log('materiali non presenti nell\'MTL: %s' % sorted(strani))
    m.V = np.concatenate(Vs); m.objs = nuovi; m.invalidate()
    # terreno
    T = np.load(terr); Hb = T['Hb']
    dH = Hb - m.H
    nan = np.isnan(dH)
    idx = ndimage.distance_transform_edt(nan, return_distances=False, return_indices=True)
    dH = dH[idx[0], idx[1]]
    Hold = m.H.copy()
    m.H = m.H + dH
    ch = np.abs(dH) > 0.05
    log('terreno ricampionato sulla superficie scolpita: %d nodi cambiati di quota (%.1f..%+.1f m), %d nodi senza superficie riempiti dai vicini; quota massima %.1f m'
        % (int(ch.sum()), float(dH.min()), float(dH.max()), int(nan.sum()), float(m.H.max())))
    # fasce laterali
    b = m.obj('Base_Sezione'); vs = np.unique(np.concatenate([np.asarray(f) for f in b['faces']])) - 1
    P = m.V[vs]
    X, Z = m.grid_xz()
    xmin, xmax, zmin, zmax = X.min(), X.max(), Z.min(), Z.max()
    fi = np.clip(np.round(P[:, 0] / 0.9 - m.I0).astype(int), 0, m.H.shape[0] - 1)
    fj = np.clip(np.round((P[:, 2] - 0.5) / 0.9 - m.J0).astype(int), 0, m.H.shape[1] - 1)
    bordo = (np.abs(P[:, 0] - xmin) < 0.02) | (np.abs(P[:, 0] - xmax) < 0.02) | (np.abs(P[:, 2] - zmin) < 0.02) | (np.abs(P[:, 2] - zmax) < 0.02)
    ho = Hold[fi, fj]; hn = m.H[fi, fj]
    top = bordo & (np.abs(P[:, 1] - ho) < 0.06)
    mid = bordo & (np.abs(P[:, 1] - (ho - 2.5)) < 0.06)
    mov = (top | mid) & (np.abs(hn - ho) > 0.02)
    m.V[vs[mov], 1] += (hn - ho)[mov]
    log('fasce laterali del plastico riadattate ai bordi scolpiti: %d vertici' % int(mov.sum()))
    m.invalidate()
    return m

def run(m):
    return LOG
