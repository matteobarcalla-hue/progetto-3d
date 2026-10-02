set -e
# da eseguire nella cartella di lavoro (tools/, fase3/, venv/ con il modulo bpy)
P=venv/bin/python
$P tools/fase3.py fase3/c_borghi.obj.state.pkl fase3/c_fin.obj f3_pale f3_sentieri f3_alberi f3_biomi f3_pulizia > fase3/c2.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/c_fin.mtl
echo "1 resto ok"
$P tools/floating.py fase3/c_fin.obj > fase3/flo_c.log 2>&1
$P tools/fase3.py fase3/c_fin.obj.state.pkl fase3/fase3_fin.obj f3_sospesi > fase3/c3.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/fase3_fin.mtl
$P tools/floating.py fase3/fase3_fin.obj > fase3/flo_fin.log 2>&1
echo "2 sospesi ok"
$P tools/conflitti4.py fase3/fase3_fin.obj.state.pkl fase3/conflitti_fin.json > fase3/conf4.log 2>&1
$P tools/fase3.py fase3/fase3_fin.obj.state.pkl fase3/mappa_fase3.obj f3_ritocchi > fase3/c4.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/mappa_fase3.mtl
$P tools/floating.py fase3/mappa_fase3.obj > fase3/flo_mf.log 2>&1
echo "3 ritocchi ok"
$P tools/fase3.py fase3/mappa_fase3.obj.state.pkl fase3/finale.obj f3_ritocchi2 > fase3/c5.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/finale.mtl
$P tools/floating.py fase3/finale.obj > fase3/flo_finale.log 2>&1
$P tools/conflitti4.py fase3/finale.obj.state.pkl fase3/conflitti_finale.json > fase3/conf4_finale.log 2>&1
$P fase3/an_spogli.py fase3/f3_base.obj.state.pkl fase3/finale.obj.state.pkl > fase3/spogli.log 2>&1
echo "4 finale ok"
