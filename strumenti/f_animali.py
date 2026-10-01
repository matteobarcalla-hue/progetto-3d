"""Animali statici più realistici: i vecchi animali (oggetto Animali e animali sparsi negli oggetti dei poderi, stalle,
pascolo, porto, villaggio) sono sostituiti da modelli low-poly articolati (stesse forme del kit), raccolti nell'oggetto Animali.
Scrive anche animali_statici.json (posizioni, orientamento, specie, colori) per il kit."""
import numpy as np, math, ast, json, collections, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animali_gen as G

LOG = []
def log(s): LOG.append(s); print('[animali]', s)

ANIMAL_OBJS = ('Pascolo_Pastore', 'Poderi_Nuovi', 'Stalle', 'Villaggio_Altopiano', 'Porto', 'Fabbro', 'Miniera_Ampliata', 'Taglialegna', 'Poderi_Dettagli', 'Dettagli_Poderi')
AM = ('fur_', 'feather_', 'beak_')
GRAZERS = ('sheep', 'cow', 'goat', 'horse', 'donkey', 'deer')

def dati_v3(path='kit.py'):
    src = open(path).read().split('\n')
    line = next(l for l in src if l.startswith('DATI = '))
    return ast.literal_eval(line.split('=', 1)[1].strip())

def zampe_col(sp, col):
    if sp == 'sheep': return 'fur_black'
    if sp == 'horse': return 'fur_black' if col in ('fur_brown', 'fur_tan', None) else col
    if sp == 'dog': return 'fur_black' if col == 'fur_brown' else col
    return col

def default_col(sp):
    return {'sheep': 'wool_white', 'cow': 'fur_white', 'horse': 'fur_brown', 'donkey': 'fur_grey', 'goat': 'fur_white', 'pig': 'wall_plaster_rose',
            'deer': 'fur_tan', 'dog': 'fur_brown', 'chicken': 'feather_white', 'duck': 'fur_brown', 'swan': 'feather_white', 'seagull': 'feather_white'}[sp]

def variante(a, i):
    """chiave del modello e argomenti del generatore (con segnaposto CORPO/ZAMPE per il kit)"""
    sp = a['sp']; col = a.get('col') or default_col(sp)
    if sp in G.Q:
        if sp == 'cow' and col == 'fur_white': return 'cow_pezzata', dict(col_corpo='fur_white', col_zampe='ZAMPE')
        if sp == 'deer': return 'deer_' + ('m' if i % 3 == 0 else 'f'), dict(col_corpo='CORPO', col_zampe='ZAMPE', maschio=(i % 3 == 0))
        return sp, dict(col_corpo='CORPO', col_zampe='ZAMPE')
    if sp == 'chicken': return 'chicken', dict(col='CORPO')
    if sp in ('duck', 'swan'):
        m_ = (sp == 'duck' and i % 2 == 0)
        return sp + ('_m' if m_ else ''), dict(col='CORPO', maschio=m_)
    return 'seagull' + ('_vola' if a.get('vola') else ''), dict(vola=bool(a.get('vola')))

def genera(key, kw):
    sp = key.split('_')[0]
    if sp in ('cow', 'deer') or sp in G.Q:
        return G.model(sp, rng=np.random.default_rng(abs(hash(key)) % 1000), **kw)
    if sp == 'chicken': return G.model('chicken', **kw)
    if sp in ('duck', 'swan'): return G.model(sp, **kw)
    return G.model('seagull', **kw)

def run(m):
    D = dati_v3()
    A = D['animali']
    K = np.array([[a['x'], a['z']] for a in A])
    from scipy.spatial import cKDTree
    kt = cKDTree(K)
    # 1) vecchi animali: tutto l'oggetto Animali + componenti con pelo/piume/becco (e lana vicina) negli oggetti dei poderi
    old = {}          # oggetto -> facce
    matched = collections.defaultdict(list)    # indice animale -> [(lo, hi, oggetto)]
    unmatched = collections.Counter()
    for nm in ('Animali',) + ANIMAL_OBJS:
        if not m.has(nm): continue
        o = m.obj(nm); cs = m.comps(nm)
        fur = []; wool = []
        for c in cs:
            ms = set(o['mats'][f] for f in c['faces'])
            big = max(c['hi'][0] - c['lo'][0], c['hi'][2] - c['lo'][2])
            if nm == 'Animali': fur.append(c); continue
            if big > 2.8: continue
            if any(x.startswith(AM) for x in ms): fur.append(c)
            elif ms <= {'wool_white', 'stone_dark', 'stone_light', 'flag_red', 'hedge', 'trunk_brown', 'wall_plaster_rose'} and big < 1.6: wool.append(c)
        sel = []
        for c in fur:
            ce = (c['lo'] + c['hi']) / 2
            d, k = kt.query([ce[0], ce[2]])
            if d <= 2.5:
                sel.append(c); matched[int(k)].append((c['lo'], c['hi'], nm))
            elif nm == 'Animali':
                sel.append(c)
            else:
                unmatched[nm] += 1
        # lana/parti accessorie attaccate agli animali trovati (entro 0.5 m dall'ingombro)
        if nm != 'Animali' and sel:
            cen = np.array([((c['lo'] + c['hi']) / 2)[[0, 2]] for c in sel])
            for c in wool:
                ce = ((c['lo'] + c['hi']) / 2)[[0, 2]]
                if np.min(np.hypot(*(cen - ce).T)) < 1.0:
                    sel.append(c)
        if sel: old[nm] = sorted(set(f for c in sel for f in c['faces']))
    n_old = sum(len(v) for v in old.values())
    log('vecchi animali rimossi: %d facce (%s)' % (n_old, ', '.join('%s %d' % (k, len(v)) for k, v in old.items())))
    if unmatched: log('componenti con pelo/piume non attribuite ad animali e lasciate al loro posto: %s' % dict(unmatched))
    m.delete(old)
    # 2) nuovi animali
    H0 = np.load('terrain_orig.npz')['H']
    def dH(x, z):
        fi, fj = m.ij(x, z); i = int(np.clip(round(fi), 0, H0.shape[0] - 1)); j = int(np.clip(round(fj), 0, H0.shape[1] - 1))
        h0 = H0[i, j]
        return float(m.H[i, j] - h0) if not np.isnan(h0) else 0.0
    cache = {}; out = []; P_all = []; F_all = []; M_all = []
    rng = np.random.default_rng(71)
    counts = collections.Counter()
    for i, a in enumerate(A):
        sp = a['sp']; col = a.get('col') or default_col(sp)
        key, kw = variante(a, i)
        if key not in cache: cache[key] = genera(key, kw)
        parts = cache[key]
        mm = matched.get(i, [])
        if mm:
            lo = np.min([x[0] for x in mm], 0); hi = np.max([x[1] for x in mm], 0)
            x, z = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
            y = float(lo[1]) + (0.0 if all(x_[2] == 'Animali' for x_ in mm) else dH(x, z))
        else:
            x, z = a['x'], a['z']; y = float(m.height_tri(x, z))
        if sp in ('duck', 'swan'): y = a.get('y', y) - 0.02
        if sp == 'seagull' and a.get('vola'): y = a.get('y', y)
        pose = {}
        if sp in GRAZERS and rng.random() < 0.5: pose['collo'] = (-0.75, 0, rng.uniform(-0.3, 0.3))
        elif sp in G.Q: pose['collo'] = (rng.uniform(-0.15, 0.1), 0, rng.uniform(-0.35, 0.35))
        if sp in ('chicken',) and rng.random() < 0.4: pose['collo'] = (-0.9, 0, 0)
        V, F, M = G.assemble(parts, pose)
        mp = {'CORPO': col, 'ZAMPE': zampe_col(sp, col)}
        M = [mp.get(t, t) for t in M]
        th = a['yaw'] - math.pi / 2      # direzione della testa in OBJ: (cos yaw, -sin yaw)
        c_, s_ = math.cos(th), math.sin(th)
        bx = V[:, 0] * c_ - V[:, 1] * s_; by = V[:, 0] * s_ + V[:, 1] * c_; bz = V[:, 2]
        P = np.stack([bx + x, bz + y, -by + z], 1)
        b = len(P_all); P_all += P.tolist(); F_all += [[b + v for v in f] for f in F]; M_all += M
        counts[sp] += 1
        out.append(dict(i=i, sp=sp, key=key, col=col, col2=zampe_col(sp, col), x=round(float(x), 2), z=round(float(z), 2), y=round(float(y), 3),
                        yaw=a['yaw'], vola=bool(a.get('vola')), anello=a['anello'], trovato=bool(mm)))
    m.add_faces('Animali', P_all, F_all, M_all, False)
    json.dump(dict(animali=out, modelli={k: v for k, v in cache.items()}), open('animali_statici.json', 'w'))
    log('nuovi animali low-poly articolati: %d (%s), %d facce in totale (prima %d); %d posizionati sui vecchi, %d dalle coordinate del kit'
        % (len(out), ', '.join('%s %d' % kv for kv in counts.most_common()), len(F_all), n_old, sum(o['trovato'] for o in out), sum(not o['trovato'] for o in out)))
    return LOG
