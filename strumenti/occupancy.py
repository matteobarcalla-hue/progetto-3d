import numpy as np
def occupancy(m, exclude=('Terreno', 'Base_Sezione', 'Mare'), minsize=0.0, skip_small_veg=True, extra_exclude=()):
    """griglia 0.9 m (celle del terreno) con True dove c'è un oggetto (bbox), una strada o acqua"""
    occ = np.zeros(m.M.shape, bool)
    for o in m.objs:
        if o['name'] in exclude or o['name'] in extra_exclude: continue
        for c in m.comps(o['name']):
            lo, hi = c['lo'], c['hi']
            if max(hi[0] - lo[0], hi[2] - lo[2]) < minsize: continue
            i0, j0 = m.ij(lo[0], lo[2]); i1, j1 = m.ij(hi[0], hi[2])
            i0 = int(np.clip(np.floor(i0), 0, occ.shape[0] - 1)); i1 = int(np.clip(np.ceil(i1), 0, occ.shape[0] - 1))
            j0 = int(np.clip(np.floor(j0), 0, occ.shape[1] - 1)); j1 = int(np.clip(np.ceil(j1), 0, occ.shape[1] - 1))
            occ[i0:i1 + 1, j0:j1 + 1] = True
    names = np.array(m.mats + ['<buco>'])[m.M]
    occ |= np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', '<buco>'])
    return occ

def occupancy_fine(m, exclude=('Terreno', 'Base_Sezione', 'Mare'), extra_exclude=(), with_mats=True):
    """come occupancy ma rasterizza le singole facce (proiezione in pianta), non gli ingombri dei componenti"""
    from PIL import Image, ImageDraw
    NI, NJ = m.M.shape
    im = Image.new('1', (NJ, NI), 0); dr = ImageDraw.Draw(im)
    V = m.V
    for o in m.objs:
        if o['name'] in exclude or o['name'] in extra_exclude or not o['faces']: continue
        for f in o['faces']:
            P = V[np.array(f) - 1]
            fi, fj = m.ij(P[:, 0], P[:, 2])
            pts = list(zip((fj - 0.5).tolist(), (fi - 0.5).tolist()))
            if len(pts) >= 3: dr.polygon(pts, fill=1, outline=1)
            else: dr.line(pts, fill=1)
    occ = np.array(im, bool)
    if with_mats:
        names = np.array(m.mats + ['<buco>'])[m.M]
        occ |= np.isin(names, ['path_dirt', 'street_stone', 'piazza_stone', '<buco>'])
    return occ
