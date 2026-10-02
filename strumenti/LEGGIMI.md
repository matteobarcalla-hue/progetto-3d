# Strumenti di lavorazione della mappa

Script Python usati per le fasi 1 e 2 (lettura/scrittura OBJ, griglia del terreno, moduli di modifica,
controlli di oggetti sospesi e conflitti, rendering di verifica, generazione del kit per Blender).
Copia di sicurezza: servono i file di stato (`*.state.pkl`, `orig.pkl`, `terrain_orig.npz`) che non sono nel repository.

## Fase 3 (dal .blend dell'utente)

Ordine di esecuzione (`fase3.py stato_in.pkl uscita.obj modulo...`, vedi `fase3/catena*.sh`):
1. `fase3/esporta.py`, `fase3/campiona.py`, `f3_base.py` – stato di partenza dal .blend (oggetti, terreno scolpito ricampionato).
2. `f3_borghi.py` (+ `borgo.py`, `case_modelli.py`) – borghi dell'altopiano e del porto con copie degli edifici esistenti;
   `f3_strade.py` – strada nel solco lungo il fiume e sentiero dei pascoli.
3. `f3_pale.py` – Pale dolomitiche a banchi sulla cima della montagna più alta; `f3_sentieri.py` – sentieri sottili;
   `f3_alberi.py` – alberi più grandi, chioma alzata, diradamento naturale, salici; `f3_biomi.py` – materiali nuovi
   dei biomi; `f3_pulizia.py` – vegetazione dentro le case.
4. `floating.py` + `f3_sospesi.py` – elementi sospesi nuovi; `conflitti4.py` – compenetrazioni esatte (BVH);
   `f3_ritocchi.py`, `f3_ritocchi2.py` – correzioni finali (case che toccano oggetti esistenti, sospesi, tronchi).
5. `kit_dati6.py` – kit di ripresa v6 con le impostazioni dell'utente (`fase3/header_utente.txt`);
   `aggiorna_blend.py` – aggiorna il .blend dell'utente (mesh nelle coordinate locali degli oggetti) ed esegue il kit.
6. Verifiche: `fase3/verifica_kit.py`, `fase3/verifica_camere.py`, `fase3/verifica_blend.py`, `fase3/an_spogli2.py`,
   `fase3/an_spunta.py`; immagini con `render_views.py` e le viste di `fase3/viste.txt`.
