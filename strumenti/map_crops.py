import sys, collections, numpy as np; sys.path.insert(0,'tools')
from model import Model
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
m = Model()
CROP = ('crop_green','crop_gold','vine')
road = np.isin(np.array(m.mats+['x'])[m.M], ['path_dirt','street_stone'])
field = np.isin(np.array(m.mats+['x'])[m.M], ['terrain_field','crop_green','soil_dark'])
img = np.ones(m.M.shape+(3,))*0.85
img[field] = (0.85,0.75,0.4); img[road] = (0.55,0.35,0.2)
fig, ax = plt.subplots(figsize=(12,16), dpi=110)
ax.imshow(np.flipud(img), extent=[-193,239,-305.1,271.8], interpolation='nearest')
cols = {}
for o in m.objs:
    if o['name'] in ('Terreno','Mercati','Dettagli_Borgo_Basso','Dettagli_Borgo_Alto','Borgo_Basso'): continue
    if not any(mm in CROP for mm in o['mats']): continue
    for c in m.comps(o['name']):
        ms = collections.Counter(o['mats'][i] for i in c['faces'])
        if ms.most_common(1)[0][0] not in CROP: continue
        P = m.V[c['verts']]
        if P[:,1].min() - m.height(P[:,0],P[:,2]).max() > 1.0: continue   # non a terra
        ce = (c['lo']+c['hi'])/2
        on = any(t in ('path_dirt','street_stone') for t in m.mat_at(P[:,0], P[:,2]))
        ax.plot(ce[2], ce[0], '.', ms=2, color='red' if on else 'green')
ax.set_xticks(np.arange(-180,240,20)); ax.set_yticks(np.arange(-300,280,20)); ax.grid(alpha=0.3); ax.tick_params(labelsize=7)
plt.tight_layout(); plt.savefig('img/map_crops.png')
