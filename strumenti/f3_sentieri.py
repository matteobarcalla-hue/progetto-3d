"""Fase 3 - sentieri sottili fra boschi e montagne (dopo le pale: il sentiero delle Pale sale dalle guglie ai loro ghiaioni)."""
import numpy as np
from scipy import ndimage
import f3_strade
from f3_strade import sentiero, ALBERI
from occupancy import occupancy_fine

LOG = f3_strade.LOG

def run(m):
    escl = ALBERI + ('Rocce', 'Rocce_Promontori', 'Siepi_e_Confini', 'Animali', 'Canneto_Fiume', 'Pareti_Rocciose', 'Fondale_Esteso', 'Mare')
    occ = occupancy_fine(m, extra_exclude=escl, with_mats=False)
    nomi = np.array(m.mats + ['<buco>'])[m.M]
    occ |= np.isin(nomi, ['<buco>', 'terrain_field', 'crop_green', 'crop_gold', 'sand'])
    occ |= m.H[:-1, :-1] < 0.5
    occ = ndimage.binary_dilation(occ, iterations=1)
    sentiero(m, 'delle Pale (dalla strada della cava alle guglie)', (-183.2, 80.2), (-297.0, 186.0), (-330, -165, 55, 239), occ)
    sentiero(m, 'delle Pale, tratto alto (dalle guglie ai ghiaioni delle Pale, fra il Campanile e lo zoccolo)', (-297.0, 186.0), (-375.0, 158.0), (-395, -280, 115, 215), occ)
    sentiero(m, 'del canyon (dalla strada della torre del mago lungo il bordo del canyon)', (-262.4, -149.3), (-352.0, -146.0), (-380, -245, -200, -105), occ)
    sentiero(m, 'del bosco di ponente (dalla strada dei campi alla valle di ponente)', (-234.5, -1.8), (-335.0, -25.0), (-350, -220, -70, 25), occ)
    return LOG
