import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURAZIONE PAGINA (Stile compatto per Smartphone)
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")
st.title("🛒 La Nostra Spesa")

# 2. CONNESSIONE AL DATABASE NATIVO
conn = sqlite3.connect("spesa_condivisa.db", check_same_thread=False)
c = conn.cursor()

# Creazione tabella
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

# 3. INTERFACCIA DI INSERIMENTO ULTRA-RAPIDA (Sempre aperta)
# Usiamo un piccolo trucco per pulire il campo di testo dopo l'invio automatizzato
if "temp_prodotto" not in st.session_state:
    st.session_state["temp_prodotto"] = ""

# Casella di inserimento sempre visibile in alto
nuovo_prodotto = st.text_input("➕ Aggiungi un elemento e premi Invio", key="input_prodotto")

# Campo fotocamera compatto e opzionale sotto il testo
foto_file = st.file_uploader("📷 Scatta o allega una foto (opzionale)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

# Funzione che scatta da sola quando premi Invio sulla tastiera del telefono
if nuovo_prodotto and nuovo_prodotto != st.session_state["temp_prodotto"]:
    foto_bytes = None
    if foto_file is not None:
        image = Image.open(foto_file)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=60)
        foto_bytes = img_byte_arr.getvalue()
    
    c.execute(
        "INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (?, ?, ?)",
        (nuovo_prodotto, "", foto_bytes)
    )
    conn.commit()
    st.rerun()

st.markdown("---")

# 4. LISTA PRINCIPALE: DA COMPRARE (Stile compatto Alexa)
prodotti_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 0 ORDER BY id DESC", conn)

if prodotti_df.empty:
    st.info("Nessun elemento rimanente. La lista è vuota!")
else:
    st.caption(f"{len(prodotti_df)} elementi rimanenti")
    
    for index, row in prodotti_df.iterrows():
        # Riga compatta
        col_spunta, col_testo, col_foto = st.columns([0.15, 0.65, 0.20])
        
        with col_spunta:
            if st.button("⬜", key=f"check_{row['id']}"):
                c.execute("UPDATE lista_spesa SET preso = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
                
        with col_testo:
            st.markdown(f"<p style='font-size:18px; margin:0; padding-top:5px;'>{row['prodotto']}</p>", unsafe_allow_html=True)
            
        with col_foto:
            if row['foto']:
                with st.popover("📷"):
                    image = Image.open(io.BytesIO(row['foto']))
                    st.image(image, use_container_width=True)
        
        st.markdown("<hr style='margin:2px 0px; border-color:#eeeeee;'>", unsafe_allow_html=True)

# 5. STORICO: ELEMENTI GIÀ PRESI
st.markdown("### 📋 Elementi già presi")
storico_df = pd.read_sql_query("SELECT * FROM lista_spesa WHERE preso = 1 ORDER BY id DESC LIMIT 20", conn)

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
            st.markdown(f"<p style='font-size:16px; text-decoration: line-through; color: gray; margin:0; padding-top:5px;'>{row['prodotto']}</p>", unsafe_allow_html=True)

# 6. PULIZIA TOTALE DELLO STORICO
st.markdown("---")
if st.button("🗑️ Cancella definitivamente lo storico"):
    c.execute("DELETE FROM lista_spesa WHERE preso = 1")
    conn.commit()
    st.success("Storico svuotato!")
    st.rerun()
