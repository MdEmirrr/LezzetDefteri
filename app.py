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

# --- YENİ ARKA PLAN RESMİ İLE GÜNCELLENMİŞ STİL (CSS) ---

# Kullanmak istediğin yeni arka plan resminin linki
arka_plan_resmi_url = "https://plus.unsplash.com/premium_photo-1663099777846-62e0c092ce0b?q=80&w=1349&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

/* --- YENİ ARKA PLAN RESMİ AYARLARI --- */
.stApp {{
    background-image: url("{arka_plan_resmi_url}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* --- OKUNAKLILIK İÇİN "BUZLU CAM" EFEKTİ --- */
div[data-testid="stVerticalBlock"] > div[style*="border-radius"],
div[data-testid="stForm"],
[data-testid="stSidebar"] {{
    background-color: rgba(255, 255, 255, 0.65) !important; /* Şeffaflığı biraz artırdık */
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
}}

/* --- ANA BAŞLIK --- */
h1 {{
    font-family: 'Dancing Script', cursive !important;
    color: #FFFFFF !important; /* Arka plan koyu olabileceğinden beyaz daha iyi */
    text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.6); /* Gölgeyi belirginleştirdik */
    text-align: center;
}}

/* Diğer başlıklar ve metinler */
h2, h3, h5 {{
    font-family: 'Quicksand', sans-serif !important;
    color: #333 !important;
}}

/* --- TARİF KARTLARI --- */
.recipe-card-link {{ text-decoration: none; }}
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
.card-image {{
    width: 100%;
    height: 220px;
    object-fit: cover;
    display: block;
}}
.card-body {{ padding: 1rem; }}
.card-body h3 {{
    font-family: 'Quicksand', sans-serif !important;
    font-weight: 700;
    font-size: 1.1rem;
    color: #333 !important;
    margin: 0 0 0.5rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.card-metadata {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.8rem;
    color: #777;
    align-items: flex-start;
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
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=600)
def fetch_all_recipes():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df = df[df['id'] != ''].copy()
        if 'hazirlanma_suresi' in df.columns:
            df['hazirlanma_suresi'] = pd.to_numeric(df['hazirlanma_suresi'], errors='coerce').fillna(0).astype(int)
    return df

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

# --- GÜNCELLENMİŞ FİLTRE PANELİ FONKSİYONU ---
def build_sidebar(df):
    with st.sidebar:
        st.markdown("<h2>Filtrele</h2>", unsafe_allow_html=True)
        
        # Kategori Filtresi
        all_categories = sorted(df['kategori'].unique())
        selected_categories = st.multiselect("Yemek Türü", options=all_categories, placeholder="Kategori seçin...")
        st.write("---")
        
        # Hazırlanma Süresi Filtresi
        min_süre = int(df['hazirlanma_suresi'].min())
        max_süre = int(df['hazirlanma_suresi'].max())
        
        selected_süre_aralığı = st.slider(
            "Hazırlanma Süresi (dakika aralığı)",
            min_value=min_süre,
            max_value=max_süre,
            value=(min_süre, max_süre) # Başlangıçta tüm aralığı seçer
        )

    # Filtreleme Mantığı
    filtered_df = df.copy()
    if selected_categories:
        filtered_df = filtered_df[filtered_df['kategori'].isin(selected_categories)]
        
    # Süreye göre filtrele
    min_secilen, max_secilen = selected_süre_aralığı
    filtered_df = filtered_df[
        (filtered_df['hazirlanma_suresi'] >= min_secilen) & 
        (filtered_df['hazirlanma_suresi'] <= max_secilen)
    ]
        
    return filtered_df

# --- FİNAL TARİF KARTI GÖRÜNTÜLEME FONKSİYONU ---
def display_recipe_cards_final(df):
    if df.empty:
        st.warning("Bu kriterlere uygun tarif bulunamadı.")
        return
    
    st.markdown(f"**{len(df)}** adet tarif bulundu.")
    st.write("---")
    
    cols = st.columns(4)
    # i değişkeni yerine recipe'nin kendi index'ini kullanalım
    for i, recipe in enumerate(df.to_dict('records')):
        col = cols[i % 4]
        with col:
            st.markdown(f"""
            <a href="{recipe['url']}" target="_blank" class="recipe-card-link">
                <div class="recipe-card">
                    <img src="{recipe['thumbnail_url']}" class="card-image">
                    <div class="card-body">
                        <h3>{html.escape(str(recipe.get('baslik','')))}</h3>
                        <div class="card-metadata">
                            <span>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.2,10.2l-1-5A1,1,0,0,0,18.22,4H5.78a1,1,0,0,0-1,.81l-1,5a1,1,0,0,0,0,.38V18a2,2,0,0,0,2,2H18a2,2,0,0,0,2-2V10.58A1,1,0,0,0,20.2,10.2ZM5.2,6H18.8l.6,3H4.6ZM18,18H6V12H18Z"/></svg>
                                Zorluk: <b>{recipe.get('yemek_zorlugu', 'N/A')}</b>
                            </span>
                            <span>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Zm4-9.5H12.5V7a1,1,0,0,0-2,0v5.5a1,1,0,0,0,1,1H16a1,1,0,0,0,0-2Z"/></svg>
                                Süre: <b>{recipe.get('hazirlanma_suresi', 0)} dk</b>
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
    options=["Tüm Tarifler", "Ne Pişirsem?", "Yeni Tarif Ekle"],
    icons=['card-list', 'lightbulb', 'plus-circle'],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

if selected_page == "Tüm Tarifler":
    all_recipes_df = fetch_all_recipes()
    filtered_recipes = build_sidebar(all_recipes_df)
    
    # KRONOLOJİK SIRALAMA BURADA YAPILIYOR
    sorted_recipes = filtered_recipes.sort_values(by='id', ascending=False)
    
    display_recipe_cards_final(sorted_recipes)

elif selected_page == "Ne Pişirsem?":
    st.markdown("<h2>Ne Pişirsem?</h2>", unsafe_allow_html=True)
    st.markdown("Elinizdeki malzemeleri seçin, size uygun tarifleri bulalım!")
    
    all_recipes_df = fetch_all_recipes()
    
    all_ingredients_list = []
    for ingredients in all_recipes_df['malzemeler'].dropna():
        all_ingredients_list.extend([i.strip().capitalize() for i in ingredients.split('\n') if i.strip()])
    unique_ingredients = sorted(list(set(all_ingredients_list)))
    
    selected_ingredients = st.multiselect("Malzemeleri seçin:", options=unique_ingredients)
    st.write("---")

    if selected_ingredients:
        filtered_df = all_recipes_df.copy()
        for ingredient in selected_ingredients:
            filtered_df = filtered_df[filtered_df['malzemeler'].str.contains(ingredient, case=False, na=False)]
        
        # Malzemeye göre bulunan tarifleri de en yeniden eskiye sıralayalım
        sorted_recipes = filtered_df.sort_values(by='id', ascending=False)
        display_recipe_cards_final(sorted_recipes)
    else:
        st.info("Sonuçları görmek için yukarıdan malzeme seçin.")

elif selected_page == "Yeni Tarif Ekle":
    st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
    with st.form("new_recipe_page_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            insta_url = st.text_input("Instagram Reel Linki")
            tarif_basligi = st.text_input("Tarif Başlığı")
            kategori = st.selectbox("Kategori", options=sorted(fetch_all_recipes()['kategori'].unique()))
            yemek_zorlugu = st.selectbox("Yemek Zorluğu", options=["Basit", "Orta", "Zor"])
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
                        # GÜNCELLENMİŞ SÜTUN SIRASI
                        new_row = [
                            datetime.now().strftime("%Y%m%d%H%M%S"), 
                            insta_url, 
                            tarif_basligi, 
                            yapilisi, 
                            malzemeler, 
                            kategori, 
                            datetime.now().strftime("%Y-%m-%d %H%M:%S"), 
                            thumbnail_url,
                            yemek_zorlugu,
                            hazirlanma_suresi
                        ]
                        worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                        st.cache_data.clear()
                        st.success("Tarif başarıyla kaydedildi!")
                    else:
                        st.error("Bu linkten kapak fotoğrafı alınamadı.")
            else:
                st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")