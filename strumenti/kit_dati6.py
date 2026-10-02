"""Kit v6 dal modello della fase 3: riparte dal kit v5 e
- usa le impostazioni del kit che l'utente aveva nel .blend (velocità, texture, onde, cielo...);
- ripara i percorsi delle persone attorno agli ostacoli nuovi (case dei borghi, Pale) e sposta nel solco il tratto di
  fondovalle lungo il fiume; nel paese dell'altopiano un giro nuovo lungo le vie del borgo;
- toglie gli animali che finirebbero dentro le case nuove e rifà i giri che attraversano ostacoli nuovi;
- aggiunge i materiali nuovi alle famiglie delle texture e i borghi ai riquadri.
Uso: python kit_dati6.py stato_finale.pkl uscita.py"""
import sys, os, ast, json, math, collections, pickle
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy import ndimage
from stato import carica
from occupancy import occupancy_fine
from kit_dati import Griglia, astar, ripara_percorso, compatto, ESCL
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

REPORT = []
def rep(s): REPORT.append(s); print('[kit6]', s)

ESCL6 = ESCL + ('Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Mare', 'Fondale_Esteso')

def leggi(path):
    src = open(path).read().split('\n')
    iD = next(i for i, l in enumerate(src) if l.startswith('DATI = '))
    iM = next(i for i, l in enumerate(src) if l.startswith('MODELLI = '))
    D = ast.literal_eval(src[iD].split('=', 1)[1].strip())
    return src, iD, iM, D

def run(stato, uscita, kit5='kit_v5.py', header='fase3/header_utente.txt', vecchio='fase2_h.obj.state.pkl'):
    m = carica(stato)
    src, iD, iM, D = leggi(kit5)
    occ_f = occupancy_fine(m, extra_exclude=ESCL6, with_mats=False)
    occ_o = occupancy_fine(carica(vecchio), extra_exclude=ESCL6, with_mats=False)
    nuovi = ndimage.binary_dilation(occ_f & ~occ_o, iterations=1)
    gx, gz = np.gradient(ndimage.gaussian_filter(m.H, 0.7), 0.9); sl = np.hypot(gx, gz)
    slc = (sl[:-1, :-1] + sl[1:, :-1] + sl[:-1, 1:] + sl[1:, 1:]) / 4
    G_new = Griglia(m, nuovi, slc); G_all = Griglia(m, nuovi | occ_f, slc)
    case = pickle.load(open('fase3/case_borghi.pkl', 'rb'))
    from shapely.ops import unary_union
    from shapely import wkt
    pale = wkt.loads(pickle.load(open('fase3/pale_impronta.pkl', 'rb'))).buffer(1.0)
    impronte = prep(unary_union([Polygon(c['tutto']).buffer(0.6) for c in case] + [pale]))
    # tratto di fondovalle: dal vecchio tracciato nell'argilla al solco
    from f3_strade import SOLCO_PUNTI
    from borgo import resample, liscia_linea
    sol = resample(liscia_linea(SOLCO_PUNTI, 2), 0.5)[0]
    def nel_vecchio_fondovalle(p): return -20 < p[0] < 55 and -104.5 < p[1] < -93.5
    def al_solco(p):
        d = np.hypot(sol[:, 0] - p[0], sol[:, 1] - p[1]); k = int(np.argmin(d)); return (round(float(sol[k, 0]), 2), round(float(sol[k, 1]), 2))
    perc = []; n_sol = 0; n_dev = 0
    for ri, rt in enumerate(D['percorsi']):
        pts = [tuple(p[:2]) for p in rt['punti']]
        if sol is not None:
            q = []
            for p in pts:
                if nel_vecchio_fondovalle(p): q.append(al_solco(p)); n_sol += 1
                else: q.append(p)
            pts = q
        pts2, nmod = ripara_percorso(pts, G_new, G_all, True)
        n_dev += nmod
        if nmod: rep('percorso %d: %d punti o tratti deviati attorno a case nuove o alle Pale' % (ri, nmod))
        perc.append(dict(punti=[list(p) for p in pts2], persone=rt['persone']))
    # giro nuovo nel paese dell'altopiano lungo le vie del borgo (sostituisce il percorso 1, che girava fra le case vecchie)
    tappe = [(141.0, -143.0), (145.0, -152.0), (147.5, -176.0), (148.0, -189.0), (145.0, -208.0), (140.5, -232.0), (134.0, -236.0),
             (121.0, -221.0), (115.5, -207.0), (111.0, -188.0), (109.5, -168.0), (109.5, -160.0), (122.0, -161.0), (137.0, -162.0), (145.0, -158.0)]
    giro = []
    for a, b in zip(tappe, tappe[1:] + tappe[:1]):
        seg = astar(G_all, a, b, margin=12.0)
        if seg is None: seg = [a, b]
        giro += seg[:-1]
    if len(D['percorsi']) > 1:
        perc[1] = dict(punti=[[round(x, 2), round(z, 2)] for x, z in giro], persone=max(2, D['percorsi'][1]['persone']))
        rep('paese dell\'altopiano: giro nuovo lungo le vie del borgo, %d punti, %d persone (percorso 1)' % (len(giro), perc[1]['persone']))
    rep('percorsi: %d punti spostati dal vecchio fondovalle nel solco, %d deviazioni attorno a ostacoli nuovi' % (n_sol, n_dev))
    # camera dei sentieri: stesso spostamento nel solco
    sen = dict(D['sentiero'])
    if sol is not None:
        nn = 0; P = []
        for p in sen['punti']:
            if nel_vecchio_fondovalle(p[:2]): q = al_solco(p[:2]); P.append([q[0], q[1]] + list(p[2:])); nn += 1
            else: P.append(p)
        B = []
        for p in sen['bersaglio']:
            if nel_vecchio_fondovalle(p[:2]): q = al_solco(p[:2]); B.append([q[0], q[1]] + list(p[2:]))
            else: B.append(p)
        sen['punti'] = P; sen['bersaglio'] = B
        rep('camera 07_Sentieri: %d punti spostati nel solco lungo il fiume' % nn)
    # animali: via quelli dentro le case nuove; giri che attraversano ostacoli nuovi rifatti
    anim = []; tolti = 0; rifatti = 0
    for a in D['animali']:
        if impronte.contains(Point(a['x'], a['z'])) and not a.get('vola'):
            tolti += 1; continue
        R = np.array(a['anello'], float)
        if not a.get('ass') and np.any(G_new.bad(R[:, 0], R[:, 1])):
            ok = None
            for r in (3.0, 2.2, 1.6, 1.1, 0.7):
                for ang in np.linspace(0, math.pi, 6, endpoint=False):
                    t = np.linspace(0, 2 * np.pi, 12, endpoint=False)
                    c, s_ = math.cos(ang), math.sin(ang)
                    px = r * np.cos(t); pz = 0.65 * r * np.sin(t)
                    Q = np.stack([a['x'] + px * c - pz * s_, a['z'] + px * s_ + pz * c], 1)
                    if not np.any(G_all.bad(Q[:, 0], Q[:, 1])): ok = Q; break
                if ok is not None: break
            if ok is not None:
                a = dict(a); a['anello'] = [[round(float(p[0]), 2), round(float(p[1]), 2)] for p in ok]; rifatti += 1
        anim.append(a)
    rep('animali: %d (tolti %d che sarebbero finiti dentro le case nuove o dentro le Pale, %d giri rifatti attorno a ostacoli nuovi)' % (len(anim), tolti, rifatti))
    # camera 05_Villaggio: la vecchia passeggiata (z -166,8) ora attraversa le case; cammina sul vicolo della chiesa fino alla piazza
    rip = []
    for r in D['riprese']:
        if r['nome'] == '05_Villaggio':
            r = dict(r)
            r['punti'] = [(112.0, -160.3, 1.7, 'g'), (117.0, -160.6, 1.7, 'g'), (122.0, -161.0, 1.7, 'g'), (127.0, -161.3, 1.7, 'g'),
                          (132.0, -161.6, 1.7, 'g'), (137.0, -161.9, 1.7, 'g'), (142.0, -162.2, 1.7, 'g')]
            r['bersaglio'] = [(124.0, -161.1, 1.6, 'g'), (129.0, -161.4, 1.6, 'g'), (134.0, -161.7, 1.6, 'g'), (139.0, -162.0, 1.6, 'g'),
                              (144.0, -162.0, 1.6, 'g'), (149.0, -161.0, 1.6, 'g'), (154.0, -160.0, 1.6, 'g')]
            rep('camera 05_Villaggio: passeggiata spostata sul vicolo della chiesa (la vecchia strada ora passa fra le case nuove)')
        rip.append(r)
    DATI = dict(D); DATI['riprese'] = rip; DATI['percorsi'] = perc; DATI['sentiero'] = sen; DATI['animali'] = anim
    # testata con le impostazioni dell'utente
    H = open(header).read().rstrip('\n').split('\n')
    H = [l.replace('KIT DI RIPRESA v5', 'KIT DI RIPRESA v6') for l in H]
    n_pers = sum(p['persone'] for p in perc) + len(D['guardie'])
    H = [(l.split('#')[0] + '# %d persone articolate su %d percorsi (con 2 guardie sulle mura)' % (n_pers, len(perc))) if l.startswith('ABITANTI') else l for l in H]
    H = [(l.split('#')[0] + "# %d animali articolati, tutti in movimento; False = restano quelli fermi dell'OBJ" % len(anim)) if l.startswith('ANIMALI') else l for l in H]
    resto = src[iM + 1:]
    testo = '\n'.join(resto)
    testo = testo.replace("""       'terra': ('terrain_grass', 'terrain_meadow', 'terrain_forest', 'terrain_field', 'terrain_gravel', 'terrain_clay', 'soil_dark', 'path_dirt', 'sand'),""",
                          """       'terra': ('terrain_grass', 'terrain_meadow', 'terrain_meadow_alpine', 'terrain_forest', 'terrain_bosco', 'terrain_field', 'terrain_gravel', 'terrain_clay', 'soil_dark', 'path_dirt', 'sand'),""")
    testo = testo.replace("""       'fogliame': ('tree_green', 'tree_light', 'tree_dark', 'tree_olive', 'tree_autumn', 'conifer', 'cypress', 'hedge', 'crop_green', 'crop_gold', 'vine', 'reed', 'lavender')}""",
                          """       'fogliame': ('tree_green', 'tree_light', 'tree_dark', 'tree_bosco', 'tree_olive', 'tree_autumn', 'conifer', 'cypress', 'hedge', 'crop_green', 'crop_gold', 'vine', 'reed', 'lavender')}""")
    testo = testo.replace("""TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Villaggio_Altopiano')""",
                          """TASSELLARE = ('Terreno', 'Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento', 'Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Villaggio_Altopiano', 'Borgo_Altopiano')""")
    assert "'terrain_meadow_alpine'" in testo and "'tree_bosco'" in testo and "'Borgo_Altopiano')" in testo
    out = '\n'.join(H) + '\n' + "VERSIONE_KIT = 'v6'\n" + 'DATI = ' + compatto(DATI) + '\n' + src[iM] + '\n' + testo
    open(uscita, 'w').write(out)
    json.dump(REPORT, open(uscita + '.report.json', 'w'), ensure_ascii=False, indent=1)
    print('scritto', uscita, len(out) // 1024, 'KB')

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
