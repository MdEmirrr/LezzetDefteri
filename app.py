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
import random

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

.stApp {{ background-color: #F8F7F4; font-family: 'Quicksand', sans-serif; }}
[data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 1px solid #EAEAEA; }}
h1 {{ font-family: 'Dancing Script', cursive !important; color: #333 !important; text-align: center; }}
h2, h5 {{ font-family: 'Quicksand', sans-serif !important; color: #333333 !important; font-weight: 700; }}
.recipe-card-link {{ text-decoration: none; }}
.recipe-card {{
    background-color: #FFFFFF !important;
    border-radius: 12px; border: 1px solid #EAEAEA;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem; overflow: hidden;
    transition: all 0.3s ease; height: 350px;
    display: flex; flex-direction: column;
}}
.recipe-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.08); }}
.card-image {{ width: 100%; height: 220px; object-fit: cover; display: block; flex-shrink: 0; }}
.card-body {{ padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{
    font-weight: 700; font-size: 1.1rem; color: #333 !important; margin: 0 0 0.5rem 0;
    line-height: 1.3; height: 2.6em; /* 2 satır */
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}}
.card-metadata {{
    display: flex; flex-direction: row; justify-content: space-between;
    align-items: center; font-size: 0.8rem; color: #777;
    margin-top: auto; padding-top: 0.5rem; border-top: 1px solid #F0F0F0;
}}
.card-metadata span {{ display: flex; align-items: center; gap: 5px; }}
.card-metadata svg {{ width: 14px; height: 14px; fill: #777; }}
.detail-image {{
    width: 100%; height: 350px; object-fit: cover;
    border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}}
.detail-title {{ font-family: 'Dancing Script', cursive !important; font-size: 3rem; color: #333; margin-top: 0; }}
.detail-metadata {{ display: flex; gap: 20px; font-size: 0.9rem; color: #777; margin-bottom: 1rem; }}
.detail-metadata span {{ display: flex; align-items: center; gap: 8px; }}
.detail-metadata svg {{ width: 18px; height: 18px; fill: #777; }}
.detail-section h5 {{ border-bottom: 2px solid #F0F0F0; padding-bottom: 8px; margin-top: 1.5rem; }}
.detail-section-text {{
    white-space: pre-wrap; font-family: 'Quicksand', sans-serif; font-size: 1rem;
    background-color: #F8F7F4; padding: 1rem; border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

# --- "NE PİŞİRSEM?" İÇİN SABİT MALZEME LİSTESİ VE EMOJİLER ---
ANA_MALZEMELER = sorted([
    "Un", "Pirinç", "Bulgur", "Makarna", "Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke", "Maya",
    "Süt", "Yoğurt", "Peynir", "Kaşar peyniri", "Krema", "Tereyağı", "Yumurta",
    "Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Balık",
    "Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar",
    "Mercimek", "Nohut", "Fasulye", "Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal",
    "Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Toz biber"
])

INGREDIENT_EMOJIS = {
    "un": "🍚", "pirinç": "🍚", "bulgur": "🌾", "makarna": "🍝", "şeker": "🍬", "tuz": "🧂", "sıvı yağ": "🪔", "zeytinyağı": "🫒", "salça": "🍅", "sirke": "🍇", "maya": "🍞",
    "süt": "🥛", "yoğurt": "🥣", "peynir": "🧀", "kaşar": "🧀", "krema": "🍦", "tereyağı": "🧈", "yumurta": "🥚",
    "kıyma": "🥩", "et": "🥩", "tavuk": "🍗", "sucuk": "🌭", "balık": "🐟",
    "soğan": "🧅", "sarımsak": "🧄", "domates": "🍅", "biber": "🌶️", "patates": "🥔", "havuç": "🥕", "patlıcan": "🍆", "kabak": "🥒", "ıspanak": "🥬", "marul": "🥬", "salatalık": "🥒", "limon": "🍋", "mantar": "🍄",
    "mercimek": "🫘", "nohut": "🫘", "fasulye": "🫘", "ceviz": "🌰", "fındık": "🌰", "badem": "🌰", "çikolata": "🍫", "kakao": "🍫", "bal": "🍯",
    "karabiber": "🌶️", "nane": "🌿", "kekik": "🌿", "pul biber": "🌶️", "kimyon": "🌿", "toz biber": "🌶️"
}

def get_emoji_for_ingredient(ingredient):
    for key, emoji in INGREDIENT_EMOJIS.items():
        if key in ingredient.lower():
            return emoji
    return "🥣" # Varsayılan emoji

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
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_text = response.text
        script_tag = re.search(r'<script type="application/ld\+json">(.+?)</script>', html_text)
        if script_tag:
            json_data = json.loads(script_tag.group(1))
            thumbnail_url = json_data.get('thumbnailUrl') or json_data.get('image')
            if thumbnail_url: return thumbnail_url
        soup = BeautifulSoup(html_text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        if meta_tag and meta_tag.get('content'): return meta_tag.get('content')
    except Exception: return None
    return None

def build_sidebar(df):
    with st.sidebar:
        st.markdown("<h2>Filtrele</h2>", unsafe_allow_html=True)
        search_query = st.text_input("Tarif Adıyla Ara...", placeholder="Örn: Kek, Makarna...")
        st.write("---")
        all_categories = sorted(df['kategori'].unique())
        selected_categories = st.multiselect("Yemek Türü", options=all_categories, placeholder="Kategori seçin...")
        st.write("---")
        min_süre = int(df['hazirlanma_suresi'].min())
        max_süre = int(df['hazirlanma_suresi'].max()) if df['hazirlanma_suresi'].max() > 0 else 120
        selected_süre_aralığı = st.slider("Hazırlanma Süresi (dakika aralığı)", min_süre, max_süre, (min_süre, max_süre))
    
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df['baslik'].str.contains(search_query, case=False, na=False)]
    if selected_categories:
        filtered_df = filtered_df[filtered_df['kategori'].isin(selected_categories)]
    min_secilen, max_secilen = selected_süre_aralığı
    if min_secilen > min_süre or max_secilen < max_süre:
        filtered_df = filtered_df[filtered_df['hazirlanma_suresi'].between(min_secilen, max_secilen)]
    return filtered_df

def display_recipe_cards_final(df):
    if df.empty:
        st.warning("Bu kriterlere uygun tarif bulunamadı.")
        return
    st.markdown(f"**{len(df)}** adet tarif bulundu.")
    st.write("---")
    cols = st.columns(4)
    for i, recipe in enumerate(df.to_dict('records')):
        col = cols[i % 4]
        with col:
            st.markdown(f"""
            <a href="/?id={recipe['id']}" target="_self" class="recipe-card-link">
                <div class="recipe-card">
                    <img src="{recipe['thumbnail_url']}" class="card-image">
                    <div class="card-body">
                        <h3>{html.escape(str(recipe.get('baslik','')))}</h3>
                        <div class="card-metadata">
                            <span title="Zorluk"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.2,10.2l-1-5A1,1,0,0,0,18.22,4H5.78a1,1,0,0,0-1,.81l-1,5a1,1,0,0,0,0,.38V18a2,2,0,0,0,2,2H18a2,2,0,0,0,2-2V10.58A1,1,0,0,0,20.2,10.2ZM5.2,6H18.8l.6,3H4.6ZM18,18H6V12H18Z"/></svg><b>{recipe.get('yemek_zorlugu', 'N/A')}</b></span>
                            <span title="Süre"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Zm4-9.5H12.5V7a1,1,0,0,0-2,0v5.5a1,1,0,0,0,1,1H16a1,1,0,0,0,0-2Z"/></svg><b>{recipe.get('hazirlanma_suresi', 0)} dk</b></span>
                        </div>
                    </div>
                </div>
            </a>""", unsafe_allow_html=True)

def show_recipe_detail(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty:
        st.error("Aradığınız tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0]
    
    if st.button("⬅️ Tüm Tariflere Geri Dön", use_container_width=True):
        st.query_params.clear(); st.rerun()
    st.markdown("---")
    
    col1, col2 = st.columns([2, 3]) 
    with col1:
        st.markdown(f"""<img src="{recipe['thumbnail_url']}" class="detail-image" alt="{recipe['baslik']}">""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h1 class='detail-title'>{recipe['baslik']}</h1>", unsafe_allow_html=True)
        # YENİ: METADATA'YI BURADA DA GÖSTER
        st.markdown(f"""
        <div class="detail-metadata">
            <span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.2,10.2l-1-5A1,1,0,0,0,18.22,4H5.78a1,1,0,0,0-1,.81l-1,5a1,1,0,0,0,0,.38V18a2,2,0,0,0,2,2H18a2,2,0,0,0,2-2V10.58A1,1,0,0,0,20.2,10.2ZM5.2,6H18.8l.6,3H4.6ZM18,18H6V12H18Z"/></svg>Zorluk: <b>{recipe.get('yemek_zorlugu', 'N/A')}</b></span>
            <span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Zm4-9.5H12.5V7a1,1,0,0,0-2,0v5.5a1,1,0,0,0,1,1H16a1,1,0,0,0,0-2Z"/></svg>Süre: <b>{recipe.get('hazirlanma_suresi', 0)} dk</b></span>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<a href='{recipe['url']}' target='_blank'>Instagram'da Gör ↗️</a>", unsafe_allow_html=True)
        st.markdown("<div class='detail-section'><h5>Malzemeler</h5></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='detail-section-text'>{recipe.get('malzemeler', 'Eklenmemiş')}</div>", unsafe_allow_html=True)
        st.markdown("<div class='detail-section'><h5>Yapılışı</h5></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='detail-section-text'>{recipe.get('yapilisi', 'Eklenmemiş')}</div>", unsafe_allow_html=True)
    
    # YENİ: BENZER TARİF ÖNERİLERİ
    st.markdown("---")
    st.markdown("<h2>Bu Kategorideki Diğer Tarifler</h2>", unsafe_allow_html=True)
    similar_recipes = df[(df['kategori'] == recipe['kategori']) & (df['id'] != recipe['id'])]
    if not similar_recipes.empty:
        # Rastgele 4 tane seçelim
        sample_size = min(len(similar_recipes), 4)
        display_recipe_cards_final(similar_recipes.sample(n=sample_size))
    else:
        st.info("Bu kategoride başka tarif bulunmuyor.")

def show_main_page():
    all_recipes_df = fetch_all_recipes()
    st.markdown("<h1 style='font-family: \"Dancing Script\", cursive;'>🌸 Ceren'in Defteri 🌸</h1>", unsafe_allow_html=True)
    selected_page = option_menu(
        menu_title=None, options=["Tüm Tarifler", "Ne Pişirsem?", "Yeni Tarif Ekle"],
        icons=['card-list', 'lightbulb', 'plus-circle'], menu_icon="cast", default_index=0, orientation="horizontal"
    )

    if selected_page == "Tüm Tarifler":
        filtered_recipes = build_sidebar(all_recipes_df)
        sorted_recipes = filtered_recipes.sort_values(by='id', ascending=False)
        display_recipe_cards_final(sorted_recipes)

    elif selected_page == "Ne Pişirsem?":
        st.markdown("<h2>Ne Pişirsem?</h2>", unsafe_allow_html=True)
        st.markdown("Elinizdeki temel malzemeleri seçin, size uygun tarifleri bulalım!")
        
        selected_ingredients = []
        cols = st.columns(5) # Sayfayı 5 sütuna bölelim
        for i, ingredient in enumerate(ANA_MALZEMELER):
            with cols[i % 5]:
                emoji = get_emoji_for_ingredient(ingredient)
                if st.checkbox(f"{emoji} {ingredient}", key=f"ing_{ingredient}"):
                    selected_ingredients.append(ingredient)
        st.write("---")

        if selected_ingredients:
            filtered_df = all_recipes_df.copy()
            for ingredient in selected_ingredients:
                # Malzeme adının tek başına bir kelime olarak geçip geçmediğini kontrol edebiliriz
                # Bu, "biber" ararken "pul biber" çıkmasını sağlar ama daha spesifiktir.
                # Şimdilik basit `contains` ile devam edelim.
                filtered_df = filtered_df[filtered_df['malzemeler'].str.contains(ingredient.lower(), case=False, na=False)]
            
            sorted_recipes = filtered_df.sort_values(by='id', ascending=False)
            display_recipe_cards_final(sorted_recipes)
        else:
            st.info("Sonuçları görmek için yukarıdan temel malzemelerden seçin.")

    elif selected_page == "Yeni Tarif Ekle":
        st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
        with st.form("new_recipe_page_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                insta_url = st.text_input("Instagram Reel Linki")
                tarif_basligi = st.text_input("Tarif Başlığı")
                kategori_options = sorted(fetch_all_recipes()['kategori'].unique())
                kategori = st.selectbox("Kategori", options=kategori_options, placeholder="Bir kategori seçin...")
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
                            new_row = [datetime.now().strftime("%Y%m%d%H%M%S"), insta_url, tarif_basligi, yapilisi, malzemeler, kategori, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), thumbnail_url, yemek_zorlugu, hazirlanma_suresi]
                            worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                            st.cache_data.clear()
                            st.success("Tarif başarıyla kaydedildi!")
                        else: st.error("Bu linkten kapak fotoğrafı alınamadı.")
                else: st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")

# --- ANA UYGULAMA YÖNLENDİRİCİSİ (ROUTER) ---
params = st.query_params
if "id" in params:
    recipe_id = params.get("id")
    all_recipes_df = fetch_all_recipes()
    show_recipe_detail(recipe_id, all_recipes_df)
else:
    show_main_page()