import sys, collections, numpy as np; sys.path.insert(0,'tools')
from model import Model
import math
def analyze(m, verbose=True):
    o = m.obj('Torri')
    # centri torri: pinnacoli in bronzo (20 facce) 
    cen = []
    for c in m.comps('Torri'):
        mats = set(o['mats'][i] for i in c['faces'])
        if mats == {'bronze'} and len(c['faces']) == 20:
            ce = (c['lo'] + c['hi']) / 2; cen.append(ce)
    cen = np.array(cen)
    # pavimenti dei passaggi: facce street_stone orizzontali in Torri
    floors = []
    for i, (f, mt) in enumerate(zip(o['faces'], o['mats'])):
        if mt != 'street_stone': continue
        P = m.V[np.array(f) - 1]
        if np.ptp(P[:, 1]) < 0.02: floors.append((i, P.mean(0), P))
    mura = m.obj('Mura'); W = []
    for f, mt in zip(mura['faces'], mura['mats']):
        if mt != 'street_stone': continue
        P = m.V[np.array(f) - 1]
        if np.ptp(P[:, 1]) < 0.35: W.append(P.mean(0))
    W = np.array(W)
    out = []
    for t in cen:
        fl = [(i, c, P) for i, c, P in floors if math.hypot(c[0] - t[0], c[2] - t[2]) < 5.5]
        # raggio torre dalla cima (anello): uso distanza max dei pavimenti
        rows = []
        for i, c, P in fl:
            d = np.array([c[0] - t[0], c[2] - t[2]]); r = np.linalg.norm(d)
            if r < 0.6:
                rows.append(dict(face=i, tipo='centro', y=c[1], dir=None)); continue
            u = d / r
            # camminamento nella stessa direzione, fra r+0.5 e r+4 m dal centro
            rel = W[:, [0, 2]] - t[[0, 2]]; dist = np.linalg.norm(rel, axis=1)
            cosang = (rel @ u) / np.maximum(dist, 1e-6)
            sel = (dist > r + 0.8) & (dist < r + 4.5) & (cosang > 0.93)
            wy = float(np.median(W[sel, 1])) if sel.sum() else None
            rows.append(dict(face=i, tipo='passaggio', y=c[1], dir=u, r=r, walk=wy, n=int(sel.sum())))
        out.append((t, rows))
    if verbose:
        for t, rows in out:
            s = ', '.join('%s y=%.2f walk=%s' % (r['tipo'][0], r['y'], ('%.2f' % r['walk']) if r.get('walk') is not None else '-') for r in rows)
            print('torre (%.1f,%.1f): %s' % (t[0], t[2], s))
    return out
if __name__ == '__main__':
    m = Model(); analyze(m)
