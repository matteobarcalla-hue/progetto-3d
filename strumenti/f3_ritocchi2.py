"""Fase 3 - ultimo passo:
- piccoli elementi originali rimasti sospesi dopo i ritocchi (il terreno sotto era stato abbassato per le vie del borgo e
  la casa nuova che li toccava è stata tolta): riappoggiati al terreno;
- tronchi rimasti senza chioma (la chioma ingrandita si era staccata dal tronco ed è stata tolta come sospesa): tolti
  anche i tronchi. I ceppi e i tronchi senza chioma che c'erano già nel modello di partenza restano."""
import json, collections, sys, os
import numpy as np
from scipy.spatial import cKDTree

LOG = []
def log(s): LOG.append(s); print('[ritocchi2]', s)
SOSPESI = 'fase3/mappa_fase3.obj.sospesi.json'
BASE = 'fase3/f3_base.obj.sospesi.json'

def run(m):
    S = json.load(open(SOSPESI)); B = json.load(open(BASE))
    Bc = np.array([o['centro'] for o in B])
    nuovi = [o for o in S if np.min(np.linalg.norm(Bc - np.array(o['centro']), axis=1)) > 0.5]
    fatti = []; restano = []
    for o in nuovi:
        c = np.array(o['centro']); d = np.array(o['dim'])
        lo = c - d / 2 - 0.02; hi = c + d / 2 + 0.02
        for nm in o['oggetti']:
            cs = [cc for cc in m.comps(nm) if np.all(cc['lo'] >= lo) and np.all(cc['hi'] <= hi)]
            if not cs: continue
            base = min(cs, key=lambda cc: cc['lo'][1])
            t = float(m.height_tri(np.array([(base['lo'][0] + base['hi'][0]) / 2]), np.array([(base['lo'][2] + base['hi'][2]) / 2]))[0])
            gap = base['lo'][1] - t
            if max(d[0], d[2]) < 4.0 and -1.5 < gap < 1.5:
                vs = np.unique(np.concatenate([cc['verts'] for cc in cs])); m.V[vs, 1] -= gap + 0.03
                m.invalidate(nm); fatti.append((nm, np.round(c, 1).tolist(), round(gap, 2)))
            else:
                restano.append((nm, np.round(c, 1).tolist()))
    log('elementi originali sospesi riappoggiati: %d %s; lasciati: %s' % (len(fatti), fatti, restano or 'nessuno'))
    # tronchi senza chioma nuovi
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase3'))
    from stato import carica
    mb = carica('fase3/f3_base.obj.state.pkl'); A = spogli(mb); B = spogli(m)
    Ac = np.array([a[1] for a in A])
    rem = collections.defaultdict(list); tolti = []; accorciati = []
    for nm, c, h, t in B:
        if np.min(np.hypot(Ac[:, 0] - c[0], Ac[:, 2] - c[2])) <= 1.0: continue
        # chiome attorno al tronco più in basso: il tronco spunta sopra la chioma e si accorcia
        o = m.obj(nm)
        sopra = [cc['hi'][1] for cc in m.comps(nm)
                 if collections.Counter(o['mats'][fi] for fi in cc['faces']).most_common(1)[0][0] in CH
                 and cc['lo'][0] - 0.3 <= t['hi'][0] and t['lo'][0] <= cc['hi'][0] + 0.3 and cc['lo'][2] - 0.3 <= t['hi'][2] and t['lo'][2] <= cc['hi'][2] + 0.3
                 and cc['hi'][1] > t['lo'][1] + 1.0 and cc['lo'][1] < t['hi'][1]]
        if sopra:
            ytop = max(sopra) - 0.3
            v = t['verts']; m.V[v, 1] = np.minimum(m.V[v, 1], ytop); m.invalidate(nm)
            accorciati.append((nm, np.round(c, 1).tolist(), round(float(t['hi'][1] - ytop), 1)))
        else:
            rem[nm] += t['faces']; tolti.append((nm, np.round(c, 1).tolist(), round(float(h), 1)))
    m.delete(dict(rem))
    # tronchi che dopo l'ingrandimento spuntano più di 1 m sopra la chioma (e non spuntavano così nel modello di partenza)
    Sb = sporgenze(mb); Sm = sporgenze(m)
    Pb = np.array([x[1][[0, 2]] for x in Sb if x[2] > 1.0]) if any(x[2] > 1.0 for x in Sb) else np.zeros((0, 2))
    for nm, c, d, ytop, t in Sm:
        if d <= 1.0: continue
        if len(Pb) and np.min(np.hypot(Pb[:, 0] - c[0], Pb[:, 1] - c[2])) < 1.5: continue
        v = t['verts']; m.V[v, 1] = np.minimum(m.V[v, 1], ytop - 0.3); m.invalidate(nm)
        accorciati.append((nm, np.round(c, 1).tolist(), round(float(d + 0.3), 1)))
    log('tronchi che spuntavano sopra la loro chioma, accorciati fin dentro la chioma: %d (di quanto, in m: %s)'
        % (len(accorciati), ', '.join('%.1f' % a[2] for a in accorciati)))
    log('tronchi rimasti senza chioma (non c\'erano nel modello di partenza), tolti: %d %s' % (len(tolti), tolti))
    return LOG

OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')
CH = {'tree_green', 'tree_light', 'tree_dark', 'tree_autumn', 'tree_olive', 'conifer', 'cypress', 'tree_bosco', 'hedge', 'vine', 'reed', 'lavender',
      'flower_red', 'flower_white', 'flower_yellow', 'flower_purple', 'crop_green', 'crop_gold'}
def spogli(m):
    """tronchi senza nessuna chioma dello stesso oggetto attorno alla loro metà alta"""
    out = []
    for nm in OGG:
        o = m.obj(nm); cs = m.comps(nm)
        prev = lambda c: collections.Counter(o['mats'][fi] for fi in c['faces']).most_common(1)[0][0]
        tr = [c for c in cs if prev(c) == 'trunk_brown']; fo = [c for c in cs if prev(c) in CH]
        if not fo: continue
        FL = np.array([c['lo'] for c in fo]); FH = np.array([c['hi'] for c in fo])
        kd = cKDTree(((FL + FH) / 2)[:, [0, 2]])
        for t in tr:
            ce = (t['lo'] + t['hi']) / 2; h = t['hi'][1] - t['lo'][1]; ymid = t['lo'][1] + 0.6 * h
            ok = any(FL[k][0] - 0.3 <= t['hi'][0] and t['lo'][0] <= FH[k][0] + 0.3 and FL[k][2] - 0.3 <= t['hi'][2] and t['lo'][2] <= FH[k][2] + 0.3
                     and FH[k][1] >= ymid and FL[k][1] <= t['hi'][1] + 0.6 for k in kd.query_ball_point(ce[[0, 2]], 12.0))
            if not ok: out.append((nm, ce, h, t))
    return out


def sporgenze(m):
    """tronchi con una chioma attorno: di quanto la cima del tronco supera la cima della chioma"""
    out = []
    for nm in OGG:
        o = m.obj(nm); cs = m.comps(nm)
        pv = lambda c: collections.Counter(o['mats'][fi] for fi in c['faces']).most_common(1)[0][0]
        tr = [c for c in cs if pv(c) == 'trunk_brown']; fo = [c for c in cs if pv(c) in CH]
        if not fo: continue
        FL = np.array([c['lo'] for c in fo]); FH = np.array([c['hi'] for c in fo]); kd = cKDTree(((FL + FH) / 2)[:, [0, 2]])
        for t in tr:
            ce = (t['lo'] + t['hi']) / 2
            ks = [k for k in kd.query_ball_point(ce[[0, 2]], 12.0) if FL[k][0] - 0.3 <= t['hi'][0] and t['lo'][0] <= FH[k][0] + 0.3
                  and FL[k][2] - 0.3 <= t['hi'][2] and t['lo'][2] <= FH[k][2] + 0.3 and FH[k][1] > t['lo'][1] + 1.0]
            if ks:
                ytop = max(FH[k][1] for k in ks); out.append((nm, ce, t['hi'][1] - ytop, ytop, t))
    return out
