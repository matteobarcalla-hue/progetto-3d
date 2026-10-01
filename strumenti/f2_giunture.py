"""Fase 2 - giunture fra mappa vecchia e terre nuove.
Lungo il vecchio bordo -Z, fra x 128 e 212, il terreno originale aveva una scarpata di 3-5 m parallela al bordo
(il ciglio del vecchio plastico): con la mappa estesa diventava una riga dritta di circa 60 m. Qui la scarpata viene
addolcita su una fascia di larghezza variabile (4-11 m per lato), con piccole ondulazioni che spezzano la linea,
e i materiali delle due parti si mescolano a chiazze invece di cambiare su una riga."""
import numpy as np
from scipy import ndimage
import ops

LOG = []
def log(s): LOG.append(s); print('[giunture]', s)

Z_BORDO = -193.0                    # prima fila della griglia originale (lato -Z)
X0, X1 = 128.0, 194.0                 # oltre x 194 comincia la scogliera sul mare: non si tocca

def run(m):
    X, Z = m.grid_xz()
    sm = ops.smoothstep
    lungo = sm(X0, X0 + 12, X) * (1 - sm(X1 - 12, X1, X))
    W = 7.5 + 3.0 * np.sin(X / 9.3) + 1.8 * np.sin(X / 4.1 + 1.3)          # semilarghezza ondulata della fascia
    d = np.abs(Z - (Z_BORDO + 2.5 + 1.5 * np.sin(X / 7.7)))
    w = (1 - sm(0.45 * W, W, d)) * lungo
    H0 = m.H.copy()
    liscio = ndimage.gaussian_filter(m.H, 3.2)
    onde = 0.55 * np.sin(X / 6.1 + 0.7 * np.sin(Z / 5.3)) * np.cos(Z / 4.7 + X / 13.0)
    m.H = m.H * (1 - w) + (liscio + onde * (1 - sm(0.2, 1.0, np.abs(Z - Z_BORDO) / np.maximum(W, 1)))) * w
    dH = m.H - H0; sel = w > 0.02
    log('scarpata del vecchio bordo -Z addolcita fra x %.0f e %.0f: fascia larga 4-11 m per lato, %d vertici, variazione di quota %.2f..%.2f m'
        % (X0, X1, int(sel.sum()), float(dH[sel].min()), float(dH[sel].max())))
    # materiali: dal lato nuovo, chiazze copiate a specchio dal lato vecchio (niente cambio di colore su una riga)
    Xc, Zc = m.cell_xz()
    i_b = int(np.floor(float(m.ij(0.0, Z_BORDO + 0.45)[1])))           # prima colonna di celle vecchie
    rng = np.random.default_rng(17)
    rumore = ndimage.gaussian_filter(rng.random(Xc.shape), 1.6)
    rumore = (rumore - rumore.min()) / (rumore.max() - rumore.min())
    n = 0
    lungo_c = sm(X0, X0 + 12, Xc) * (1 - sm(X1 - 12, X1, Xc))
    for j in range(max(0, i_b - 9), i_b):
        k = 2 * i_b - 1 - j                                            # cella a specchio nel lato vecchio
        if k >= m.M.shape[1]: continue
        prob = (1 - (i_b - j) / 10.0) * lungo_c[:, j]
        cop = (rumore[:, j] < prob) & (m.M[:, k] >= 0) & (m.M[:, j] >= 0)
        nomi_k = np.array(m.mats + ['<buco>'])[m.M[:, k]]
        cop &= ~np.isin(nomi_k, ['path_dirt', 'street_stone', 'piazza_stone', 'terrain_field', 'crop_green', 'crop_gold'])
        m.M[cop, j] = m.M[cop, k]; n += int(cop.sum())
    # e dal lato vecchio la fascia di bordo (colore uniforme lungo il ciglio) prende chiazze dei materiali più interni
    n2 = 0; vietati = ['path_dirt', 'street_stone', 'piazza_stone', 'terrain_field', 'crop_green', 'crop_gold']
    nomi = np.array(m.mats + ['<buco>'])
    for j in range(i_b, min(i_b + 9, m.M.shape[1] - 10)):
        k = j + 8
        prob = 0.6 * (1 - (j - i_b) / 9.0) * lungo_c[:, j]
        cop = (rumore[:, j] < prob) & (m.M[:, k] >= 0) & (m.M[:, j] >= 0)
        cop &= ~np.isin(nomi[m.M[:, k]], vietati) & ~np.isin(nomi[m.M[:, j]], vietati)
        m.M[cop, j] = m.M[cop, k]; n2 += int(cop.sum())
    log('materiali mescolati a chiazze lungo la giuntura: %d celle del lato nuovo, %d della fascia di bordo vecchia' % (n, n2))
    return LOG
