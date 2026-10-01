"""Modelli low-poly articolati di animali e persone (stesse forme per l'OBJ e per il kit).
Sistema locale "Blender": X destra, Y avanti, Z su. Ogni modello = parti con perno (pivot) e genitore.
parte: dict(nome, genitore, perno (relativo al perno del genitore), V (relativi al proprio perno), F, M)"""
import numpy as np, math

def _frame(T, up=(0, 0, 1)):
    T = np.asarray(T, float); T = T / (np.linalg.norm(T) + 1e-12)
    up = np.asarray(up, float)
    if abs(np.dot(T, up)) > 0.95: up = np.array([0, 1.0, 0]) if abs(T[1]) < 0.9 else np.array([1.0, 0, 0])
    S = np.cross(T, up); S /= np.linalg.norm(S); U = np.cross(S, T)
    return S, U

def loft(path, rx, ry, n=6, up=(0, 0, 1), caps=(True, True), jitter=0.0, rng=None, phase=0.0, flat_bottom=0.0):
    """tubo a sezioni ellittiche lungo path (k,3); rx/ry raggi per stazione. Restituisce V, F (facce orientate fuori)"""
    path = np.asarray(path, float); k = len(path)
    V = []; F = []
    for i in range(k):
        T = path[min(i + 1, k - 1)] - path[max(i - 1, 0)]
        S, U = _frame(T, up)
        for j in range(n):
            a = phase + 2 * math.pi * j / n
            cx, cy = math.cos(a) * rx[i], math.sin(a) * ry[i]
            if flat_bottom and cy < -ry[i] * (1 - flat_bottom): cy = -ry[i] * (1 - flat_bottom)
            p = path[i] + cx * S + cy * U
            if jitter and rng is not None and 0 < i < k - 1:
                p = p + rng.normal(0, jitter, 3) * (rx[i] + ry[i]) / 2
            V.append(p)
    for i in range(k - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            F.append([a, b, b + n, a + n])
    if caps[0] and rx[0] > 1e-4: F.append(list(range(n))[::-1])
    if caps[1] and rx[-1] > 1e-4: F.append([(k - 1) * n + j for j in range(n)])
    V = np.array(V)
    # orientamento: normale verso l'esterno rispetto all'asse locale
    out = []
    for f in F:
        Q = V[f]; nn = np.zeros(3)
        for t in range(len(Q)): nn += np.cross(Q[t], Q[(t + 1) % len(Q)])
        c = Q.mean(0)
        if len(f) == 4:
            i0 = f[0] // n; axis = (path[i0] + path[min(i0 + 1, k - 1)]) / 2
            ref = c - axis
        else:
            ref = (path[0] - path[1]) if f[0] < n else (path[-1] - path[-2])
        out.append(f if np.dot(nn, ref) >= 0 else f[::-1])
    return V, out

def cone(base, tip, r, n=5):
    base = np.asarray(base, float); tip = np.asarray(tip, float)
    S, U = _frame(tip - base)
    V = [base + r * (math.cos(2 * math.pi * j / n) * S + math.sin(2 * math.pi * j / n) * U) for j in range(n)] + [tip]
    F = [[j, (j + 1) % n, n] for j in range(n)] + [list(range(n))[::-1]]
    V = np.array(V); c = V.mean(0); out = []
    for f in F:
        Q = V[f]; nn = np.cross(Q[1] - Q[0], Q[2] - Q[0])
        out.append(f if np.dot(nn, Q.mean(0) - c) >= 0 else f[::-1])
    return V, out

def blade(pts_a, pts_b):
    """striscia a doppia faccia (criniera, pinne, ali sottili): due polilinee -> quad su entrambi i lati"""
    A = np.asarray(pts_a, float); Bp = np.asarray(pts_b, float); k = len(A)
    V = np.concatenate([A, Bp]); F = []
    for i in range(k - 1):
        F.append([i, i + 1, k + i + 1, k + i]); F.append([k + i, k + i + 1, i + 1, i])
    return V, F

class Part:
    def __init__(self, nome, genitore, perno):
        self.nome = nome; self.genitore = genitore; self.perno = np.asarray(perno, float)
        self.V = []; self.F = []; self.M = []
    def add(self, VF, mat, origin=(0, 0, 0)):
        V, F = VF; b = len(self.V)
        self.V += (np.asarray(V, float) - np.asarray(origin, float)).tolist()
        mats = mat if isinstance(mat, list) else [mat] * len(F)
        self.F += [[b + v for v in f] for f in F]; self.M += mats
        return self
    def dict(self):
        return dict(nome=self.nome, genitore=self.genitore, perno=[round(float(v), 3) for v in self.perno],
                    V=[[round(float(c), 3) for c in v] for v in self.V], F=self.F, M=self.M)

# ------------------------------------------------------------------ quadrupedi
Q = {
 # L corpo, larghezza, altezza corpo, altezza al garrese (terra->schiena), collo (lunghezza, inclinazione gradi), testa (lunghezza, larg., alt.), coda, extra
 'cow':    dict(L=1.75, W=0.62, Hb=0.72, back=1.38, neck=(0.45, 25), head=(0.55, 0.22, 0.26), tail=(0.85, 'ciuffo'), ears=0.13, horns='corna_vacca', legr=0.085, hoof='stone_dark', udder=True),
 'horse':  dict(L=1.55, W=0.48, Hb=0.62, back=1.55, neck=(0.85, 50), head=(0.62, 0.17, 0.24), tail=(0.95, 'crine'), ears=0.14, mane=True, legr=0.07, hoof='stone_dark'),
 'donkey': dict(L=1.2, W=0.42, Hb=0.52, back=1.15, neck=(0.55, 40), head=(0.5, 0.16, 0.2), tail=(0.6, 'ciuffo'), ears=0.26, mane=True, legr=0.06, hoof='stone_dark', muso='fur_white'),
 'sheep':  dict(L=0.95, W=0.56, Hb=0.55, back=0.85, neck=(0.25, 30), head=(0.3, 0.12, 0.15), tail=(0.18, None), ears=0.1, legr=0.04, hoof='stone_dark', lana=True),
 'goat':   dict(L=0.9, W=0.36, Hb=0.42, back=0.8, neck=(0.35, 45), head=(0.3, 0.1, 0.14), tail=(0.14, 'su'), ears=0.1, horns='corna_capra', legr=0.035, hoof='stone_dark', barba=True),
 'pig':    dict(L=1.1, W=0.5, Hb=0.52, back=0.78, neck=(0.12, 10), head=(0.36, 0.2, 0.22), tail=(0.14, 'ricciolo'), ears=0.1, legr=0.05, hoof='stone_dark', grugno=True),
 'deer':   dict(L=1.15, W=0.36, Hb=0.46, back=1.1, neck=(0.55, 50), head=(0.36, 0.11, 0.15), tail=(0.14, None), ears=0.13, horns='palchi', legr=0.04, hoof='stone_dark', slanciato=True),
 'dog':    dict(L=0.65, W=0.24, Hb=0.3, back=0.55, neck=(0.2, 45), head=(0.26, 0.1, 0.12), tail=(0.35, 'su'), ears=0.09, legr=0.03, hoof=None),
}

def quadrupede(sp, col_corpo, col_zampe=None, rng=None, maschio=True):
    p = Q[sp]; rng = rng or np.random.default_rng(0)
    L, W, Hb, back = p['L'], p['W'], p['Hb'], p['back']
    zc = back - Hb / 2                              # centro corpo
    legs_mat = col_zampe or col_corpo
    parts = {}
    corpo = Part('corpo', None, (0, 0, zc))
    # tronco: stazioni dalla groppa al petto (y), con garrese più alto per cavalli/cervi
    st = [(-0.5, 0.55, 0.62, 0.02), (-0.42, 0.85, 0.9, 0.02), (-0.25, 1.0, 1.0, 0.0), (0.0, 1.0, 1.0, -0.03),
          (0.25, 0.95, 1.0, 0.0), (0.4, 0.82, 0.92, 0.04), (0.5, 0.5, 0.62, 0.06)]
    if p.get('lana'): st = [(y, rx * 1.08, rz * 1.05, dz) for (y, rx, rz, dz) in st]
    path = [(0, y * L, dz * Hb) for (y, rx, rz, dz) in st]
    rx = [rx * W / 2 for (y, rx, rz, dz) in st]; rz = [rz * Hb / 2 for (y, rx, rz, dz) in st]
    body_mat = 'wool_white' if p.get('lana') and col_corpo in ('wool_white', None) else col_corpo
    corpo.add(loft(path, rx, rz, n=8 if not p.get('lana') else 10, up=(0, 0, 1), jitter=0.06 if p.get('lana') else 0.0, rng=rng, phase=math.pi / 8), body_mat)
    if sp == 'cow' and col_corpo == 'fur_white':
        Vb = np.array(corpo.V); cen = [(rng.uniform(-0.4, 0.3) * L, rng.choice([-1, 1]) * W * 0.5, rng.uniform(-0.1, 0.3) * Hb) for _ in range(4)]
        for fi, f in enumerate(corpo.F):
            c = Vb[f].mean(0)
            if any(math.hypot(c[1] - cy, (c[0] - cx) * 0.6) < 0.22 and np.sign(c[0]) == np.sign(cx) for cy, cx, cz in cen):
                corpo.M[fi] = 'fur_black'
    if p.get('udder'):
        corpo.add(loft([(0, -0.18 * L, -Hb * 0.45), (0, -0.18 * L, -Hb * 0.62)], [0.12, 0.08], [0.1, 0.07], n=5), 'wall_plaster_rose')
    parts['corpo'] = corpo
    # collo + testa
    nl, na = p['neck']; a = math.radians(na)
    nb = np.array([0, 0.42 * L, 0.18 * Hb])                     # base del collo (rispetto al corpo)
    collo = Part('collo', 'corpo', nb)
    d = np.array([0, math.cos(a), math.sin(a)])
    n0 = np.zeros(3); n1 = n0 + d * nl
    nr0 = min(W, Hb) * 0.36; nr1 = nr0 * 0.62
    hl, hw, hh = p['head']
    if nl > 0.15:
        collo.add(loft([n0 - d * 0.08, n0 + d * nl * 0.5, n1], [nr0 * 0.95, nr0 * 0.78, nr1], [nr0 * 1.15, nr0 * 0.9, nr1 * 1.05], n=6, up=(0, -1, 0) if na > 60 else (0, 0, 1)), col_corpo if not p.get('lana') else legs_mat)
    # testa: dal cranio al muso, inclinata verso il basso
    ha = math.radians(-55 if sp in ('horse', 'donkey', 'deer', 'goat') else (-35 if sp in ('cow', 'sheep') else -15))
    hd = np.array([0, math.cos(ha), math.sin(ha)])
    h0 = n1 + np.array([0, 0.02, hh * 0.25]); h1 = h0 + hd * hl
    head_mat = legs_mat if sp == 'sheep' else col_corpo
    collo.add(loft([h0 - hd * hl * 0.12, h0 + hd * hl * 0.3, h0 + hd * hl * 0.72, h1], [hw * 0.8, hw, hw * 0.78, hw * 0.55], [hh * 0.8, hh, hh * 0.72, hh * 0.5], n=6, up=(0, 0, 1)), head_mat)
    muso = p.get('muso')
    if sp in ('cow', 'pig') or muso:
        collo.add(loft([h1 - hd * 0.04, h1 + hd * 0.02], [hw * 0.58, hw * 0.5], [hh * 0.52, hh * 0.45], n=6), 'wall_plaster_rose' if sp in ('cow', 'pig') else muso)
    # occhi (piccoli rombi scuri)
    for s in (-1, 1):
        e = h0 + hd * hl * 0.3 + np.array([s * hw * 0.98, 0, hh * 0.28])
        collo.add(cone(e - np.array([s * 0.012, 0, 0]), e + np.array([s * 0.02, 0, 0]), 0.022 * (1 + L), n=4), 'stone_dark')
    # orecchie
    er = p['ears']
    for s in (-1, 1):
        base = h0 + np.array([s * hw * 0.75, -hl * 0.02, hh * 0.72])
        if sp in ('pig', 'dog') or (sp == 'sheep'):
            tip = base + np.array([s * er * 0.9, er * 0.35, -er * 0.25])
        else:
            tip = base + np.array([s * er * 0.45, -er * 0.25, er * 0.9])
        collo.add(cone(base, tip, er * 0.28, n=4), head_mat)
    # corna / palchi
    hr = p.get('horns')
    if hr == 'corna_vacca':
        for s in (-1, 1):
            b0 = h0 + np.array([s * hw * 0.7, 0, hh * 0.85])
            collo.add(cone(b0, b0 + np.array([s * 0.18, 0.05, 0.12]), 0.035, n=5), 'stone_light')
    elif hr == 'corna_capra':
        for s in (-1, 1):
            b0 = h0 + np.array([s * hw * 0.45, 0, hh * 0.9])
            collo.add(loft([b0, b0 + np.array([s * 0.03, -0.08, 0.12]), b0 + np.array([s * 0.06, -0.2, 0.14])], [0.03, 0.022, 0.004], [0.03, 0.022, 0.004], n=4), 'stone_light')
    elif hr == 'palchi' and maschio:
        for s in (-1, 1):
            b0 = h0 + np.array([s * hw * 0.5, -0.02, hh * 0.9])
            m1 = b0 + np.array([s * 0.12, -0.06, 0.28]); t1 = m1 + np.array([s * 0.1, -0.05, 0.22])
            collo.add(loft([b0, m1, t1], [0.022, 0.016, 0.004], [0.022, 0.016, 0.004], n=4), 'trunk_brown')
            collo.add(cone(m1, m1 + np.array([s * 0.02, 0.12, 0.14]), 0.012, n=4), 'trunk_brown')
            collo.add(cone(b0 + (m1 - b0) * 0.4, b0 + (m1 - b0) * 0.4 + np.array([0, 0.14, 0.08]), 0.012, n=4), 'trunk_brown')
    if p.get('mane'):
        A = [n0 + d * t * nl + np.array([0, -0.02, nr0 * (1.05 - 0.4 * t)]) for t in np.linspace(0.0, 1.0, 5)]
        Bm = [q + np.array([0, -0.05, 0.1 + 0.02 * k]) for k, q in enumerate(A)]
        collo.add(blade(A, Bm), legs_mat if sp == 'horse' else 'fur_black')
    if p.get('barba'):
        b0 = h1 - hd * 0.05 + np.array([0, 0, -hh * 0.4])
        collo.add(cone(b0, b0 + np.array([0, -0.02, -0.12]), 0.03, n=4), col_corpo)
    if p.get('grugno'):
        collo.add(loft([h1, h1 + hd * 0.05], [hw * 0.45, hw * 0.45], [hh * 0.38, hh * 0.38], n=6), 'wall_plaster_rose')
    parts['collo'] = collo
    # coda
    tl, tt = p['tail']
    tb = np.array([0, -0.5 * L + 0.02, 0.3 * Hb])
    coda = Part('coda', 'corpo', tb)
    if tt == 'su':
        tp = [(0, 0, 0), (0, -tl * 0.4, tl * 0.5), (0, -tl * 0.7, tl * 0.75)]
    elif tt == 'ricciolo':
        tp = [(0, 0, 0), (0, -tl * 0.5, 0.02), (0.04, -tl * 0.7, 0.08), (0.02, -tl * 0.55, 0.12)]
    else:
        tp = [(0, 0, 0), (0, -tl * 0.18, -tl * 0.35), (0, -tl * 0.22, -tl * 0.95)]
    rr = 0.028 if sp not in ('sheep', 'deer') else 0.06
    coda.add(loft(tp, [rr] * (len(tp) - 1) + [rr * 0.5], [rr] * (len(tp) - 1) + [rr * 0.5], n=4), col_corpo if sp not in ('horse',) else legs_mat)
    if tt == 'ciuffo':
        e = np.array(tp[-1]); coda.add(cone(e + np.array([0, 0, 0.1]), e + np.array([0, -0.02, -0.18]), 0.05, n=5), 'fur_black' if col_corpo != 'fur_black' else 'fur_brown')
    if tt == 'crine':
        coda.parts_note = 'crine'
        coda.add(loft([(0, 0, 0), (0, -0.12, -0.25), (0, -0.16, -0.7), (0, -0.14, -tl)], [0.06, 0.09, 0.08, 0.02], [0.05, 0.07, 0.06, 0.02], n=5), legs_mat)
    parts['coda'] = coda
    # zampe: anca/spalla -> ginocchio/garretto -> zoccolo
    lr = p['legr']; zbot = -zc                           # quota del suolo rispetto al corpo
    for nome, sx, sy in (('ant_sx', -1, 1), ('ant_dx', 1, 1), ('post_sx', -1, -1), ('post_dx', 1, -1)):
        hip = np.array([sx * W * 0.28, sy * L * 0.33, -Hb * 0.12])
        leg_len = hip[2] - zbot
        up_len = leg_len * 0.48; lo_len = leg_len - up_len
        up = Part('zampa_' + nome, 'corpo', hip)
        k1 = 1.0 if sy > 0 else 1.25
        up.add(loft([(0, 0, 0.1), (0, 0.01 * sy, -up_len * 0.5), (0, 0, -up_len)], [lr * 1.9 * k1, lr * 1.35 * k1, lr * 0.95], [lr * 2.3 * k1, lr * 1.5 * k1, lr], n=5, up=(0, 1, 0)), legs_mat if sp in ('sheep',) else col_corpo)
        lo = Part('stinco_' + nome, 'zampa_' + nome, (0, 0, -up_len))
        lm = legs_mat
        lo.add(loft([(0, 0, 0.02), (0, -0.015 * sy, -lo_len * 0.55), (0, 0, -lo_len + 0.07)], [lr * 0.95, lr * 0.75, lr * 0.8], [lr, lr * 0.8, lr * 0.85], n=5, up=(0, 1, 0)), lm)
        if p.get('hoof'):
            lo.add(loft([(0, 0.01, -lo_len + 0.08), (0, 0.02, -lo_len)], [lr * 0.95, lr * 1.05], [lr * 1.05, lr * 1.2], n=5, up=(0, 1, 0)), p['hoof'])
        else:
            lo.add(loft([(0, 0.0, -lo_len + 0.07), (0, 0.05, -lo_len + 0.01)], [lr * 1.0, lr * 1.1], [lr * 0.9, lr * 0.6], n=5, up=(0, 1, 0)), lm)
        parts[up.nome] = up; parts[lo.nome] = lo
    return parts

# ------------------------------------------------------------------ uccelli
def gallina(col, rng=None):
    parts = {}
    c = Part('corpo', None, (0, 0, 0.3))
    c.add(loft([(0, -0.16, 0.02), (0, -0.08, 0.0), (0, 0.04, 0.0), (0, 0.13, 0.03)], [0.07, 0.12, 0.12, 0.07], [0.08, 0.12, 0.12, 0.08], n=6), col)
    for k, (ax, az) in enumerate(((-0.03, 0.2), (0.0, 0.24), (0.03, 0.2))):
        c.add(cone((ax, -0.12, 0.05), (ax * 2, -0.24, az), 0.03, n=3), col)
    for s in (-1, 1):
        c.add(blade([(s * 0.11, 0.08, 0.04), (s * 0.12, -0.02, 0.05), (s * 0.11, -0.12, 0.05)], [(s * 0.115, 0.06, -0.04), (s * 0.125, -0.03, -0.05), (s * 0.115, -0.12, -0.02)]), col)
    parts['corpo'] = c
    n = Part('collo', 'corpo', (0, 0.11, 0.06))
    n.add(loft([(0, 0, 0), (0, 0.03, 0.09), (0, 0.04, 0.15)], [0.05, 0.045, 0.045], [0.05, 0.045, 0.045], n=5), col)
    n.add(loft([(0, 0.03, 0.15), (0, 0.07, 0.19), (0, 0.1, 0.18)], [0.045, 0.045, 0.03], [0.05, 0.05, 0.035], n=5), col)
    n.add(cone((0, 0.1, 0.18), (0, 0.15, 0.17), 0.015, n=4), 'beak_orange')
    n.add(blade([(0, 0.02, 0.22), (0, 0.06, 0.235), (0, 0.1, 0.215)], [(0, 0.02, 0.2), (0, 0.06, 0.2), (0, 0.1, 0.195)]), 'flag_red')
    n.add(cone((0, 0.1, 0.155), (0, 0.11, 0.11), 0.012, n=3), 'flag_red')
    parts['collo'] = n
    for nome, s in (('zampa_sx', -1), ('zampa_dx', 1)):
        z = Part(nome, 'corpo', (s * 0.05, 0.0, -0.08))
        z.add(loft([(0, 0, 0.02), (0, 0, -0.2)], [0.012, 0.01], [0.012, 0.01], n=4), 'beak_orange')
        z.add(blade([(0, -0.02, -0.215), (0, 0.07, -0.215)], [(s * 0.03, 0.05, -0.22), (-s * 0.03, 0.05, -0.22)]), 'beak_orange')
        parts[nome] = z
    return parts

def anatra(col, sp='duck', maschio=True):
    s_ = 1.0 if sp == 'duck' else 1.9
    parts = {}
    c = Part('corpo', None, (0, 0, 0.05 * s_))
    c.add(loft([(0, -0.24 * s_, 0.05 * s_), (0, -0.14 * s_, 0.0), (0, 0.04 * s_, -0.01 * s_), (0, 0.17 * s_, 0.02 * s_)],
               [0.04 * s_, 0.12 * s_, 0.13 * s_, 0.07 * s_], [0.03 * s_, 0.08 * s_, 0.09 * s_, 0.06 * s_], n=6, flat_bottom=0.35), col)
    parts['corpo'] = c
    n = Part('collo', 'corpo', (0, 0.14 * s_, 0.04 * s_))
    head_col = 'hedge' if (sp == 'duck' and maschio) else col
    if sp == 'swan':
        pth = [(0, 0, 0), (0, 0.05 * s_, 0.12 * s_), (0, 0.02 * s_, 0.26 * s_), (0, 0.07 * s_, 0.36 * s_)]
        n.add(loft(pth, [0.035 * s_, 0.028 * s_, 0.026 * s_, 0.03 * s_], [0.04 * s_, 0.03 * s_, 0.028 * s_, 0.035 * s_], n=5), col)
        hp = np.array(pth[-1])
    else:
        n.add(loft([(0, 0, 0), (0, 0.02, 0.09), (0, 0.04, 0.14)], [0.04, 0.035, 0.035], [0.045, 0.04, 0.04], n=5), head_col)
        hp = np.array([0, 0.04, 0.14])
    n.add(loft([hp - (0, 0.02 * s_, 0), hp + (0, 0.04 * s_, 0)], [0.04 * s_ * (0.7 if sp == 'swan' else 1), 0.035 * s_ * 0.7], [0.042 * s_, 0.035 * s_ * 0.8], n=5), head_col)
    n.add(loft([hp + (0, 0.04 * s_, -0.005 * s_), hp + (0, 0.1 * s_, -0.012 * s_)], [0.02 * s_, 0.018 * s_], [0.01 * s_, 0.006 * s_], n=4), 'beak_orange')
    parts['collo'] = n
    return parts

def gabbiano(vola=False):
    parts = {}
    c = Part('corpo', None, (0, 0, 0.16))
    c.add(loft([(0, -0.2, 0.02), (0, -0.1, 0.0), (0, 0.06, 0.0), (0, 0.15, 0.02)], [0.02, 0.07, 0.075, 0.05], [0.015, 0.06, 0.07, 0.05], n=6), 'feather_white')
    c.add(blade([(-0.04, -0.18, 0.02), (0.04, -0.18, 0.02)], [(-0.05, -0.28, 0.03), (0.05, -0.28, 0.03)]), 'feather_white')
    parts['corpo'] = c
    n = Part('collo', 'corpo', (0, 0.14, 0.03))
    n.add(loft([(0, -0.02, 0), (0, 0.03, 0.04), (0, 0.08, 0.04)], [0.045, 0.045, 0.03], [0.045, 0.05, 0.032], n=5), 'feather_white')
    n.add(cone((0, 0.08, 0.035), (0, 0.13, 0.025), 0.012, n=4), 'beak_orange')
    parts['collo'] = n
    for nome, s in (('ala_sx', -1), ('ala_dx', 1)):
        a = Part(nome, 'corpo', (s * 0.05, 0.02, 0.04))
        if vola:
            a.add(blade([(0, 0.07, 0), (0, -0.1, 0.0)], [(s * 0.32, 0.03, 0.01), (s * 0.3, -0.1, 0.0)]), 'fur_grey')
            a.add(blade([(s * 0.32, 0.03, 0.01), (s * 0.3, -0.1, 0.0)], [(s * 0.62, -0.06, 0.0), (s * 0.6, -0.12, 0.0)]), 'fur_grey')
        else:   # ala chiusa lungo il fianco, punte nere sulla coda
            a.add(blade([(s * 0.025, 0.06, 0.0), (s * 0.03, -0.08, 0.0), (s * 0.015, -0.25, 0.01)], [(s * 0.03, 0.05, -0.06), (s * 0.035, -0.08, -0.06), (s * 0.015, -0.24, -0.01)]), 'fur_grey')
            a.add(cone((s * 0.012, -0.22, 0.0), (s * 0.005, -0.31, 0.0), 0.012, n=3), 'fur_black')
        parts[nome] = a
    if not vola:
        for nome, s in (('zampa_sx', -1), ('zampa_dx', 1)):
            z = Part(nome, 'corpo', (s * 0.03, 0.0, -0.05))
            z.add(loft([(0, 0, 0.01), (0, 0, -0.11)], [0.008, 0.007], [0.008, 0.007], n=3), 'beak_orange')
            parts[nome] = z
    return parts

# ------------------------------------------------------------------ persone
def persona(veste, brache, pelle, capelli, cappello=None, gonna=False, guardia=False, h=1.72):
    k = h / 1.72
    parts = {}
    b = Part('bacino', None, (0, 0, 0.95 * k))
    # busto: vita -> petto -> spalle
    b.add(loft([(0, 0, -0.02 * k), (0, 0, 0.18 * k), (0, 0.01, 0.4 * k), (0, 0, 0.55 * k), (0, 0, 0.6 * k)],
               [0.16 * k, 0.15 * k, 0.19 * k, 0.21 * k, 0.12 * k], [0.1 * k, 0.1 * k, 0.12 * k, 0.1 * k, 0.07 * k], n=8, phase=math.pi / 8), veste)
    # tunica/gonna attaccata al bacino (le gambe si muovono sotto)
    if gonna:
        b.add(loft([(0, 0, 0.02 * k), (0, 0, -0.4 * k), (0, 0, -0.86 * k)], [0.17 * k, 0.24 * k, 0.29 * k], [0.12 * k, 0.2 * k, 0.25 * k], n=8, caps=(False, True)), veste)
    else:
        b.add(loft([(0, 0, 0.02 * k), (0, 0, -0.22 * k), (0, 0, -0.34 * k)], [0.17 * k, 0.21 * k, 0.23 * k], [0.11 * k, 0.15 * k, 0.17 * k], n=8, caps=(False, True)), veste)
    b.add(loft([(0, 0, 0.05 * k), (0, 0, 0.1 * k)], [0.165 * k, 0.165 * k], [0.108 * k, 0.108 * k], n=8), 'wood_trim')   # cintura
    if guardia:
        b.add(loft([(0, 0, 0.2 * k), (0, 0, 0.56 * k)], [0.2 * k, 0.215 * k], [0.125 * k, 0.11 * k], n=8), 'iron_dark')
    parts['bacino'] = b
    t = Part('collo', 'bacino', (0, 0, 0.6 * k))
    t.add(loft([(0, 0, 0), (0, 0, 0.08 * k)], [0.05 * k, 0.05 * k], [0.05 * k, 0.05 * k], n=6), pelle)
    t.add(loft([(0, 0.0, 0.07 * k), (0, 0.01, 0.13 * k), (0, 0.01, 0.22 * k), (0, 0, 0.29 * k)], [0.07 * k, 0.095 * k, 0.09 * k, 0.05 * k], [0.08 * k, 0.1 * k, 0.1 * k, 0.06 * k], n=7), pelle)
    t.add(cone((0, 0.09 * k, 0.17 * k), (0, 0.125 * k, 0.15 * k), 0.018 * k, n=4), pelle)
    for s in (-1, 1):
        t.add(cone((s * 0.035 * k, 0.085 * k, 0.2 * k), (s * 0.035 * k, 0.1 * k, 0.2 * k), 0.012 * k, n=4), 'stone_dark')
    if guardia:
        t.add(loft([(0, 0, 0.16 * k), (0, 0, 0.26 * k), (0, 0, 0.36 * k)], [0.115 * k, 0.11 * k, 0.02 * k], [0.12 * k, 0.115 * k, 0.02 * k], n=8), 'iron_dark')
    elif cappello:
        t.add(loft([(0, 0, 0.23 * k), (0, 0, 0.25 * k)], [0.2 * k, 0.2 * k], [0.2 * k, 0.2 * k], n=8), cappello)
        t.add(loft([(0, 0, 0.25 * k), (0, 0, 0.33 * k)], [0.1 * k, 0.07 * k], [0.1 * k, 0.07 * k], n=8), cappello)
    else:
        t.add(loft([(0, -0.02 * k, 0.12 * k), (0, -0.015 * k, 0.22 * k), (0, -0.005 * k, 0.3 * k)], [0.1 * k, 0.1 * k, 0.05 * k], [0.1 * k, 0.1 * k, 0.05 * k], n=7, caps=(False, True)), capelli)
    parts['collo'] = t
    for nome, s in (('sx', -1), ('dx', 1)):
        a = Part('anca_' + nome, 'bacino', (s * 0.09 * k, 0, 0))
        a.add(loft([(0, 0, 0.02 * k), (0, 0, -0.44 * k)], [0.08 * k, 0.06 * k], [0.085 * k, 0.065 * k], n=6), brache)
        g = Part('ginocchio_' + nome, 'anca_' + nome, (0, 0, -0.45 * k))
        g.add(loft([(0, 0, 0.02 * k), (0, 0, -0.4 * k)], [0.058 * k, 0.045 * k], [0.062 * k, 0.05 * k], n=6), brache)
        g.add(loft([(0, -0.03 * k, -0.4 * k), (0, 0.0, -0.46 * k), (0, 0.13 * k, -0.47 * k)], [0.05 * k, 0.05 * k, 0.04 * k], [0.04 * k, 0.035 * k, 0.025 * k], n=5, up=(0, 0, 1)), 'wood_trim')
        sp_ = Part('spalla_' + nome, 'bacino', (s * 0.22 * k, 0, 0.53 * k))
        sp_.add(loft([(0, 0, 0.03 * k), (s * 0.01, 0, -0.28 * k)], [0.055 * k, 0.045 * k], [0.06 * k, 0.05 * k], n=6), veste if not guardia else 'iron_dark')
        go = Part('gomito_' + nome, 'spalla_' + nome, (s * 0.01, 0, -0.29 * k))
        go.add(loft([(0, 0, 0.01 * k), (0, 0, -0.24 * k)], [0.043 * k, 0.035 * k], [0.046 * k, 0.037 * k], n=6), veste if gonna or guardia else pelle)
        go.add(loft([(0, 0, -0.24 * k), (0, 0.01, -0.3 * k), (0, 0.0, -0.33 * k)], [0.035 * k, 0.04 * k, 0.02 * k], [0.02 * k, 0.025 * k, 0.015 * k], n=5), pelle)
        parts[a.nome] = a; parts[g.nome] = g; parts[sp_.nome] = sp_; parts[go.nome] = go
    if guardia:
        parts['gomito_dx'].add(loft([(0, 0.04, -1.25), (0, 0.04, 1.05)], [0.018, 0.018], [0.018, 0.018], n=4, up=(0, 1, 0)), 'wood_trim')
        parts['gomito_dx'].add(cone((0, 0.04, 1.05), (0, 0.04, 1.27), 0.04, n=4), 'iron_dark')
    return parts

def model(tipo, **kw):
    if tipo in Q: parts = quadrupede(tipo, **kw)
    elif tipo == 'chicken': parts = gallina(**kw)
    elif tipo in ('duck', 'swan'): parts = anatra(sp=tipo, **kw)
    elif tipo == 'seagull': parts = gabbiano(**kw)
    elif tipo == 'persona': parts = persona(**kw)
    else: raise ValueError(tipo)
    return [p.dict() for p in parts.values()]

def rotm(axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    if axis == 'x': return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'y': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def assemble(parts, pose=None):
    """posa statica: pose = {nome_parte: (rx, ry, rz)} (radianti, rotazioni locali XYZ). Restituisce V (Blender), F, M"""
    pose = pose or {}
    byname = {p['nome']: p for p in parts}
    W = {}
    def world(nome):
        if nome in W: return W[nome]
        p = byname[nome]; r = pose.get(nome, (0, 0, 0))
        R = rotm('z', r[2]) @ rotm('y', r[1]) @ rotm('x', r[0])
        if p['genitore'] is None:
            Rw, tw = R, np.array(p['perno'])
        else:
            Rp, tp = world(p['genitore'])
            Rw, tw = Rp @ R, tp + Rp @ np.array(p['perno'])
        W[nome] = (Rw, tw); return W[nome]
    V = []; F = []; M = []
    for p in parts:
        Rw, tw = world(p['nome'])
        b = len(V)
        V += [tuple(tw + Rw @ np.array(v)) for v in p['V']]
        F += [[b + i for i in f] for f in p['F']]; M += p['M']
    return np.array(V), F, M
