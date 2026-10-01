"""Conflitti della fase 2: componenti degli oggetti nuovi (case, scala, grotta, ponticello, dettagli) che si
compenetrano con altri oggetti (escluso terreno, acqua, mare). Controllo per riquadri, poi per vertici dentro."""
import sys, collections; sys.path.insert(0, 'tools')
import numpy as np
from stato import carica
m = carica(sys.argv[1])
NUOVI = ('Villaggio_Altopiano_Nuovo', 'Porto_Paese_Nuovo', 'Torre_Mago_Scala', 'Torre_Mago_Grotta', 'Torre_Mago_Ponticello', 'Torre_Mago_Dettagli')
SALTA = ('Terreno', 'Base_Sezione', 'Acqua', 'Mare', 'Fondale_Esteso') + NUOVI
altri = []
for o in m.objs:
    if o['name'] in SALTA or not o['faces']: continue
    for c in m.comps(o['name']): altri.append((o['name'], c))
LO = np.array([c['lo'] for _, c in altri]); HI = np.array([c['hi'] for _, c in altri])
R = collections.Counter(); es = []
for nm in NUOVI:
    if not m.has(nm): continue
    # gruppi dell'oggetto nuovo per riquadro (case intere)
    for c in m.comps(nm):
        ov = np.minimum(HI, c['hi']) - np.maximum(LO, c['lo'])
        k = np.nonzero(np.all(ov > 0.08, 1))[0]
        for i in k:
            on, oc = altri[i]
            V = m.V[oc['verts']]
            dentro = np.all((V > c['lo'] + 0.05) & (V < c['hi'] - 0.05), 1).sum()
            if dentro >= 2:
                R[(nm, on)] += 1
                if len(es) < 15: es.append((nm, on, np.round((oc['lo'] + oc['hi']) / 2, 1).tolist(), len(oc['faces'])))
print('compenetrazioni (componenti nuove / altro oggetto):', dict(R))
for e in es: print('  ', e)
# per case intere (riquadro dell'insieme delle parti a contatto)
from f2_appoggio import gruppi_bbox
R2 = collections.Counter(); es2 = []
for nm in ('Villaggio_Altopiano_Nuovo', 'Porto_Paese_Nuovo'):
    for g in gruppi_bbox(m.comps(nm), gap=0.12):
        if sum(len(c['faces']) for c in g) < 100: continue
        lo = np.min([c['lo'] for c in g], 0) + [0.3, 0.3, 0.3]; hi = np.max([c['hi'] for c in g], 0) - [0.3, 0.3, 0.3]
        ov = np.minimum(HI, hi) - np.maximum(LO, lo)
        for i in np.nonzero(np.all(ov > 0, 1))[0]:
            on, oc = altri[i]
            V = m.V[oc['verts']]
            if np.all((V > lo) & (V < hi), 1).sum() >= 2:
                R2[(nm, on)] += 1
                if len(es2) < 15: es2.append((nm, on, np.round((oc['lo'] + oc['hi']) / 2, 1).tolist(), len(oc['faces'])))
print('dentro le case nuove (case intere):', dict(R2))
for e in es2: print('  ', e)
