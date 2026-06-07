import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURAZIONE PAGINA PER SMARTPHONE
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")

# Trucco CSS per eliminare spazi, margini e nascondere il bordo del modulo
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        h1 { font-size: 24px !important; margin-bottom: 10px !important; }
        .stButton > button { padding: 2px 10px !important; font-size: 14px !important; height: auto !important; min-height: 0px !important; }
        hr { margin: 4px 0px !important; border-color: #dddddd !important; }
        p { margin: 0px !important; padding: 0px !important; }
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🛒 La Nostra Spesa")

# 2. CONNESSIONE AL DATABASE NATIVO
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

# 3. INTERFACCIA DI INSERIMENTO: MODULO NATIVO
# "clear_on_submit=True" svuota la casella di testo e la foto automaticamente senza errori
with st.form(key="inserimento_rapido", clear_on_submit=True):
    nuovo_prodotto = st.text_input("➕ Aggiungi un elemento e premi Invio")
    foto_file = st.file_uploader("📷 Scatta o allega una foto (opzionale)", type=["png", "jpg", "jpeg"])
    
    # Questo bottone fa funzionare nativamente il tasto "Invio" della tastiera
    inviato = st.form_submit_button("Inserisci in lista")

# Se premiamo il tasto o premiamo Invio dalla tastiera
if inviato:
    testo_pulito = nuovo_prodotto.strip()
    if testo_pulito:
        foto_bytes = None
        if foto_file is not None:
            image = Image.open(foto_file)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=60)
            foto_bytes = img_byte_arr.getvalue()
        
        # Ora salva contemporaneamente sia il testo che la foto nel database!
        c.execute("INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (?, ?, ?)", (testo_pulito, "", foto_bytes))
        conn.commit()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# 4. LISTA PRINCIPALE: DA COMPRARE (Stile ultra-compatto Alexa)
prodotti_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 0 ORDER BY id DESC", conn)

if prodotti_df.empty:
    st.info("La lista è vuota!")
else:
    st.caption(f"{len(prodotti_df)} elementi rimanenti")
    
    for index, row in prodotti_df.iterrows():
        col_spunta, col_testo, col_foto = st.columns([0.12, 0.73, 0.15])
        
        with col_spunta:
            if st.button("⬜", key=f"check_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo:
            st.markdown(f"<p style='font-size:16px; font-weight:500; padding-top:4px;'>{row['prodotto']}</p>", unsafe_allow_html=True)
            
        with col_foto:
            # L'icona compare SOLO se la foto è stata salvata correttamente
            if row['foto']:
                with st.popover("📷"):
                    image = Image.open(io.BytesIO(row['foto']))
                    st.image(image, use_container_width=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 5. STORICO: ELEMENTI GIÀ PRESI
st.markdown("### 📋 Elementi già presi")
storico_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 1 ORDER BY id DESC LIMIT 15", conn)

if storico_df.empty:
    st.caption("Nessun elemento nello storico.")
else:
    for index, row in storico_df.iterrows():
        col_ripristina, col_testo_spuntato = st.columns([0.12, 0.88])
        
        with col_ripristina:
            if st.button("🔄", key=f"uncheck_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 0 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo_spuntato:
            st.markdown(f"<p style='font-size:15px; text-decoration: line-through; color: #888888; padding-top:4px;'>{row['prodotto']}</p>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 6. PULIZIA TOTALE DELLO STORICO
if not storico_df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Cancella definitivamente lo storico"):
        c.execute("DELETE FROM lista_spesa WHERE preso = 1")
        conn.commit()
        st.rerun()
