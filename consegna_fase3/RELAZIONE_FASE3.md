# Fase 3 – relazione

Lavoro fatto **sul tuo file** `castello sul mare.blend` (Blender 5.0.1, 48,1 MB), non sul mio OBJ precedente: tutte le
modifiche che avevi fatto a mano (terreno scolpito, alberi tolti o spostati, mulino, dettagli dei poderi, mare, ecc.)
sono il punto di partenza e restano dove le avevi messe, salvo dove la richiesta di questa fase chiedeva di intervenire.

Coordinate in metri come nell'OBJ: X verso il mare, Z verso la campagna, quote Y verso l'alto.

---

## 1. Pale dolomitiche (nuovo oggetto `Pale_Dolomitiche`)

**Dove.** La montagna più alta è il massiccio a nord-ovest (verso −X/+Z), quello dove avevi rialzato la cima a cupola
fino a **167,8 m**. La sua spalla sommitale sta a 136-144 m, cioè all'altezza delle cime delle 15 guglie esistenti
(113-149 m). Le pale sorgono lì, sulla cima; le 15 guglie restano dove sono, davanti, **non toccate**.

**Forma.** Massiccio largo a pareti verticali, sul modello delle Pale di San Martino, costruito a banchi di roccia
(12 banchi di 4,5-8 m, da 139 a 203 m): dove la parete è a picco i banchi formano sottili cenge orizzontali, dove il
pendio è a gradoni diventano cenge larghe erbose. Pareti chiare con colature verticali più scure e camini (intagli
verticali che si allargano verso l'alto).

| parte | quota massima |
|---|---|
| Zoccolo con la cengia grande (copre tutta la cima) | circa 162-167 m |
| **Pala Grande** (sopra la tua cupola) | **203,4 m – punto più alto della mappa** |
| Cima di Mezzo | 197,8 m |
| Pala del Sud | 178,7 m |
| Campanile (guglia isolata davanti, con due aghi minori) | 168,4 m |

- Impronta del massiccio: 96 × 135 m (8.343 m² alla base); 3.126 facce.
- Prima della fase 3 il punto più alto era la tua cupola, 167,8 m: ora è la Pala Grande, 35,6 m più in alto.
- La cupola resta sotto la Pala Grande (il terreno non è stato abbassato; è coperto dalla roccia).
- Ghiaioni chiari ai piedi delle pareti: 2.554 celle di ghiaia, terreno rialzato fino a 7,2 m al piede; vicino al
  bordo della mappa il rialzo sfuma a zero, così le fasce laterali del plastico (`Base_Sezione`) combaciano ancora.
- Tolti sotto il massiccio, a meno di 6 m dalle pareti e sui ghiaioni: 183 alberi (`Alberi_Aree_Nuove`) e 4 sassi.
- Le cenge erbose hanno il prato giallo d'alta quota (vedi punto 5).

## 2. Strada dal paese dell'altopiano al fiume, nel solco

- Il tratto lungo il fiume è stato spostato nel solco della riva: **90 m**, larga 3 m, a quota 1,9-2,8 m,
  pendenza massima 8%. Il vecchio tratto stava a −0,9…+0,9 m, cioè dentro l'argilla e in 2 punti nell'acqua.
- Le 128 celle del vecchio tracciato sono tornate argilla (vicino all'acqua) o prato.
- I due capi sono agganciati alla strada esistente alla stessa quota; fuori dal borgo, il resto della strada fra il
  paese e il fiume è quello di prima.
- Tolti lungo il nuovo tracciato: 16 alberi di `Alberi`, 2 di `Alberi_Nuovi`, 5 sassi.

## 3. Sentieri sottili fra boschi e montagne

Tracciati sul terreno cercando il percorso meno ripido (larghi circa 1 m, terra battuta, incisi nel pendio):

| sentiero | lunghezza | quote | pendenza media / massima |
|---|---|---|---|
| dei pascoli (dal paese dell'altopiano al bosco e ai prati alti) | 215 m | 47 → 97 m | 23% / 32% |
| delle Pale (dalla strada della cava alle guglie) | 447 m | 28 → 111 m | 18% / 32% |
| delle Pale, tratto alto (dalle guglie ai ghiaioni, fra il Campanile e lo zoccolo) | 155 m | 110 → 136 m | 16% / 31% |
| del canyon (lungo il bordo del canyon) | 189 m | 47 → 89 m | 22% / 42% |
| del bosco di ponente (dalla strada dei campi alla valle) | 119 m | 25 → 34 m | 8% / 30% |

Le pendenze massime sono su tratti di 4 m. Lungo i sentieri sono stati tolti gli alberi e i sassi che ci stavano sopra.

## 4. Borghi medievali fitti

Tutte le case nuove sono **copie** (spostate, ruotate, scalate) di 43 edifici esistenti presi da `Borgo_Basso`,
`Villaggio_Altopiano`, `Porto` e `Borgo_Alto` con i loro dettagli: nessuna casa è fatta con geometria generica.
Le case stanno a schiera lungo le vie, con la porta sulla via, tetti a quote diverse e passaggi fra le schiere.

**Paese dell'altopiano – nuovo oggetto `Borgo_Altopiano`: 129 case.**
- Tolte le case sparse: 25 del villaggio vecchio e 18 dell'allargamento della fase 2. Restano la chiesa,
  la torretta, i 2 pozzi e i filari degli orti (`Villaggio_Altopiano` passa da 9.590 a 3.490 facce;
  `Villaggio_Altopiano_Nuovo` da 5.509 a 69: resta solo il pozzo).
- 2 piazze (della chiesa 370 m², sud 225 m²) e 16 vie e vicoli: via Maestra 75 m, di Ponente 100 m, di Levante 103 m,
  traverse, vicolo della chiesa, del pozzo, degli orti, belvedere, mulattiera dei monti, 4 vicoli interni.
  Pendenza massima 10% (fino al 12,4% in due vicoli interni corti).
- 7 orti a strisce dietro le case; 1.450 celle di roccia in piano dentro il borgo diventate cortili.

**Porto – nuovo oggetto `Borgo_Porto`: 37 case** (39 posate, 2 tolte nei controlli finali, vedi punto 7).
- Tolte le 7 case sparse della fase 2 (`Porto_Paese_Nuovo`, rimasto vuoto e quindi eliminato dal .blend);
  le case e i magazzini originali del porto restano tutti dove sono.
- Piazza del porto (132 m²), via del Molo 87 m, del Porto, di Mezzo, della Costa, Alta, del Belvedere, del Colle,
  disposte a terrazze sul pendio (pendenza massima 10%, 12% in via del Colle) e collegate da 5 scalinate di pietra
  (113 gradini in tutto, alzata massima 17 cm).

## 5. Biomi più distinguibili (3 materiali nuovi)

- **Prati d'alta quota gialli** – materiale nuovo `terrain_meadow_alpine` (colore 0,70 / 0,65 / 0,33):
  36.914 celle (29.900 m²) sopra circa 91 m, con soglia irregolare fra 82 e 100 m e un passaggio a chiazze.
- **Bosco più scuro** – materiale nuovo `terrain_bosco` (0,15 / 0,27 / 0,11) per il suolo del bosco sotto circa 95 m:
  86.276 celle (69.884 m²); le chiome delle latifoglie dentro il bosco scurite di un grado (1.242 alberi), con il
  materiale nuovo `tree_bosco` (0,10 / 0,23 / 0,09). Gli alberi isolati nei prati restano chiari.
- **Alta montagna**: 327 latifoglie sopra circa 100 m sostituite da conifere (copie intere di conifere esistenti).

## 6. Alberi più grandi, alti da passarci sotto, disposizione naturale

- Ingranditi 5.964 alberi: scala media 1,76 (fra 1,45 e 2,10; ridotta in 13 casi per non urtare edifici).
- Altezza mediana **9,7 m** (prima 5,0 m); il 90% arriva fino a 12,6 m.
- Chioma alzata allungando il tronco: sotto restano almeno **2,8 m** per le latifoglie e 2,3 m per conifere e ulivi.
  Fanno eccezione gli 11 salici piangenti: i rami pendono fino a terra, sono stati ingranditi interi.
- **Disposizione naturale**: diradamento irregolare dove le chiome ingrandite si sarebbero sovrapposte troppo, con una
  soglia diversa per ogni albero (restano macchie fitte e radure, non una griglia): 4.175 alberi tolti su 10.139 (41%).
- 140 alberi che toccano altri oggetti (staccionate, arnie, carri, frutti) lasciati come erano.
- 2.383 alberi e cespugli con il piede staccato dal suolo (anche dove avevi scolpito il terreno) riappoggiati;
  105 chiome che nel tuo file stavano per aria senza tronco tolte.
- Ritocchi dopo l'ingrandimento: 43 tronchi che spuntavano sopra la chioma accorciati fin dentro la chioma; 2 tronchi
  rimasti senza chioma tolti. 32 tronchi sporgono ancora più di 2 m
  sopra la chioma: sono alberi che già nel tuo file sporgevano più di 1 m, lasciati com'erano disegnati.

## 7. Controlli – cosa ho verificato

| controllo | risultato |
|---|---|
| Compenetrazioni degli oggetti nuovi (borghi e Pale) con tutti gli altri oggetti – controllo esatto triangolo contro triangolo | **nessuna** |
| Vertici di altri oggetti chiusi dentro la roccia delle Pale | **nessuno** |
| Elementi sospesi (staccati da terra e da altri oggetti) | **133**, tutti già presenti nel tuo file (che ne aveva **236**); **0 nuovi**; 103 del tuo file non sono più sospesi (alberi diradati o riappoggiati, pezzi delle case vecchie tolte) |
| Tronchi senza chioma | nessuno nuovo (nel tuo file erano 156, ceppi compresi; ora 41) |
| Percorsi delle persone del kit che attraversano case nuove o Pale | 0 (32 deviazioni attorno agli ostacoli nuovi) |
| Animali del kit dentro case nuove o Pale | 0 (2 tolti: 143 animali animati) |
| Camera 05_Villaggio | spostata sul vicolo della chiesa: passa a 1,4 m minimo dai muri, non attraversa case |
| Altre camere | distanza minima dal terreno 3,5 m (06_Porto), tutte sopra terreno, case e Pale |
| .blend riaperto e confrontato con il modello | 94 oggetti della mappa identici al modello (facce, posizione nel mondo, materiale di ogni faccia), 0 differenze |

**Correzioni fatte durante i controlli** (si toglie o si sposta sempre il nuovo, mai l'originale):
- tolta 1 casa del porto che inglobava un pezzo dell'oggetto `Porto` (a X 197, Z −44);
- tolta 1 casa di via di Mezzo che toccava una lastra di pietra del `Porto` (a X 189, Z −19); la lastra, rimasta 40 cm
  sopra il terreno abbassato per la via, è stata riappoggiata;
- 23 parti staccate delle case copiate e 115 chiome rimaste per aria dopo l'ingrandimento: tolte;
- 62 alberi e cespugli e 5 piccoli oggetti (2 sassi, 1 dettaglio dei poderi, 1 siepe, 1 pezzo del vecchio villaggio)
  rimasti sospesi dopo le modifiche al terreno: riappoggiati.

**Oggetti cambiati** rispetto al tuo file: `Terreno`, i 4 oggetti degli alberi, `Animali` (110 pezzi di animali fermi
dentro le case o le vie del borgo; nel video il kit li nasconde comunque), `Rocce`, `Rocce_Promontori`, `Porto` (solo la
lastra riappoggiata), `Poderi_Dettagli` e `Siepi_e_Confini` (1 elemento riappoggiato ciascuno), `Villaggio_Altopiano`,
`Villaggio_Altopiano_Nuovo`, `Porto_Paese_Nuovo` (eliminato perché vuoto). **Tutti gli altri 80 oggetti sono identici.**
Cubo, camera e le 3 luci del tuo file non sono stati toccati.

Facce totali dell'OBJ: 1.391.595 (la mappa del tuo file, senza gli oggetti del kit, ne aveva 1.609.720; il calo viene
dal diradamento degli alberi).

## 8. Cosa NON ho verificato

- Le immagini sono rese in Workbench (colori piatti): non ho fatto render Eevee/Cycles con il kit, quindi luce e
  colori finali nel video possono differire un poco.
- Non ho riprodotto i 7.013 fotogrammi delle camere: percorsi e camere sono controllati solo geometricamente.
- Non ho misurato la fluidità in Blender sul tuo computer (le facce sono il 13,5% in meno di prima).
- Lo spazio sotto le chiome è calcolato sugli alberi ingranditi; i 140 alberi lasciati com'erano e i 13 con scala
  ridotta hanno l'altezza di prima.

## 9. Interpretazioni da confermare

1. **Pale**: le ho messe sulla cima della montagna più alta (dove avevi fatto la cupola), alla quota delle guglie.
   Se intendevi metterle proprio al posto delle 15 guglie, dimmelo.
2. **Solco**: ho inteso il ripiano lungo la riva fra X −27 e X 58 (Z da −96 a −111). Se il solco che hai scavato
   è un altro, indicami dove.
3. **Animali fermi** (`Animali`): nel tuo file la mesh era ruotata di 90 gradi attorno a X (animali coricati);
   l'ho rimessa diritta. Il kit li nasconde quando gli animali animati sono accesi. Se la rotazione era voluta,
   dimmelo e la ripristino.
4. **Prato giallo d'alta quota** da circa 91 m in su (passaggio fra 82 e 100 m).

## 10. Il .blend aggiornato

- Stessi oggetti, stessi nomi, stessa collezione, stessa rotazione degli oggetti: è cambiata solo la mesh dentro.
- 3 oggetti nuovi nella collezione della mappa: `Borgo_Altopiano`, `Borgo_Porto`, `Pale_Dolomitiche`.
- 3 materiali nuovi: `terrain_meadow_alpine`, `terrain_bosco`, `tree_bosco`.
- Kit di ripresa **v6** già eseguito dentro il file, con **le tue impostazioni** (FPS 25, colori del cielo, ombre
  leggere, onde e texture spente, velocità di persone e animali 2,0, modalità schermo accesa, riquadri spenti).
  Lo trovi nell'editor di testo come `kit_ripresa_mappa_v6.py`; la tua versione precedente
  (`kit_ripresa_mappa (3).py`) è ancora lì, non l'ho cancellata.
- Salvato con Blender 5.0.1, la tua stessa versione.
