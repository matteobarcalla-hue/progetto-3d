"""Fase 2 - rilievi nuovi con lo stesso trattamento roccioso dei promontori della fase 1:
sfaccettature, rugosità, materiali per faccetta, pareti a strati, massi e affioramenti (solo nelle aree nuove)."""
import f_pareti, f_promontori
LOG = []
ZONE_NUOVE = [('montagne nuove lato altopiano', -460, 275, -346, -194.5), ('montagne nuove lato cascata', -460, -306.5, -346, 240)]
def run(m):
    f_pareti.ZONES[:] = ZONE_NUOVE
    f_pareti.SOGLIA_PENDENZA = 2.1; f_pareti.SALTO_STRATI = 50
    f_promontori.ZONES = ZONE_NUOVE
    LOG.extend(f_promontori.run(m)); LOG.extend(f_pareti.run(m))
    return LOG
