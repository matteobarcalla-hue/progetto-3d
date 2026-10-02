"""Fase 3 - alberi più grandi, alti da passarci sotto, disposizione naturale; biomi più distinguibili.
1) Pulizia: chiome rimaste per aria senza tronco tolte; chiome laterali staccate riunite al loro albero; alberi con il piede
   su strade, campi, buchi o acqua tolti; tronchi a meno di 0,8 m da un altro: tolto il più piccolo.
2) Alta montagna (oltre ~100 m): le latifoglie diventano conifere (copie intere di conifere esistenti).
3) Ogni albero è scalato attorno al piede del tronco (1,45-2,1 volte, in media ~1,75) e la chioma è alzata allungando il
   tronco finché sotto resta lo spazio per passare (2,8 m per le latifoglie, 2,3 m per conifere e ulivi). Se la chioma
   ingrandita urterebbe un edificio, la scala scende; se l'albero urta comunque una casa nuova, è tolto.
4) Disposizione naturale: diradamento irregolare dove le chiome ingrandite si coprirebbero troppo (soglia diversa per
   ogni albero, così restano macchie e radure e non una griglia).
5) Colori: nel bosco di pianura chiome più scure; i prati d'alta quota diventano gialli (materiale nuovo)."""
import numpy as np, math, collections
from scipy import ndimage
from scipy.spatial import cKDTree
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[alberi]', s)

OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')
CHIOME = ('tree_green', 'tree_light', 'tree_dark', 'tree_autumn', 'tree_olive', 'conifer', 'cypress')
LATIFOGLIE = ('tree_green', 'tree_light', 'tree_dark', 'tree_autumn')
VIETATI = ('path_dirt', 'street_stone', 'piazza_stone', '<buco>')          # nei campi e negli orti gli alberi da frutto restano
NON_EDIFICI = ('Terreno', 'Base_Sezione', 'Mare', 'Acqua', 'Fondale_Esteso', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose',
               'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Campi', 'Strade_Rurali', 'Strade_Borgo', 'Pietre_Miliari', 'Guglie',
               'Pale_Dolomitiche', 'Grotte', 'Gallerie_Miniera') + OGG
NUOVI = ('Borgo_Altopiano', 'Borgo_Porto')
QUOTA_ALPINA = 100.0

def edifici(m):
    B = []; nomi = []
    for o in m.objs:
        if o['name'] in NON_EDIFICI or not o['faces']: continue
        for c in m.comps(o['name']):
            if c['hi'][1] - c['lo'][1] < 1.0: continue
            B.append(np.r_[c['lo'], c['hi']]); nomi.append(o['name'])
    B = np.array(B)
    return B, np.array(nomi)

class Griglia:
    def __init__(self, B, cella=12.0):
        self.B = B; self.c = cella; self.d = collections.defaultdict(list)
        for k, b in enumerate(B):
            for i in range(int(b[0] // cella), int(b[3] // cella) + 1):
                for j in range(int(b[2] // cella), int(b[5] // cella) + 1):
                    self.d[(i, j)].append(k)
    def urta(self, lo, hi, marg=0.1):
        ks = set()
        for i in range(int(lo[0] // self.c), int(hi[0] // self.c) + 1):
            for j in range(int(lo[2] // self.c), int(hi[2] // self.c) + 1):
                ks.update(self.d.get((i, j), ()))
        out = []
        for k in ks:
            b = self.B[k]
            if np.all(lo < b[3:] - marg) and np.all(hi > b[:3] + marg): out.append(k)
        return out

def raccogli(m, nm):
    """alberi dell'oggetto: tronco + chiome; chiome sospese senza tronco riunite o segnate da togliere"""
    o = m.obj(nm); cs = m.comps(nm)
    gr = gruppi_alberi(m, nm, cs)
    # alberi fatti di più pezzi di tronco che si toccano (tronco + ramo, come i salici): un albero solo
    gtr = []; soli = []
    for g in gr:
        tr = [c for c in g if any(o['mats'][f] == 'trunk_brown' for f in c['faces'])]
        if tr: gtr.append((tr, g))
        else: soli.append(g)
    padre = list(range(len(gtr)))
    def radice(i):
        while padre[i] != i: padre[i] = padre[padre[i]]; i = padre[i]
        return i
    if gtr:
        T = [(np.min([c['lo'] for c in tr], 0), np.max([c['hi'] for c in tr], 0)) for tr, g in gtr]
        Ct = np.array([(a + b) / 2 for a, b in T]); kdt = cKDTree(Ct[:, [0, 2]])
        for i, j in kdt.query_pairs(3.0):
            if np.all(T[i][0] - 0.15 <= T[j][1]) and np.all(T[j][0] - 0.15 <= T[i][1]):
                padre[radice(i)] = radice(j)
    insiemi = collections.defaultdict(list)
    for i in range(len(gtr)): insiemi[radice(i)].append(i)
    alberi = []; fusi = 0
    for idx in insiemi.values():
        comps = [c for i in idx for c in gtr[i][1]]
        trs = [c for i in idx for c in gtr[i][0]]
        alberi.append(dict(tr=min(trs, key=lambda c: c['lo'][1]), trs=trs, comps=comps, rami=0))
        fusi += len(idx) - 1
    # rami pendenti dei salici: lamine sottili e alte sotto una chioma, agganciate al loro albero
    if alberi:
        loa = np.array([np.min([c['lo'] for c in a['comps']], 0) for a in alberi]); hia = np.array([np.max([c['hi'] for c in a['comps']], 0) for a in alberi])
        kda = cKDTree(((loa + hia) / 2)[:, [0, 2]])
        resto = []
        for g in soli:
            c = g[0]
            mt = collections.Counter(o['mats'][f] for f in c['faces']).most_common(1)[0][0]
            d = c['hi'] - c['lo']
            if len(g) == 1 and len(c['faces']) <= 6 and mt in CHIOME and d[1] > 1.2 and max(d[0], d[2]) < 0.9:
                ce = (c['lo'] + c['hi']) / 2; fatto = False
                for k in sorted(kda.query_ball_point(ce[[0, 2]], 5.0), key=lambda k: np.hypot(*((loa[k] + hia[k]) / 2 - ce)[[0, 2]])):
                    if loa[k][0] - 0.8 <= ce[0] <= hia[k][0] + 0.8 and loa[k][2] - 0.8 <= ce[2] <= hia[k][2] + 0.8 and c['hi'][1] >= loa[k][1] + 1.0:
                        alberi[k]['comps'] = alberi[k]['comps'] + [c]; alberi[k]['rami'] += 1; fatto = True; break
                if fatto: continue
            resto.append(g)
        soli = resto
    # chiome sospese: unite all'albero di cui toccano la chioma, altrimenti da togliere
    if alberi:
        lo = np.array([np.min([c['lo'] for c in a['comps']], 0) for a in alberi]); hi = np.array([np.max([c['hi'] for c in a['comps']], 0) for a in alberi])
        C = (lo + hi) / 2; kd = cKDTree(C[:, [0, 2]])
    via = []; unite = 0
    for g in soli:
        c = g[0]
        mt = collections.Counter(o['mats'][f] for f in c['faces']).most_common(1)[0][0]
        if mt not in CHIOME: continue
        ce = (c['lo'] + c['hi']) / 2
        suolo = float(m.height(ce[0], ce[2]))
        if c['lo'][1] - suolo < 0.4: continue                     # cespuglio a terra
        ok = False
        if alberi:
            for k in kd.query_ball_point(ce[[0, 2]], 6.0):
                if np.all(c['lo'] - 0.25 <= hi[k]) and np.all(lo[k] - 0.25 <= c['hi']):
                    alberi[k]['comps'] = alberi[k]['comps'] + [c]; ok = True; unite += 1; break
        if not ok and c['lo'][1] - suolo > 1.0 and max(c['hi'][0] - c['lo'][0], c['hi'][2] - c['lo'][2]) > 0.5:
            via.append(c)
    for a in alberi:
        t = a['tr']
        a['x'] = float((t['lo'][0] + t['hi'][0]) / 2); a['z'] = float((t['lo'][2] + t['hi'][2]) / 2); a['y0'] = float(t['lo'][1])
        a['salice'] = a['rami'] >= 4
        cr = [c for c in a['comps'] if not any(c is x for x in a['trs'])]
        a['mat'] = collections.Counter(o['mats'][f] for c in cr for f in c['faces']).most_common(1)[0][0] if cr else 'trunk_brown'
        lo = np.min([c['lo'] for c in a['comps']], 0); hi = np.max([c['hi'] for c in a['comps']], 0)
        a['w'] = float(max(hi[0] - lo[0], hi[2] - lo[2])); a['h'] = float(hi[1] - a['y0'])
        a['obj'] = nm
    return alberi, via, unite, fusi

def modelli_conifera(m, alberi):
    """conifere intere (tronco + coni) da copiare in alta quota"""
    out = []
    for a in alberi:
        if a['mat'] != 'conifer' or a['obj'] != 'Alberi_Aree_Nuove' or not (4.0 < a['h'] < 6.5): continue
        o = m.obj(a['obj'])
        vs = np.unique(np.concatenate([c['verts'] for c in a['comps']])); rm = {v: i for i, v in enumerate(vs)}
        F = []; M = []
        for c in a['comps']:
            for f in c['faces']:
                F.append([rm[v - 1] for v in o['faces'][f]]); M.append(o['mats'][f])
        P = m.V[vs] - np.array([a['x'], a['y0'], a['z']])
        out.append((P, F, M))
        if len(out) >= 24: break
    return out

def run(m):
    rng = np.random.default_rng(303)
    nomi_c = np.array(m.mats + ['<buco>'])[m.M]
    A = []; rem = collections.defaultdict(list); n_via = 0; n_unite = 0
    n_fusi = 0
    for nm in OGG:
        al, via, un, fu = raccogli(m, nm)
        A += al; n_unite += un; n_fusi += fu
        for c in via: rem[nm] += c['faces']
        n_via += len(via)
    log('alberi con tronco: %d; chiome staccate riunite al loro albero: %d; chiome sospese senza tronco tolte: %d' % (len(A), n_unite, n_via))
    log('alberi con più pezzi di tronco (tronco e rami) riconosciuti come un albero solo: %d pezzi uniti; salici (con rami pendenti agganciati): %d'
        % (n_fusi, sum(a['salice'] for a in A)))
    # 1) piede su suoli vietati, acqua, tronchi sovrapposti
    tolti = collections.Counter()
    vivi = []
    for a in A:
        fi, fj = m.ij(a['x'], a['z']); i = int(np.clip(np.floor(fi), 0, nomi_c.shape[0] - 1)); j = int(np.clip(np.floor(fj), 0, nomi_c.shape[1] - 1))
        su = nomi_c[i, j]
        if su in VIETATI or m.H[i, j] < 0.2:
            tolti['piede su ' + su] += 1
            for c in a['comps']: rem[a['obj']] += c['faces']
        else:
            vivi.append(a)
    A = vivi
    P = np.array([(a['x'], a['z']) for a in A]); kd = cKDTree(P)
    morti = set()
    for i, j in sorted(kd.query_pairs(0.8)):
        if i in morti or j in morti: continue
        k = i if A[i]['h'] < A[j]['h'] else j
        morti.add(k)
    for k in morti:
        for c in A[k]['comps']: rem[A[k]['obj']] += c['faces']
    tolti['tronco a meno di 0,8 m da un altro'] = len(morti)
    A = [a for k, a in enumerate(A) if k not in morti]
    # 2) alta quota: latifoglie -> conifere
    tpl = modelli_conifera(m, A)
    nuove = []
    for a in A:
        if a['mat'] in LATIFOGLIE and float(m.height(a['x'], a['z'])) > QUOTA_ALPINA + rng.uniform(-8, 8) and tpl:
            P_, F_, M_ = tpl[rng.integers(0, len(tpl))]
            th = rng.uniform(0, 2 * np.pi); c_, s_ = math.cos(th), math.sin(th)
            Q = np.stack([P_[:, 0] * c_ - P_[:, 2] * s_, P_[:, 1], P_[:, 0] * s_ + P_[:, 2] * c_], 1) * rng.uniform(0.9, 1.1)
            nuove.append((a, Q, F_, M_))
    for a, Q, F_, M_ in nuove:
        for c in a['comps']: rem[a['obj']] += c['faces']
    A = [a for a in A if not any(a is n[0] for n in nuove)]
    # cancellazioni prima di trasformare (gli indici delle facce valgono sullo stato attuale)
    m.delete(dict(rem))
    for a, Q, F_, M_ in nuove:
        m.add_faces('Alberi_Aree_Nuove', (Q + [a['x'], a['y0'], a['z']]).tolist(), F_, M_, False)
    log('alta montagna (oltre %d m circa): %d latifoglie sostituite da conifere intere' % (QUOTA_ALPINA, len(nuove)))
    log('tolti prima di ingrandire: ' + ', '.join('%s %d' % kv for kv in tolti.most_common()))
    # ricostruzione degli alberi dopo le cancellazioni
    A = []
    for nm in OGG:
        al, via, un, fu = raccogli(m, nm)
        A += al
    # alberi che toccano un altro oggetto (staccionate, arnie, carri, frutti...): restano come sono
    picc = []
    for o in m.objs:
        if (o['name'] in NON_EDIFICI and o['name'] != 'Campi') or not o['faces']: continue
        for c in m.comps(o['name']):
            if np.linalg.norm(c['hi'] - c['lo']) < 20.0: picc.append(np.r_[c['lo'], c['hi']])
    Gp = Griglia(np.array(picc), cella=8.0)
    n_leg = 0
    for a in A:
        lo = np.min([c['lo'] for c in a['comps']], 0); hi = np.max([c['hi'] for c in a['comps']], 0)
        a['legato'] = bool(Gp.urta(lo - 0.15, hi + 0.15, marg=0.0))
        n_leg += a['legato']
    log('alberi che toccano un altro oggetto (staccionate, arnie, carri, frutti...), lasciati come sono: %d' % n_leg)
    # 3) scala, chioma alzata, urti con gli edifici
    Bx, Bn = edifici(m); G = Griglia(Bx)
    scale = np.clip(rng.normal(1.75, 0.16, len(A)), 1.45, 2.1)
    piano = []
    n_rid = 0; n_via_urto = 0
    for a, s0 in zip(A, scale):
        o = m.obj(a['obj'])
        b = np.array([a['x'], a['y0'], a['z']])
        tr = a['tr']; cr = [c for c in a['comps'] if not any(c is x for x in a['trs'])]
        if not cr or a['legato']:
            continue
        suolo = float(m.height(a['x'], a['z']))
        conif = a['mat'] in ('conifer', 'cypress', 'tree_olive')
        alto = (2.3 if conif else 2.8) + rng.uniform(0.0, 0.5)
        if a['salice']: alto = -1e3                                     # i rami del salice pendono fino a terra: si ingrandisce intero
        lo_c = np.min([c['lo'] for c in cr], 0); hi_c = np.max([c['hi'] for c in cr], 0)
        scelta = None
        for s in [s0] + [x for x in (1.5, 1.3, 1.15) if x < s0] + [1.0]:
            lo2 = b + (lo_c - b) * s; hi2 = b + (hi_c - b) * s
            lift = max(0.0, alto - (lo2[1] - suolo)) if s > 1.0 else 0.0
            lo2[1] += lift; hi2[1] += lift
            urti = G.urta(lo2, hi2)
            if not urti:
                scelta = (s, lift); break
            if s == 1.0:
                if any(Bn[k] in NUOVI for k in urti): scelta = None
                else: scelta = (1.0, 0.0)
        if scelta is None:
            n_via_urto += 1
            piano.append((a, None, None)); continue
        if scelta[0] < s0: n_rid += 1
        a['s'] = scelta[0]; a['lift'] = scelta[1]; a['w2'] = a['w'] * scelta[0]
        piano.append((a, scelta[0], scelta[1]))
    # 4) diradamento naturale: soglie diverse per albero, i più grandi restano
    ok = [(a, s, l) for a, s, l in piano if s is not None]
    ordine = sorted(range(len(ok)), key=lambda k: -ok[k][0]['w2'])
    P = np.array([(ok[k][0]['x'], ok[k][0]['z']) for k in range(len(ok))])
    kd = cKDTree(P)
    fatt = rng.uniform(0.26, 0.44, len(ok))
    tenuti = np.zeros(len(ok), bool)
    diradati = []
    for k in ordine:
        a = ok[k][0]
        vic = kd.query_ball_point(P[k], 0.44 * (a['w2'] + 6.0))
        trop = False
        for j in vic:
            if j == k or not tenuti[j]: continue
            soglia = fatt[k] * (a['w2'] + ok[j][0]['w2'])
            if np.hypot(*(P[j] - P[k])) < soglia: trop = True; break
        if trop: diradati.append(k)
        else: tenuti[k] = True
    rem = collections.defaultdict(list)
    for a, s, l in piano:
        if s is None:
            for c in a['comps']: rem[a['obj']] += c['faces']
    for k in diradati:
        a = ok[k][0]
        for c in a['comps']: rem[a['obj']] += c['faces']
    # 5) trasformazioni (prima delle cancellazioni: gli indici dei vertici non cambiano con delete)
    n_cam = collections.Counter(); scl = []; alti = []
    for k in np.nonzero(tenuti)[0]:
        a, s, lift = ok[k]
        b = np.array([a['x'], a['y0'], a['z']])
        tr = a['tr']; cr = [c for c in a['comps'] if not any(c is x for x in a['trs'])]
        vt = np.unique(np.concatenate([x['verts'] for x in a['trs']])); vc = np.unique(np.concatenate([c['verts'] for c in cr]))
        vc = np.setdiff1d(vc, vt)
        m.V[vt] = b + (m.V[vt] - b) * s
        m.V[vc] = b + (m.V[vc] - b) * s
        if lift > 0:
            yt = m.V[vt, 1]; mid = yt.min() + 0.5 * (yt.max() - yt.min())
            su = vt[yt > mid]
            m.V[su, 1] += lift; m.V[vc, 1] += lift
        # i ciuffi della chioma si gonfiano un poco sul proprio centro: le fessure fra ciuffi, ingrandite con la scala, si richiudono
        for c in cr:
            v = np.setdiff1d(c['verts'], vt); cc = m.V[v].mean(0)
            m.V[v] = cc + (m.V[v] - cc) * 1.07
        # il tronco entra nella chioma: cima del tronco 35 cm sopra il fondo della chioma che gli sta sopra
        yt = m.V[vt, 1]; mid = yt.min() + 0.5 * (yt.max() - yt.min()); su = vt[yt > mid]
        PC = m.V[vc]; dxz = np.hypot(PC[:, 0] - a['x'], PC[:, 2] - a['z'])
        sopra = PC[dxz < max(0.6, 0.35 * s), 1]
        fondo = float(sopra.min()) if len(sopra) else float(PC[:, 1].min())
        if m.V[su, 1].max() < fondo + 0.35:
            m.V[su, 1] += fondo + 0.35 - m.V[su, 1].max()
        scl.append(s)
        hi = m.V[vc, 1].max() - float(m.height(a['x'], a['z']))
        alti.append(hi)
    for nm in OGG: m.invalidate(nm)
    m.delete(dict(rem))
    # alberi con il piede staccato dal suolo (anche quelli del modello di partenza, dove il terreno è stato scolpito): riappoggiati
    n_app = 0
    for nm in OGG:
        o = m.obj(nm)
        for g in gruppi_alberi(m, nm):
            tr = [c for c in g if any(o['mats'][f] == 'trunk_brown' for f in c['faces'])]
            b = tr[0] if tr else min(g, key=lambda c: c['lo'][1])
            # sospeso davvero: il punto più basso sta sopra anche il punto più alto del terreno sotto la base
            xs = np.linspace(b['lo'][0], b['hi'][0], 3); zs = np.linspace(b['lo'][2], b['hi'][2], 3)
            XX, ZZ = np.meshgrid(xs, zs); t = float(m.height_tri(XX.ravel(), ZZ.ravel()).max())
            gap = b['lo'][1] - t
            if gap > 0.12 and (tr or gap < 3.0):
                vs = np.unique(np.concatenate([c['verts'] for c in g])); m.V[vs, 1] -= gap + 0.06; n_app += 1
        m.invalidate(nm)
    log('alberi e cespugli col piede staccato dal suolo riappoggiati: %d' % n_app)
    scl = np.array(scl); alti = np.array(alti)
    log('ingranditi %d alberi: scala media %.2f (%.2f-%.2f); scala ridotta per non urtare edifici: %d; tolti perché urterebbero le case nuove: %d'
        % (len(scl), scl.mean(), scl.min(), scl.max(), n_rid, n_via_urto))
    log('altezza degli alberi: mediana %.1f m (prima %.1f m), 90%% fino a %.1f m' % (np.median(alti), np.median([a['h'] for a in A]), np.percentile(alti, 90)))
    log('diradamento naturale dove le chiome ingrandite si coprirebbero troppo: %d alberi tolti su %d (%.0f%%)' % (len(diradati), len(ok), 100 * len(diradati) / max(1, len(ok))))
    return LOG
