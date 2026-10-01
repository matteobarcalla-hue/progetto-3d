"""Correzione degli elementi sospesi individuati sul modello di partenza (orig.obj.sospesi.json)."""
import json, numpy as np, collections, math
import ops

LOG = []
def log(s): LOG.append(s); print('[sospesi]', s)

GROUND = {'Alberi', 'Alberi_Nuovi', 'Rocce', 'Poderi', 'Poderi_Nuovi', 'Campi', 'Siepi_e_Confini', 'Salice', 'Taverne',
          'Rovine', 'Cava', 'Elementi_Unici', 'Presidio', 'Villaggio_Altopiano', 'Porto', 'Borgo_Basso_Nuovo', 'Stalle',
          'Pascolo_Pastore', 'Poderi_Dettagli', 'Capitelli_Nuovi', 'Miniera_Ampliata', 'Borgo_Basso'}
WINDOW_OBJS = {'Borgo_Basso', 'Dettagli_Borgo_Basso', 'Villaggio_Altopiano', 'Porto', 'Borgo_Basso_Nuovo'}

def groups_from_json(m, S):
    out = []
    for s in S:
        c = np.array(s['centro']); d = np.array(s['dim']) / 2 + 0.02
        sel = {}
        for nm in s['oggetti']:
            fs = []
            for comp in m.comps(nm):
                if (comp['lo'] >= c - d).all() and (comp['hi'] <= c + d).all():
                    fs += comp['faces']
            if fs: sel[nm] = fs
        out.append((s, sel))
    return out

def terrain_under(m, lo, hi):
    xs = np.linspace(lo[0], hi[0], 5); zs = np.linspace(lo[2], hi[2], 5); X, Z = np.meshgrid(xs, zs)
    h = m.height(X.ravel(), Z.ravel()); return h.min(), h.max()

def window_sills(m, name):
    """vani finestra (window_dark) con quota inferiore e orientamento"""
    o = m.obj(name); W = []
    for i, (f, mt) in enumerate(zip(o['faces'], o['mats'])):
        if mt != 'window_dark': continue
        P = m.V[np.array(f) - 1]
        if np.ptp(P[:, 1]) < 0.5: continue
        W.append((P.mean(0), P[:, 1].min(), P))
    return W

def run(m):
    S = json.load(open('orig.obj.sospesi.json'))
    G = groups_from_json(m, S)
    reseat = 0; reattach = 0; skipped = collections.Counter()
    # finestre candidate per il riaggancio (tutti gli oggetti con edifici)
    WIN = {}
    for nm in ('Borgo_Basso', 'Villaggio_Altopiano', 'Porto', 'Borgo_Basso_Nuovo'):
        WIN[nm] = window_sills(m, nm)
    used = set()
    for s, sel in G:
        if not sel: skipped['non trovato'] += 1; continue
        vs = m.sel_verts(sel); P = m.V[vs]; lo, hi = P.min(0), P.max(0)
        tmin, tmax = terrain_under(m, lo, hi)
        gap = lo[1] - tmax
        objs = set(sel)
        mats = collections.Counter()
        for nm, fs in sel.items():
            o = m.obj(nm); mats.update(o['mats'][i] for i in fs)
        is_window = objs <= WINDOW_OBJS and ('wood_trim' in mats or 'stone_dark' in mats) and max(hi[0] - lo[0], hi[2] - lo[2]) < 1.1 and 0.5 < (hi[1] - lo[1]) < 1.6 and gap > 0.8
        if is_window:
            # cerca il vano con base alla quota del davanzale e senza davanzale proprio
            host = 'Villaggio_Altopiano' if 'Villaggio_Altopiano' in objs else ('Porto' if 'Porto' in objs else 'Borgo_Basso')
            best = None
            for k, (wc, wy, WP) in enumerate(WIN[host]):
                if (host, k) in used: continue
                dist = math.hypot(wc[0] - (lo[0] + hi[0]) / 2, wc[2] - (lo[2] + hi[2]) / 2)
                dyy = abs(wy - (lo[1] + 0.09))
                if dist < 9 and dyy < 0.25:
                    # il vano non deve avere già una cornice sotto
                    if best is None or dist < best[0]: best = (dist, k, wc, wy)
            if best:
                dist, k, wc, wy = best
                used.add((host, k))
                # centro orizzontale della cornice sul centro del vano; quota invariata
                c = (lo + hi) / 2
                m.V[vs, 0] += wc[0] - c[0]; m.V[vs, 2] += wc[2] - c[2]
                for nm in sel: m.invalidate(nm)
                reattach += 1; continue
            skipped['finestra senza vano libero'] += 1; continue
        gap2 = lo[1] - tmin
        if any(nm in GROUND for nm in objs) and 0.12 < gap2 < 8.0 and (hi[1] - lo[1]) < 12:
            dy = tmin - lo[1] - 0.03
            m.V[vs, 1] += dy
            for nm in sel: m.invalidate(nm)
            reseat += 1; continue
        skipped[next(iter(s['oggetti']))] += 1
    log('elementi riappoggiati al terreno: %d' % reseat)
    log('cornici/davanzali riagganciati alla propria finestra: %d' % reattach)
    log('non modificati (strutture con appoggio non a contatto, originali o da trattare altrove): %s' % dict(skipped))
    return LOG
