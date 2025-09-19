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
# import google.generativeai as genai # Yapay zeka kütüphanesini şimdilik yorum satırı yapalım

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
:root {{
    --primary-green: #8BC34A;--secondary-green: #A5D6A7;--background-cream: #FFF8E1;
    --card-bg-color: #FFFFFF;--text-dark: #36454F;--text-light: #6A7B8E;
    --border-light: #E0E0E0;--button-hover: #7CB342;
}}
.stApp {{ background-color: var(--background-cream); font-family: 'Quicksand', sans-serif; }}
div[data-testid="stAppViewContainer"] > .main {{ padding-top: 0rem; }}
header {{
    background-image: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.1)),
                      url("https://plus.unsplash.com/premium_photo-1663099777846-62e0c092ce0b?q=80&w=1349&auto=format&fit=crop");
    background-size: cover; background-position: center 35%; padding: 3rem 1rem;
    border-bottom: 2px solid var(--primary-green); text-align: center; margin-bottom: 2rem;
}}
header h1 {{ font-family: 'Dancing Script', cursive !important; color: var(--card-bg-color) !important; font-size: 4.5rem; text-shadow: 2px 2px 5px rgba(0,0,0,0.6); margin: 0; }}
div[data-testid="stHeading"] {{ display: none; }}
div[data-testid="stSidebar"] {{ background-color: var(--secondary-green) !important; }}
div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p {{ color: var(--text-dark) !important; }}
div[data-testid="stSidebar"] .stMultiSelect>div>div, div[data-testid="stSidebar"] .stSlider>div, div[data-testid="stSidebar"] .stTextInput>div>div>input {{ background-color: rgba(255,255,255,0.7) !important; border: 1px solid var(--primary-green); }}
nav.st-emotion-cache-19rxjzo {{ background-color: var(--card-bg-color); border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin: 0 auto 2rem auto; padding: 0.5rem; width: fit-content; border: 1px solid var(--border-light); }}
.st-emotion-cache-1nm7f8b {{ background-color: var(--primary-green) !important; border-radius: 8px; }}
.st-emotion-cache-1nm7f8b p {{ color: white !important; font-weight: 600; }}
.recipe-card-link {{ text-decoration: none; }}
.recipe-card {{ background-color: var(--card-bg-color) !important; border-radius: 12px; border: 1px solid var(--border-light); box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 1.5rem; overflow: hidden; transition: all 0.3s ease; height: 420px; display: flex; flex-direction: column; }}
.recipe-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
.card-image {{ width: 100%; height: 300px; object-fit: cover; display: block; flex-shrink: 0; }}
.card-body {{ padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{ font-weight: 700; font-size: 1.1rem; color: var(--text-dark) !important; margin: 0 0 0.5rem 0; line-height: 1.3; height: 2.6em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
.card-metadata {{ display: flex; flex-direction: row; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #777; margin-top: auto; padding-top: 0.5rem; border-top: 1px solid var(--border-light); }}
.detail-page-title {{ font-family: 'Dancing Script', cursive !important; font-size: 3.5rem; text-align: center; margin-bottom: 1rem; color: var(--text-dark); }}
.detail-card {{ padding: 1.5rem; height: 100%; background-color: var(--card-bg-color); border-radius: 12px; border: 1px solid var(--border-light); }}
.detail-card img {{ width: 100%; border-radius: 8px; object-fit: cover; height: 450px; }}
.detail-card h5 {{ border-bottom: 2px solid var(--border-light); padding-bottom: 8px; margin-top: 0; }}
</style>
""", unsafe_allow_html=True)


# --- "NE PİŞİRSEM?" İÇİN KATEGORİLİ MALZEME LİSTESİ ---
CATEGORIZED_INGREDIENTS = {
    "Süt & Süt Ürünleri 🥛": ["Süt", "Yoğurt", "Peynir", "Kaşar peyniri", "Krema", "Tereyağı", "Yumurta"],"Et, Tavuk & Balık 🥩": ["Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Balık"],"Sebzeler 🥕": ["Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar"],"Bakliyat & Tahıl 🍚": ["Un", "Pirinç", "Bulgur", "Makarna", "Mercimek", "Nohut", "Fasulye", "Maya"],"Temel Gıdalar & Soslar 🧂": ["Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke"],"Kuruyemiş & Tatlı 🍫": ["Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal"],"Baharatlar 🌿": ["Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Toz biber"]
}

# --- VERİTABANI BAĞLANTISI ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}"); st.stop()


# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=600)
def fetch_all_recipes():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        df = df[df['id'] != ''].copy()
        if 'hazirlanma_suresi' in df.columns:
            df['hazirlanma_suresi'] = pd.to_numeric(df['hazirlanma_suresi'], errors='coerce').fillna(0).astype(int)
    return df

# YENİ VE GÜNCELLENMİŞ FOTOĞRAF ÇEKME FONKSİYONU
def get_instagram_thumbnail(url):
    clean_url = url.split("?")[0]
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        response = requests.get(clean_url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        if meta_tag and meta_tag.get('content'):
            return meta_tag.get('content')
        
        script_tag = soup.find('script', type='application/ld+json')
        if script_tag:
            json_data = json.loads(script_tag.string)
            if isinstance(json_data, list): json_data = json_data[0]
            if 'image' in json_data:
                return json_data['image'][0] if isinstance(json_data['image'], list) else json_data['image']
            if 'thumbnailUrl' in json_data:
                return json_data['thumbnailUrl']
        
        return None
    except Exception:
        return None

# YENİDEN EKLENEN FOTOĞRAFLARI YENİLEME FONKSİYONU
def refresh_all_thumbnails():
    st.info("Eski ve bozuk kapak fotoğrafları yenileniyor... Bu işlem biraz zaman alabilir.")
    all_recipes_df = fetch_all_recipes()
    header = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)]
    try:
        thumbnail_col_index = header.index('thumbnail_url') + 1
    except ValueError:
        st.error("'thumbnail_url' sütunu E-Tabloda bulunamadı!"); return

    updated_count = 0
    total_rows = len(all_recipes_df)
    progress_bar = st.progress(0, text="Yenileme işlemi başladı...")

    for index, row in all_recipes_df.iterrows():
        progress_text = f"Satır {index + 2}/{total_rows + 1} işleniyor..."
        progress_bar.progress((index + 1) / total_rows, text=progress_text)
        
        original_post_url = row.get('url')
        current_thumbnail_url = row.get('thumbnail_url')
        recipe_id = str(row.get('id'))

        if original_post_url and recipe_id:
            try:
                new_thumbnail_url = get_instagram_thumbnail(original_post_url)
                if new_thumbnail_url and new_thumbnail_url != current_thumbnail_url:
                    cell = worksheet.find(recipe_id)
                    if cell:
                        worksheet.update_cell(cell.row, thumbnail_col_index, new_thumbnail_url)
                        updated_count += 1
                        time.sleep(1.1)
            except Exception as e:
                st.warning(f"'{row.get('baslik')}' tarifi işlenirken bir hata oluştu: {e}")

    progress_bar.empty()
    st.success(f"Yenileme tamamlandı! Toplam {updated_count} adet tarifin kapak fotoğrafı güncellendi.")
    st.cache_data.clear(); st.rerun()

# GÜNCELLENMİŞ SIDEBAR
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
        selected_süre_aralığı = st.slider("Hazırlanma Süresi (dk)", min_süre, max_süre, (min_süre, max_süre))
        
        st.markdown("---")
        st.markdown("<h5>🛠️ Bakım Araçları</h5>", unsafe_allow_html=True)
        if st.button("🔄 Bozuk Fotoğrafları Düzelt"):
            refresh_all_thumbnails()

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
                        <h3>{html.escape(str(recipe.get('baslik','')).title())}</h3>
                        <div class="card-metadata">
                            <span title="Zorluk"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.2,10.2l-1-5A1,1,0,0,0,18.22,4H5.78a1,1,0,0,0-1,.81l-1,5a1,1,0,0,0,0,.38V18a2,2,0,0,0,2,2H18a2,2,0,0,0,2-2V10.58A1,1,0,0,0,20.2,10.2ZM5.2,6H18.8l.6,3H4.6ZM18,18H6V12H18Z"/></svg><b>{recipe.get('yemek_zorlugu', 'N/A')}</b></span>
                            <span title="Süre"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12,2A10,10,0,1,0,22,12,10,10,0,0,0,12,2Zm0,18a8,8,0,1,1,8-8A8,8,0,0,1,12,20Zm4-9.5H12.5V7a1,1,0,0,0-2,0v5.5a1,1,0,0,0,1,1H16a1,1,0,0,0,0-2Z"/></svg><b>{recipe.get('hazirlanma_suresi', 0)} dk</b></span>
                        </div>
                    </div>
                </div>
            </a>""", unsafe_allow_html=True)
            
def show_recipe_detail(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty: st.error("Aradığınız tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0]

    col_b1, col_b2, col_b3, col_b4 = st.columns([2, 2, 2, 6])
    with col_b1:
        if st.button("⬅️ Geri"):
            st.query_params.clear(); st.rerun()
    with col_b2:
        is_favorite = recipe.get('favori') == 'EVET'
        fav_text = "⭐ Favoriden Çıkar" if is_favorite else "⭐ Favorilere Ekle"
        if st.button(fav_text):
            cell = worksheet.find(str(recipe['id'])); favori_col_index = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)].index('favori') + 1
            new_status = "HAYIR" if is_favorite else "EVET"; worksheet.update_cell(cell.row, favori_col_index, new_status)
            st.cache_data.clear(); st.rerun()
    with col_b3:
        if st.button("✏️ Düzenle"):
            st.session_state.recipe_to_edit_id = recipe['id']
            st.query_params.clear(); st.rerun()

    st.markdown(f"<h1 class='detail-page-title'>{recipe['baslik'].title()}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 2, 2], gap="large")
    with col1:
        st.markdown(f"""<a href="{recipe['url']}" target="_blank" title="Instagram'da gör"><div class="detail-card"><img src="{recipe['thumbnail_url']}" alt="{recipe['baslik']}"></div></a>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="detail-card"><h5>Malzemeler</h5><div class="detail-card-text">{recipe.get('malzemeler', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="detail-card"><h5>Yapılışı</h5><div class="detail-card-text">{recipe.get('yapilisi', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander("🔴 Tarifi Kalıcı Olarak Sil"):
        st.warning("Bu işlem geri alınamaz. Tarifi silmek istediğinizden emin misiniz?")
        if st.button("Evet, Bu Tarifi Sil", type="primary"):
            cell = worksheet.find(str(recipe['id']))
            worksheet.delete_rows(cell.row)
            st.cache_data.clear()
            st.success(f"'{recipe['baslik']}' tarifi kalıcı olarak silindi.")
            time.sleep(2)
            st.query_params.clear()
            st.rerun()

def show_edit_form(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty: st.error("Düzenlenecek tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0].to_dict()

    st.markdown(f"<h2>✏️ Tarifi Düzenle: *{recipe['baslik'].title()}*</h2>", unsafe_allow_html=True)
    with st.form("edit_recipe_form"):
        edit_insta_url = st.text_input("Instagram Reel Linki", value=recipe['url'])
        edit_baslik = st.text_input("Tarif Başlığı", value=recipe['baslik'].title())
        kategori_options = sorted(df['kategori'].unique())
        kategori_index = kategori_options.index(recipe['kategori']) if recipe['kategori'] in kategori_options else 0
        edit_kategori = st.selectbox("Kategori", options=kategori_options, index=kategori_index)
        zorluk_options = ["Basit", "Orta", "Zor"]
        zorluk_index = zorluk_options.index(recipe.get('yemek_zorlugu')) if recipe.get('yemek_zorlugu') in zorluk_options else 0
        edit_yemek_zorlugu = st.selectbox("Yemek Zorluğu", options=zorluk_options, index=zorluk_index)
        süre_degeri = int(recipe.get('hazirlanma_suresi', 1))
        baslangic_suresi = max(1, süre_degeri)
        edit_hazirlanma_suresi = st.number_input("Hazırlanma Süresi (dakika)", min_value=1, step=5, value=baslangic_suresi)
        edit_malzemeler = st.text_area("Malzemeler", value=recipe.get('malzemeler', ''), height=200)
        edit_yapilisi = st.text_area("Yapılışı", value=recipe.get('yapilisi', ''), height=200)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            submitted_edit = st.form_submit_button("💾 Değişiklikleri Kaydet", use_container_width=True)
        with col_s2:
            if st.form_submit_button("❌ İptal", use_container_width=True):
                st.session_state.recipe_to_edit_id = None; st.rerun()
        if submitted_edit:
            try:
                cell = worksheet.find(str(recipe['id']))
                header = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)]
                worksheet.update_cell(cell.row, header.index('baslik') + 1, edit_baslik.title())
                worksheet.update_cell(cell.row, header.index('url') + 1, edit_insta_url)
                worksheet.update_cell(cell.row, header.index('kategori') + 1, edit_kategori)
                worksheet.update_cell(cell.row, header.index('yemek_zorlugu') + 1, edit_yemek_zorlugu)
                worksheet.update_cell(cell.row, header.index('hazirlanma_suresi') + 1, edit_hazirlanma_suresi)
                worksheet.update_cell(cell.row, header.index('malzemeler') + 1, edit_malzemeler)
                worksheet.update_cell(cell.row, header.index('yapilisi') + 1, edit_yapilisi)
                st.success("Tarif başarıyla güncellendi!")
                st.cache_data.clear(); st.session_state.recipe_to_edit_id = None; time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"Güncelleme sırasında bir hata oluştu: {e}")

def show_main_page():
    st.markdown("""<header><h1>🌸 Ceren'in Defteri 🌸</h1></header>""", unsafe_allow_html=True)
    all_recipes_df = fetch_all_recipes()
    selected_page = option_menu(
        menu_title=None, 
        options=["Tüm Tarifler", "⭐ Favorilerim", "Ne Pişirsem?", "Yeni Tarif Ekle"],
        icons=['card-list', 'star-fill', 'lightbulb', 'plus-circle'], 
        menu_icon="cast", default_index=0, orientation="horizontal"
    )
    if selected_page == "Tüm Tarifler":
        filtered_recipes = build_sidebar(all_recipes_df)
        display_recipe_cards_final(filtered_recipes.sort_values(by='id', ascending=False))
    elif selected_page == "⭐ Favorilerim":
        st.markdown("<h2>⭐ Favori Tariflerim</h2>", unsafe_allow_html=True)
        favorites_df = all_recipes_df[all_recipes_df['favori'] == 'EVET']
        display_recipe_cards_final(favorites_df.sort_values(by='id', ascending=False))
    elif selected_page == "Ne Pişirsem?":
        st.markdown("<h2>Ne Pişirsem?</h2>", unsafe_allow_html=True)
        # ... (Ne Pişirsem logic)
    elif selected_page == "Yeni Tarif Ekle":
        st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
        # ... (Yeni Tarif Ekle logic)

# ANA UYGULAMA YÖNLENDİRİCİSİ (ROUTER)
if 'recipe_to_edit_id' not in st.session_state:
    st.session_state.recipe_to_edit_id = None
all_recipes_df = fetch_all_recipes()
if st.session_state.recipe_to_edit_id is not None:
    show_edit_form(st.session_state.recipe_to_edit_id, all_recipes_df)
elif "id" in st.query_params:
    recipe_id = st.query_params.get("id")
    show_recipe_detail(recipe_id, all_recipes_df)
else:
    show_main_page()