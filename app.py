import streamlit as st
import pandas as pd
from PIL import Image, ImageOps
import io
from sqlalchemy import text

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="La Nostra Spesa", page_icon="🛒", layout="centered")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 100% !important; overflow-x: hidden !important; }
        h1 { font-size: 24px !important; margin-bottom: 10px !important; }
        hr { margin: 4px 0px !important; border-color: rgba(128, 128, 128, 0.2) !important; }
        [data-testid="stForm"] { border: none !important; padding: 0 !important; }
        
        [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 40px 1fr 50px !important;
            gap: 0px !important;
            width: 100% !important;
            align-items: center !important;
        }
        
        [data-testid="column"] { width: 100% !important; min-width: 0 !important; padding: 0 !important; }

        [data-testid="stHorizontalBlock"] .stButton > button, 
        [data-testid="stHorizontalBlock"] [data-testid="stPopover"] > button {
            width: 35px !important; height: 35px !important; padding: 0 !important; margin: 0 auto !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
        }
        
        [data-testid="stFormSubmitButton"] > button { width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🛒 La Nostra Spesa")

# 2. CONNESSIONE AL DATABASE CLOUD SUPABASE (Sicuro e permanente)
conn = st.connection("supabase", type="sql", url=st.secrets["DB_URL"])

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
            image = ImageOps.exif_transpose(image)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=60)
            foto_bytes = img_byte_arr.getvalue()
        
        with conn.session as s:
            s.execute(
                text("INSERT INTO lista_spesa (prodotto, categoria, foto) VALUES (:prodotto, :categoria, :foto)"),
                {"prodotto": testo_pulito, "categoria": "", "foto": foto_bytes}
            )
            s.commit()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# 4. LISTA PRINCIPALE (Aggiornamento in tempo reale)
prodotti_df = conn.query("SELECT * FROM lista_spesa WHERE preso = 0 ORDER BY id DESC", ttl=0)

if prodotti_df.empty:
    st.info("La lista è vuota!")
else:
    st.caption(f"{len(prodotti_df)} elementi rimanenti")
    
    for index, row in prodotti_df.iterrows():
        col_spunta, col_testo, col_foto = st.columns(3) 
        
        with col_spunta:
            if st.button("⬜", key=f"check_{row['id']}"):
                with conn.session as s:
                    s.execute(text("UPDATE lista_spesa SET preso = 1 WHERE id = :id"), {"id": row['id']})
                    s.commit()
                st.rerun()
                
        with col_testo:
            st.markdown(f"<div style='font-size: 16px; font-weight: 500; line-height: 1.2; word-wrap: break-word; padding-top: 2px;'>{row['prodotto']}</div>", unsafe_allow_html=True)
            
        with col_foto:
            if row['foto']:
                with st.popover("📷"):
                    image = Image.open(io.BytesIO(row['foto']))
                    st.image(image, use_container_width=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 5. STORICO
st.markdown("### 📋 Elementi già presi")
storico_df = conn.query("SELECT * FROM lista_spesa WHERE preso = 1 ORDER BY id DESC LIMIT 15", ttl=0)

if storico_df.empty:
    st.caption("Nessun elemento nello storico.")
else:
    for index, row in storico_df.iterrows():
        col_ripristina, col_testo_spuntato = st.columns(2)
        
        with col_ripristina:
            if st.button("🔄", key=f"uncheck_{row['id']}"):
                with conn.session as s:
                    s.execute(text("UPDATE lista_spesa SET preso = 0 WHERE id = :id"), {"id": row['id']})
                    s.commit()
                st.rerun()
                
        with col_testo_spuntato:
            st.markdown(f"<div style='font-size: 15px; text-decoration: line-through; color: #888888; line-height: 1.2; word-wrap: break-word; padding-top: 2px;'>{row['prodotto']}</div>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 6. PULIZIA
if not storico_df.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Cancella definitivamente lo storico"):
        with conn.session as s:
            s.execute(text("DELETE FROM lista_spesa WHERE preso = 1"))
            s.commit()
        st.rerun()
