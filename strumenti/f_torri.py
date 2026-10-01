"""Ingressi delle torri ai camminamenti: pavimento di ogni passaggio alla quota del camminamento che serve."""
import numpy as np, math, collections
from scipy.cluster.hierarchy import fcluster, linkage

LOG = []
def log(s): LOG.append(s); print('[torri]', s)

def run(m):
    o = m.obj('Torri')
    F = [np.array(f) - 1 for f in o['faces']]
    floors = []
    for i, (f, mt) in enumerate(zip(F, o['mats'])):
        if mt != 'street_stone': continue
        P = m.V[f]
        if np.ptp(P[:, 1]) < 0.02: floors.append((i, P.mean(0), P))
    C = np.array([c for _, c, _ in floors])
    lab = fcluster(linkage(C[:, [0, 2]], 'single'), 2.6, 'distance')
    mura = m.obj('Mura'); W = []
    for f, mt in zip(mura['faces'], mura['mats']):
        if mt != 'street_stone': continue
        P = m.V[np.array(f) - 1]
        if np.ptp(P[:, 1]) < 0.35: W.append(P.mean(0))
    W = np.array(W)
    # tutti i vertici di Torri (le facce non condividono vertici)
    allv = np.unique(np.concatenate(F))
    PV = m.V[allv]
    changed = 0; steps_before = []; steps_after = []; ntow = 0
    for k in range(1, lab.max() + 1):
        grp = [floors[i] for i in range(len(floors)) if lab[i] == k]
        cs = np.array([c for _, c, _ in grp])
        # centro = pavimento che minimizza la somma delle distanze
        dsum = [np.sum(np.hypot(cs[:, 0] - c[0], cs[:, 2] - c[2])) for c in cs]
        ci = int(np.argmin(dsum)); t = cs[ci]
        ntow += 1
        for j, (fi, c, P) in enumerate(grp):
            if j == ci: continue
            d = np.array([c[0] - t[0], c[2] - t[2]]); r = np.linalg.norm(d); u = d / r; v = np.array([-u[1], u[0]])
            # estensione del passaggio lungo u e larghezza
            rel = P[:, [0, 2]] - t[[0, 2]]
            a = rel @ u; b = rel @ v
            a0, a1 = a.min(), a.max(); hw = (b.max() - b.min()) / 2; bm = (b.max() + b.min()) / 2
            relw = W[:, [0, 2]] - t[[0, 2]]; dist = np.linalg.norm(relw, axis=1)
            cosang = (relw @ u) / np.maximum(dist, 1e-6)
            sel = (dist > a1 + 0.3) & (dist < a1 + 3.5) & (cosang > 0.93)
            if sel.sum() == 0: continue
            # quota del camminamento al piede della torre: il più vicino
            near = np.argsort(dist[sel])[:4]
            wy = float(np.median(W[sel][near, 1]))
            fy = c[1]
            # soffitto del passaggio: facce stone_dark orizzontali sopra il pavimento nella stessa area
            relv = PV[:, [0, 2]] - t[[0, 2]]
            av = relv @ u; bv = relv @ v
            inreg = (av > a0 - 0.05) & (av < a1 + 0.45) & (np.abs(bv - bm) < hw + 0.3)
            ys = PV[inreg, 1]
            cand = np.unique(np.round(ys[(ys > fy + 1.5) & (ys < fy + 3.0)], 2))
            if len(cand) == 0: continue
            cy = float(cand.min())
            steps_before.append(abs(wy - fy))
            if abs(wy - fy) < 0.06: steps_after.append(abs(wy - fy)); continue
            nf = wy
            h = cy - nf
            nc = cy if 1.9 <= h <= 2.6 else nf + 2.2
            # sposta vertici alle quote del pavimento e del soffitto nella regione del passaggio
            mf = inreg & (np.abs(PV[:, 1] - fy) < 0.025)
            mc = inreg & (np.abs(PV[:, 1] - cy) < 0.025)
            m.V[allv[mf], 1] = nf
            m.V[allv[mc], 1] = nc
            PV = m.V[allv]
            changed += 1; steps_after.append(0.0)
    m.invalidate('Torri')
    log('torri analizzate: %d; passaggi corretti: %d' % (ntow, changed))
    sb = np.array(steps_before)
    log('gradino all\'ingresso prima: medio %.2f m, max %.2f m (%d passaggi oltre 0.1 m); dopo: max %.2f m' % (sb.mean(), sb.max(), int((sb > 0.1).sum()), max(steps_after) if steps_after else 0))
    return LOG
