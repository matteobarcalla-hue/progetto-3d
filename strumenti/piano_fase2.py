from PIL import Image, ImageDraw, ImageFont
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f14 = ImageFont.truetype(F, 14); f16 = ImageFont.truetype(FB, 16); f20 = ImageFont.truetype(FB, 22); f12 = ImageFont.truetype(F, 12)
S = 1.5                       # pixel per metro
XMAX, ZMIN = 330, -365        # angolo in alto a sinistra della tavola
W, H = int((255 - ZMIN) * S) + 360, int((XMAX + 470) * S) + 70
def P(x, z): return (int((z - ZMIN) * S), int((XMAX - x) * S) + 50)
base = Image.open('img/fin_top.png').convert('RGB')
base = base.crop((60, 28, 1140, 1470)); base = base.resize((int(base.width * 0.6), int(base.height * 0.6)))
can = Image.new('RGB', (W, H), (236, 240, 244))
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
# mare esteso (alto) e verso sinistra oltre la costa
d.rectangle([P(XMAX, ZMIN), P(272, 255)], fill=(40, 90, 150, 255))
d.polygon([P(XMAX, ZMIN), P(XMAX, -193), P(200, -193), P(150, -260), P(140, ZMIN)], fill=(40, 90, 150, 255))
can.paste(base, P(272, -193))
# estensione lato altopiano (-Z): montagna
d.polygon([P(150, ZMIN), P(150, -260), P(200, -193), P(-305, -193), P(-305, ZMIN)], fill=(150, 120, 90, 150), outline=(90, 60, 40, 255))
# estensione lato cascata (-X): montagna, valle, canyon
d.rectangle([P(-305, ZMIN), P(-455, 239)], fill=(130, 110, 85, 150), outline=(90, 60, 40, 255))
# fiume e canyon che proseguono
d.line([P(-305, -165), P(-350, -175), P(-400, -195), P(-455, -205)], fill=(60, 140, 220, 255), width=6)
d.line([P(-305, -150), P(-455, -185)], fill=(90, 60, 40, 200), width=2); d.line([P(-305, -180), P(-455, -228)], fill=(90, 60, 40, 200), width=2)
# valle verso il basso a destra
d.line([P(-305, 60), P(-380, 80), P(-455, 70)], fill=(120, 160, 90, 255), width=8)
# espansione paese altopiano
d.polygon([P(190, -190), P(185, -235), P(140, -262), P(95, -250), P(95, -192)], fill=(230, 140, 40, 170), outline=(160, 80, 0, 255))
# porto -> paesino portuale
d.rectangle([P(222, -78), P(190, -8)], fill=(230, 140, 40, 150), outline=(160, 80, 0, 255))
d.rectangle([P(222, 12), P(196, 40)], fill=(230, 140, 40, 150), outline=(160, 80, 0, 255))
# alberi ai poderi laterali
for x0, x1 in ((-95, -55), (-5, 35), (85, 125)):
    d.rectangle([P(x1, 168), P(x0, 238)], fill=(60, 150, 60, 110), outline=(30, 100, 30, 255))
# torre del mago
cx, cy = P(-229, -177); d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline=(170, 40, 200, 255), width=4)
can.paste(ov, (0, 0), ov)
d = ImageDraw.Draw(can)
def lab(x, z, t, f=f14, c=(20, 20, 20), bg=(255, 255, 255)):
    p = P(x, z); bb = d.textbbox(p, t, font=f); d.rectangle([bb[0] - 4, bb[1] - 3, bb[2] + 4, bb[3] + 3], fill=bg); d.text(p, t, font=f, fill=c)
lab(318, -350, 'MARE ESTESO FINO ALL\'ORIZZONTE (superficie piatta, poche facce)', f16, (255, 255, 255), (40, 90, 150))
lab(60, -350, 'LATO ALTOPIANO (-Z, +150 m):\nmontagna con varietà rocciosa', f16)
lab(170, -355, 'paese dell\'altopiano\nche si allarga\nfra monti e mare', f14, (120, 60, 0))
lab(-330, -330, 'LATO CASCATA (-X, +150 m): proseguono montagna, valle e canyon con il fiume', f16)
lab(-410, -330, 'canyon + fiume', f14, (20, 60, 140))
lab(-360, 90, 'valle', f14, (40, 90, 30))
lab(250, -140, 'case portuali', f14, (120, 60, 0))
lab(-150, 120, 'più alberi ai 3 poderi laterali\n(densità come le zone vicine)', f14, (20, 80, 20))
d.line([P(-150, 160), P(-95, 200)], fill=(30, 100, 30), width=2)
lab(-200, -330, 'torre del mago: scala scavata nella roccia\nfino alla strada, grotta d\'ingresso\nsotto la torre, calderone', f14, (110, 20, 140))
d.line([P(-212, -300), P(-226, -184)], fill=(170, 40, 200), width=2)
# orientamento e legenda
lx = int((255 - ZMIN) * S) + 25
d.text((lx, 60), 'PIANO FASE 2 (proposta)', font=f20, fill=(20, 20, 20))
leg = [((40, 90, 150), 'mare esteso'), ((150, 120, 90), 'nuove aree montane'), ((230, 140, 40), 'nuovi edifici (paese, porto)'),
       ((60, 150, 60), 'infittimento alberi'), ((60, 140, 220), 'fiume/canyon che prosegue'), ((170, 40, 200), 'torre del mago')]
for k, (c, t) in enumerate(leg):
    y = 110 + k * 28; d.rectangle([lx, y, lx + 22, y + 18], fill=c); d.text((lx + 32, y), t, font=f14, fill=(20, 20, 20))
txt = ['Orientamento:', 'alto = +X (mare)', 'basso = -X (cascata, miniera)', 'sinistra = -Z (fiume, altopiano)', 'destra = +Z (campagna)', '',
       'Scala: 1 quadretto = 50 m', 'Mappa attuale: 577 x 432 m', 'Con le estensioni: ~730 x 600 m', '', 'Stima peso (da confermare):',
       ' dopo la fase 1: 1,22 M facce, 63,7 MB', ' + terreno nuovo 0,9 m: ~215 mila facce', ' + alberi/rocce nuove aree: ~250-370 mila', ' + paese, porto, scala: ~40 mila',
       ' totale: ~1,72-1,84 milioni di facce,', ' ~90-96 MB: OLTRE il limite 1,5 M/80 MB', '', 'Alternativa nei limiti:', ' terreno lontano a maglia 1,8 m e', ' alberi più radi in quota:', ' ~1,45-1,5 M facce, ~76-80 MB']
for k, t in enumerate(txt): d.text((lx, 300 + k * 21), t, font=f14, fill=(20, 20, 20))
# griglia 50 m
for x in range(-450, 330, 50):
    a = P(x, ZMIN); b = P(x, 255); d.line([a, b], fill=(255, 255, 255), width=1)
for z in range(-350, 256, 50):
    a = P(XMAX, z); b = P(-470, z); d.line([a, b], fill=(255, 255, 255), width=1)
can.save('consegna/07_piano_fase2_vista_dall_alto.png'); print(can.size)
