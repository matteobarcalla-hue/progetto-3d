import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def components(faces, nv=None):
    """faces: list of lists (0-based global idx). returns labels per face (connected via shared vertices)"""
    rows=[]; cols=[]
    for k,f in enumerate(faces):
        for v in f: rows.append(k); cols.append(v)
    rows=np.array(rows); cols=np.array(cols)
    uv, inv = np.unique(cols, return_inverse=True)
    nf=len(faces); n=nf+len(uv)
    A = coo_matrix((np.ones(len(rows)), (rows, nf+inv)), shape=(n,n))
    nc, lab = connected_components(A, directed=False)
    fl = lab[:nf]; _, fl = np.unique(fl, return_inverse=True)
    return fl
