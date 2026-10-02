"""Fase 3 - biomi più distinguibili.
- Prati d'alta quota gialli: le celle di prato e d'erba sopra ~90 m (soglia irregolare 82-100 m, con una fascia di
  passaggio a chiazze) prendono il materiale nuovo terrain_meadow_alpine; anche le cenge erbose e l'altopiano delle Pale.
- Bosco di pianura e di mezza costa più scuro: sotto ~95 m il suolo del bosco prende il materiale nuovo terrain_bosco
  (verde più cupo) e le chiome delle latifoglie che stanno nel bosco scuriscono di un grado
  (tree_light -> tree_green -> tree_dark -> tree_bosco, materiale nuovo). Gli alberi isolati nei prati restano chiari:
  così il bosco si stacca dalla campagna aperta."""
import numpy as np, collections
from scipy import ndimage

LOG = []
def log(s): LOG.append(s); print('[biomi]', s)

NUOVI_MAT = {'terrain_meadow_alpine': (0.70, 0.65, 0.33), 'terrain_bosco': (0.15, 0.27, 0.11), 'tree_bosco': (0.10, 0.23, 0.09)}
SCURISCI = {'tree_light': 'tree_green', 'tree_green': 'tree_dark', 'tree_dark': 'tree_bosco'}
OGG = ('Alberi', 'Alberi_Nuovi', 'Alberi_Aree_Nuove', 'Alberi_Infittimento')

def run(m):
    rng = np.random.default_rng(77)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    Hc = (m.H[:-1, :-1] + m.H[1:, 1:] + m.H[1:, :-1] + m.H[:-1, 1:]) / 4
    rumore = ndimage.gaussian_filter(rng.normal(0, 1, Hc.shape), 12)
    rumore /= rumore.std() + 1e-9
    # 1) prati alpini
    soglia = 91.0 + 5.0 * rumore
    p = np.clip((Hc - (soglia - 6.0)) / 12.0, 0, 1)                    # passaggio a chiazze su ~12 m di quota
    prato = np.isin(nomi, ['terrain_meadow', 'terrain_grass'])
    sel = prato & (rng.random(Hc.shape) < p)
    sel = ndimage.binary_opening(sel, iterations=1) | (prato & (p >= 1.0))
    m.M[sel] = m.mat_index('terrain_meadow_alpine')
    log('prati d\'alta quota gialli (terrain_meadow_alpine): %d celle (%.0f m2), sopra 82-100 m con passaggio a chiazze' % (int(sel.sum()), sel.sum() * 0.81))
    # cenge e altopiano delle Pale
    n_p = 0
    if m.has('Pale_Dolomitiche'):
        o = m.obj('Pale_Dolomitiche')
        for k, mt in enumerate(o['mats']):
            if mt == 'terrain_meadow':
                o['mats'][k] = 'terrain_meadow_alpine'; n_p += 1
    # 2) bosco scuro sotto ~95 m
    soglia_b = 95.0 + 6.0 * rumore
    bosco = (nomi == 'terrain_forest') & (Hc < soglia_b)
    m.M[bosco] = m.mat_index('terrain_bosco')
    log('suolo del bosco di pianura e di mezza costa più scuro (terrain_bosco): %d celle (%.0f m2); le celle di bosco più in alto restano terrain_forest'
        % (int(bosco.sum()), bosco.sum() * 0.81))
    # 3) chiome delle latifoglie nel bosco
    from alberi_util import gruppi_alberi
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    dentro = np.isin(nomi, ['terrain_bosco', 'terrain_forest'])
    dentro = ndimage.binary_erosion(dentro, iterations=1)              # al margine del bosco restano chiare
    cnt = collections.Counter(); n_alb = 0
    for nm in OGG:
        o = m.obj(nm)
        for g in gruppi_alberi(m, nm):
            tr = [c for c in g if any(o['mats'][f] == 'trunk_brown' for f in c['faces'])]
            if not tr: continue
            t = tr[0]; x = (t['lo'][0] + t['hi'][0]) / 2; z = (t['lo'][2] + t['hi'][2]) / 2
            fi, fj = m.ij(x, z); i = int(np.clip(np.floor(fi), 0, dentro.shape[0] - 1)); j = int(np.clip(np.floor(fj), 0, dentro.shape[1] - 1))
            if not dentro[i, j] or Hc[i, j] > soglia_b[i, j]: continue
            cambi = 0
            for c in g:
                if c is t: continue
                for f in c['faces']:
                    nv = SCURISCI.get(o['mats'][f])
                    if nv:
                        cnt[o['mats'][f] + ' -> ' + nv] += 1; o['mats'][f] = nv; cambi += 1
            n_alb += cambi > 0
    log('chiome delle latifoglie dentro il bosco scurite di un grado: %d alberi (%s)' % (n_alb, ', '.join('%s %d facce' % kv for kv in cnt.most_common())))
    if n_p: log('cenge erbose e altopiano delle Pale con prato alpino: %d facce' % n_p)
    return LOG

def mtl_nuovi(path_mtl):
    """aggiunge all'MTL i materiali nuovi (stesso formato degli altri)"""
    righe = open(path_mtl).read()
    blocchi = righe.split('newmtl ')
    modello = None
    for b in blocchi[1:]:
        if b.startswith('terrain_meadow'): modello = b; break
    out = righe.rstrip('\n') + '\n'
    for nome, col in NUOVI_MAT.items():
        if ('newmtl ' + nome + '\n') in righe: continue
        corpo = modello.split('\n', 1)[1]
        linee = []
        for l in corpo.split('\n'):
            if l.startswith('Kd '): l = 'Kd %.3f %.3f %.3f' % col
            linee.append(l)
        out += '\nnewmtl ' + nome + '\n' + '\n'.join(linee).rstrip('\n') + '\n'
    return out
