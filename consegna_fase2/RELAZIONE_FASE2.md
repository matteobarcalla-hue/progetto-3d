# Mappa del regno – Fase 2: terre nuove, mare all'orizzonte, paese, porto, torre del mago

## Contenuto della consegna

| File | Cosa contiene |
|---|---|
| `castello_mappa_estesa.obj` | modello aggiornato (OBJ per Blender 5.0.1, Y in alto), parte dallo stato finale della fase 1 |
| `castello_mappa_estesa.mtl` | materiali: gli stessi 71 dell'originale, nessuno nuovo |
| `kit_ripresa_mappa.py` | kit di ripresa **v5**: sostituisce la v4 ed è un file completo (2 camere nuove) |
| `immagini/01…07` | controlli visivi prima/dopo e fotogrammi del kit (anteprime, vedi nota) |
| `strumenti/` | script Python della fase 2, in ordine: `f2_estensione`, `f2_giunture`, `f2_rocce`, `f2_paesi`, `f2_mago`, `f2_alberi`, `f2_mare`, `f2_appoggio` (lanciati da `fase2.py`); poi `kit_dati.py` per il kit e i controlli. Documentano i passaggi; per rieseguirli servono anche i file di stato del lavoro (centinaia di MB), che non ho messo nello zip |

**Nota sulle anteprime.** Le immagini 01–06 sono render Workbench (anteprima semplificata: niente texture, niente cielo, luce da studio), fatti con Blender 5.0.1 senza scheda video. Il fotogramma Eevee del kit è in `07_kit_v5.png`.

**Peso (scelta A, superare il limite).** Il modello ha **1.700.768 facce e 92,3 MB**. Il limite del prompt era 1,5 M facce / 80 MB: lo supera del 13% (facce) e del 15% (MB), come avevi approvato. La stima della fase 1 era 1,72–1,84 M facce e 90–96 MB.

## Richieste e stato

| Richiesta | Stato | Sezione |
|---|---|---|
| Mare esteso fino all'orizzonte | fatto | 1 |
| Mappa estesa sul lato dell'altopiano (−Z): paese che si allarga un po', il resto montagna | fatto | 2, 4 |
| Mappa estesa sul lato corto della cascata (−X): montagna, valle, canyon con il fiume che prosegue | fatto | 2 |
| Variabilità morfologica e rocciosa | fatto | 2, 3 |
| Insediamento dell'altopiano ampliato nello spazio nuovo fra montagne e mare | fatto | 4 |
| Scala ripida scavata nella roccia dalla torre del mago alla strada, che arriva a una grotta sotto la torre (il suo ingresso); calderone e dettagli fuori dalla torre | fatto | 5 |
| Stessa densità di alberi nelle zone create dopo (es. 3 poderi laterali) | fatto | 6 |
| Porto che diventa un paesino di case portuali | fatto | 4 |
| Linee dritte di giunzione | fatto per la nuova giuntura | 2 |
| File che funzionano insieme | fatto: kit v5 provato con l'OBJ finale | 7 |

## 1. Mare fino all'orizzonte
- La superficie del mare prosegue per **2,6 km** oltre il lato mare (+X) e oltre i due lati corti verso il mare: 232 facce grandi aggiunte all'oggetto `Mare`, alla stessa quota (−0,88 m).
- Fondale piatto a −9 m con raccordi inclinati dai bordi del terreno: oggetto nuovo `Fondale_Esteso` (228 facce, materiale `sand`).
- Lungo la costa nuova (lato −Z) 954 bolle di schiuma, come quelle esistenti.
- Nel kit la distanza di visione del viewport passa da 1500 a 6000 m, così l'orizzonte si vede anche in modalità cammina; le camere arrivano a 5000 m.

## 2. Terre nuove (lati −Z e −X)
- **Griglia del terreno** da 642 × 481 a 809 × 648 vertici, stessa maglia di 0,9 m: +150 m sul lato dell'altopiano (−Z) e +150 m sul lato corto della cascata (−X). Estensione ora X −455…272, Z −343…239. **Celle nuove: 215.096 (174.228 m²)**, circa +70% di superficie.
- **Montagne**: massicci con creste a frattale "ridged", valli di drenaggio e una valle larga sul lato −X; quote fino a 154 m, contro i 129,5 m della vetta più alta della mappa vecchia: verso i bordi le montagne nuove fanno da quinta, più alte del centro.
- **Canyon**: il fiume prosegue per 150 m verso −X dentro un canyon a pareti ripide (letto da 61,8 a 77,1 m, pendenza media 10,5%), con strisce d'argilla sulle rive come nel tratto vecchio; 170 facce d'acqua nell'oggetto `Acqua`, larghezza 6,8 m come il fiume ristretto in fase 1.
- **Pianoro fra monti e mare** (lato −Z, x 98–200) a quota ~40 m, dove si allarga il paese (sezione 4); falesie e spiaggia verso il mare.
- **Raccordo con la mappa vecchia**: fascia di raccordo larga 35–60 m con bordo irregolare; le prime 4–7 file di celle nuove riprendono i materiali del bordo vecchio.
- **Giuntura senza riga dritta**: fra x 128 e 194 il terreno originale aveva una scarpata di 3–5 m parallela al vecchio bordo del plastico. Con la mappa estesa diventava una riga dritta di circa 60 m. L'ho addolcita su una fascia ondulata larga 4–11 m per lato, con variazioni da −2,6 a +2,9 m su 1153 vertici, e ho mescolato i materiali a chiazze ai due lati della giuntura (65 + 28 celle). Lungo il resto del bordo vecchio non c'era una scarpata sistematica: lì il raccordo è solo quello del punto precedente.
- **Materiali delle celle nuove**: bosco 67.580, roccia 46.778, prato 31.809, pietra scura 20.005, erba 19.611, muschio 17.776, sabbia 7.852, ghiaia 2.039, terra scura 1.220, argilla 426.
- **Bordi del plastico**: tolte 3823 facce delle fasce laterali che erano diventate interne (e quelle sul lato mare), aggiunte 3130 sui bordi nuovi.

## 3. Rocce delle montagne nuove
Ho usato gli stessi passaggi dei promontori della fase 1, applicati solo alle 2 zone nuove:
- **Sfaccettature**: 1579 piani di roccia di ~8 m su 107.514 vertici (spostamento medio 0,27 m, massimo 1,40 m); rugosità leggera e cenge su 111.650 vertici ripidi.
- **Materiali per faccetta**: 52.030 celle di parete, 42.370 di pendio, 128 cenge erbose.
- **Pareti a strati**: 233 fasce di roccia (3800 facce) nell'oggetto `Pareti_Rocciose`.
- **Massi**: 240 massi ai piedi delle pareti e 300 gruppi di affioramenti semisepolti (28.680 facce in più nell'oggetto `Rocce_Promontori`, copie dei massi esistenti).

## 4. Paese dell'altopiano e paesino del porto
- **Paese dell'altopiano** (oggetto nuovo `Villaggio_Altopiano_Nuovo`, 5509 facce):
  - 14 case nel pianoro nuovo, copie ruotate delle 14 case del villaggio esistente (stessi materiali), con la porta verso la strada;
  - strada principale di 43 m che prosegue quella del paese e una traversa di 87 m;
  - piazzetta 13 × 12 m lastricata con un pozzo al centro (copia del pozzo del chiostro, 69 facce).
- **Porto → paesino** (oggetto nuovo `Porto_Paese_Nuovo`, 1804 facce): 7 case portuali (copie delle case del porto e del borgo basso) sul fronte del molo e lungo la strada, 2 vicoli lastricati. Avevo previsto 12 lotti: 5 sono stati scartati dal controllo perché occupati o troppo in pendenza.
- Le case stanno su piazzole spianate; le parti staccate dal corpo della casa (gradini, panche, botti, carretti: 13) sono appoggiate al suolo.
- Tolti 18 alberi `Alberi`, 22 `Alberi_Nuovi` e 3 massi che sarebbero finiti dentro le case nuove o sulle strade nuove.

## 5. Torre del mago: scala, grotta, ponticello, calderone
**Come ho letto la richiesta** (ipotesi dichiarata): la grotta è l'ingresso della torre e sta nella rupe sotto la torre; la scala sale dalla strada di sotto fino alla grotta.
- **Strada sottostante**: l'unica strada sotto la torre arriva sulla riva opposta del fiume (lato +Z) e lì finisce. Le celle "strada" che si vedono lungo la riva della rupe sono sotto l'acqua del fiume già nel modello originale. Per collegare davvero la scala alla strada ho aggiunto un **ponticello di legno** (oggetto `Torre_Mago_Ponticello`, 469 facce): 8,8 m, impalcato a 0,70 m sopra l'acqua, pila centrale, parapetti, testate di pietra, una scaletta di 18 gradini fino alla strada, lanterna e cartello.
- **Scala** (oggetto `Torre_Mago_Scala`, 1181 facce): ripida, scavata nella roccia, dalla riva (quota 38,4) alla grotta (quota 72,2).
  - 4 rampe di 16,6 + 10,8 + 12,1 + 8,8 m e 3 pianerottoli di svolta;
  - 172 gradini con alzata 0,20 m e pedata 0,27–0,29 m; pendenza media 70% (35°);
  - il tracciato l'ho scelto con una ricerca sul terreno reale: pendenze delle rampe 0,68–0,73, scavo massimo 2,6 m;
  - il solco: parete tagliata a monte e parapetto di roccia a valle lungo tutte le rampe; 4 lanterne su palo.
- **Grotta d'ingresso** (oggetto `Torre_Mago_Grotta`, 275 facce): apertura 2,4 × 2,7 m nella rupe 7,4 m sotto la spianata della torre, pianerottolo di terra battuta davanti. Portale ad arco di 9 conci con chiave chiara e gemma viola, piedritti, porta ad arco con bande di ferro arretrata nel buio, rocce di raccordo, 2 lanterne a staffa, cristalli.
- **Fuori dalla torre** (oggetto `Torre_Mago_Dettagli`, 474 facce), sulla spianata a 4 m dalla porta: calderone su treppiede con pozione luminosa, fuoco e focolare di pietre; tavolo con 5 ampolle e un libro aperto; sgabello; catasta di legna con una scopa; 4 cristalli.
- Tolti dal corridoio della scala, dalla grotta e dal ponticello: 31 alberi e 6 massi o fasce di roccia; 2 piccole rocce della torre spostate fuori dal pianerottolo.

## 6. Alberi
- **Densità di riferimento**, misurata sul nucleo originale della mappa per tipo di suolo (alberi per m²): bosco 0,110, erba 0,035, prato 0,035, roccia 0,026, pietra scura 0,015, muschio 0,037, ghiaia 0,029.
- **Aree nuove**: 5367 alberi (oggetto nuovo `Alberi_Aree_Nuove`, 214.762 facce). Le specie dipendono dalla quota: conifere in alto, latifoglie in basso, ulivi vicino al mare, qualche albero autunnale e qualche siepe.
- **Zone delle espansioni precedenti** (i poderi laterali e la striscia bassa): mancava soprattutto il bosco (0,052 alberi/m² in meno). Aggiunti 262 alberi (oggetto nuovo `Alberi_Infittimento`, 13.016 facce).
- Gli alberi nuovi sono copie intere (tronco + chioma) di quelli esistenti, ruotate e scalate dell'85–120%. Nelle copie il tronco entra 30 cm nella chioma, perché in alcuni modelli originali la chioma lo sfiorava appena.
- Esclusi strade, piazze, campi, sabbia, argilla, pendenze oltre 1,15, edifici e la scala del mago; nel pianoro del paese e al porto la densità è ridotta al 12% e al 20%.

## 7. Kit di ripresa v5
- **Camere nuove**, dopo `07_Sentieri`:
  - `08_Scala_del_mago` (325 fotogrammi): sale dal ponticello lungo la scala e arriva davanti alla grotta;
  - `09_Terre_nuove` (500 fotogrammi): parte dal mare, passa sul paese nuovo e prosegue sulle montagne fino al canyon.
  In tutto 9 camere e 7013 fotogrammi (281 s a 25 fps).
- **Griglia estesa**: i percorsi delle persone e i giri degli animali sono ricontrollati sul terreno nuovo. I 4 percorsi deviati sono gli stessi della v4 (nessuna deviazione in più per le case nuove); 28 giri di animali rifatti perché finivano in ostacoli o fuori dall'acqua (erano 7 in v4).
- **Orizzonte**: viewport fino a 6000 m.
- **Riquadri**: anche gli alberi e le rocce nuovi si possono dividere in riquadri (`RIQUADRI = True`).
- **Prova in Blender 5.0.1** con l'OBJ finale: nessun errore. 44 persone e 145 animali in movimento, fotogrammi Workbench dalle due camere nuove e un fotogramma Eevee (immagine 07).

## 8. Controlli finali (modello `castello_mappa_estesa.obj`)

| Tipo | Controllo | Esito | Numeri |
|---|---|---|---|
| Realismo | Continuità del terreno | superato | raccordo irregolare 35–60 m; scarpata del vecchio bordo addolcita (sezione 2); nessun gradino nella maglia |
| Realismo | Pendenze | invariato dove non toccato | scala del mago 70% (è una scalinata ripida, richiesta); celle di strada oltre il 15%: 20,2% (fase 1 20,6%; originale 22,8%) |
| Realismo | Acqua | superato | bordi d'acqua come in fase 1 (490 vertici > 0,1 m, massimo 0,76 m); fiume del canyon nel suo letto; ponticello 0,70 m sopra l'acqua |
| Realismo | Scala | superato | gradini 0,20 × 0,28 m, porta della grotta 1,24 × 2,0 m, case copiate in scala 1:1 |
| Realismo | Posizioni impossibili | superato | case nuove: nessuna compenetrazione con altri oggetti; alberi su strada 160 (fase 1: 160; originale 157) |
| Realismo | Vegetazione | superato | densità del nucleo riportata nelle aree nuove e nelle zone delle espansioni |
| Design | Coerenza, palette | superato | solo i 71 materiali esistenti; case, alberi, massi e pozzo copiati da quelli del modello |
| Design | Composizione, leggibilità | superato | immagini 01–06 |
| Debug | Validità OBJ | superato | 0 indici non validi, 0 NaN, 71 materiali usati e tutti definiti |
| Debug | Elementi sospesi | superato | **95** (fase 1: 96). Sono tutti elementi che c'erano già prima della fase 2 (bandiere, pale del mulino, gabbiani in volo, tetti dei torrioni, parti della torre del mago…). Nessuno degli oggetti nuovi è sospeso |
| Debug | Conflitti | superato | 0 compenetrazioni fra le parti nuove (case, scala, grotta, ponticello, calderone) e gli altri oggetti |
| Debug | Integrità | superato | 83 oggetti della fase 1 tutti presenti con lo stesso nome, più 9 nuovi; variazioni di facce elencate sotto |
| Debug | Terreno | superato | 0 normali rivolte in basso; buchi solo nelle 134 celle delle grotte, come prima |
| Debug | Peso | **oltre il limite, approvato** | **1.700.768 facce, 92,3 MB** (fase 1: 1.217.388, 63,7 MB); limite 1,5 M / 80 MB |

**Facce cambiate per oggetto** (fase 1 → fase 2):

| Oggetto | Fase 1 | Fase 2 | Motivo |
|---|---|---|---|
| Terreno (celle) | 307.546 | 522.642 | terre nuove |
| Alberi_Aree_Nuove (nuovo) | 0 | 214.762 | 5367 alberi |
| Rocce_Promontori | 28.200 | 56.880 | massi delle montagne nuove |
| Alberi_Infittimento (nuovo) | 0 | 13.016 | 262 alberi |
| Villaggio_Altopiano_Nuovo (nuovo) | 0 | 5.509 | 14 case e pozzo |
| Pareti_Rocciose | 12.208 | 16.008 | pareti a strati nuove |
| Porto_Paese_Nuovo (nuovo) | 0 | 1.804 | 7 case |
| Mare | 47.623 | 48.809 | mare all'orizzonte e schiuma |
| Torre_Mago_Scala / _Grotta / _Ponticello / _Dettagli (nuovi) | 0 | 1.181 / 275 / 469 / 474 | sezione 5 |
| Fondale_Esteso (nuovo) | 0 | 228 | fondale |
| Acqua | 6.277 | 6.447 | fiume del canyon |
| Base_Sezione | 5.044 | 4.351 | fasce dei bordi rifatte |
| Alberi_Nuovi | 200.654 | 198.821 | alberi tolti da scala, case e strade nuove |
| Alberi | 365.688 | 365.044 | idem |
| Rocce | 46.020 | 45.920 | 2 massi sulla scala |

**Elementi spostati**:
- 66 elementi della mappa vecchia riallineati al terreno dove l'ho cambiato (49 alberi `Alberi_Nuovi`, 8 ciuffi di canne, 2 alberi, 2 elementi del porto, 2 rocce della torre, 2 case del villaggio vicino alla giuntura, 1 masso). Le 2 case sono salite o scese di −0,10…+0,40 m.
- 2 piccole rocce della torre del mago spostate di 1 e 4 m fuori dal pianerottolo della grotta.

## 9. Ipotesi e limiti dichiarati
- **Grotta**: il terreno è una superficie a quota unica per punto, quindi non può avere sottosquadri. La grotta è un portale con la bocca buia e la porta arretrata: dall'esterno si legge come un ingresso, ma non c'è un interno percorribile.
- **Lato destro (+Z, campagna)**: non era da estendere ed è rimasto il bordo del plastico. Con il mare che ora prosegue anche lì, dal mare si vede il fianco della montagna tagliato al bordo.
- **Montagne nuove**: sono procedurali, nello stesso stile a facce piatte. Alcuni versanti grandi restano lisci a distanza.
- **Linea chiara tratteggiata** sulla rupe sotto la torre del mago, nelle anteprime Workbench: c'è già nel modello originale. È una piega del terreno che l'effetto "cavity" di Workbench mette in risalto. Non l'ho toccata.
- **Porto**: 7 case invece delle 12 previste, per mancanza di spazio piano libero (vedi sezione 4).
- **Peso**: sopra il limite come da scelta A. Se servisse rientrare, la via più semplice è alleggerire `Alberi_Aree_Nuove` (215 mila facce): per esempio togliere il 30% degli alberi lontani dalle strade porterebbe a ~1,64 M facce.
