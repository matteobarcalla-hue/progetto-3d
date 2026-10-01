"""Raggruppamento degli alberi: un albero = un tronco (trunk_brown) + le chiome assegnate a quel tronco.
Una chioma va al tronco più vicino il cui centro cade sotto la chioma (o entro 1.5 m); senza tronco resta da sola
(siepi, cespugli). Serve per togliere, spostare o copiare alberi interi senza lasciare chiome sospese."""
import numpy as np
from scipy.spatial import cKDTree

def gruppi_alberi(m, nm, comps=None):
    o = m.obj(nm)
    cs = comps if comps is not None else m.comps(nm)
    if not cs: return []
    tr = [k for k, c in enumerate(cs) if any(o['mats'][f] == 'trunk_brown' for f in c['faces'])]
    altri = [k for k in range(len(cs)) if k not in set(tr)]
    gr = {k: [k] for k in tr}
    if tr:
        T = np.array([((cs[k]['lo'] + cs[k]['hi']) / 2)[[0, 2]] for k in tr])
        kd = cKDTree(T)
        for k in altri:
            c = cs[k]; ce = ((c['lo'] + c['hi']) / 2)[[0, 2]]
            r = max(c['hi'][0] - c['lo'][0], c['hi'][2] - c['lo'][2]) / 2 + 0.3
            idx = kd.query_ball_point(ce, max(r, 1.5))
            dentro = [i for i in idx if c['lo'][0] - 0.3 <= T[i, 0] <= c['hi'][0] + 0.3 and c['lo'][2] - 0.3 <= T[i, 1] <= c['hi'][2] + 0.3]
            cand = dentro or [i for i in idx if np.hypot(*(T[i] - ce)) <= 1.5]
            # il tronco deve stare sotto la chioma (la chioma parte sopra la base del tronco)
            cand = [i for i in cand if cs[tr[i]]['lo'][1] < c['lo'][1] + 0.5]
            if cand:
                i = min(cand, key=lambda i: np.hypot(*(T[i] - ce)))
                gr[tr[i]].append(k)
            else:
                gr[('solo', k)] = [k]
    else:
        for k in altri: gr[('solo', k)] = [k]
    return [[cs[k] for k in v] for v in gr.values()]

def _dist_punti_triangoli(P, T):
    """distanza minima fra i punti P (n,3) e i triangoli T (m,3,3)"""
    best = np.inf
    for tri in T:
        a, b, c = tri
        ab = b - a; ac = c - a; ap = P - a
        d1 = ap @ ab; d2 = ap @ ac
        bp = P - b; d3 = bp @ ab; d4 = bp @ ac
        cp = P - c; d5 = cp @ ab; d6 = cp @ ac
        va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
        den = va + vb + vc; den = np.where(np.abs(den) < 1e-12, 1e-12, den)
        v = vb / den; w = vc / den
        Q = a + np.outer(v, ab) + np.outer(w, ac)
        # proiezione fuori dal triangolo: ripiego sul punto più vicino fra i vertici e i lati campionati
        fuori = (v < 0) | (w < 0) | (v + w > 1)
        if fuori.any():
            S = np.concatenate([a + np.outer(np.linspace(0, 1, 6), ab), a + np.outer(np.linspace(0, 1, 6), ac), b + np.outer(np.linspace(0, 1, 6), c - b)])
            dq = np.sqrt(((P[fuori, None, :] - S[None]) ** 2).sum(-1)).min(1)
            dd = np.linalg.norm(P - Q, axis=1); dd[fuori] = dq
        else:
            dd = np.linalg.norm(P - Q, axis=1)
        best = min(best, float(dd.min()))
    return best

def _tri(m, c, o):
    T = []
    for f in c['faces']:
        q = m.V[np.array(o['faces'][f]) - 1]
        for k in range(1, len(q) - 1): T.append((q[0], q[k], q[k + 1]))
    return np.array(T)

def _dentro(P, Q):
    """punti P dentro l'inviluppo convesso di Q"""
    from scipy.spatial import Delaunay
    try: return bool((Delaunay(Q).find_simplex(P) >= 0).any())
    except Exception: return False

def collegati(m, gruppo, soglia=0.15, nm=None):
    """parti del gruppo collegate alla parte più bassa per contatto (punto-faccia <= soglia) o compenetrazione
    (un vertice dentro l'altra parte); le altre sono staccate"""
    if len(gruppo) == 1: return gruppo, []
    o = None
    if nm is not None: o = m.obj(nm)
    base = min(range(len(gruppo)), key=lambda k: gruppo[k]['lo'][1])
    V = [m.V[c['verts']] for c in gruppo]
    T = [_tri(m, c, o) for c in gruppo] if o is not None else None
    vis = {base}; fr = [base]
    while fr:
        a = fr.pop()
        for b in range(len(gruppo)):
            if b in vis: continue
            ca, cb = gruppo[a], gruppo[b]
            if np.any(ca['lo'] - soglia > cb['hi']) or np.any(cb['lo'] - soglia > ca['hi']): continue
            ok = _dentro(V[b], V[a]) or _dentro(V[a], V[b])
            if not ok and T is not None:
                ok = _dist_punti_triangoli(V[b], T[a]) <= soglia or _dist_punti_triangoli(V[a], T[b]) <= soglia
            if ok: vis.add(b); fr.append(b)
    return [gruppo[k] for k in sorted(vis)], [gruppo[k] for k in range(len(gruppo)) if k not in vis]
