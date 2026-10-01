# Mappa del regno – Fase 1: correzioni, rocca, promontori, fiume, animali e kit

## Contenuto della consegna

| File | Cosa contiene |
|---|---|
| `castello_mappa_estesa.obj` | modello aggiornato (OBJ per Blender 5.0.1, Y in alto) |
| `castello_mappa_estesa.mtl` | materiali: stessi 71 materiali dell'originale, nessuno nuovo |
| `kit_ripresa_mappa.py` | kit di ripresa **v4**: sostituisce la v3 ed è un file completo |
| `immagini/01…06` | controlli visivi prima/dopo (anteprime Workbench, vedi nota sotto) |
| `immagini/07_piano_fase2_vista_dall_alto.png` | pianta dall'alto della proposta per la fase 2 |
| `strumenti/` | script Python usati per la fase 1, utili per ripetere i passaggi |

**Nota sulle anteprime.** Le immagini 01–06 sono render Workbench (anteprima semplificata, senza texture né luce del kit), fatti con Blender 5.0.1 senza scheda video. Ho provato il kit anche in Eevee: il fotogramma di prova è in `immagini/06_animali_e_kit.png`.

## Richieste di questa sessione

| Richiesta | Fase 1 | Note |
|---|---|---|
| Mare esteso fino all'orizzonte | fase 2 | vedi pianta 07 |
| Mappa estesa sul lato dell'altopiano e sul lato corto della cascata, con varietà rocciosa | fase 2 | vedi pianta 07 |
| Promontori più realistici, con più roccia | fatto | sezione 3 |
| Più realismo alla foce | fatto | sezione 4 |
| Sentiero fra il ponte sul fiume e il paese sull'altopiano | fatto | sezione 5 |
| Percorsi dai fossati agli ingressi della fortezza | fatto | sezione 5 |
| Linee dritte lasciate dalle espansioni precedenti | fatto | sezione 4 |
| Torri del mastio sospese, podere inglobato, campi tagliati o sollevati | fatto | sezioni 1 e 5 |
| Ultimo compartimento: chiostro a destra, cappella con cimitero sopra, mastio a sinistra | fatto | sezione 1 |
| Ingressi delle torri ai camminamenti | fatto | sezione 2 |
| Fiume più sottile con due strisce d'argilla | fatto | sezione 4 |
| Animali e persone più realistici, animali tutti in movimento | fatto | sezione 6 |
| Texture semplici e delicate | nel kit | sezione 6 |
| File diversi che funzionano insieme | fatto | sezione 6, kit provato con l'OBJ finale |
| Paese dell'altopiano esteso fra monti e mare | fase 2 | vedi pianta 07 |
| Scala nella roccia fra la torre del mago e la strada, con grotta e calderone | fase 2 | vedi pianta 07 |
| Stessa densità di alberi nelle zone aggiunte dopo, come i 3 poderi laterali | fase 2 | vedi pianta 07 |
| Porto che diventa un paesino di case portuali | fase 2 | vedi pianta 07 |

## 1. Rocca (ultimo compartimento murato)
- **Mastio**: spostato in blocco di 6 m verso sinistra (−Z); a destra resta lo spazio libero.
- **Chiostro nuovo**: 15 × 15 m, a destra (X 61,5–76,5; Z 24–39). Il muro esterno è sottile (0,50 m) e contiene il portico, profondo 3 m. Il cortile centrale misura 8 × 8 m. L'arcata è ricavata dal chiostro vecchio (2180 facce). Il chiostro non copre più l'ingresso del compartimento. Fontana e albero del chiostro vecchio sono conservati. Le 4 aiuole del giardino sono nei quadranti del cortile.
- **Cappella con cimitero**: ruotata di −90° e spostata sopra il chiostro. Il recinto è nuovo, con il varco verso la strada, e 8 gruppi di elementi sono stati ricollocati all'interno.
- **Altri spostamenti**: casa grigia in basso a sinistra, pozzo nella piazzetta davanti al chiostro (ora appoggiato al suolo), pavimentazioni rifatte con 64 tratti di nastro e la piazzetta del pozzo.
- **Mastio sospeso**: le 16 mensole staccate sono state riagganciate sotto i torrioni.

## 2. Fortezza
- **Ingressi delle torri ai camminamenti**: corretti 53 passaggi su 28 torri. Il gradino all'ingresso era in media 0,51 m (massimo 2,23 m). Ora il massimo è 0,06 m.
- **Rampe dai fossati alle porte**: la porta bassa ha una rampa di 35 m e la porta destra una di 34 m. La pendenza massima era 142% e 158%, ora è 13,9% per entrambe. Ho spostato 136 alberi e rocce dalla carreggiata.

## 3. Promontori più rocciosi
Le zone trattate sono sei: promontorio sul mare a sinistra, sperone della rocca e fianchi della fortezza, montagna della miniera e vetta, collina del teatro con le scogliere, scogliere fra porto e teatro, montagne della cascata e del canyon.
- **Sfaccettature**: 1043 piani di roccia di circa 8 m su 59.119 vertici del terreno. Lo spostamento è in media 0,40 m, al massimo 2,38 m (sullo sperone della rocca, dove è più marcato).
- **Rugosità e cenge**: rugosità leggera e cenge poco marcate su 57.800 vertici ripidi.
- **Materiali per faccetta**, a macchie e non a puntini: 35.308 celle di parete (roccia, pietra scura, muschio), 19.443 di pendio (ghiaione, muschio, roccia), 319 cenge erbose.
- **Pareti a strati** (`Pareti_Rocciose`, nuovo): 739 fasce di roccia incassate nelle pareti più ripide, che seguono strati ondulati e inclinati di 6–12° (12.208 facce).
- **Rocce** (`Rocce_Promontori`, nuovo): 240 massi ai piedi delle pareti e 300 affioramenti di massi grandi semisepolti sui pendii medi (28.200 facce in tutto, copie dei massi esistenti).
- Strade, edifici, muri e acqua sono protetti da una fascia di rispetto di 2–3 celle.

## 4. Fiume, foce e linee delle vecchie espansioni
- **Fiume**: una striscia d'argilla di 1,1 m per lato, a pelo d'acqua e raccordata alle sponde, su 2387 celle. La larghezza bagnata media passa da 8,9 a 6,8 m.
- **Foce**:
  - tolta la lastra d'acqua dolce sovrapposta al mare (1712 celle);
  - aggiunti un imbuto sabbioso largo da 8 a 24 m, una barra sabbiosa trasversale e un fondale più basso davanti alla bocca;
  - nuovo oggetto `Canneto_Fiume`: 502 ciuffi di canne lungo l'argilla e alla foce.
- **Bordi dell'acqua**: i vertici di bordo più di 0,1 m sopra il terreno erano 707 e ora sono 490. Il massimo scende da 8,12 m a 0,76 m.
- **Linee dritte delle espansioni precedenti**: smussate le cinque giunture X = −225, Z = −130, −138, 169, 179. La curvatura lungo la linea mediana scende per esempio da 0,357 a 0,067. I confini fra materiali non sono più rettilinei (circa 6700 celle).

## 5. Sentieri, podere e campi
- **Sentiero ponte–altopiano**:
  - fondovalle ricucito sulla riva sinistra: 82 m, pendenza massima 10%;
  - salita a tornanti: 274 m, 4 rampe e 3 tornanti, 29 m di dislivello;
  - pendenza di progetto massima 14,6%; misurata sul terreno: 95° percentile 14,4%, massimo 15,4% in un solo punto;
  - il vecchio tracciato, con pendenze fino al 275%, è tornato prato (485 celle).
- **Podere inglobato dallo sperone**: spostato in blocco con le sue 1453 facce, da (116, −23) a una radura piana in (139, 8), ruotato di 180°.
  - recinto rifatto: 37 pali con doppia traversa al posto di 266 facce di recinto sul pendio;
  - sentiero d'accesso di 27 m;
  - 49 alberi e rocce spostati ai margini della radura.
- **Campi tagliati o sollevati**:
  - 3 carrarecce tra i filari al posto delle strade diagonali;
  - 157 segmenti di filare ricuciti;
  - 352 rocce e alberi e 87 pezzi di siepe spostati ai margini dei campi;
  - terreno dei campi spianato.

## 6. Animali, persone, texture e kit v4
- **Animali dell'OBJ**: i vecchi animali (oggetto `Animali` più quelli sparsi in poderi, stalle, pascolo, porto e villaggio: 101.354 facce) sono sostituiti da 145 animali low-poly più realistici (27.245 facce).
  - forme modellate a sezioni: zampe in due segmenti con zoccoli, testa con orecchie, corna o palchi, criniera, coda, mucche pezzate, pecore con vello irregolare, galline con cresta;
  - stesse specie, colori, posizioni e orientamenti di prima: 139 sui vecchi, 6 dalle coordinate del kit v3;
  - tutti gli animali sono ora nell'oggetto `Animali`.
- **Kit v4**:
  - **animali**: tutti e 145 si muovono, articolati con le stesse forme dell'OBJ. 128 alternano tratti di cammino e soste in cui le zampe si fermano e l'animale bruca o becca. Anatre e cigni nuotano, i gabbiani in volo battono le ali. Le zampe seguono un'andatura a quattro tempi, sincronizzata con la velocità.
  - **persone**: le 44 persone (con 2 guardie) sono più realistiche: busto, tunica o veste lunga, cappelli. Restano dritte in salita e in discesa.
  - **animali dell'OBJ nascosti**: con `ANIMALI = True` il kit nasconde quelli fermi, così non ci sono doppioni (nella v3 restavano visibili sotto quelli animati).
  - **percorsi e telecamera**: i percorsi delle persone che attraversavano il nuovo chiostro e il nuovo cimitero sono deviati; il percorso del porto e la telecamera `07_Sentieri` seguono i nuovi tornanti. La ripresa passa da 379 a 541 m e da 3026 a 4318 fotogrammi.
- **Prova in Blender 5.0.1**, con l'OBJ finale:
  - nessun errore;
  - 2136 oggetti contro i 4531 della v3;
  - tutti i 1916 driver sono "espressioni semplici", che Blender calcola senza Python;
  - valutazione della scena 16 ms per fotogramma contro i 35 ms della v3, misurata senza disegno a schermo. La fluidità reale dipende dalla scheda video e non l'ho potuta misurare.
- **Texture**: sono quelle procedurali leggere del kit, con `TEXTURE = True`: rumore di colore e rilievo delicato su pietra, intonaco, tetti, legno, terreno (anche l'argilla nuova) e fogliame. Si vedono in vista Rendered, Eevee o Cycles, non in vista Solida.
- **Luce del kit**:
  - nella prova Eevee l'immagine della v3 era chiara e slavata. Ora `LUCE_CIELO` è 0,6, il sole vale 4,0, l'esposizione −0,6 e il contrasto "AgX – Punchy": sono regolabili in testa al file.
  - la foschia volumetrica (`NEBBIA`) ora è spenta di default perché nella prova senza scheda video produceva un fotogramma nero. Si può riaccendere.

## 7. Controlli finali (modello `castello_mappa_estesa.obj`)

| Tipo | Controllo | Esito | Numeri |
|---|---|---|---|
| Realismo | Continuità del terreno | superato | 5 giunture smussate (curvatura mediana per es. 0,357 → 0,067); nessun gradino ai bordi |
| Realismo | Pendenze | **parziale** | percorsi corretti ≤ 15% (porte 13,9%; tornanti massimo 15,4% in 1 punto su 274 m). Sull'insieme delle celle di strada, misurando la pendenza nella direzione peggiore, il 20,6% supera il 15% (era 22,8%): sono soprattutto le vie originali del borgo sul colle e le pendenze trasversali, che non ho toccato |
| Realismo | Acqua | migliorato | vertici di bordo > 0,1 m sopra le sponde: 707 → 490 (massimo 8,12 → 0,76 m) |
| Realismo | Scala | superato | porte del chiostro 1,7 × 2,7 m, portico 3 m, persone 1,72 m, animali con misure reali |
| Realismo | Posizioni impossibili | quasi | nessun edificio in acqua, nei fossati o sulle mura; alberi su strada 157 → 160 (+3) |
| Realismo | Vegetazione | invariata | alberi tolti dai sentieri e dalle carreggiate e messi ai margini; densità da pareggiare in fase 2 |
| Design | Coerenza, palette | superato | solo materiali già esistenti; rocce nuove copiate da quelle esistenti |
| Design | Composizione, leggibilità | superato | vedi immagini 01–05 |
| Debug | Validità OBJ | superato | 0 indici non validi, 0 NaN, 71 materiali usati e tutti definiti nell'MTL |
| Debug | Elementi sospesi (> 0,15 m senza appoggio) | migliorato | **604 → 96**. Di questi, 94 c'erano già nell'originale e sono elementi di progetto (bandiere e lanterne sulle porte, pale del mulino, 3 gabbiani in volo, cristalli del cerchio megalitico, tetti dei torrioni, parti del pozzo, torre del mago). Gli altri 2 sono piccoli conci di 5 facce sopra due porte di torre, apparsi dopo l'allineamento dei passaggi: li ho lasciati e li segnalo |
| Debug | Conflitti | superato | nessuna sovrapposizione fra edifici nelle aree modificate (rocca, nuovo podere); solo chiome d'albero sovrapposte ai margini della radura |
| Debug | Integrità | superato | 80 oggetti originali tutti presenti e con lo stesso nome, più 3 nuovi (`Canneto_Fiume`, `Pareti_Rocciose`, `Rocce_Promontori`); variazioni di facce elencate sotto |
| Debug | Terreno | superato | nessun buco oltre le 134 celle delle grotte (come prima); 0 normali rivolte in basso |
| Debug | Peso | superato | **1.217.388 facce, 63,7 MB** (originale 1.248.114 facce, 64,2 MB); limite 1,5 M / 80 MB |

**Facce cambiate per oggetto** (prima → dopo):

| Oggetto | Prima | Dopo | Motivo |
|---|---|---|---|
| Animali | 43.040 | 27.245 | nuovi modelli |
| Pascolo_Pastore | 13.496 | 163 | animali spostati nell'oggetto `Animali` |
| Poderi_Nuovi | 49.540 | 27.101 | animali spostati nell'oggetto `Animali` |
| Stalle | 4.169 | 409 | animali spostati nell'oggetto `Animali` |
| Villaggio_Altopiano | 21.074 | 9.590 | animali spostati nell'oggetto `Animali` |
| Porto | 11.215 | 8.035 | animali spostati nell'oggetto `Animali` |
| Fabbro | 946 | 189 | animali spostati nell'oggetto `Animali` |
| Miniera_Ampliata | 2.159 | 335 | animali spostati nell'oggetto `Animali` |
| Taglialegna | 2.084 | 1.172 | animali spostati nell'oggetto `Animali` |
| Acqua | 7.989 | 6.277 | lastra sovrapposta al mare tolta, fiume più stretto |
| Chiostro | 1.340 | 2.335 | chiostro nuovo |
| Cimitero | 4.264 | 4.262 | nuovo recinto |
| Poderi | 16.161 | 16.440 | recinto nuovo |
| Strade_Borgo | 648 | 666 | pavimentazioni della rocca |
| Canneto_Fiume (nuovo) | 0 | 2.772 | |
| Pareti_Rocciose (nuovo) | 0 | 12.208 | |
| Rocce_Promontori (nuovo) | 0 | 28.200 | |

**Elementi spostati**:
- mastio (−6 m), 16 mensole, casa grigia, pozzo, cappella e cimitero, un albero e 4 aiuole della rocca;
- podere da (116, −23) a (139, 8);
- alberi, rocce e siepi tolti da sentieri, rampe e campi (49 + 136 + 166 + 352 + 87);
- 739 elementi riappoggiati al suolo (474 sospesi dell'originale e 265 dopo i cambi di terreno).

**Elementi rimossi** (tutti sostituiti):
- chiostro vecchio (tranne fontana e albero);
- recinto e pavimento vecchi del cimitero (67 facce);
- recinto del podere sul pendio (266 facce);
- lastra d'acqua dolce sul mare;
- vecchi animali;
- vecchi tratti di pavimentazione della rocca e strade diagonali nei campi.

## 8. Ipotesi e limiti dichiarati
- **Conteggio dell'originale**: il PDF indica 1.224.102 facce e 81 oggetti, il file ricevuto ne ha 1.248.114 e 80. Ho lavorato sul file ricevuto.
- **Velocità degli animali**: nel modello sono fermi, ma scelti in pose naturali (metà dei brucatori con la testa bassa). Il movimento è nel kit, perché un OBJ non contiene animazioni.
- **Persone**: esistono solo nel kit. L'OBJ originale non conteneva persone.
- **Pendenza delle vie del borgo**: non l'ho corretta, perché non era richiesta e cambierebbe l'aspetto della città alta.

## 9. Fase 2: proposta (pianta 07) e una domanda sul budget
**Cosa propongo:**
1. **Mare fino all'orizzonte**, con poche facce grandi e il fondale uguale.
2. **Lato altopiano** (−Z): +150 m di montagna con varietà rocciosa. Il paese dell'altopiano si allarga fra i monti e il mare.
3. **Lato corto della cascata** (−X): +150 m in cui proseguono la montagna, la valle e il canyon con il fiume.
4. **Porto**: diventa un paesino di case portuali.
5. **Torre del mago**: scala ripida scavata nella roccia fino alla strada sotto, con l'ingresso in una grotta sotto la torre, il calderone e altri dettagli fuori.
6. **Densità degli alberi**: pareggiata attorno ai 3 poderi laterali.

**Stima del peso**: dopo la fase 1 il modello ha 1,22 M facce. A dettaglio pieno si aggiungono:

| Voce | Facce in più |
|---|---|
| terreno nuovo, maglia 0,9 m | ~215 mila |
| alberi e rocce delle nuove aree | ~250–370 mila |
| paese, porto, scala | ~40 mila |

Il totale è **~1,72–1,84 M facce e ~90–96 MB**, quindi oltre il limite di 1,5 M facce / 80 MB.

**Domanda unica**: per la fase 2 preferisci
- **(A)** dettaglio pieno, superando il limite fino a ~1,85 M facce / ~96 MB, oppure
- **(B)** restare nei limiti: maglia di 1,8 m nelle parti lontane delle estensioni e alberi più radi in quota, per ~1,45–1,5 M facce / ~76–80 MB?
