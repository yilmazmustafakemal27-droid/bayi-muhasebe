import streamlit as st
import pandas as pd
from datetime import date
import sqlite3
import hashlib

PASSWORD_HASH = hashlib.sha256("3SBayi@2026".encode()).hexdigest()

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("3S Bayi Muhasebe Sistemi")
        pwd = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Şifre yanlış")
        st.stop()

check_password()

conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS cari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT,
    telefon TEXT,
    adres TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS hareket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cari_id INTEGER,
    tarih TEXT,
    tip TEXT,
    tutar REAL,
    aciklama TEXT
)
""")
conn.commit()

st.title("📊 3S Bayi Muhasebe")

menu = st.sidebar.radio("Menü", ["Cari Kart", "Hareket Girişi", "Cari Durum"])

if menu == "Cari Kart":
    st.subheader("Cari Kart Ekle")

    ad = st.text_input("Ad Soyad / Ünvan")
    tel = st.text_input("Telefon")
    adr = st.text_area("Adres")

    if st.button("Cari Kaydet"):
        c.execute("INSERT INTO cari (ad, telefon, adres) VALUES (?, ?, ?)", (ad, tel, adr))
        conn.commit()
        st.success("Cari kaydedildi")

    st.subheader("Cari Listesi")
    df = pd.read_sql("SELECT * FROM cari", conn)
    st.dataframe(df)

elif menu == "Hareket Girişi":
    st.subheader("Satış / Alış Girişi")

    cariler = pd.read_sql("SELECT * FROM cari", conn)
    if cariler.empty:
        st.warning("Önce cari ekleyin")
    else:
        cari_map = dict(zip(cariler["ad"], cariler["id"]))
        secilen = st.selectbox("Cari", cari_map.keys())
        tip = st.selectbox("Hareket Tipi", ["Satış", "Alış"])
        tutar = st.number_input("Tutar", min_value=0.0, step=100.0)
        aciklama = st.text_input("Açıklama")

        if st.button("Kaydet"):
            c.execute(
                "INSERT INTO hareket (cari_id, tarih, tip, tutar, aciklama) VALUES (?, ?, ?, ?, ?)",
                (cari_map[secilen], str(date.today()), tip, tutar, aciklama)
            )
            conn.commit()
            st.success("Hareket kaydedildi")

elif menu == "Cari Durum":
    st.subheader("Cari Borç / Alacak")

    query = """
    SELECT c.ad,
    SUM(CASE WHEN h.tip='Satış' THEN h.tutar ELSE 0 END) -
    SUM(CASE WHEN h.tip='Alış' THEN h.tutar ELSE 0 END) AS bakiye
    FROM cari c
    LEFT JOIN hareket h ON c.id = h.cari_id
    GROUP BY c.ad
    """
    df = pd.read_sql(query, conn)
    st.dataframe(df)
