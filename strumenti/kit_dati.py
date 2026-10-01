"""Dati del kit v4 dal modello finale: animali (tutti con giro), percorsi delle persone ricontrollati, sentiero della camera
sul nuovo tracciato a tornanti; modelli articolati. Scrive kit_v4.py.
Uso: python kit_dati.py stato.pkl animali_statici.json uscita.py"""
import sys, os, json, ast, math, heapq, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy import ndimage
from stato import carica
from occupancy import occupancy_fine
import animali_gen as G

ESCL = ('Alberi', 'Alberi_Nuovi', 'Rocce', 'Rocce_Promontori', 'Pareti_Rocciose', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Strade_Rurali', 'Strade_Borgo',
        'Ponte', 'Ponti_Nuovi', 'Ponticelli', 'Porte', 'Dettagli_Porte_Fortezza', 'Salice', 'Pietre_Miliari', 'Fontanelle', 'Arredo_Piazza', 'Mercati', 'Capitelli', 'Capitelli_Nuovi',
        'Dettagli_Borgo_Basso', 'Dettagli_Borgo_Alto', 'Campi', 'Guglie')
REPORT = []
def rep(s): REPORT.append(s); print('[kit]', s)

def dati_v3(path='kit.py'):
    line = next(l for l in open(path).read().split('\n') if l.startswith('DATI = '))
    return ast.literal_eval(line.split('=', 1)[1].strip())

class Griglia:
    def __init__(self, m, mask, slope):
        self.m = m; self.mask = mask; self.slope = slope
    def idx(self, x, z):
        i, j = self.m.ij(np.asarray(x, float), np.asarray(z, float))
        return np.clip(np.floor(i).astype(int), 0, self.mask.shape[0] - 1), np.clip(np.floor(j).astype(int), 0, self.mask.shape[1] - 1)
    def bad(self, x, z):
        i, j = self.idx(x, z); return self.mask[i, j]

def astar(G_, a, b, margin=25.0, max_slope=0.45):
    """percorso a 8 vicini fra due punti (x,z) evitando la maschera; costo con pendenza. Restituisce lista di (x,z) o None"""
    m = G_.m
    x0, x1 = min(a[0], b[0]) - margin, max(a[0], b[0]) + margin; z0, z1 = min(a[1], b[1]) - margin, max(a[1], b[1]) + margin
    i0, j0 = G_.idx(x0, z0); i1, j1 = G_.idx(x1, z1)
    blk = G_.mask[i0:i1 + 1, j0:j1 + 1]; sl = G_.slope[i0:i1 + 1, j0:j1 + 1]
    sa = tuple(np.subtract(G_.idx(*a), (i0, j0))); sb = tuple(np.subtract(G_.idx(*b), (i0, j0)))
    NI, NJ = blk.shape
    cost = 1.0 + 8.0 * np.clip(sl / max_slope, 0, 3) ** 2
    cost[blk] = np.inf
    dist = {sa: 0.0}; prev = {}; pq = [(0.0, sa)]
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == sb: break
        if d > dist.get(u, 1e18): continue
        for di, dj, w in nb:
            v = (u[0] + di, u[1] + dj)
            if not (0 <= v[0] < NI and 0 <= v[1] < NJ): continue
            c = cost[v]
            if not np.isfinite(c): continue
            nd = d + w * c
            if nd < dist.get(v, 1e18):
                dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd + math.hypot(v[0] - sb[0], v[1] - sb[1]), v))
    if sb not in prev and sb != sa: return None
    out = [sb]
    while out[-1] != sa: out.append(prev[out[-1]])
    out = out[::-1]
    X, Z = m.xz(np.array([p[0] + i0 for p in out]) + 0.5, np.array([p[1] + j0 for p in out]) + 0.5)
    pts = list(zip(X.tolist(), Z.tolist()))
    # semplifica: un punto ogni ~3 m
    keep = [pts[0]]
    for p in pts[1:-1]:
        if math.hypot(p[0] - keep[-1][0], p[1] - keep[-1][1]) >= 3.0: keep.append(p)
    keep.append(pts[-1])
    return keep

def ripara_percorso(pts, G_new, G_all, chiuso=True):
    """sposta i punti finiti in ostacoli nuovi e aggira con A* i tratti che li attraversano"""
    P = [tuple(p) for p in pts]; n_mod = 0
    # 1) punti dentro ostacoli nuovi -> cella libera più vicina
    idx = ndimage.distance_transform_edt(G_new.mask, return_distances=False, return_indices=True)
    for k, p in enumerate(P):
        if G_new.bad(*p):
            i, j = G_new.idx(*p); ni, nj = idx[0][i, j], idx[1][i, j]
            x, z = G_new.m.xz(ni + 0.5, nj + 0.5); P[k] = (float(x), float(z)); n_mod += 1
    # 2) tratti che attraversano ostacoli nuovi -> deviazione
    out = [P[0]]; seg = list(zip(P, P[1:] + ([P[0]] if chiuso else [])))
    for a, b in seg:
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(2, int(L / 0.4))
        t = np.linspace(0, 1, n); xs = a[0] + (b[0] - a[0]) * t; zs = a[1] + (b[1] - a[1]) * t
        if np.any(G_new.bad(xs, zs)):
            det = astar(G_all, a, b)
            if det:
                out += det[1:-1]; n_mod += 1
        out.append(b)
    if chiuso: out = out[:-1]
    return [(round(x, 2), round(z, 2)) for x, z in out], n_mod

def nuovo_tracciato(path='sentiero_nuovo.json'):
    s = json.load(open(path))
    r = [(p[0], p[1]) for p in s['tornanti']][::-1]            # dal fondovalle al paese
    r += [(141.2, -145.0), (141.4, -150.0), (141.3, -155.0), (141.3, -158.0)]
    # un punto ogni ~3 m
    out = [r[0]]
    for p in r[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= 3.0: out.append(p)
    if out[-1] != r[-1]: out.append(r[-1])
    return out

J0, J1 = (101.5, -101.5), (141.3, -158.0)
def sostituisci_vecchio(pts, NEW, chiuso):
    """sostituisce i tratti del vecchio sentiero ripido (fra fondovalle e paese) con il nuovo tracciato a tornanti"""
    P = [tuple(p[:2]) for p in pts]; n = len(P); out = []; k = 0; sost = 0
    def near(p, q, r=6.5): return math.hypot(p[0] - q[0], p[1] - q[1]) < r
    def in_zone(p): return 95 <= p[0] <= 156 and -160 <= p[1] <= -95
    while k < n:
        p = P[k]; out.append(p)
        for A_, B_, seq in ((J0, J1, NEW), (J1, J0, NEW[::-1])):
            if near(p, A_):
                b = k + 1
                while b < n and in_zone(P[b]) and not near(P[b], B_): b += 1
                if b < n and near(P[b], B_) and b - k >= 3:
                    out += seq[1:-1]; k = b - 1; sost += 1
                break
        k += 1
    return out, sost

def run(stato, statici, uscita):
    m = carica(stato)
    D = dati_v3()
    S = json.load(open(statici))
    # maschere: ostacoli finali, ostacoli originali, nuovi ostacoli
    occ_f = occupancy_fine(m, extra_exclude=ESCL, with_mats=False)
    m0 = carica(None)
    occ_o0 = occupancy_fine(m0, extra_exclude=ESCL, with_mats=False)
    # griglia della fase 2 più grande: l'occupazione originale va riportata nella posizione giusta
    di, dj = m0.I0 - m.I0, m0.J0 - m.J0
    occ_o = np.zeros(occ_f.shape, bool)
    occ_o[di:di + occ_o0.shape[0], dj:dj + occ_o0.shape[1]] = occ_o0
    if di or dj: rep('griglia del terreno estesa: occupazione originale spostata di %d x %d celle' % (di, dj))
    nuovi = ndimage.binary_dilation(occ_f & ~occ_o, iterations=1)
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 0.7), 0.9); sl = np.hypot(gx, gz)
    slc = (sl[:-1, :-1] + sl[1:, :-1] + sl[:-1, 1:] + sl[1:, 1:]) / 4
    G_new = Griglia(m, nuovi, slc); G_all = Griglia(m, nuovi | (occ_f & ~occ_o), slc)
    # --- percorsi delle persone
    NEW = nuovo_tracciato()
    perc = []; tot_mod = 0; tot_sost = 0
    for ri, rt in enumerate(D['percorsi']):
        pts, ns = sostituisci_vecchio(rt['punti'], NEW, True)
        pts, nm = ripara_percorso(pts, G_new, G_all, True)
        tot_mod += nm; tot_sost += ns
        if nm or ns: rep('percorso %d: %s%s' % (ri, ('tratto del vecchio sentiero sostituito dai tornanti (%d volte); ' % ns) if ns else '', ('%d punti/tratti deviati attorno a edifici nuovi' % nm) if nm else ''))
        perc.append(dict(punti=[list(p) for p in pts], persone=rt['persone']))
    # --- camera del sentiero
    sen = dict(D['sentiero'])
    P0 = [tuple(p[:2]) for p in sen['punti']]
    P1, ns = sostituisci_vecchio(P0, NEW, False)
    def plen(P): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(P, P[1:]))
    L0, L1 = plen(P0), plen(P1)
    # ricampiono ogni ~8 m (come prima) e bersagli 12 m più avanti
    cum = np.r_[0, np.cumsum([math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(P1, P1[1:])])]
    ss = np.arange(0, cum[-1], 8.0); ss = np.r_[ss, cum[-1]]
    X1 = np.interp(ss, cum, [p[0] for p in P1]); Z1 = np.interp(ss, cum, [p[1] for p in P1])
    tb = np.minimum(ss + 12.0, cum[-1]); XB = np.interp(tb, cum, [p[0] for p in P1]); ZB = np.interp(tb, cum, [p[1] for p in P1])
    sen['punti'] = [[round(float(x), 2), round(float(z), 2), 2.0, 'w'] for x, z in zip(X1, Z1)]
    sen['bersaglio'] = [[round(float(x), 2), round(float(z), 2), 1.7, 'w'] for x, z in zip(XB, ZB)]
    sen['fotogrammi'] = int(round(sen['fotogrammi'] * L1 / L0))
    rep('camera 07_Sentieri: tratto ripido sostituito dai tornanti (%d); percorso %.0f m -> %.0f m, fotogrammi %d' % (ns, L0, L1, sen['fotogrammi']))
    # --- animali
    anim = []; nuovi_giri = 0; rifatti = 0
    rng = np.random.default_rng(5)
    Hm = m.H
    def acqua_ok(x, z, y):
        return bool(np.all(m.height_tri(np.asarray(x), np.asarray(z)) < y - 0.12))
    def terra_ok(xs, zs):
        return not np.any(G_all.bad(xs, zs)) and not np.any(occ_f[G_all.idx(xs, zs)]) and float(np.max(slc[G_all.idx(xs, zs)])) < 0.7
    def anello(x, z, r1, r2, ang, n=12):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        c, s = math.cos(ang), math.sin(ang)
        px = r1 * np.cos(t); pz = r2 * np.sin(t)
        return np.stack([x + px * c - pz * s, z + px * s + pz * c], 1)
    for a in S['animali']:
        sp = a['sp']; x, z, y = a['x'], a['z'], a['y']
        ring = np.array(a['anello'], float) if a['anello'] else None
        acqua = sp in ('duck', 'swan'); vola = a['vola']; appollaiato = sp == 'seagull' and not vola
        ok = ring is not None
        if ok and acqua:
            ok = acqua_ok(ring[:, 0], ring[:, 1], y + 0.02)
        elif ok and not vola and not appollaiato:
            ok = not np.any(G_new.bad(ring[:, 0], ring[:, 1]))
        if appollaiato:
            ring = anello(x, z, 0.35, 0.25, rng.uniform(0, 3.14), 8); ok = True; nuovi_giri += 1
        if not ok:
            found = None
            for r in (4.0, 3.0, 2.2, 1.6, 1.1, 0.7):
                for ang in np.linspace(0, math.pi, 6, endpoint=False):
                    R = anello(x, z, r, r * 0.65, ang)
                    if (acqua and acqua_ok(R[:, 0], R[:, 1], y + 0.02)) or (not acqua and terra_ok(R[:, 0], R[:, 1])):
                        found = R; break
                if found is not None: break
            if found is None:
                found = anello(x, z, 0.5, 0.35, 0.0, 8)
            if ring is None: nuovi_giri += 1
            else: rifatti += 1
            ring = found
        d = dict(m=a['key'], sp=sp, c=a['col'], c2=a['col2'], x=a['x'], z=a['z'], y=round(y, 3), yaw=a['yaw'],
                 anello=[[round(float(p[0]), 2), round(float(p[1]), 2)] for p in ring])
        if vola: d['vola'] = True
        if acqua or vola or appollaiato: d['ass'] = True
        anim.append(d)
    rep('animali: %d, tutti con un giro (%d giri nuovi, %d rifatti perché finivano fuori dall\'acqua o in ostacoli nuovi)' % (len(anim), nuovi_giri, rifatti))
    # --- modelli articolati
    MOD = dict(S['modelli'])
    MOD['seagull_vola'] = G.model('seagull', vola=True)
    for gonna in (False, True):
        for cap in (False, True):
            k = 'persona' + ('_gonna' if gonna else '') + ('_cappello' if cap else '')
            MOD[k] = G.model('persona', veste='VESTE', brache='BRACHE', pelle='PELLE', capelli='CAPELLI', cappello='CAPPELLO' if cap else None, gonna=gonna)
    MOD['guardia'] = G.model('persona', veste='VESTE', brache='BRACHE', pelle='PELLE', capelli='CAPELLI', guardia=True)
    DATI = dict(centro_fortezza=D['centro_fortezza'], riprese=D['riprese'], guardie=D['guardie'], sentiero=sen, percorsi=perc, animali=anim)
    nuove = riprese_fase2(m)
    if nuove:
        DATI['riprese_nuove'] = nuove
        rep('camere nuove della fase 2: ' + ', '.join('%s (%d fotogrammi)' % (r['nome'], r['fotogrammi']) for r in nuove))
    nf = {k: sum(len(p['F']) for p in v) for k, v in MOD.items()}
    rep('modelli articolati: %d (facce per modello: %s)' % (len(MOD), ', '.join('%s %d' % kv for kv in sorted(nf.items()))))
    scrivi_kit(DATI, MOD, uscita, len(anim), sum(r['persone'] for r in perc) + len(D['guardie']), len(perc))
    json.dump(REPORT, open(uscita + '.report.json', 'w'), ensure_ascii=False, indent=1)

def riprese_fase2(m):
    """camere sulle parti nuove: scala della torre del mago (dal ponticello alla grotta) e sorvolo delle terre nuove"""
    if not m.has('Torre_Mago_Scala'): return []
    def alza(pts, minimo):
        out = []
        for x, z, h in pts:
            t = float(m.height(x, z)); out.append((round(x, 2), round(z, 2), round(max(h, t + minimo), 2), 'a'))
        return out
    sc = dict(nome='08_Scala_del_mago',
              punti=alza([(-213.0, -117.0, 48.0), (-214.0, -127.0, 56.0), (-216.0, -137.0, 65.0), (-219.5, -146.0, 74.0), (-225.5, -155.0, 78.0)], 6.0),
              bersaglio=[(-227.6, -131.0, 38.6, 'a'), (-233.0, -141.0, 44.0, 'a'), (-237.0, -151.0, 55.0, 'a'), (-235.0, -160.0, 66.0, 'a'), (-230.0, -165.8, 73.6, 'a')],
              fotogrammi=325, lente=28, fstop=8)
    tn = dict(nome='09_Terre_nuove',
              punti=alza([(265.0, -255.0, 45.0), (205.0, -250.0, 55.0), (150.0, -262.0, 65.0), (60.0, -285.0, 105.0), (-60.0, -300.0, 150.0),
                          (-180.0, -305.0, 175.0), (-300.0, -255.0, 180.0), (-360.0, -170.0, 150.0), (-360.0, -60.0, 130.0)], 25.0),
              bersaglio=[(150.0, -228.0, 45.0, 'a'), (140.0, -232.0, 46.0, 'a'), (100.0, -250.0, 50.0, 'a'), (0.0, -265.0, 70.0, 'a'), (-120.0, -270.0, 85.0, 'a'),
                         (-250.0, -240.0, 80.0, 'a'), (-370.0, -180.0, 75.0, 'a'), (-400.0, -120.0, 75.0, 'a'), (-420.0, -40.0, 70.0, 'a')],
              fotogrammi=500, lente=24, fstop=11)
    return [sc, tn]

def compatto(o):
    t = repr(o).replace(', ', ',').replace(': ', ':')
    assert eval(t) == o
    return t

def scrivi_kit(DATI, MOD, uscita, n_anim, n_pers, n_perc):
    v3 = open('kit.py').read().split('\n')
    T = os.path.dirname(os.path.abspath(__file__))
    head = v3[:30]
    versione = 'v5' if DATI.get('riprese_nuove') else 'v4'
    head[1] = '#  KIT DI RIPRESA %s - Mappa del regno (castello_mappa_estesa)' % versione
    head = [l.replace('# 42 persone su 24 percorsi + 2 guardie', '# %d persone articolate su %d percorsi (con 2 guardie sulle mura)' % (n_pers, n_perc))
             .replace('# 145 animali articolati che si muovono', '# %d animali articolati, tutti in movimento; False = restano quelli fermi dell\'OBJ' % n_anim) for l in head]
    head = [l.replace("LUCE_CIELO = 1.0              # intensita' della luce diffusa del cielo",
                      "LUCE_CIELO = 0.6              # intensita' della luce diffusa del cielo\nESPOSIZIONE = -0.6            # 0 = come la v3 (immagine piu' chiara e slavata)\nCONTRASTO = \"AgX - Punchy\"    # \"AgX - Base Contrast\", \"AgX - Medium High Contrast\", \"AgX - Punchy\" ...")
             .replace("NEBBIA = True", "NEBBIA = False                # True = foschia volumetrica (piu' pesante; nella prova senza GPU dava un fotogramma nero)") for l in head]
    extra = ("VELOCITA_PERSONE = 1.0        # 1.0 = passo normale (1,05-1,35 m/s); 1.5 = piu' veloci del 50%; 2.0 = il doppio\n"
             "VELOCITA_ANIMALI = 1.0        # come sopra per gli animali; le zampe si adeguano al passo\n"
             "SOSTE_ANIMALI = 1.0           # durata delle soste per brucare o beccare: 0.5 = la meta', 1.0 = come prima")
    head = [l + '\n' + extra if l.startswith('TEXTURE = ') else l for l in head]
    code = v3[31:]
    txt = '\n'.join(code)
    a = txt.index('# --------------------------------------------------------------- pezzi, articolazioni, movimento')
    b = txt.index('# --------------------------------------------------------------- mare, rendering, schermo')
    c = txt.index('# --------------------------------------------------------------- avvio')
    rig = open(os.path.join(T, 'kit_rig.py.txt')).read(); main = open(os.path.join(T, 'kit_main.py.txt')).read()
    mid = txt[b:c].replace("""    for obj, attr, val in ((SC.view_settings, 'view_transform', 'AgX'), (r, 'use_motion_blur', True)):
        try: setattr(obj, attr, val)
        except Exception: pass""", """    for obj, attr, val in ((SC.view_settings, 'view_transform', 'AgX'), (r, 'use_motion_blur', True), (SC.view_settings, 'exposure', ESPOSIZIONE)):
        try: setattr(obj, attr, val)
        except Exception: pass
    for lk in (CONTRASTO, CONTRASTO.replace('AgX - ', ''), 'None'):
        try:
            SC.view_settings.look = lk; break
        except Exception: pass""").replace("TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Animali', 'Villaggio_Altopiano')",
                           "TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Villaggio_Altopiano')")
    pre = txt[:a].replace('import bpy, bmesh, math, traceback', 'import bpy, bmesh, math, random, traceback')
    pre = pre.replace("ld = bpy.data.lights.new('Sole', 'SUN'); ld.energy = 3.5", "ld = bpy.data.lights.new('Sole', 'SUN'); ld.energy = 4.0")
    pre = pre.replace("    b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0); b.inputs['Roughness'].default_value = rough",
                      "    b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0); b.inputs['Roughness'].default_value = rough\n    m.diffuse_color = (col[0], col[1], col[2], 1.0)   # stesso colore anche nella vista Solida")
    pre = pre.replace("""    for ob in bpy.data.objects:
        if ob.name.startswith('Mare'):""", """    for me in list(bpy.data.meshes):
        if me.get('kit') and me.users == 0:
            bpy.data.meshes.remove(me)
    for ob in bpy.data.objects:
        if ob.name.startswith('Mare'):""")
    pre = pre.replace("    nomi = {r['nome'] for r in DATI['riprese']} | {'07_Sentieri'}",
                      "    nomi = {r['nome'] for r in DATI['riprese'] + DATI.get('riprese_nuove', [])} | {'07_Sentieri'}")
    mid = mid.replace("(sp, 'clip_end', 1500.0)", "(sp, 'clip_end', 6000.0)")
    mid = mid.replace("TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Rocce', 'Siepi_e_Confini', 'Villaggio_Altopiano')",
                      "TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Villaggio_Altopiano')")
    # TEXTURE = False toglie anche le texture aggiunte da un'esecuzione precedente (restano salvate nei materiali)
    vecchio = """        if TEXTURE and not m.get('kit_texture'):
            for fam, nomi in FAM.items():
                if nome in nomi and texture(m, fam):
                    m['kit_texture'] = True; nt_ += 1; break
    log('Materiali ritoccati; texture procedurali aggiunte a %d materiali' % nt_)"""
    nuovo = """        if TEXTURE and not m.get('kit_texture'):
            for fam, nomi in FAM.items():
                if nome in nomi and texture(m, fam):
                    m['kit_texture'] = True; nt_ += 1; break
        elif not TEXTURE and m.get('kit_texture'):
            togli_texture(m); tolte += 1
    if TEXTURE:
        log('Materiali ritoccati; texture procedurali aggiunte a %d materiali' % nt_)
    else:
        log('Texture procedurali spente: tolte da %d materiali (colori pieni originali)' % tolte)

def togli_texture(m):
    \"\"\"toglie i nodi aggiunti da texture(): il colore torna quello pieno del materiale\"\"\"
    nt = m.node_tree
    for n in [n for n in nt.nodes if n.type in ('TEX_COORD', 'TEX_NOISE', 'TEX_WAVE', 'TEX_VORONOI', 'VALTORGB', 'BUMP')]:
        nt.nodes.remove(n)
    if 'kit_texture' in m:
        del m['kit_texture']"""
    assert vecchio in pre
    pre = pre.replace(vecchio, nuovo).replace("def migliora_materiali():\n    nt_ = 0", "def migliora_materiali():\n    nt_ = 0; tolte = 0")
    out = '\n'.join(head) + '\n' + 'VERSIONE_KIT = %r\n' % versione + 'DATI = ' + compatto(DATI) + '\n' + 'MODELLI = ' + compatto(MOD) + '\n' + pre + rig + '\n' + mid + main
    open(uscita, 'w').write(out)
    print('scritto', uscita, len(out) // 1024, 'KB')

if __name__ == '__main__':
    run(*sys.argv[1:4])
