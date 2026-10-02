"""Quota del terreno del .blend sui punti della griglia (interpolazione sui triangoli) + materiale per cella."""
import sys, pickle, numpy as np
sys.path.insert(0, 'tools')
from stato import carica
m = carica('fase2_h.obj.state.pkl')
B = pickle.load(open('fase3/blend_mesh.pkl', 'rb'))
t = B['Terreno']; P = t['V']; ls, lt, lv = t['ls'], t['lt'], t['lv']
tri = []; tmat = []
for k in range(3, int(lt.max()) + 1):
    sel = np.nonzero(lt == k)[0]
    for q in range(1, k - 1):
        tri.append(np.stack([lv[ls[sel]], lv[ls[sel] + q], lv[ls[sel] + q + 1]], 1)); tmat.append(t['mi'][sel])
tri = np.concatenate(tri); tmat = np.concatenate(tmat)
A, Bq, C = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
NI, NJ = m.H.shape
Hb = np.full((NI, NJ), np.nan); Hn = np.full((NI, NJ), -1e9)
def gi(x): return x / 0.9 - m.I0
def gj(z): return (z - 0.5) / 0.9 - m.J0
lo_i = np.ceil(gi(np.minimum(np.minimum(A[:, 0], Bq[:, 0]), C[:, 0])) - 1e-6).astype(int)
hi_i = np.floor(gi(np.maximum(np.maximum(A[:, 0], Bq[:, 0]), C[:, 0])) + 1e-6).astype(int)
lo_j = np.ceil(gj(np.minimum(np.minimum(A[:, 2], Bq[:, 2]), C[:, 2])) - 1e-6).astype(int)
hi_j = np.floor(gj(np.maximum(np.maximum(A[:, 2], Bq[:, 2]), C[:, 2])) + 1e-6).astype(int)
for di in range(0, int((hi_i - lo_i).max()) + 1):
    for dj in range(0, int((hi_j - lo_j).max()) + 1):
        ii = lo_i + di; jj = lo_j + dj
        ok = (ii <= hi_i) & (jj <= hi_j) & (ii >= 0) & (ii < NI) & (jj >= 0) & (jj < NJ)
        idx = np.nonzero(ok)[0]
        x = 0.9 * (ii[idx] + m.I0); z = 0.5 + 0.9 * (jj[idx] + m.J0)
        a, b, c = A[idx], Bq[idx], C[idx]
        v0 = np.stack([b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]], 1); v1 = np.stack([c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]], 1)
        v2 = np.stack([x - a[:, 0], z - a[:, 2]], 1)
        den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        good = np.abs(den) > 1e-9
        den = np.where(good, den, 1)
        u = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
        w = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
        ins = good & (u >= -1e-5) & (w >= -1e-5) & (u + w <= 1 + 1e-5)
        y = a[:, 1] + u * (b[:, 1] - a[:, 1]) + w * (c[:, 1] - a[:, 1])
        k = idx[ins]; y = y[ins]
        # superficie piu' alta (in caso di sovrapposizioni)
        np.maximum.at(Hn, (ii[k], jj[k]), y)
Hb = np.where(Hn > -1e8, Hn, np.nan)
print('punti griglia senza superficie nel blend:', int(np.isnan(Hb).sum()), '(nel mio: buchi M<0 adiacenti)')
dH = Hb - m.H
ch = np.abs(np.nan_to_num(dH)) > 0.05
print('punti con quota cambiata >5cm:', int(ch.sum()), 'min %.2f max %.2f' % (np.nanmin(dH), np.nanmax(dH)))
print('quota max mio %.1f  blend %.1f' % (m.H.max(), np.nanmax(Hb)))
X, Z = m.grid_xz()
from scipy import ndimage
lab, n = ndimage.label(ndimage.binary_dilation(ch, iterations=3))
zone = []
for k in range(1, n + 1):
    s = (lab == k) & ch
    if s.sum() == 0: continue
    zone.append((s.sum(), X[s].min(), X[s].max(), Z[s].min(), Z[s].max(), np.nanmin(dH[s]), np.nanmax(dH[s]), np.nanmax(Hb[s])))
zone.sort(reverse=True)
for zz in zone[:40]: print(' %6d punti x %.0f..%.0f z %.0f..%.0f dH %.2f..%.2f quota max %.1f' % zz)
print('zone totali', len(zone))
# materiali per cella dal centro dei triangoli
names = np.array(t['mats'])
cen = (A + Bq + C) / 3
ci = np.floor(gi(cen[:, 0])).astype(int); cj = np.floor(gj(cen[:, 2])).astype(int)
ok = (ci >= 0) & (ci < NI - 1) & (cj >= 0) & (cj < NJ - 1)
Mb = np.full(m.M.shape, -1)
mi_map = np.array([m.mat_index(nm) if nm else -1 for nm in t['mats']])
Mb[ci[ok], cj[ok]] = mi_map[tmat[ok]]
tol = (m.M >= 0) & (Mb < 0); nuove = (m.M < 0) & (Mb >= 0)
camb = (m.M >= 0) & (Mb >= 0) & (Mb != m.M)
print('celle tolte %d, nuove %d, materiale cambiato %d' % (tol.sum(), nuove.sum(), camb.sum()))
Xc, Zc = m.cell_xz()
for nome, s in (('tolte', tol), ('materiale', camb)):
    lab, n = ndimage.label(ndimage.binary_dilation(s, iterations=2))
    zz = []
    for k in range(1, n + 1):
        q = (lab == k) & s
        if q.sum(): zz.append((q.sum(), Xc[q].min(), Xc[q].max(), Zc[q].min(), Zc[q].max()))
    zz.sort(reverse=True)
    for z_ in zz[:12]: print(' %s: %d celle x %.0f..%.0f z %.0f..%.0f' % ((nome,) + z_))
np.savez('fase3/terreno_blend.npz', Hb=Hb, Mb=Mb, mats=np.array(m.mats))
