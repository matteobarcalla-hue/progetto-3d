"""Fase 3 - borghi fitti e medievali: paese sull'altopiano e paese del porto rifatti.
Case: copie (ruotate, scalate di poco) delle case originali del borgo, del villaggio e del porto, con tutti i loro dettagli.
Vie strette lastricate che seguono il terreno (pendenza limitata), piazze, case a schiera sul filo della via con la porta
sulla via, passaggi fra le schiere, orti dietro le case."""
import numpy as np, math, collections, pickle
from scipy import ndimage
from shapely.geometry import Polygon, Point
import ops, case_modelli
from borgo import Borgo
from occupancy import occupancy_fine
from alberi_util import gruppi_alberi

LOG = []
def log(s): LOG.append(s); print('[borghi]', s)

VEG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini',
       'Animali', 'Canneto_Fiume')
STRADE = ('path_dirt', 'street_stone', 'piazza_stone')

def modelli(m):
    T = case_modelli.estrai(m)
    vis = {}; out = []
    for t in T:
        k = (t['nf'], round(t['larg'], 1), round(t['prof'], 1), round(t['alt'], 1))
        if k in vis: continue
        vis[k] = 1; out.append(t)
    return out

def gruppi_in(m, nm, test):
    """componenti dell'oggetto raggruppati per contatto (case con i loro pezzi)"""
    return [g for g in case_modelli._gruppi(m, (nm, None)) if test(g)]

def togli_gruppi(m, nm, gruppi):
    o = m.obj(nm); fs = []
    for g in gruppi:
        for _, c in g: fs += c['faces']
    if fs: m.delete({nm: fs})
    return sum(len(g) for g in gruppi)

def togli_ingombri(m, area, zona_bbox):
    """vegetazione, sassi, siepi, animali fermi dentro l'area (shapely): via interi"""
    from shapely.prepared import prep
    pa = prep(area)
    x0, x1, z0, z1 = zona_bbox
    tolti = collections.Counter(); rem = {}
    for nm in VEG:
        if not m.has(nm): continue
        cs = [c for c in m.comps(nm) if c['hi'][0] >= x0 and c['lo'][0] <= x1 and c['hi'][2] >= z0 and c['lo'][2] <= z1]
        if not cs: continue
        gr = gruppi_alberi(m, nm, cs) if nm.startswith('Alberi') else [[c] for c in cs]
        fs = []
        for g in gr:
            base = min(g, key=lambda c: c['lo'][1])
            lo = base['lo']; hi = base['hi']
            fp = Polygon([(lo[0], lo[2]), (hi[0], lo[2]), (hi[0], hi[2]), (lo[0], hi[2])]).buffer(0.2)
            if pa.intersects(fp):
                for c in g: fs += c['faces']
                tolti[nm] += 1
        if fs: rem[nm] = fs
    m.delete(rem)
    return tolti

def strade_vecchie(m, poly_pts):
    cel = ops.cells_in_poly(m, poly_pts)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    old = cel & np.isin(nomi, STRADE)
    ops.fill_mat_from_neighbors(m, old, exclude=STRADE)
    return int(old.sum())

def ostacoli(m, escludi):
    occ = occupancy_fine(m, extra_exclude=escludi, with_mats=False)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    occ |= np.isin(nomi, ['<buco>', 'water', 'terrain_field', 'crop_green', 'crop_gold'])
    return occ

# ====================================================================== altopiano
def altopiano(m, T, rng):
    log('PAESE DELL\'ALTOPIANO')
    # 1) via le case vecchie (resta la chiesa, la torretta, il pozzo della piazza, i filari degli orti)
    def da_togliere(g):
        L = np.min([c['lo'] for _, c in g], 0); H = np.max([c['hi'] for _, c in g], 0); ce = (L + H) / 2
        nf = sum(len(c['faces']) for _, c in g)
        if nf > 1000: return False                                   # chiesa
        if abs(ce[0] - 190.7) < 2 and abs(ce[2] + 151.9) < 2: return False      # torretta
        if abs(ce[0] - 140.0) < 2 and abs(ce[2] + 165.0) < 2: return False      # pozzo
        if max(H[0] - L[0], H[2] - L[2]) > 20 and H[1] - L[1] < 3.5: return False  # filari
        return True                                                   # case e minuterie rimaste sparse (pali, lanterne...)
    g1 = gruppi_in(m, 'Villaggio_Altopiano', da_togliere)
    n1 = togli_gruppi(m, 'Villaggio_Altopiano', g1)
    def nuovo(g):
        L = np.min([c['lo'] for _, c in g], 0); H = np.max([c['hi'] for _, c in g], 0); ce = (L + H) / 2
        return not (abs(ce[0] - 140.25) < 2 and abs(ce[2] + 239.75) < 2)      # tengo il pozzo della piazza sud
    g2 = gruppi_in(m, 'Villaggio_Altopiano_Nuovo', nuovo)
    togli_gruppi(m, 'Villaggio_Altopiano_Nuovo', g2)
    log('tolte le case sparse: %d dal villaggio, %d dall\'allargamento della fase 2 (restano chiesa, torretta, 2 pozzi, filari degli orti)' % (len(g1), len(g2)))
    zona = [(84, -139.5), (194, -139.5), (194, -264), (84, -264)]
    nv = strade_vecchie(m, [(80, -136), (200, -136), (200, -268), (80, -268)])
    log('vecchie strade larghe del villaggio tornate prato: %d celle' % nv)
    occ = ostacoli(m, VEG + ('Villaggio_Altopiano_Nuovo',))
    B = Borgo(m, 'Borgo_Altopiano', zona, occ, T, rng, log)
    # 2) piazze e vie
    h_top = float(m.height(140.5, -141.5))
    p1 = B.piazza([(136.5, -146.0), (150.0, -145.0), (154.5, -152.0), (153.0, -167.5), (137.0, -168.0)], nome='della chiesa', y=h_top + 0.2)
    p2 = B.piazza([(133.0, -232.5), (148.5, -232.5), (148.5, -247.0), (133.0, -247.0)], nome='sud', y=float(m.height(140.5, -240.0)))
    vm1 = B.via([(140.5, -141.5), (141.5, -144.0), (143.0, -147.5)], 3.4, nome='Maestra (ingresso)', quota_inizio=h_top, liscia=1)
    vm2 = B.via([(145.0, -167.0), (147.0, -176.0), (148.5, -188.0), (147.0, -201.0), (143.5, -214.0), (141.0, -226.0), (140.5, -233.5)], 3.4, nome='Maestra')
    vp = B.via([(106.0, -142.0), (108.5, -154.0), (109.5, -168.0), (110.5, -182.0), (112.5, -196.0), (116.0, -210.0), (122.0, -222.0), (133.5, -236.0)], 3.0, nome='di Ponente')
    vl = B.via([(166.0, -142.0), (170.0, -155.0), (172.5, -169.0), (172.5, -183.0), (170.5, -197.0), (167.0, -211.0), (160.0, -224.0), (148.0, -237.0)], 3.0, nome='di Levante')
    v1 = B.via([(109.5, -160.0), (122.0, -161.0), (137.5, -162.0)], 2.4, nome='vicolo della chiesa')
    v2 = B.via([(153.5, -157.0), (162.0, -156.5), (171.0, -157.5)], 2.4, nome='vicolo del pozzo')
    v3 = B.via([(110.8, -187.5), (122.0, -189.0), (135.0, -190.0), (148.3, -190.0)], 2.6, nome='traversa di mezzo (ovest)')
    v4 = B.via([(148.3, -190.0), (160.0, -189.5), (172.3, -189.0)], 2.6, nome='traversa di mezzo (est)')
    v5 = B.via([(115.5, -209.0), (128.0, -211.5), (143.5, -213.5)], 2.4, nome='traversa sud (ovest)')
    v6 = B.via([(143.5, -213.5), (155.0, -213.5), (167.0, -211.0)], 2.4, nome='traversa sud (est)')
    v7 = B.via([(109.8, -175.0), (97.0, -176.0), (84.0, -177.0), (74.0, -177.5)], 2.4, mat='path_dirt', nome='via degli orti')
    v8 = B.via([(172.5, -176.0), (183.0, -177.5), (192.0, -179.0)], 2.2, mat='path_dirt', nome='belvedere')
    v9 = B.via([(140.0, -247.0), (136.0, -256.0), (130.0, -265.0)], 2.4, mat='path_dirt', nome='mulattiera dei monti')
    # vicoli interni agli isolati
    i1 = B.via([(122.0, -161.3), (126.0, -170.0), (127.0, -180.0), (128.0, -189.4)], 2.2, nome='vicolo interno nord-ovest')
    i2 = B.via([(162.0, -156.8), (160.0, -166.0), (160.5, -178.0), (160.0, -189.6)], 2.2, nome='vicolo interno nord-est')
    i3 = B.via([(130.0, -190.0), (130.5, -200.0), (129.5, -211.6)], 2.2, nome='vicolo interno sud-ovest')
    i4 = B.via([(158.0, -189.6), (158.0, -200.0), (157.0, -213.5)], 2.2, nome='vicolo interno sud-est')
    # 3) case: prima le vie principali, poi le traverse
    n = 0
    for v in (vm2, vp, vl):
        n += B.fronte(v, +1); n += B.fronte(v, -1)
    for v in (vm1,):
        n += B.fronte(v, +1, s0=0.5); n += B.fronte(v, -1, s0=0.5)
    for v in (v1, v2, v3, v4, v5, v6):
        n += B.fronte(v, +1, schiera=(2, 5)); n += B.fronte(v, -1, schiera=(2, 5))
    for v in (i1, i2, i3, i4):
        n += B.fronte(v, +1, schiera=(2, 4), passaggio=(1.6, 3.0)); n += B.fronte(v, -1, schiera=(2, 4), passaggio=(1.6, 3.0))
    n += B.fronte(v7, +1, s1=24.0, schiera=(2, 4)); n += B.fronte(v7, -1, s1=24.0, schiera=(2, 4))
    n += B.fronte(v8, +1, s1=10.0, schiera=(2, 3)); n += B.fronte(v8, -1, s1=10.0, schiera=(2, 3))
    # piazze: case sul bordo, porta verso la piazza
    for pz in (p1, p2):
        n += fronte_piazza(B, pz)
    log('case posate: %d' % len(B.case))
    nf = B.costruisci()
    area = B.impronte()
    tolti = togli_ingombri(m, area.buffer(0.3), (80, 200, -270, -134))
    log('nuovo oggetto Borgo_Altopiano: %d case, %d facce; tolti perché dentro case o vie: %s' % (len(B.case), nf, ', '.join('%s %d' % kv for kv in tolti.most_common())))
    cortili(m, B)
    orti(m, B, rng)
    return B

def fronte_piazza(B, pz):
    """case sui lati della piazza, con la porta verso il centro"""
    P = list(pz['poly'].exterior.coords)
    n = 0
    for a, b in zip(P[:-1], P[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 6: continue
        v = dict(P=np.array([a, b]), s=np.array([0.0, L]), h=np.array([pz['y'], pz['y']]), larg=0.2, nome='piazza ' + pz['nome'])
        from borgo import resample
        Pp, s = resample([a, b], 0.5); v['P'] = Pp; v['s'] = s; v['h'] = np.full(len(s), pz['y'])
        # il lato esterno: a destra percorrendo il contorno in senso antiorario, a sinistra in senso orario
        lato = -1 if Polygon(P).exterior.is_ccw else 1
        n += B.fronte(v, lato, s0=1.0, s1=L - 1.0, schiera=(2, 6))
    return n

def cortili(m, B):
    """dentro il borgo le chiazze di roccia e ghiaia in piano diventano prato o terra battuta"""
    hull = B.impronte().convex_hull.buffer(-2.0)
    cel = ops.cells_in_poly(m, list(hull.exterior.coords))
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    gy, gx = np.gradient(m.H, 0.9); pend = np.hypot(gx, gy)[:-1, :-1]
    sel = cel & np.isin(nomi, ['terrain_rock', 'stone_dark', 'terrain_gravel', 'moss_stone']) & (pend < 0.45)
    m.M[sel] = np.where(np.random.default_rng(5).random(int(sel.sum())) < 0.75, m.mat_index('terrain_grass'), m.mat_index('soil_dark'))
    log('cortili: %d celle di roccia/ghiaia in piano dentro il borgo diventano prato o terra battuta' % int(sel.sum()))

def orti(m, B, rng):
    """dietro una parte delle case, piccoli orti: celle di terra scura con filari verdi"""
    from shapely.prepared import prep
    area = prep(B.impronte().buffer(0.6))
    Xc, Zc = m.cell_xz()
    nomi = np.array(m.mats + ['<buco>'])
    n = 0
    for c in B.case:
        if rng.random() > 0.35: continue
        # direzione dal fronte al retro
        th = c['th']; back = np.array([math.sin(th), -math.cos(th)])
        bl, bh = c['t']['corpo']
        p0 = np.array([c['cx'], c['cz']]) + back * (c['t']['prof'] / 2 + 1.2)
        w = 3.0 + rng.random() * 2.0; d = 3.0 + rng.random() * 3.0
        side = np.array([-back[1], back[0]])
        poly = Polygon([tuple(p0 + side * w / 2), tuple(p0 - side * w / 2), tuple(p0 - side * w / 2 + back * d), tuple(p0 + side * w / 2 + back * d)])
        if area.intersects(poly): continue
        cel = ops.cells_in_poly(m, list(poly.exterior.coords))
        if not cel.any(): continue
        cur = nomi[m.M[cel]]
        if np.isin(cur, list(STRADE) + ['<buco>', 'terrain_rock', 'stone_dark']).any(): continue
        # filari: celle alterne
        ii, jj = np.nonzero(cel)
        alt = (jj % 2 == 0) if abs(back[0]) > abs(back[1]) else (ii % 2 == 0)
        m.M[ii, jj] = np.where(alt, m.mat_index('crop_green'), m.mat_index('soil_dark'))
        n += 1
    log('orti dietro le case: %d' % n)

# ====================================================================== porto
def porto(m, T, rng):
    log('PAESE DEL PORTO')
    g = gruppi_in(m, 'Porto_Paese_Nuovo', lambda g: True)
    togli_gruppi(m, 'Porto_Paese_Nuovo', g)
    log('tolte le 7 case sparse della fase 2 (le case e i magazzini originali del porto restano dove sono)')
    zona = [(164, -62), (206.2, -62), (206.2, -12), (204.6, -12), (204.6, 2), (216, 2), (216, 46), (162, 46), (162, 8)]
    nv = strade_vecchie(m, [(176, -30), (206, -30), (206, 40), (176, 40)])
    log('vecchi vicoli del porto rifatti: %d celle' % nv)
    occ = ostacoli(m, VEG + ('Porto_Paese_Nuovo',))
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    occ |= m.H[:-1, :-1] < 0.9                                          # spiaggia bassa e acqua
    B = Borgo(m, 'Borgo_Porto', zona, occ, [t for t in T if t['prof'] <= 7.2 and t['larg'] <= 7.5], rng, log)
    yq = float(np.median(m.height(np.array([196.0, 200.0, 197.0]), np.array([-28.0, -18.0, -22.0]))))
    p1 = B.piazza([(192.5, -30.0), (201.4, -30.0), (201.4, -15.2), (192.5, -15.2)], nome='del porto', y=yq)
    vmolo = B.via([(203.0, -49.0), (203.0, -30.0), (203.0, -13.0), (203.2, -2.0), (203.6, 6.0), (204.4, 15.0), (205.2, 26.0), (205.0, 37.5)], 3.0, nome='del Molo')
    vpor = B.via([(176.0, -22.6), (184.0, -22.4), (192.5, -22.5)], 3.2, nome='del Porto (ultimo tratto)')
    vpq = B.via([(201.4, -22.5), (206.5, -22.5)], 3.2, nome='uscita sul molo', liscia=0)
    vmez = B.via([(190.6, -39.0), (190.6, -31.0), (191.0, -22.5), (191.2, -13.0), (191.2, -4.5)], 2.6, nome='di Mezzo')
    # terrazze lungo le curve di livello (quota quasi costante), collegate alla via del Molo da scalinate
    e1 = B.via([(197.5, 15.0), (190.0, 12.5), (183.0, 10.5), (179.0, 9.5)], 2.6, nome='della Costa', gmax=0.08)
    e2 = B.via([(198.5, 25.5), (190.0, 23.5), (181.0, 20.5), (173.0, 16.5), (165.0, 13.0)], 2.6, nome='Alta', gmax=0.08)
    e3 = B.via([(199.0, 36.5), (190.0, 34.5), (181.0, 32.5), (172.0, 32.5), (165.0, 28.0)], 2.4, nome='del Belvedere', gmax=0.08)
    c1 = B.via([(203.4, 7.5), (200.5, 11.5), (197.5, 15.0)], 2.2, nome='scalinata della Costa', liscia=0)
    c2 = B.via([(193.0, 13.2), (192.0, 18.5), (191.0, 23.8)], 2.2, nome='scalinata Alta', liscia=0)
    c3 = B.via([(186.5, 22.2), (186.0, 28.0), (185.5, 33.7)], 2.2, nome='scalinata del Belvedere', liscia=0)
    c4 = B.via([(179.0, 9.5), (177.0, 18.6)], 2.2, nome='scalinata di ponente (bassa)', liscia=0)
    c5 = B.via([(177.0, 18.6), (174.5, 32.5)], 2.2, nome='scalinata di ponente (alta)', liscia=0)
    vcol = B.via([(198.0, -48.5), (190.0, -52.0), (182.0, -55.0), (173.0, -58.0)], 2.6, nome='del Colle', gmax=0.12)
    n = 0
    n += B.fronte(vmolo, +1, schiera=(3, 8)); n += B.fronte(vmolo, -1, schiera=(3, 8))
    n += B.fronte(vmez, +1); n += B.fronte(vmez, -1)
    n += B.fronte(vpor, +1, s0=4.0); n += B.fronte(vpor, -1, s0=4.0)
    for v in (e1, e2, e3):
        n += B.fronte(v, +1, schiera=(3, 7)); n += B.fronte(v, -1, schiera=(2, 4))
    n += B.fronte(vcol, +1, schiera=(2, 5)); n += B.fronte(vcol, -1, schiera=(2, 4))
    n += fronte_piazza(B, p1)
    cont = collections.Counter(c['via'] for c in B.case)
    log('case per via: ' + ', '.join('%s %d' % kv for kv in cont.most_common()))
    nf = B.costruisci()
    area = B.impronte()
    tolti = togli_ingombri(m, area.buffer(0.3), (160, 220, -66, 48))
    log('nuovo oggetto Borgo_Porto: %d case, %d facce; tolti perché dentro case o vie: %s' % (len(B.case), nf, ', '.join('%s %d' % kv for kv in tolti.most_common())))
    cortili(m, B)
    orti(m, B, rng)
    return B

def run(m):
    rng = np.random.default_rng(2026)
    T = modelli(m)
    log('modelli di casa (copie degli edifici esistenti, con i loro dettagli): %d' % len(T))
    altopiano(m, T, rng)
    porto(m, T, rng)
    return LOG
