set -e
# da eseguire nella cartella di lavoro (tools/, fase3/, venv/ con il modulo bpy)
venv/bin/python tools/fase3.py fase3/f3_base.obj.state.pkl fase3/c_borghi.obj f3_borghi f3_strade > fase3/c1.log 2>&1
echo borghi-strade ok
venv/bin/python tools/fase3.py fase3/c_borghi.obj.state.pkl fase3/c_fin.obj f3_pale f3_sentieri f3_alberi f3_biomi f3_pulizia > fase3/c2.log 2>&1
echo resto ok
venv/bin/python -c "
import sys; sys.path.insert(0,'tools'); import f3_biomi
open('fase3/castello_mappa_estesa.mtl','w').write(f3_biomi.mtl_nuovi('fase3/castello_mappa_estesa.mtl'))" 
cp fase3/castello_mappa_estesa.mtl fase3/c_fin.mtl
venv/bin/python tools/floating.py fase3/c_fin.obj > fase3/flo_c.log 2>&1
echo sospesi ok
venv/bin/python tools/fase3.py fase3/c_fin.obj.state.pkl fase3/fase3_fin.obj f3_sospesi > fase3/c3.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/fase3_fin.mtl
venv/bin/python tools/floating.py fase3/fase3_fin.obj > fase3/flo_fin.log 2>&1
echo finale ok
