import streamlit as st
import pandas as pd
from PIL import Image
import io

# 1. CONFIGURAZIONE PAGINA PER SMARTPHONE
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")
st.title("🛒 La Nostra Spesa")

# 2. CONNESSIONE AL DATABASE CONDIVISO
conn = st.connection('tidy_spesa_db', type='sql')

# Creazione tabella se non esiste
with conn.session as session:
    session.execute('''
        CREATE TABLE IF NOT EXISTS lista_spesa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prodotto TEXT,
            categoria TEXT,
            foto BLOB,
            preso INTEGER DEFAULT 0
        )
    ''')
    session.commit()

# 3. INTERFACCIA: INSERIMENTO NUOVO PRODOTTO
with st.expander("➕ Aggiungi un prodotto alla lista", expanded=False):
    nuovo_prodotto = st.text_input("Nome Prodotto")
    categoria = st.selectbox("Categoria", ["Frigo", "Dispensa", "Ortofrutta", "Panetteria", "Igiene/Casa", "Altro"])
    
    # ACCESSO ALLA FOTOCAMERA: Su smartphone attiva la camera
    foto_file = st.file_uploader("Scatta una foto al prodotto", type=["png", "jpg", "jpeg"])
    
    if st.button("Inserisci nella lista"):
        if nuovo_prodotto:
            foto_bytes = None
            if foto_file is not None:
                image = Image.open(foto_file)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG', quality=60)
                foto_bytes = img_byte_arr.getvalue()
            
            with conn.session as session:
                session.execute(
                    "INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (:prodotto, :categoria, :foto)",
                    {"prodotto": nuovo_prodotto, "categoria": categoria, "foto": foto_bytes}
                )
                session.commit()
            st.success(f"'{nuovo_prodotto}' aggiunto!")
            st.rerun()

st.markdown("---")

# 4. INTERFACCIA: VISUALIZZAZIONE IN TEMPO REALE
prodotti_df = conn.query("SELECT * FROM lista_spesa WHERE preso = 0", ttl=1)

if prodotti_df.empty:
    st.info("La lista è vuota!")
else:
    col1, col2 = st.columns(2)
    
    for index, row in prodotti_df.iterrows():
        target_col = col1 if index % 2 == 0 else col2
        with target_col:
            with st.container(border=True):
                st.markdown(f"### **{row['prodotto']}**")
                st.caption(f"📁 {row['categoria']}")
                
                if row['foto']:
                    image = Image.open(io.BytesIO(row['foto']))
                    st.image(image, use_container_width=True)
                
                if st.button("✅ Preso", key=f"btn_{row['id']}"):
                    with conn.session as session:
                        session.execute("UPDATE lista_spesa SET preso = 1 WHERE id = :id", {"id": row['id']})
                        session.commit()
                    st.rerun()

# 5. PULIZIA
st.markdown("---")
if st.button("🗑️ Svuota prodotti presi"):
    with conn.session as session:
        session.execute("DELETE FROM lista_spesa WHERE preso = 1")
        session.commit()
    st.rerun()
