from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
def pair(a, b, w):
    A = Image.open(a).convert('RGB'); Bm = Image.open(b).convert('RGB')
    h = int(A.height * w / A.width); A = A.resize((w, h)); Bm = Bm.resize((w, h))
    return A, Bm
def label(im, t):
    d = ImageDraw.Draw(im); bb = d.textbbox((10, 8), t, font=F); d.rectangle([bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4], fill=(255, 255, 255)); d.text((10, 8), t, font=F, fill=(20, 20, 20)); return im
def sheet(rows, out, w=800, title=None):
    ims = []
    for a, b, t in rows:
        A, Bm = pair(a, b, w); ims.append((label(A, 'PRIMA - ' + t), label(Bm, 'DOPO - ' + t)))
    H = sum(A.height for A, _ in ims) + 6 * len(ims)
    S = Image.new('RGB', (2 * w + 6, H), 'white'); y = 0
    for A, Bm in ims:
        S.paste(A, (0, y)); S.paste(Bm, (w + 6, y)); y += A.height + 6
    S.save(out)
C = 'consegna/'
sheet([('img/ori_top.png', 'img/fin_top.png', 'vista dall\'alto (alto = mare, +X)')], C + '01_vista_dall_alto_prima_dopo.png', w=700)
sheet([('img/ori_pan.png', 'img/fin_pan.png', 'panoramica obliqua dal mare')], C + '02_panoramica_obliqua_prima_dopo.png', w=900)
sheet([('img/ori_rocca_top.png', 'img/fin_rocca_top.png', 'rocca dall\'alto (chiostro a destra, cappella e cimitero sopra)'),
       ('img/ori_rocca_obl.png', 'img/fin_rocca_obl.png', 'rocca e sperone roccioso')], C + '03_rocca_prima_dopo.png', w=800)
sheet([('img/ori_foce_top.png', 'img/fin_foce_top.png', 'foce dall\'alto'), ('img/ori_foce_obl.png', 'img/fin_foce_obl.png', 'foce, canneto e argini d\'argilla'),
       ('img/ori_sent_top.png', 'img/fin_sent_top.png', 'sentiero ponte-altopiano a tornanti')], C + '04_fiume_foce_sentiero_prima_dopo.png', w=700)
sheet([('img/ori_mare_sx.png', 'img/fin_mare_sx.png', 'promontorio sul mare'), ('img/ori_rocca_fiume.png', 'img/fin_rocca_fiume.png', 'sperone sotto la rocca'),
       ('img/ori_cascata.png', 'img/fin_cascata.png', 'montagne della cascata'), ('img/ori_teatro.png', 'img/fin_teatro.png', 'scogliera del teatro')], C + '05_promontori_prima_dopo.png', w=700)
sheet([('img/ori_pascolo.png', 'img/fin_pascolo.png', 'animali nel modello (pascolo)'), ('img/ori_mucche.png', 'img/fin_mucche.png', 'animali nel modello (podere)')], C + '06_animali_prima_dopo.png', w=700)
print('ok')
