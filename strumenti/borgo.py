"""Generatore di borghi fitti: vie con pendenza limitata, piazze, case a schiera copiate dai modelli originali.
Le case si allineano sul filo della via, con la porta verso la via; si toccano muro contro muro (schiere) e ogni tanto
lasciano un passaggio. Altezze e larghezze variano poco (scala 0.92-1.15) e le gronde vicine non sono mai alla stessa quota."""
import numpy as np, math, collections
from scipy import ndimage
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
from shapely.prepared import prep
import ops

def resample(pts, step=0.5):
    P = np.asarray(pts, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    s = np.arange(0, d[-1] + 1e-9, step)
    if s[-1] < d[-1] - 1e-6: s = np.r_[s, d[-1]]
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1), s

def liscia_linea(pts, n=2):
    """Chaikin: angoli arrotondati"""
    P = np.asarray(pts, float)
    for _ in range(n):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1]); P = np.array(Q)
    return P

def limita_pendenza(h, s, g, fissi=None, iters=60):
    """g: pendenza massima (scalare o per tratto: g[i] vale fra i-1 e i)"""
    h = h.copy(); fissi = np.zeros(len(h), bool) if fissi is None else fissi
    g = np.full(len(h), g, float) if np.isscalar(g) else np.asarray(g, float)
    for _ in range(iters):
        for i in range(1, len(h)):
            if fissi[i]: continue
            ds = s[i] - s[i - 1]; h[i] = np.clip(h[i], h[i - 1] - g[i] * ds, h[i - 1] + g[i] * ds)
        for i in range(len(h) - 2, -1, -1):
            if fissi[i]: continue
            ds = s[i + 1] - s[i]; h[i] = np.clip(h[i], h[i + 1] - g[i + 1] * ds, h[i + 1] + g[i + 1] * ds)
    return h

def rot_y(P, th):
    c, s = math.cos(th), math.sin(th)
    return np.stack([P[:, 0] * c - P[:, 2] * s, P[:, 1], P[:, 0] * s + P[:, 2] * c], 1)

class Borgo:
    def __init__(self, m, nome_obj, zona, ostacoli, modelli, rng, log, vietati_mat=()):
        """zona: poligono (x,z) dove si può costruire; ostacoli: maschera celle (True = non costruire)"""
        self.m = m; self.obj = nome_obj; self.zona = prep(Polygon(zona)); self.zona_poly = Polygon(zona)
        self.ost = ostacoli; self.mod = modelli; self.rng = rng; self.log = log
        self.strade = []; self.piazze = []; self.case = []
        self.vietati_mat = vietati_mat
        self.n_mod = collections.Counter()

    # ------------------------------------------------------------ vie
    def via(self, pts, larg, mat='street_stone', gmax=0.10, liscia=2, nome='', quota_inizio=None, quota_fine=None, spalla=1.4):
        m = self.m
        P0 = liscia_linea(pts, liscia) if liscia else np.asarray(pts, float)
        P, s = resample(P0, 0.5)
        t = ndimage.uniform_filter1d(m.height(P[:, 0], P[:, 1]), 15, mode='nearest')
        fissi = np.zeros(len(P), bool)
        # incroci con vie già fatte: stessa quota
        for v in self.strade:
            d = np.hypot(P[:, None, 0] - v['P'][None, :, 0], P[:, None, 1] - v['P'][None, :, 1])
            k = d.argmin(1); dm = d[np.arange(len(P)), k]
            vic = dm < v['larg'] / 2 + 0.3
            t[vic] = v['h'][k[vic]]; fissi |= vic
        for pz in self.piazze:
            dentro = np.array([pz['poly'].contains(Point(p)) for p in P])
            t[dentro] = pz['y']; fissi |= dentro
        if quota_inizio is not None: t[0] = quota_inizio; fissi[0] = True
        if quota_fine is not None: t[-1] = quota_fine; fissi[-1] = True
        # pendenza necessaria fra due tratti fissi: se supera il 16% il tratto diventa una scalinata
        garr = np.full(len(P), gmax); gradini = []
        idx = np.nonzero(fissi)[0]
        for a, b in zip(idx[:-1], idx[1:]):
            if b - a < 2: continue
            req = abs(t[b] - t[a]) / (s[b] - s[a])
            if req > gmax:
                garr[a + 1:b + 1] = req * 1.03
                if req > 0.16:
                    gradini.append((a, b)); t[a:b + 1] = np.linspace(t[a], t[b], b - a + 1); fissi[a:b + 1] = True
        h = limita_pendenza(t, s, garr, fissi)
        ops.carve_path(m, [tuple(p) for p in P], list(h), width=larg, shoulder=spalla, mat=mat)
        poly = LineString(P).buffer(larg / 2, cap_style=2, join_style=2)
        v = dict(P=P, s=s, h=h, larg=larg, poly=poly, mat=mat, nome=nome, spalla=spalla, gradini=gradini)
        self.strade.append(v)
        g = np.abs(np.diff(h)) / np.diff(s)
        rampa = np.ones(len(g), bool)
        for a, b in gradini: rampa[a:b] = False
        ng = sum(int(np.ceil(abs(h[b] - h[a]) / 0.17)) for a, b in gradini)
        self.log('  via %s: %.0f m, larga %.1f m, quota %.1f-%.1f, pendenza max %.1f%%%s' % (nome, s[-1], larg, h.min(), h.max(), (g[rampa].max() if rampa.any() else 0) * 100,
                 ', scalinata di %d gradini' % ng if gradini else ''))
        return v

    def scalinate(self):
        """gradini di pietra sui tratti troppo ripidi delle vie (alzata <= 17 cm)"""
        Pts = []; F = []; M = []; n = 0
        for v in self.strade:
            for a, b in v['gradini']:
                P = v['P']; s = v['s']; h = v['h']
                ha, hb = h[a], h[b]; L = s[b] - s[a]
                k = int(np.ceil(abs(hb - ha) / 0.17)); alz = (hb - ha) / k
                w = v['larg'] / 2 - 0.05
                for q in range(k):
                    s0 = s[a] + L * q / k; s1 = s[a] + L * (q + 1) / k
                    def pt(sv):
                        x = np.interp(sv, s, P[:, 0]); z = np.interp(sv, s, P[:, 1])
                        i = min(np.searchsorted(s, sv), len(s) - 1); i0 = max(i - 2, 0); i1 = min(i + 2, len(s) - 1)
                        tg = P[i1] - P[i0]; tg = tg / (np.linalg.norm(tg) + 1e-9)
                        return np.array([x, z]), np.array([-tg[1], tg[0]])
                    (c0, n0), (c1, n1) = pt(s0), pt(s1)
                    # in salita (alz > 0) il gradino q copre [s0, s1] alla quota ha + (q+1) alz; in discesa ha + q alz
                    top = ha + (q + 1) * alz if alz > 0 else ha + q * alz
                    bot = min(np.interp(s0, s, h), np.interp(s1, s, h)) - 0.3
                    base = len(Pts)
                    for c, nn in ((c0, n0), (c1, n1)):
                        for sg in (-1, 1):
                            pp = c + nn * w * sg
                            Pts.append((pp[0], bot, pp[1])); Pts.append((pp[0], top, pp[1]))
                    # 0 b0- 1 t0- 2 b0+ 3 t0+ 4 b1- 5 t1- 6 b1+ 7 t1+
                    quads = [([1, 3, 7, 5], 'street_stone'), ([0, 2, 3, 1], 'stone_dark'), ([4, 5, 7, 6], 'stone_dark'),
                             ([0, 1, 5, 4], 'stone_dark'), ([2, 6, 7, 3], 'stone_dark')]
                    for f, mt in quads:
                        F.append([base + i for i in f]); M.append(mt)
                    n += 1
        if F:
            Pa = np.array(Pts)
            # normali verso l'esterno: la faccia di sopra verso l'alto, le altre lontano dal centro del gradino
            for i in range(0, len(F), 5):
                cen = Pa[F[i][0] - 0:F[i][0] + 8].mean(0) if False else None
            self.m.add_faces(self.obj, Pts, F, M, False)
        return n

    def piazza(self, poly_pts, mat='piazza_stone', y=None, blend=2.0, nome=''):
        m = self.m
        poly = Polygon(poly_pts)
        if y is None:
            xs = np.array([p[0] for p in poly_pts]); zs = np.array([p[1] for p in poly_pts])
            c = poly.centroid
            y = float(np.median(m.height(np.r_[xs, c.x], np.r_[zs, c.y])))
        ops.flatten_pad(m, poly_pts, y, blend=blend)
        cel = ops.cells_in_poly(m, poly_pts)
        m.M[cel & (m.M >= 0)] = m.mat_index(mat)
        pz = dict(poly=poly, y=y, nome=nome, pts=poly_pts)
        self.piazze.append(pz)
        self.log('  piazza %s: %.0f m2 a quota %.1f' % (nome, poly.area, y))
        return pz

    def ripassa_vie(self):
        """dopo le piazzole delle case: le vie e le piazze tornano esatte"""
        for pz in self.piazze:
            ops.flatten_pad(self.m, pz['pts'], pz['y'], blend=0.6)
        for v in self.strade:
            ops.carve_path(self.m, [tuple(p) for p in v['P']], list(v['h']), width=v['larg'], shoulder=0.5, mat=v['mat'])
        for pz in self.piazze:
            cel = ops.cells_in_poly(self.m, pz['pts']); self.m.M[cel & (self.m.M >= 0)] = self.m.mat_index('piazza_stone')

    def quota_via(self, v, x, z):
        d = np.hypot(v['P'][:, 0] - x, v['P'][:, 1] - z); return float(v['h'][d.argmin()])

    # ------------------------------------------------------------ case
    def _poligoni(self, t, xs, cx, cz, th):
        bl, bh = t['corpo']; lo, hi = t['tutto']
        def rett(a, b):
            Q = np.array([[a[0] * xs, 0, a[2]], [b[0] * xs, 0, a[2]], [b[0] * xs, 0, b[2]], [a[0] * xs, 0, b[2]]])
            Q = rot_y(Q, th)
            return Polygon([(cx + q[0], cz + q[2]) for q in Q])
        lo2 = lo.copy(); hi2 = hi.copy(); hi2[2] = min(hi[2], bh[2] + 0.02)      # davanti: gradini e soglie possono sporgere sulla via
        return rett(bl, bh), rett(lo2, hi2), rett(lo, hi)

    def _celle(self, poly):
        b = poly.bounds
        i0, j0 = self.m.ij(b[0], b[1]); i1, j1 = self.m.ij(b[2], b[3])
        i0 = max(int(np.floor(i0)), 0); j0 = max(int(np.floor(j0)), 0)
        i1 = min(int(np.ceil(i1)), self.ost.shape[0] - 1); j1 = min(int(np.ceil(j1)), self.ost.shape[1] - 1)
        out = []
        pp = prep(poly)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                x = 0.9 * (i + self.m.I0 + 0.5); z = 0.5 + 0.9 * (j + self.m.J0 + 0.5)
                if pp.intersects(Polygon([(x - 0.45, z - 0.45), (x + 0.45, z - 0.45), (x + 0.45, z + 0.45), (x - 0.45, z + 0.45)])):
                    out.append((i, j))
        return out

    def prova_casa(self, t, xs, ys, cx, cz, th, y, max_dislivello=2.8):
        corpo, ingombro, tutto = self._poligoni(t, xs, cx, cz, th)
        if not self.zona.contains(tutto): return None
        for v in self.strade:
            if corpo.intersects(v['poly'].buffer(-0.12)): return None
            if ingombro.buffer(-0.05).intersects(v['poly']): return None
        for pz in self.piazze:
            if ingombro.intersects(pz['poly'].buffer(-0.1)): return None
        cb = corpo.buffer(-0.14)
        for c in self.case:
            if cb.intersects(c['corpo']): return None
            if tutto.intersects(c['corpo'].buffer(-0.14)) and not ingombro.buffer(-0.3).disjoint(c['corpo']) : return None
        cel = self._celle(tutto)
        if any(self.ost[i, j] for i, j in cel): return None
        if self.vietati_mat:
            nomi = np.array(self.m.mats + ['<buco>'])
            if any(nomi[self.m.M[i, j]] in self.vietati_mat for i, j in cel): return None
        # terreno sotto il corpo
        b = corpo.bounds
        xx, zz = np.meshgrid(np.linspace(b[0], b[2], 6), np.linspace(b[1], b[3], 6))
        pts = [(a, c) for a, c in zip(xx.ravel(), zz.ravel()) if corpo.buffer(0.05).contains(Point(a, c))]
        if pts:
            hh = self.m.height(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
            if np.abs(hh - y).max() > max_dislivello: return None
        return corpo, ingombro, tutto

    def posa(self, t, xs, ys, cx, cz, th, y, polys, via=None):
        corpo, ingombro, tutto = polys
        self.case.append(dict(t=t, xs=xs, ys=ys, cx=cx, cz=cz, th=th, y=y, corpo=corpo, tutto=tutto, alt=t['alt'] * ys, via=via))
        self.n_mod[id(t)] += 1

    def fronte(self, v, lato, s0=None, s1=None, arretra=(0.0, 0.35), schiera=(3, 7), passaggio=(1.3, 2.4), scala_alt=(0.92, 1.15),
               max_larg=10.0, max_prof=10.5, prob_salto=0.0, tentativi=10):
        """case lungo un lato della via (lato +1 = sinistra nel verso dei punti, -1 = destra)"""
        rng = self.rng
        S = v['s']; P = v['P']
        s0 = 1.0 if s0 is None else s0; s1 = S[-1] - 1.0 if s1 is None else s1
        cand = [t for t in self.mod if t['larg'] <= max_larg and t['prof'] <= max_prof]
        s = s0; prev = None; n_fila = 0; lung_fila = rng.integers(*schiera); n = 0
        def punto(sc):
            x = np.interp(sc, S, P[:, 0]); z = np.interp(sc, S, P[:, 1])
            k = min(np.searchsorted(S, sc), len(S) - 1); k0 = max(k - 2, 0); k1 = min(k + 2, len(S) - 1)
            tg = P[k1] - P[k0]; tg = tg / (np.linalg.norm(tg) + 1e-9)
            return np.array([x, z]), tg
        while s < s1:
            ok = False
            if prob_salto and rng.random() < prob_salto:
                s += rng.uniform(3.0, 7.0); prev = None; n_fila = 0; continue
            # preferenze: modelli meno usati
            pesi = np.array([1.0 / (1 + self.n_mod[id(t)]) for t in cand]); pesi /= pesi.sum()
            ordine = rng.choice(len(cand), size=min(tentativi, len(cand)), replace=False, p=pesi)
            for k in ordine:
                t = cand[k]
                if prev is not None and (t['sporg']['sx'] > 0.45 or t['sporg']['dx'] > 0.45): continue
                xs = rng.uniform(0.96, 1.06)
                ys = rng.uniform(*scala_alt)
                if prev is not None and abs(t['alt'] * ys - prev['alt']) < 0.45:
                    ys = (prev['alt'] + (0.6 if rng.random() < 0.5 else -0.6)) / t['alt']
                    if not (0.85 <= ys <= 1.22): continue
                w = t['larg'] * xs
                sovr = 0.06 if prev is not None else 0.0
                sc = s - sovr + w / 2
                if sc + w / 2 > s1 + 0.5: continue
                p, tg = punto(sc)
                nrm = np.array([-tg[1], tg[0]]) * lato
                arr = rng.uniform(*arretra) if prev is None or rng.random() < 0.5 else (prev['arr'] if prev else 0.0)
                bl, bh = t['corpo']
                # distanza del centro del corpo dall'asse: metà via + arretramento + metà profondità del corpo
                dfr = v['larg'] / 2 + 0.05 + arr
                th = math.atan2(nrm[0], -nrm[1])
                # il fronte del corpo (bh.z locale) va a dfr dall'asse: centro locale (0,0) a dfr + bh.z
                c = p + nrm * (dfr + bh[2])
                y = float(np.interp(sc, S, v['h'])) - 0.08
                polys = self.prova_casa(t, xs, ys, c[0], c[1], th, y)
                if polys is None: continue
                # continuità della schiera: il nuovo corpo deve toccare il precedente (niente fessure di pochi cm)
                if prev is not None:
                    gap = polys[0].distance(prev['corpo'])
                    if 0.02 < gap < 0.9: continue
                self.posa(t, xs, ys, c[0], c[1], th, y, polys, via=v['nome'])
                prev = dict(alt=t['alt'] * ys, corpo=polys[0], arr=arr)
                s = sc + w / 2; ok = True; n += 1; n_fila += 1
                break
            if not ok:
                s += 0.7; prev = None; n_fila = 0
            elif n_fila >= lung_fila:
                s += rng.uniform(*passaggio); prev = None; n_fila = 0; lung_fila = rng.integers(*schiera)
        return n

    def casa_libera(self, t, cx, cz, th, y=None, xs=1.0, ys=1.0):
        if y is None: y = float(self.m.height(cx, cz)) - 0.08
        polys = self.prova_casa(t, xs, ys, cx, cz, th, y)
        if polys is None: return False
        self.posa(t, xs, ys, cx, cz, th, y, polys); return True

    # ------------------------------------------------------------ costruzione
    def costruisci(self, blend=1.3):
        m = self.m
        from matplotlib.path import Path
        X, Z = m.grid_xz()
        lab = np.full(m.H.shape, -1); ylab = np.full(m.H.shape, -1e9)
        Pall = []
        for k, c in enumerate(self.case):
            t = c['t']
            Q = t['P'] * np.array([c['xs'], c['ys'], 1.0])
            Q = rot_y(Q, c['th']) + np.array([c['cx'], c['y'], c['cz']])
            Pall.append(Q)
            ext = c['tutto'].buffer(0.3, join_style=2)
            b = ext.bounds
            i0, j0 = m.ij(b[0], b[1]); i1, j1 = m.ij(b[2], b[3])
            i0 = max(int(np.floor(i0)), 0); j0 = max(int(np.floor(j0)), 0); i1 = int(np.ceil(i1)) + 1; j1 = int(np.ceil(j1)) + 1
            sub = np.stack([X[i0:i1, j0:j1].ravel(), Z[i0:i1, j0:j1].ravel()], 1)
            ins = Path(np.array(ext.exterior.coords)).contains_points(sub).reshape(X[i0:i1, j0:j1].shape)
            yv = c['y'] + 0.05
            sel = ins & (yv > ylab[i0:i1, j0:j1])
            lab[i0:i1, j0:j1][sel] = k; ylab[i0:i1, j0:j1][sel] = yv
        inside = lab >= 0
        if inside.any():
            dist, idx = ndimage.distance_transform_edt(~inside, return_indices=True)
            dist = dist * 0.9
            tgt = ylab[idx[0], idx[1]]
            w = 1 - ops.smoothstep(0, blend, dist)
            m.H = np.where(inside, ylab, m.H * (1 - w) + tgt * w)
        V = np.concatenate(Pall) if Pall else np.zeros((0, 3))
        F = []; M = []; k = 0
        for c, Q in zip(self.case, Pall):
            F += [[i + k for i in f] for f in c['t']['F']]; M += c['t']['M']; k += len(Q)
        if len(V):
            m.add_faces(self.obj, V.tolist(), F, M, False)
        self.ripassa_vie()
        ng = self.scalinate()
        if ng: self.log('  gradini di pietra sui vicoli ripidi: %d' % ng)
        return len(F)

    def impronte(self):
        return unary_union([c['tutto'] for c in self.case] + [v['poly'] for v in self.strade] + [p['poly'] for p in self.piazze])
