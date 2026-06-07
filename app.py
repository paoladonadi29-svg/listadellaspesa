import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURAZIONE PAGINA PER SMARTPHONE
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")

# CSS: Trucchi per compattare e bloccare gli "a capo" sui telefoni
st.markdown("""
    <style>
        /* Tolgo margini inutili in alto e in basso */
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        h1 { font-size: 24px !important; margin-bottom: 10px !important; }
        
        /* Rimpicciolisco i bottoni per farli stare comodamente in riga */
        .stButton > button { padding: 2px 8px !important; font-size: 16px !important; height: auto !important; min-height: 0px !important; }
        
        /* Riga sottile per separare i prodotti (colore che sta bene sia su sfondo bianco che nero) */
        hr { margin: 4px 0px !important; border-color: rgba(128, 128, 128, 0.3) !important; }
        
        /* Centratura verticale del testo del prodotto */
        p { margin: 0px !important; padding: 0px !important; line-height: 1.6 !important; }
        
        /* Nascondo il bordo del form di inserimento in alto */
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        
        /* ==========================================================
           MAGIA PER IMPEDIRE ASSOLUTAMENTE L'A CAPO SUGLI SMARTPHONE
           ========================================================== */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
        }
        
        div[data-testid="column"] {
            width: auto !important;
            padding: 0px !important;
        }
        
        /* Colonna 1: Il quadratino di spunta (stretta e fissa) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
            flex: 0 0 40px !important;
        }
        
        /* Colonna 2: Il nome del prodotto (prende tutto lo spazio centrale disponibile) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            flex: 1 1 auto !important;
            overflow: hidden !important;
        }
        
        /* Colonna 3: La fotocamera (stretta, fissa e incollata a destra) */
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) {
            flex: 0 0 45px !important;
            display: flex !important;
            justify-content: flex-end !important;
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

# 3. INTERFACCIA DI INSERIMENTO RAPIDO
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
            # Sistema le foto con sfondi trasparenti (spesso accade sugli iPhone)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=60)
            foto_bytes = img_byte_arr.getvalue()
        
        c.execute("INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (?, ?, ?)", (testo_pulito, "", foto_bytes))
        conn.commit()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# 4. LISTA PRINCIPALE
prodotti_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 0 ORDER BY id DESC", conn)

if prodotti_df.empty:
    st.info("La lista è vuota!")
else:
    st.caption(f"{len(prodotti_df)} elementi rimanenti")
    
    for index, row in prodotti_df.iterrows():
        # Usiamo 3 colonne: i CSS sopra si assicureranno che restino tutte e 3 sulla stessa riga!
        col_spunta, col_testo, col_foto = st.columns([1, 6, 1])
        
        with col_spunta:
            if st.button("⬜", key=f"check_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo:
            st.markdown(f"<p style='font-size:17px; font-weight:500;'>{row['prodotto']}</p>", unsafe_allow_html=True)
            
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
        col_ripristina, col_testo_spuntato = st.columns([1, 7])
        
        with col_ripristina:
            if st.button("🔄", key=f"uncheck_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 0 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo_spuntato:
            st.markdown(f"<p style='font-size:15px; text-decoration: line-through; color: #888888;'>{row['prodotto']}</p>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 6. PULIZIA
if not storico_df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Cancella definitivamente lo storico"):
        c.execute("DELETE FROM lista_spesa WHERE preso = 1")
        conn.commit()
        st.rerun()
