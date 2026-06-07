import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURAZIONE PAGINA PER SMARTPHONE
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")

# CSS: PERCENTUALI ESATTE PER BLOCCARE GLI ELEMENTI SULLO SCHERMO
st.markdown("""
    <style>
        /* Ottimizzazione degli spazi generali */
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; overflow-x: hidden !important; }
        h1 { font-size: 24px !important; margin-bottom: 10px !important; }
        hr { margin: 4px 0px !important; border-color: rgba(128, 128, 128, 0.2) !important; }
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        
        /* Rimpicciolisce e uniforma tutti i bottoni (quadratino e fotocamera) */
        .stButton > button, [data-testid="stPopover"] > button { 
            padding: 0px !important; 
            font-size: 16px !important; 
            height: 35px !important; 
            width: 100% !important; 
        }
        
        /* =======================================================
           LA MAGIA PER LO SCHERMO DEL TELEFONO (Percentuali fisse)
           ======================================================= */
        /* Obbliga Streamlit a restare in riga e a non allargarsi oltre lo schermo */
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            width: 100% !important;
        }
        
        /* Riduce a zero i margini interni delle colonne */
        [data-testid="column"] {
            padding: 0px 4px !important;
        }

        /* COLONNA 1: Il quadratino di spunta (15% dello schermo) */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {
            width: 15% !important;
            min-width: 15% !important;
            flex: 0 0 15% !important;
        }
        
        /* COLONNA 2 (Lista Principale): Il testo del prodotto (70% dello schermo) */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2):not(:last-child) {
            width: 70% !important;
            min-width: 70% !important;
            flex: 0 0 70% !important;
        }
        
        /* COLONNA 3: L'icona della fotocamera (15% dello schermo) */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
            width: 15% !important;
            min-width: 15% !important;
            flex: 0 0 15% !important;
        }
        
        /* COLONNA 2 (Nello Storico): Il testo del prodotto (Prende l'85% perché manca la foto) */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2):last-child {
            width: 85% !important;
            min-width: 85% !important;
            flex: 0 0 85% !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛒 La Nostra Spesa")

# 2. CONNESSIONE AL DATABASE
conn = sqlite3.connect("spesa_condivisa.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS lista_spesa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prodotto TEXT,
        categoria TEXT,
        foto BLOB,
        preso INTEGER DEFAULT 0
    )
''')
conn.commit()

# 3. INTERFACCIA DI INSERIMENTO
with st.form(key="inserimento_rapido", clear_on_submit=True):
    nuovo_prodotto = st.text_input("➕ Aggiungi un elemento e premi Invio")
    foto_file = st.file_uploader("📷 Scatta o allega una foto (opzionale)", type=["png", "jpg", "jpeg"])
    inviato = st.form_submit_button("Inserisci in lista")

if inviato:
    testo_pulito = nuovo_prodotto.strip()
    if testo_pulito:
        foto_bytes = None
        if foto_file is not None:
            image = Image.open(foto_file)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=60)
            foto_bytes = img_byte_arr.getvalue()
        
        c.execute("INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (?, ?, ?)", (testo_pulito, "", foto_bytes))
        conn.commit()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# 4. LISTA PRINCIPALE (Bloccata su un'unica riga)
prodotti_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 0 ORDER BY id DESC", conn)

if prodotti_df.empty:
    st.info("La lista è vuota!")
else:
    st.caption(f"{len(prodotti_df)} elementi rimanenti")
    
    for index, row in prodotti_df.iterrows():
        # Creiamo le colonne: il CSS le forzerà alle percentuali 15% - 70% - 15%
        col_spunta, col_testo, col_foto = st.columns([0.15, 0.70, 0.15]) 
        
        with col_spunta:
            if st.button("⬜", key=f"check_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo:
            # Il padding-top aiuta ad allineare il testo perfettamente al centro del bottone
            st.markdown(f"<div style='padding-top: 6px; font-size: 16px; font-weight: 500;'>{row['prodotto']}</div>", unsafe_allow_html=True)
            
        with col_foto:
            if row['foto']:
                with st.popover("📷"):
                    image = Image.open(io.BytesIO(row['foto']))
                    st.image(image, use_container_width=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 5. STORICO PRODOTTI GIÀ PRESI
st.markdown("### 📋 Elementi già presi")
storico_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 1 ORDER BY id DESC LIMIT 15", conn)

if storico_df.empty:
    st.caption("Nessun elemento nello storico.")
else:
    for index, row in storico_df.iterrows():
        col_ripristina, col_testo_spuntato = st.columns([0.15, 0.85])
        
        with col_ripristina:
            if st.button("🔄", key=f"uncheck_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 0 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo_spuntato:
            st.markdown(f"<div style='padding-top: 6px; font-size: 15px; text-decoration: line-through; color: #888888;'>{row['prodotto']}</div>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 6. PULIZIA TOTALE
if not storico_df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Cancella definitivamente lo storico"):
        c.execute("DELETE FROM lista_spesa WHERE preso = 1")
        conn.commit()
        st.rerun()
