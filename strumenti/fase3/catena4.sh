set -e
# da eseguire nella cartella di lavoro (tools/, fase3/, venv/ con il modulo bpy)
P=venv/bin/python
$P tools/fase3.py fase3/mappa_fase3.obj.state.pkl fase3/finale.obj f3_ritocchi2 > fase3/c5.log 2>&1
cp fase3/castello_mappa_estesa.mtl fase3/finale.mtl
$P tools/floating.py fase3/finale.obj > fase3/flo_finale.log 2>&1
$P tools/conflitti4.py fase3/finale.obj.state.pkl fase3/conflitti_finale.json > fase3/conf4_finale.log 2>&1
$P fase3/an_spogli2.py fase3/f3_base.obj.state.pkl fase3/finale.obj.state.pkl > fase3/spogli.log 2>&1
$P fase3/an_spunta.py fase3/f3_base.obj.state.pkl fase3/finale.obj.state.pkl >> fase3/spogli.log 2>&1
echo "finale ok"
