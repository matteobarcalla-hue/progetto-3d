"""Tavole di controllo della fase 2 (prima = fine fase 1, dopo = fase 2)."""
from PIL import Image, ImageDraw, ImageFont
import sys
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
def label(im, t):
    d = ImageDraw.Draw(im); bb = d.textbbox((10, 8), t, font=F); d.rectangle([bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4], fill=(255, 255, 255)); d.text((10, 8), t, font=F, fill=(20, 20, 20)); return im
def fit(path, w):
    A = Image.open(path).convert('RGB'); h = int(A.height * w / A.width); return A.resize((w, h))
def sheet(rows, out, w=800):
    """rows: (prima, dopo, titolo) oppure (None, dopo, titolo) per le sole viste nuove, o lista di (img, titolo) per una riga libera"""
    ims = []
    for r in rows:
        if isinstance(r, list):
            ws = (2 * w + 6 - 6 * (len(r) - 1)) // len(r)
            ims.append([label(fit(p, ws), t) for p, t in r])
        else:
            a, b, t = r
            ims.append([label(fit(a, w), 'PRIMA (fase 1) - ' + t), label(fit(b, w), 'DOPO (fase 2) - ' + t)] if a else [label(fit(b, 2 * w + 6), 'DOPO - ' + t)])
    H = sum(max(i.height for i in row) for row in ims) + 6 * len(ims)
    S = Image.new('RGB', (2 * w + 6, H), 'white'); y = 0
    for row in ims:
        x = 0
        for im in row: S.paste(im, (x, y)); x += im.width + 6
        y += max(i.height for i in row) + 6
    S.save(out); print(out, S.size)
C = 'consegna2/immagini/'
import os; os.makedirs(C, exist_ok=True)
sheet([('img/p2o_top.png', 'img/p2h_top.png', "vista dall'alto (in alto il mare)")], C + '01_vista_dall_alto_prima_dopo.png', w=700)
sheet([('img/p2o_pan.png', 'img/p2h_pan.png', 'panoramica dal mare'), ('img/p2o_orizzonte.png', 'img/p2h_orizzonte.png', "verso il mare: orizzonte"),
       ('img/p2o_mare_sud.png', 'img/p2h_mare_sud.png', 'costa nuova sul lato altopiano')], C + '02_mare_orizzonte_prima_dopo.png', w=800)
sheet([('img/p2o_paese.png', 'img/p2h_paese.png', 'paese allargato nel pianoro fra monti e mare'), ('img/p2o_montagne_alt.png', 'img/p2h_montagne_alt.png', 'montagne nuove lato altopiano')],
      C + '03_lato_altopiano_prima_dopo.png', w=800)
sheet([('img/p2o_canyon2.png', 'img/p2h_canyon2.png', 'canyon: il fiume prosegue'), ('img/p2o_valle.png', 'img/p2h_valle.png', 'valle lato cascata'),
       ('img/p2o_canyon.png', 'img/p2h_canyon.png', 'montagne lato cascata')], C + '04_lato_cascata_prima_dopo.png', w=800)
sheet([('img/p2o_torre.png', 'img/p2h_torre.png', 'scala scavata nella roccia fino alla grotta'),
       [('img/p2h_ponte.png', 'DOPO - ponticello e scaletta verso la strada'), ('img/p2h_grotta.png', "DOPO - grotta d'ingresso sotto la torre"), ('img/p2h_calderone.png', 'DOPO - calderone e dettagli')]],
      C + '05_torre_del_mago_prima_dopo.png', w=800)
sheet([('img/p2o_porto.png', 'img/p2h_porto.png', 'porto diventato paesino'), ('img/p2o_poderi_dx.png', 'img/p2h_poderi_dx.png', 'poderi laterali: alberi infittiti'),
       ('img/p2o_poderi_basso.png', 'img/p2h_poderi_basso.png', 'striscia bassa: alberi infittiti')], C + '06_porto_e_alberi_prima_dopo.png', w=800)
sheet([[('img/k6_08_0.png', 'kit v5 - camera 08: dal ponticello'), ('img/k6_08_1.png', '08: lungo la scala'), ('img/k6_08_2.png', '08: arrivo alla grotta')],
       [('img/k5_09_0.png', 'camera 09: dal mare al paese nuovo'), ('img/k5_09_1.png', '09: montagne nuove'), ('img/k5_09_2.png', '09: verso il canyon')],
       [('img/k7_08_eevee.png', 'fotogramma di prova Eevee (camera 08, texture e luce del kit)')]], C + '07_kit_v5.png', w=800)
