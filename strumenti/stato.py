"""Carica lo stato finale della pipeline (pickle scritto da fase1.py) in un Model."""
import pickle, numpy as np
from model import Model
def carica(path):
    m = Model('orig.pkl', 'terrain_orig.npz')
    if path:
        s = pickle.load(open(path, 'rb'))
        m.V = s['V']; m.objs = s['objs']; m.H = s['H']; m.M = s['M']; m.mats = s['mats']; m.invalidate()
        if 'I0' in s: m.I0, m.J0 = s['I0'], s['J0']
    return m
