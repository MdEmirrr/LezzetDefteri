import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- GOOGLE SHEETS BAĞLANTISI ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open("CereninDefteri").sheet1

# --- GRİ RESİM (varsayılan thumbnail) ---
DEFAULT_THUMBNAIL = "https://raw.githubusercontent.com/EmirOzfindik/cerenin-defteri/main/assets/default_thumbnail.png"

# --- TARİFLERİ GÖSTERME ---
def display_recipe_cards(recipes):
    st.subheader("📖 Tarifler")
    if not recipes:
        st.info("Henüz hiç tarif eklenmemiş.")
        return

    for recipe in recipes:
        with st.container():
            thumbnail = recipe.get("thumbnail_url", "") or DEFAULT_THUMBNAIL
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(thumbnail, width=120)

            with col2:
                st.markdown(f"### {recipe.get('id')}")
                st.markdown(f"**Kategori:** {recipe.get('kategori', '-')}")
                st.markdown(f"**Tarih:** {recipe.get('saved_date', '-')}")

                with st.expander("👩‍🍳 Yapılışı"):
                    st.write(recipe.get("yapilisi", ""))

                with st.expander("🥗 Malzemeler"):
                    st.write(recipe.get("malzemeler", ""))

            st.markdown("---")

# --- YENİ TARİF EKLEME ---
def add_new_recipe():
    st.subheader("➕ Yeni Tarif Ekle")

    url = st.text_input("Instagram URL")
    yapilisi = st.text_area("Yapılışı")
    malzemeler = st.text_area("Malzemeler")
    kategori = st.text_input("Kategori")

    if st.button("Kaydet"):
        # id olarak zaman damgası kullanalım
        recipe_id = str(int(datetime.now().timestamp()))
        saved_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # şimdilik thumbnail boş = default atanacak
        thumbnail_url = ""

        new_row = [recipe_id, url, "", yapilisi, malzemeler, kategori, saved_date, thumbnail_url]
        sheet.append_row(new_row)

        st.success("✅ Tarif eklendi!")

# --- UYGULAMA MENÜSÜ ---
menu = ["Tarifler", "Yeni Tarif Ekle"]
choice = st.sidebar.selectbox("Menü", menu)

data = sheet.get_all_records()
df = pd.DataFrame(data)

if choice == "Tarifler":
    display_recipe_cards(df.to_dict(orient="records"))
elif choice == "Yeni Tarif Ekle":
    add_new_recipe()
