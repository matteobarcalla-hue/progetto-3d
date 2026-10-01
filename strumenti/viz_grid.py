import numpy as np, sys
from PIL import Image
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d = np.load(sys.argv[1]); H = d['H']; M = d['M']; mats = list(d['mats']); D = d['D']
out = sys.argv[2]
Hf = np.where(np.isnan(H), np.nanmin(H), H)
gx, gz = np.gradient(Hf, 0.9)
az = np.radians(315); alt = np.radians(40)
slope = np.arctan(np.hypot(gx, gz)); aspect = np.arctan2(-gz, gx)
hs = np.sin(alt)*np.cos(slope) + np.cos(alt)*np.sin(slope)*np.cos(az-aspect)
def orient(a): return np.flipud(a)   # righe = i (X), in alto +X
fig, ax = plt.subplots(1, 1, figsize=(12, 16), dpi=110)
ax.imshow(orient(hs), cmap='gray', extent=[-193, 239, -305.1, 271.8])
cs = ax.contour(np.linspace(-193,239,H.shape[1]), np.linspace(-305.1,271.8,H.shape[0]), Hf, levels=np.arange(-8,130,4), linewidths=0.4, cmap='terrain')
ax.set_xlabel('Z (destra = campagna)'); ax.set_ylabel('X (alto = mare)'); ax.grid(alpha=0.3)
ax.set_xticks(np.arange(-180,240,20)); ax.set_yticks(np.arange(-300,280,20)); ax.tick_params(labelsize=7)
plt.tight_layout(); plt.savefig(out+'_hillshade.png'); plt.close()
fig, ax = plt.subplots(1, 1, figsize=(12, 16), dpi=110)
Dm = np.ma.masked_less(D, 2)
ax.imshow(orient(hs), cmap='gray', extent=[-193, 239, -305.1, 271.8])
ax.imshow(orient(Dm), cmap='autumn', extent=[-193, 239, -305.1, 271.8], interpolation='nearest')
ax.set_xticks(np.arange(-180,240,20)); ax.set_yticks(np.arange(-300,280,20)); ax.tick_params(labelsize=7); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(out+'_dup.png'); plt.close()
cols = {'crop_green':(0.4,0.6,0.2),'moss_stone':(0.4,0.45,0.35),'path_dirt':(0.6,0.45,0.3),'piazza_stone':(0.75,0.72,0.65),'sand':(0.9,0.83,0.6),'soil_dark':(0.35,0.25,0.18),'stone_dark':(0.3,0.3,0.32),'stone_light':(0.7,0.7,0.7),'street_stone':(0.55,0.55,0.55),'terrain_clay':(0.7,0.45,0.3),'terrain_field':(0.8,0.7,0.35),'terrain_forest':(0.2,0.38,0.18),'terrain_grass':(0.38,0.58,0.25),'terrain_gravel':(0.6,0.58,0.52),'terrain_meadow':(0.55,0.68,0.3),'terrain_rock':(0.5,0.48,0.45)}
C = np.zeros(M.shape+(3,))
for k, m in enumerate(mats): C[M==k] = cols.get(m, (1,0,1))
C[M<0] = (1,0,1)
fig, ax = plt.subplots(1, 1, figsize=(12, 16), dpi=110)
ax.imshow(orient(C), extent=[-193, 239, -305.1, 271.8], interpolation='nearest')
ax.set_xticks(np.arange(-180,240,20)); ax.set_yticks(np.arange(-300,280,20)); ax.tick_params(labelsize=7); ax.grid(alpha=0.3)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=cols[m], label=m) for m in mats], loc='lower right', fontsize=7)
plt.tight_layout(); plt.savefig(out+'_mat.png'); plt.close()
