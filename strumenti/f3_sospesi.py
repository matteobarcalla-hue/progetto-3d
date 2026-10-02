"""Fase 3 - elementi sospesi introdotti dalla fase 3 (confronto con il modello di partenza dell'utente):
- parti staccate delle case nuove (copiate dai modelli originali che le avevano già staccate): tolte;
- alberi e cespugli sospesi: riappoggiati al suolo (gruppo intero); chiome sospese senza tronco: tolte;
- tutto il resto: solo riportato (non si tocca)."""
import json, collections, numpy as np
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[sospesi]', s)
SOSPESI = 'fase3/c_fin.obj.sospesi.json'
BASE = 'fase3/f3_base.obj.sospesi.json'
OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')

def run(m):
    S = json.load(open(SOSPESI)); B = json.load(open(BASE))
    Bc = np.array([o['centro'] for o in B])
    nuovi = [o for o in S if np.min(np.linalg.norm(Bc - np.array(o['centro']), axis=1)) > 0.5]
    rem = collections.defaultdict(list); fatti = collections.Counter(); restano = collections.Counter()
    for o in nuovi:
        c = np.array(o['centro']); d = np.array(o['dim'])
        lo = c - d / 2 - 0.02; hi = c + d / 2 + 0.02
        for nm in o['oggetti']:
            if not m.has(nm): continue
            cs = [cc for cc in m.comps(nm) if np.all(cc['lo'] >= lo) and np.all(cc['hi'] <= hi)]
            if not cs: continue
            if nm in ('Borgo_Altopiano', 'Borgo_Porto'):
                for cc in cs: rem[nm] += cc['faces']
                fatti['parti staccate delle case nuove tolte'] += 1
            elif nm in OGG:
                ob = m.obj(nm)
                tr = [cc for cc in cs if any(ob['mats'][f] == 'trunk_brown' for f in cc['faces'])]
                base = tr[0] if tr else min(cs, key=lambda cc: cc['lo'][1])
                t = float(m.height_tri(np.array([(base['lo'][0] + base['hi'][0]) / 2]), np.array([(base['lo'][2] + base['hi'][2]) / 2]))[0])
                gap = base['lo'][1] - t
                if tr or gap < 1.0:
                    vs = np.unique(np.concatenate([cc['verts'] for cc in cs])); m.V[vs, 1] -= gap + 0.08
                    fatti['alberi e cespugli riappoggiati'] += 1
                else:
                    for cc in cs: rem[nm] += cc['faces']
                    fatti['chiome sospese senza tronco tolte'] += 1
                m.invalidate(nm)
            else:
                # piccoli elementi rimasti sopra un terreno abbassato (pozzo della piazza, sassi, siepi lungo i sentieri): riappoggiati
                base = min(cs, key=lambda cc: cc['lo'][1])
                t = float(m.height_tri(np.array([(base['lo'][0] + base['hi'][0]) / 2]), np.array([(base['lo'][2] + base['hi'][2]) / 2]))[0])
                gap = base['lo'][1] - t
                if max(d[0], d[2]) < 4.0 and -1.5 < gap < 1.5:
                    vs = np.unique(np.concatenate([cc['verts'] for cc in cs])); m.V[vs, 1] -= gap + 0.05
                    fatti['piccoli elementi riappoggiati (%s)' % nm] += 1; m.invalidate(nm)
                else:
                    restano[nm] += 1
    m.delete(dict(rem))
    log('elementi sospesi nuovi rispetto al modello di partenza: %d; corretti: %s; lasciati (da controllare): %s'
        % (len(nuovi), ', '.join('%s %d' % kv for kv in fatti.most_common()) or 'nessuno', dict(restano) or 'nessuno'))
    return LOG
