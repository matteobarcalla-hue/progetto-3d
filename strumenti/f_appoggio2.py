"""Seconda passata di appoggio (alberi rimasti sollevati dopo la prima)."""
import f_appoggio
LOG = f_appoggio.LOG
def run(m):
    f_appoggio.NUOVI_OK = ()
    return f_appoggio.run(m, lista='fase1_c.obj.sospesi.json')
