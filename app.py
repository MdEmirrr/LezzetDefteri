import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import html
from streamlit_option_menu import option_menu

# --- STİL (CSS) ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")
st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Quicksand:wght@400;500;600&display=swap');body, .stApp { background-color: #FFFFFF !important; }.main .block-container { padding-top: 1rem !important; }h1 {font-family: 'Dancing Script', cursive !important;color: #2E8B57 !important;text-align: center;}h2, h3, h5 {font-family: 'Quicksand', sans-serif !important;color: #2F4F4F !important;}.recipe-card {background-color: #FFFFFF;border: 1px solid #e9e9e9;border-radius: 15px;box-shadow: 0 4px 12px rgba(0,0,0,0.05);margin-bottom: 2rem;overflow: hidden;}.card-image {width: 100%;height: 250px;object-fit: cover;}.card-body { padding: 1rem; }.card-body .category-badge {background-color: #D1E7DD;color: #0F5132;padding: 4px 10px;border-radius: 5px;font-size: 0.8rem;font-weight: 600;margin-top: 10px; display: inline-block;}div[data-testid="stExpander"] > summary p {color: #2F4F4F !important;font-weight: 600;}div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {color: #333 !important;}</style>""", unsafe_allow_html=True)

# --- SABİT DEĞİŞKENLER ---
# TUM_KATEGORILER artık veritabanından gelecek
CATEGORIZED_INGREDIENTS = { "Temel Gıdalar": ["Un", "Pirinç", "Bulgur", "Makarna", "Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke", "Maya"], "Süt & Süt Ürünleri": ["Süt", "Yoğurt", "Peynir", "Beyaz peynir", "Kaşar peyniri", "Lor peyniri", "Krema", "Tereyağı", "Yumurta"], "Et, Tavuk & Balık": ["Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Sosis", "Balık"], "Sebzeler": ["Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar"], "Bakliyat": ["Mercimek", "Nohut", "Fasulye", "Yeşil mercimek"], "Meyveler": ["Elma", "Muz", "Çilek", "Portakal"], "Kuruyemiş & Tatlı": ["Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal", "Pekmez", "Vanilya"], "Baharatlar": ["Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Tarçın"] }

# --- VERİTABANI BAĞLANTISI (GOOGLE SHEETS) ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    # İKİ AYRI SAYFA KULLANACAĞIZ
    recipes_worksheet = spreadsheet.worksheet("Tarifler")
    categories_worksheet = spreadsheet.worksheet("Kategoriler")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}")
    st.info("E-Tablonuzda 'Tarifler' ve 'Kategoriler' adında iki sayfa olduğundan ve paylaşım ayarlarınızın doğru olduğundan emin olun.")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=10)
def fetch_all_recipes():
    records = recipes_worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty: df = df[df['id'] != ''].copy()
    return df
@st.cache_data(ttl=10)
def fetch_all_categories():
    records = categories_worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty: df = df[df['name'] != ''].copy()
    return df
def get_instagram_thumbnail(url):
    try:
        response = requests.get(url, timeout=10); response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser'); meta_tag = soup.find('meta', property='og:image')
        return meta_tag['content'] if meta_tag else None
    except requests.exceptions.RequestException: return None

# ... (display_recipe_cards fonksiyonu aynı, değişiklik yok)
def display_recipe_cards(df):
    if df.empty: st.warning("Bu kriterlere uygun tarif bulunamadı."); return
    st.markdown(f"**{len(df)}** adet tarif bulundu."); st.write("")
    cols = st.columns(4)
    recipes_list = df.to_dict('records')
    for i, recipe in enumerate(reversed(recipes_list)):
        if pd.notna(recipe.get('thumbnail_url')) and recipe.get('thumbnail_url'):
            col = cols[i % 4]
            with col:
                # ... (Kart gösterme kodu aynı)

# --- ANA UYGULAMA AKIŞI ---
if 'recipe_to_edit_id' not in st.session_state: st.session_state.recipe_to_edit_id = None
st.markdown("<h1 style='font-family: \"Dancing Script\", cursive;'>Ceren'in Defteri</h1>", unsafe_allow_html=True)

selected_page = option_menu(
    menu_title=None, options=["Tüm Tarifler", "Ne Pişirsem?", "Yeni Tarif Ekle", "Kategorileri Yönet"],
    icons=['card-list', 'lightbulb', 'plus-circle', 'pencil-square'], menu_icon="cast", default_index=0, orientation="horizontal",
    styles={ "container": {"border-bottom": "2px solid #eee", "padding-bottom": "10px"}, "nav-link": {"font-family": "'Quicksand', sans-serif", "font-weight":"600"}, "nav-link-selected": {"background-color": "#D1E7DD", "color": "#2F4F4F"}, }
)

# KATEGORİ LİSTESİNİ VERİTABANINDAN (E-TABLO'DAN) ÇEK
categories_df = fetch_all_categories()
TUM_KATEGORILER = sorted(categories_df['name'].tolist()) if not categories_df.empty else []

if st.session_state.recipe_to_edit_id is not None:
    # ... (Düzenleme formu kodu, kategori listesini TUM_KATEGORILER'den alacak şekilde çalışır, değişiklik yok)
    pass
else:
    if selected_page == "Tüm Tarifler":
        st.markdown("<h2>Tüm Tarifler</h2>", unsafe_allow_html=True)
        all_recipes_df = fetch_all_recipes()
        selected_category = st.selectbox("Kategoriye göre filtrele:", ["Tümü"] + TUM_KATEGORILER)
        if selected_category != "Tümü": filtered_df = all_recipes_df[all_recipes_df['kategori'] == selected_category]
        else: filtered_df = all_recipes_df
        display_recipe_cards(filtered_df)
    
    elif selected_page == "Ne Pişirsem?":
        # ... (Ne Pişirsem? sayfası kodu aynı, değişiklik yok)
        pass

    elif selected_page == "Yeni Tarif Ekle":
        st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
        with st.form("new_recipe_page_form", clear_on_submit=True):
            insta_url = st.text_input("Instagram Reel Linki")
            tarif_basligi = st.text_input("Tarif Başlığı")
            kategori = st.selectbox("Kategori", TUM_KATEGORILER) # Artık dinamik listeyi kullanıyor
            malzemeler = st.text_area("Malzemeler (Her satıra bir tane)", height=200)
            yapilisi = st.text_area("Yapılışı (Açıklama)", height=200)
            submitted_add = st.form_submit_button("✨ Tarifi Kaydet", use_container_width=True)
            if submitted_add:
                if insta_url and tarif_basligi:
                    with st.spinner("İşleniyor..."):
                        thumbnail_url = get_instagram_thumbnail(insta_url)
                        if thumbnail_url:
                            new_row = [datetime.now().strftime("%Y%m%d%H%M%S"), insta_url, tarif_basligi, yapilisi, malzemeler, kategori, datetime.now().strftime("%Y-%m-%d %H%M%S"), thumbnail_url]
                            recipes_worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                            st.cache_data.clear(); st.success("Tarif başarıyla kaydedildi!")
                        else: st.error("Bu linkten kapak fotoğrafı alınamadı.")
                else: st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")

    elif selected_page == "Kategorileri Yönet":
        st.markdown("<h2>🏷️ Kategorileri Yönet</h2>", unsafe_allow_html=True)
        
        st.subheader("Yeni Kategori Ekle")
        with st.form("new_category_form", clear_on_submit=True):
            new_cat_name = st.text_input("Yeni kategori adı")
            if st.form_submit_button("Ekle"):
                if new_cat_name and new_cat_name not in TUM_KATEGORILER:
                    categories_worksheet.append_row([new_cat_name])
                    st.cache_data.clear(); st.rerun()

        st.markdown("---")
        st.subheader("Mevcut Kategoriler")
        if not TUM_KATEGORILER:
            st.info("Henüz hiç kategori eklenmemiş.")
        else:
            for cat_name in TUM_KATEGORILER:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(cat_name)
                with col2:
                    if st.button("Sil", key=f"delete_cat_{cat_name}", use_container_width=True):
                        try:
                            cell = categories_worksheet.find(cat_name)
                            categories_worksheet.delete_rows(cell.row)
                            st.cache_data.clear(); st.rerun()
                        except gspread.CellNotFound:
                            st.error("Kategori bulunamadı.")