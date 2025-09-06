import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import html
from streamlit_option_menu import option_menu
import json
import re
import time
from streamlit_lottie import st_lottie

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

# --- YENİ, MODERN VE TEMİZ STİL (CSS) ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

/* --- GENEL SAYFA AYARLARI --- */
.stApp {{
    background-color: #F8F7F4; /* Temiz ve yumuşak bir arka plan rengi */
    font-family: 'Quicksand', sans-serif;
}}

/* --- SOL FİLTRE PANELİ (SIDEBAR) STİLLERİ --- */
[data-testid="stSidebar"] {{
    background-color: #FFFFFF;
    border-right: 1px solid #EAEAEA;
}}
[data-testid="stSidebar"] h2 {{
    font-family: 'Quicksand', sans-serif;
    font-weight: 700;
    color: #333;
}}
[data-testid="stSidebar"] .stMultiSelect, [data-testid="stSidebar"] .stSlider {{
    border-radius: 8px;
    padding: 10px;
    background-color: #F8F7F4;
}}

/* --- ANA BAŞLIK --- */
h1 {{
    font-family: 'Dancing Script', cursive !important;
    color: #333 !important;
    text-align: center;
}}

/* --- TARİF KARTLARI (YENİ TASARIM) --- */
.recipe-card-link {{
    text-decoration: none;
}}
.recipe-card {{
    background-color: #FFFFFF !important;
    border-radius: 12px;
    border: 1px solid #EAEAEA;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
    overflow: hidden;
    transition: all 0.3s ease;
}}
.recipe-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}}
.card-image-container {{
    position: relative;
}}
.card-image {{
    width: 100%;
    height: 220px;
    object-fit: cover;
    display: block;
}}
.card-body {{
    padding: 1rem;
}}
.card-body h3 {{
    font-family: 'Quicksand', sans-serif !important;
    font-weight: 700;
    font-size: 1.1rem;
    color: #333 !important;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.card-metadata {{
    display: flex;
    gap: 15px;
    font-size: 0.8rem;
    color: #777;
    margin-top: 0.5rem;
    align-items: center;
}}
.card-metadata span {{
    display: flex;
    align-items: center;
    gap: 5px;
}}
.card-metadata svg {{
    width: 14px;
    height: 14px;
    fill: #777;
}}

/* --- DİĞER ELEMANLAR --- */
/* Butonlar, expander gibi elemanların stilleri buraya eklenebilir */
div[data-testid="stExpander"] summary {{
    font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)


# --- VERİTABANI BAĞLANTISI (Aynı kalıyor) ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}")
    st.stop()


# --- YARDIMCI FONKSİYONLAR (Aynı kalıyor)---
@st.cache_data(ttl=600)
def fetch_all_recipes():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df = df[df['id'] != ''].copy()
        # Yeni sütunlar için sayısal dönüşüm yapalım
        for col in ['malzeme_sayisi', 'hazirlanma_suresi']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    return df

# ... get_instagram_thumbnail, refresh_all_thumbnails, load_lottieurl fonksiyonları aynı kalacak ...
# ... (Bu fonksiyonları aşağıya ekledim) ...
def get_instagram_thumbnail(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1'}
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_text = response.text
        script_tag = re.search(r'<script type="application/ld\+json">(.+?)</script>', html_text)
        if script_tag:
            json_data = json.loads(script_tag.group(1))
            thumbnail_url = json_data.get('thumbnailUrl') or json_data.get('image')
            if thumbnail_url: return thumbnail_url
        soup = BeautifulSoup(html_text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        if meta_tag and meta_tag.get('content'): return meta_tag['content']
    except Exception: return None
    return None

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# --- YENİ FİLTRE PANELİ FONKSİYONU ---
def build_sidebar(df):
    with st.sidebar:
        st.markdown("<h2>Filtrele</h2>", unsafe_allow_html=True)
        
        # Kategori Filtresi
        all_categories = sorted(df['kategori'].unique())
        selected_categories = st.multiselect("Yemek Türü", options=all_categories)
        
        # Malzeme Filtresi
        st.markdown("---")
        st.markdown("<h5>İçindekiler</h5>", unsafe_allow_html=True)
        # Tüm malzemeleri alıp tekilleştirelim
        all_ingredients_list = []
        for ingredients in df['malzemeler'].dropna():
            all_ingredients_list.extend([i.strip().capitalize() for i in ingredients.split('\n') if i.strip()])
        unique_ingredients = sorted(list(set(all_ingredients_list)))
        selected_ingredients = st.multiselect("Malzemelere göre ara", options=unique_ingredients)

        # Hazırlanma Süresi Filtresi
        st.markdown("---")
        max_time = int(df['hazirlanma_suresi'].max()) if not df.empty else 60
        selected_max_time = st.slider("Maks. Hazırlanma Süresi (dakika)", 0, max_time, max_time)

    # Filtreleme Mantığı
    filtered_df = df.copy()
    if selected_categories:
        filtered_df = filtered_df[filtered_df['kategori'].isin(selected_categories)]
    if selected_ingredients:
        for ingredient in selected_ingredients:
            filtered_df = filtered_df[filtered_df['malzemeler'].str.contains(ingredient, case=False, na=False)]
    if selected_max_time < max_time:
        filtered_df = filtered_df[filtered_df['hazirlanma_suresi'] <= selected_max_time]
        
    return filtered_df

# --- YENİ TARİF KARTI GÖRÜNTÜLEME FONKSİYONU ---
def display_recipe_cards_new(df):
    if df.empty:
        st.warning("Bu kriterlere uygun tarif bulunamadı.")
        return
    
    st.markdown(f"**{len(df)}** adet tarif bulundu.")
    st.write("---")
    
    cols = st.columns(4)
    for i, recipe in df.iterrows():
        col = cols[i % 4]
        with col:
            st.markdown(f"""
            <a href="{recipe['url']}" target="_blank" class="recipe-card-link">
                <div class="recipe-card">
                    <div class="card-image-container">
                        <img src="{recipe['thumbnail_url']}" class="card-image">
                    </div>
                    <div class="card-body">
                        <h3>{html.escape(str(recipe.get('baslik','')))}</h3>
                        <div class="card-metadata">
                            <span>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M21.58,16.09,13.89,8.4a2,2,0,0,0-2.82,0L2.42,17.09A2,2,0,0,0,2,18.5a2,2,0,0,0,2,2H16v2a1,1,0,0,0,2,0V17.5a1.5,1.5,0,0,0-1.5-1.5H5.41l5.29-5.3,6.88,6.89Z"/></svg>
                                {recipe.get('malzeme_sayisi', 0)} malzeme
                            </span>
                            <span>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Zm4-9.5H12.5V7a1,1,0,0,0-2,0v5.5a1,1,0,0,0,1,1H16a1,1,0,0,0,0-2Z"/></svg>
                                {recipe.get('hazirlanma_suresi', 0)} dk
                            </span>
                        </div>
                    </div>
                </div>
            </a>
            """, unsafe_allow_html=True)

# --- ANA UYGULAMA AKIŞI ---
st.markdown("<h1 style='font-family: \"Dancing Script\", cursive;'>🌸 Ceren'in Defteri 🌸</h1>", unsafe_allow_html=True)

selected_page = option_menu(
    menu_title=None,
    options=["Tüm Tarifler", "Yeni Tarif Ekle"],
    icons=['card-list', 'plus-circle'],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

if selected_page == "Tüm Tarifler":
    all_recipes_df = fetch_all_recipes()
    filtered_recipes = build_sidebar(all_recipes_df)
    display_recipe_cards_new(filtered_recipes)

elif selected_page == "Yeni Tarif Ekle":
    st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
    with st.form("new_recipe_page_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            insta_url = st.text_input("Instagram Reel Linki")
            tarif_basligi = st.text_input("Tarif Başlığı")
            kategori = st.selectbox("Kategori", options=sorted(fetch_all_recipes()['kategori'].unique()))
            malzeme_sayisi = st.number_input("Malzeme Sayısı", min_value=1, step=1)
            hazirlanma_suresi = st.number_input("Hazırlanma Süresi (dakika)", min_value=1, step=5)
        with col2:
            malzemeler = st.text_area("Malzemeler (Her satıra bir tane)", height=280)
        
        yapilisi = st.text_area("Yapılışı (Açıklama)")
        submitted_add = st.form_submit_button("✨ Tarifi Kaydet", use_container_width=True)
        
        if submitted_add:
            if insta_url and tarif_basligi:
                with st.spinner("İşleniyor..."):
                    thumbnail_url = get_instagram_thumbnail(insta_url)
                    if thumbnail_url:
                        new_row = [
                            datetime.now().strftime("%Y%m%d%H%M%S"), 
                            insta_url, 
                            tarif_basligi, 
                            yapilisi, 
                            malzemeler, 
                            kategori, 
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                            thumbnail_url,
                            malzeme_sayisi,
                            hazirlanma_suresi
                        ]
                        worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                        st.cache_data.clear()
                        st.success("Tarif başarıyla kaydedildi!")
                    else:
                        st.error("Bu linkten kapak fotoğrafı alınamadı.")
            else:
                st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")