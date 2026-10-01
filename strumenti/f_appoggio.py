"""Appoggio finale: gli elementi naturali (alberi, siepi, rocce, canne) e i pochi oggetti rimasti sollevati dopo le
modifiche del terreno vengono riabbassati fino a toccare il suolo. Usa l'elenco degli elementi sospesi del giro
precedente della pipeline (stessa sequenza di moduli, quindi stesse componenti)."""
import json, os, numpy as np, collections
import ops

LOG = []
def log(s): LOG.append(s); print('[appoggio]', s)

NATURALI = ('Alberi', 'Alberi_Nuovi', 'Siepi_e_Confini', 'Canneto_Fiume', 'Rocce', 'Rocce_Promontori')
NUOVI_OK = ('Torre_Mago', 'Dettagli_Porte_Fortezza', 'Poderi_Dettagli', 'Poderi')

def run(m, lista='fase1_b.obj.sospesi.json', orig='orig.obj.sospesi.json'):
    if not os.path.exists(lista):
        log('elenco degli elementi sospesi non trovato: nessuna correzione'); return LOG
    S = json.load(open(lista)); O = json.load(open(orig))
    Co = np.array([g['centro'] for g in O])
    fixed = collections.Counter(); skipped = collections.Counter()
    for g in S:
        nm = list(g['oggetti'])[0]
        c = np.array(g['centro']); d = np.array(g['dim'])
        nuovo = np.min(np.linalg.norm(Co - c, axis=1)) > 1.0
        tg = float(m.height_tri(c[0], c[2])); gap = g['y_min'] - tg
        ok = nm in NATURALI or (nm == 'Animali' and gap < 2.0) or (nm in NUOVI_OK and nuovo and gap < 1.0)
        if not ok:
            skipped[nm] += 1; continue
        lo = c - d / 2 - 0.05; hi = c + d / 2 + 0.05
        sel = {}
        for name in g['oggetti']:
            fs = []
            for comp in m.comps(name):
                if np.all(comp['lo'] >= lo) and np.all(comp['hi'] <= hi): fs += comp['faces']
            if fs: sel[name] = fs
        if not sel:
            skipped[nm] += 1; continue
        P = m.V[m.sel_verts(sel)]; ymin = P[:, 1].min()
        base = P[P[:, 1] < ymin + 0.3]
        t = ops.footprint_min(m, np.r_[base[:, 0].min(), 0, base[:, 2].min()], np.r_[base[:, 0].max(), 0, base[:, 2].max()], 5)
        dy = t - ymin - 0.03
        if dy < 0:
            m.translate(sel, (0, dy, 0)); fixed[nm] += 1
    log('elementi riappoggiati al suolo: %d (%s); lasciati come nel progetto originale: %d (%s)' % (
        sum(fixed.values()), ', '.join('%s %d' % kv for kv in fixed.most_common()), sum(skipped.values()), ', '.join('%s %d' % kv for kv in skipped.most_common())))
    return LOG
