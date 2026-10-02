"""Fase 3 - ritocchi finali dopo i controlli esatti:
- case nuove le cui superfici intersecano un oggetto esistente (controllo triangolo contro triangolo, conflitti4):
  tolta la casa nuova intera (si toglie il nuovo, mai l'originale);
- elementi sospesi nuovi rimasti dopo f3_sospesi (secondo controllo): chiome senza tronco tolte, il resto solo riportato."""
import json, collections, pickle
import numpy as np
from shapely.geometry import Polygon, Point

LOG = []
def log(s): LOG.append(s); print('[ritocchi]', s)
CONFLITTI = 'fase3/conflitti_fin.json'
SOSPESI = 'fase3/fase3_fin.obj.sospesi.json'
BASE = 'fase3/f3_base.obj.sospesi.json'
OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')

def run(m):
    rem = collections.defaultdict(list)
    # 1) case nuove che intersecano oggetti esistenti
    C = json.load(open(CONFLITTI)); case = pickle.load(open('fase3/case_borghi.pkl', 'rb'))
    tolte = []
    for coppia, esempi in C['esempi'].items():
        nuovo, altro = [s.strip() for s in coppia.split('/')]
        if nuovo not in ('Borgo_Altopiano', 'Borgo_Porto'): continue
        for e in esempi:
            x, y, z = e['dove']
            for k, c in enumerate(case):
                if c['obj'] != nuovo or k in [t[0] for t in tolte]: continue
                T = Polygon(c['tutto'])
                if T.buffer(0.6).contains(Point(x, z)) and c['y'] - 1.0 < y < c['y'] + c['alt'] + 1.0:
                    for cc in m.comps(nuovo):
                        ce = (cc['lo'] + cc['hi']) / 2
                        if T.contains(Point(ce[0], ce[2])) and c['y'] - 1.0 < ce[1] < c['y'] + c['alt'] + 1.0:
                            rem[nuovo] += cc['faces']
                    tolte.append((k, nuovo, altro, c.get('via'), [round(x, 1), round(y, 1), round(z, 1)]))
                    break
    log('case nuove tolte perché toccavano un oggetto esistente: %d %s' % (len(tolte), [(t[1], 'via ' + str(t[3]), 'contro ' + t[2], t[4]) for t in tolte]))
    # 2) sospesi nuovi rimasti
    S = json.load(open(SOSPESI)); B = json.load(open(BASE))
    Bc = np.array([o['centro'] for o in B])
    nuovi = [o for o in S if np.min(np.linalg.norm(Bc - np.array(o['centro']), axis=1)) > 0.5]
    fatti = collections.Counter(); restano = []
    for o in nuovi:
        c = np.array(o['centro']); d = np.array(o['dim'])
        lo = c - d / 2 - 0.02; hi = c + d / 2 + 0.02
        for nm in o['oggetti']:
            if not m.has(nm): continue
            cs = [cc for cc in m.comps(nm) if np.all(cc['lo'] >= lo) and np.all(cc['hi'] <= hi)]
            if not cs: continue
            ob = m.obj(nm)
            senza_tronco = not any(ob['mats'][f] == 'trunk_brown' for cc in cs for f in cc['faces'])
            if nm in OGG and senza_tronco:
                for cc in cs: rem[nm] += cc['faces']
                fatti['chiome sospese senza tronco tolte'] += 1
            else:
                restano.append((nm, np.round(c, 1).tolist()))
    m.delete(dict(rem))
    log('elementi sospesi nuovi al secondo controllo: %d; %s; lasciati: %s' % (len(nuovi), ', '.join('%s %d' % kv for kv in fatti.items()) or 'nessuna correzione', restano or 'nessuno'))
    return LOG
