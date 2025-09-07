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
# import google.generativeai as genai # Yapay zeka kütüphanesini şimdilik yorum satırı yapalım

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

/* --- YENİ PASTA YEŞİL & KREM PALETİ --- */
:root {{
    --primary-green: #8BC34A;     /* Canlı Pastel Yeşil - Butonlar, Vurgu */
    --secondary-green: #A5D6A7;   /* Açık Pastel Yeşil - Sidebar, Hover */
    --background-cream: #FFF8E1;  /* Krem Arka Plan */
    --card-bg-color: #FFFFFF;     /* Kartlar ve Ana İçerik Alanı - Beyaz */
    --text-dark: #36454F;         /* Koyu Antrasit - Ana Metin */
    --text-light: #6A7B8E;        /* Gri Mavi - Alt Metinler */
    --border-light: #E0E0E0;      /* İnce Sınırlar */
    --button-hover: #7CB342;      /* Buton Hover - Daha Koyu Yeşil */
}}

/* --- GENEL SAYFA AYARLARI --- */
.stApp {{
    background-color: var(--background-cream); /* Tüm sayfa arka planı */
    font-family: 'Quicksand', sans-serif;
}}

/* Streamlit'in varsayılan üst boşluğunu kaldırıyoruz */
div[data-testid="stAppViewContainer"] > .main {{
    padding-top: 0rem;
}}

/* --- HEADER (RESİMLİ HEADER GERİ GELDİ) --- */
header {{
    background-image: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.1)),
                      url("https://plus.unsplash.com/premium_photo-1663099777846-62e0c092ce0b?q=80&w=1349&auto=format&fit=crop");
    background-size: cover;
    background-position: center 35%; /* Resmin dikey konumunu ayarla */
    padding: 3rem 1rem; /* İç boşluğu artırarak daha ferah bir görünüm */
    border-bottom: 2px solid var(--primary-green);
    text-align: center;
    margin-bottom: 2rem;
}}

header h1 {{
    font-family: 'Dancing Script', cursive !important;
    color: var(--card-bg-color) !important; /* Başlık beyaz, resim üzerinde daha iyi durur */
    font-size: 4.5rem; /* Başlığı daha da büyüttük */
    text-shadow: 2px 2px 5px rgba(0,0,0,0.6);
    margin: 0;
}}

/* Streamlit'in ana başlığını gizle, bizim header'ımız görünsün */
div[data-testid="stHeading"] {{
    display: none;
}}

/* --- SİDEBAR (SOL FİLTRE MENÜSÜ) --- */
div[data-testid="stSidebar"] {{
    background-color: var(--secondary-green) !important; /* Pastel yeşil sidebar */
    border-right: 1px solid var(--primary-green);
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}}
div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p {{
    color: var(--text-dark) !important; /* Sidebar içindeki yazılar koyu metin rengi */
    text-shadow: none; /* Gölgeyi kaldırdık */
}}
div[data-testid="stSidebar"] .stMultiSelect>div>div, div[data-testid="stSidebar"] .stSlider>div, div[data-testid="stSidebar"] .stTextInput>div>div>input {{
    background-color: rgba(255,255,255,0.7) !important; /* Açık beyaz arkaplan */
    border: 1px solid var(--primary-green);
    color: var(--text-dark) !important;
}}
div[data-testid="stSidebar"] .st-emotion-cache-1g0hp8h {{ /* Slider track */
    background-color: var(--primary-green) !important;
}}
div[data-testid="stSidebar"] .st-emotion-cache-1g0hp8h > div[data-testid="stThumbValue"] {{ /* Slider thumb */
    background-color: var(--primary-green) !important;
    border: 2px solid var(--card-bg-color);
}}
div[data-testid="stSidebar"] .st-emotion-cache-nahz7x p {{ /* multiselect seçili item text */
    color: var(--text-dark) !important;
}}


/* --- ÜST NAVİGASYON MENÜSÜ --- */
nav.st-emotion-cache-19rxjzo {{ /* Bu selector menünün ana konteynerini hedefler */
    background-color: var(--card-bg-color); /* Menü arka planı beyaz */
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin: 0 auto 2rem auto;
    padding: 0.5rem;
    width: fit-content;
    border: 1px solid var(--border-light);
}}
/* Seçili menü öğesi */
.st-emotion-cache-1nm7f8b {{ 
    background-color: var(--primary-green) !important; /* Seçili menü öğesi ana yeşil */
    border-radius: 8px;
    color: white !important;
}}
.st-emotion-cache-1nm7f8b p {{ /* Seçili menü öğesinin metni */
    color: white !important;
    font-weight: 600;
}}
.st-emotion-cache-1nm7f8b:hover {{
    background-color: var(--button-hover) !important; /* Hover rengi daha koyu yeşil */
}}
/* Diğer menü öğeleri */
.st-emotion-cache-pkpr8m p {{ 
    color: var(--text-dark) !important;
}}
.st-emotion-cache-pkpr8m:hover {{
    background-color: var(--border-light) !important; /* Hover rengi açık gri */
    border-radius: 8px;
}}


/* --- KARTLAR --- */
.recipe-card-link {{ text-decoration: none; }}
.recipe-card {{ 
    background-color: var(--card-bg-color) !important; 
    border-radius: 12px; border: 1px solid var(--border-light); 
    box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
    margin-bottom: 1.5rem; overflow: hidden; 
    transition: all 0.3s ease; height: 420px; 
    display: flex; flex-direction: column; 
}}
.recipe-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
.card-image {{ 
    width: 100%; 
    height: 300px; 
    object-fit: cover; /* Resmin bozulmasını engeller */
    display: block; 
    flex-shrink: 0; 
}}
.card-body {{ padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{ 
    font-weight: 700; font-size: 1.1rem; color: var(--text-dark) !important; margin: 0 0 0.5rem 0; 
    line-height: 1.3; height: 2.6em; /* 2 satır */
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box; 
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}}
.card-metadata {{ 
    display: flex; flex-direction: row; justify-content: space-between; 
    align-items: center; font-size: 0.8rem; color: var(--text-light); 
    margin-top: auto; padding-top: 0.5rem; border-top: 1px solid var(--border-light);
}}
.card-metadata span {{ display: flex; align-items: center; gap: 5px; }}
.card-metadata svg {{ width: 14px; height: 14px; fill: var(--text-light); }}

/* --- BUTONLAR --- */
.stButton > button {{
    background-color: var(--primary-green); /* Daha canlı yeşil */
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.7rem 1.2rem;
    font-weight: 600;
    transition: background-color 0.2s ease;
}}
.stButton > button:hover {{
    background-color: var(--button-hover); /* Hover rengi bir tık daha koyu */
}}
.stButton > button:active {{
    background-color: var(--primary-green);
}}
/* AI butonu için özel stil (eğer type="primary" ise) */
.stButton [data-testid="stFormSubmitButton"] > button {{ /* Sadece form içindeki primary submit butonları için */
    background-color: var(--primary-green) !important;
    color: white !important;
}}
.stButton [data-testid="stFormSubmitButton"] > button:hover {{
    background-color: var(--button-hover) !important;
}}


/* --- FORM ELEMENTLERİ --- */
.stTextInput>div>div>input, .stSelectbox>div>div, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {{
    background-color: var(--card-bg-color);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 0.5rem;
    color: var(--text-dark);
}}
label {{
    color: var(--text-dark);
    font-weight: 500;
}}

/* --- DETAY SAYFASI --- */
.detail-page-title {{ font-family: 'Dancing Script', cursive !important; font-size: 3.5rem; text-align: center; margin-bottom: 1rem; color: var(--text-dark); }}
.detail-card {{ padding: 1.5rem; height: 100%; background-color: var(--card-bg-color); border-radius: 12px; border: 1px solid var(--border-light); }}
.detail-card img {{ width: 100%; border-radius: 8px; object-fit: cover; height: 450px; }}
.detail-card h5 {{ border-bottom: 2px solid var(--border-light); padding-bottom: 8px; margin-top: 0; color: var(--text-dark); }}
.detail-card-text {{ white-space: pre-wrap; font-size: 0.9rem; line-height: 1.7; color: var(--text-dark); }}

/* --- YAPAY ZEKA KUTUSU --- */
.ai-response {{
    background-color: #E6FFE6; /* Çok açık yeşil */
    border-left: 5px solid var(--primary-green);
    padding: 1rem;
    border-radius: 8px;
    white-space: pre-wrap;
    font-family: 'Quicksand', sans-serif;
    line-height: 1.7;
    color: var(--text-dark);
}}

</style>
""", unsafe_allow_html=True)


# --- GOOGLE SHEETS BAĞLANTISI ---
# ... (Aynı kalacak)
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}"); st.stop()


# --- YARDIMCI FONKSİYONLAR ---
# ... (fetch_all_recipes, get_instagram_thumbnail, build_sidebar, display_recipe_cards_final aynı kalıyor)
CATEGORIZED_INGREDIENTS = {
    "Süt & Süt Ürünleri 🥛": ["Süt", "Yoğurt", "Peynir", "Kaşar peyniri", "Krema", "Tereyağı", "Yumurta"],
    "Et, Tavuk & Balık 🥩": ["Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Balık"],
    "Sebzeler 🥕": ["Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar"],
    "Bakliyat & Tahıl 🍚": ["Un", "Pirinç", "Bulgur", "Makarna", "Mercimek", "Nohut", "Fasulye", "Maya"],
    "Temel Gıdalar & Soslar 🧂": ["Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke"],
    "Kuruyemiş & Tatlı 🍫": ["Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal"],
    "Baharatlar 🌿": ["Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Toz biber"]
}

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

def get_instagram_thumbnail(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1'}
        response = requests.get(url, headers=headers, timeout=15)
        html_text = response.text
        script_tag = re.search(r'<script type="application/ld\+json">(.+?)</script>', html_text)
        if script_tag:
            json_data = json.loads(script_tag.group(1))
            thumbnail_url = json_data.get('thumbnailUrl') or json_data.get('image');
            if thumbnail_url: return thumbnail_url
    except Exception: pass
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
        selected_süre_aralığı = st.slider("Hazırlanma Süresi (dk)", min_süre, max_süre, (min_süre, max_süre))
    
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


# --- TARİF DETAY SAYFASI ---
def show_recipe_detail(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty:
        st.error("Aradığınız tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0]

    # Butonlar için sütunlar
    col_b1, col_b2, col_b3, col_b4 = st.columns([2, 2, 2, 6])
    with col_b1:
        if st.button("⬅️ Geri", key="back_button_detail"):
            st.query_params.clear(); st.rerun()
    with col_b2:
        is_favorite = recipe.get('favori') == 'EVET'
        fav_text = "⭐ Favoriden Çıkar" if is_favorite else "⭐ Favorilere Ekle"
        if st.button(fav_text, key="favorite_button_detail"):
            cell = worksheet.find(str(recipe['id']))
            favori_col_index = worksheet.row_values(1).index('favori') + 1
            new_status = "HAYIR" if is_favorite else "EVET"
            worksheet.update_cell(cell.row, favori_col_index, new_status)
            st.cache_data.clear(); st.rerun()
    with col_b3:
        if st.button("✏️ Düzenle", key="edit_button_detail"):
            st.session_state.recipe_to_edit_id = recipe['id']
            st.query_params.clear(); st.rerun()

    st.markdown(f"<h1 class='detail-page-title'>{recipe['baslik']}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 2, 2], gap="large")
    with col1:
        st.markdown(f"""<div class="detail-card"><img src="{recipe['thumbnail_url']}" alt="{recipe['baslik']}"></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="detail-card"><h5>Malzemeler</h5><div class="detail-card-text">{recipe.get('malzemeler', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="detail-card"><h5>Yapılışı</h5><div class="detail-card-text">{recipe.get('yapilisi', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)
    
    # Silme butonu için tehlikeli bölge
    st.markdown("---")
    with st.expander("🔴 Tarifi Kalıcı Olarak Sil"):
        st.warning("Bu işlem geri alınamaz. Tarifi silmek istediğinizden emin misiniz?")
        if st.button("Evet, Bu Tarifi Sil", type="primary", key="delete_confirm_button"):
            cell = worksheet.find(str(recipe['id']))
            worksheet.delete_rows(cell.row)
            st.cache_data.clear()
            st.success(f"'{recipe['baslik']}' tarifi kalıcı olarak silindi.")
            time.sleep(2)
            st.query_params.clear()
            st.rerun()

# --- DÜZENLEME FORMU SAYFASI ---
def show_edit_form(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty:
        st.error("Düzenlenecek tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0].to_dict()

    st.markdown(f"<h2>✏️ Tarifi Düzenle: *{recipe['baslik']}*</h2>", unsafe_allow_html=True)
    with st.form("edit_recipe_form"):
        # Form elemanları...
        edit_baslik = st.text_input("Tarif Başlığı", value=recipe['baslik'])
        edit_insta_url = st.text_input("Instagram Reel Linki", value=recipe['instagram_reel_link'])
        
        kategori_options = sorted(df['kategori'].unique())
        kategori_index = kategori_options.index(recipe['kategori']) if recipe['kategori'] in kategori_options else 0
        edit_kategori = st.selectbox("Kategori", options=kategori_options, index=kategori_index)
        
        edit_yemek_zorlugu = st.selectbox("Yemek Zorluğu", options=["Basit", "Orta", "Zor"], index=["Basit", "Orta", "Zor"].index(recipe['yemek_zorlugu']))
        edit_hazirlanma_suresi = st.number_input("Hazırlanma Süresi (dakika)", min_value=1, step=5, value=recipe['hazirlanma_suresi'])
        
        edit_malzemeler = st.text_area("Malzemeler (Her satıra bir tane)", value=recipe.get('malzemeler', ''), height=200)
        edit_yapilisi = st.text_area("Yapılışı (Açıklama)", value=recipe.get('yapilisi', ''), height=200)

        submitted_edit = st.form_submit_button("💾 Değişiklikleri Kaydet")
        if submitted_edit:
            try:
                cell = worksheet.find(str(recipe['id']))
                header = worksheet.row_values(1)
                
                # Sadece değişen alanları güncelle
                if edit_baslik != recipe['baslik']:
                    worksheet.update_cell(cell.row, header.index('baslik') + 1, edit_baslik)
                if edit_insta_url != recipe['instagram_reel_link']:
                    worksheet.update_cell(cell.row, header.index('instagram_reel_link') + 1, edit_insta_url)
                    # Thumbnail URL'sini de güncelle
                    new_thumbnail = get_instagram_thumbnail(edit_insta_url)
                    if new_thumbnail:
                        worksheet.update_cell(cell.row, header.index('thumbnail_url') + 1, new_thumbnail)
                    else:
                        st.warning("Yeni Instagram linkinden kapak fotoğrafı alınamadı, eski fotoğraf kaldı.")
                if edit_kategori != recipe['kategori']:
                    worksheet.update_cell(cell.row, header.index('kategori') + 1, edit_kategori)
                if edit_yemek_zorlugu != recipe['yemek_zorlugu']:
                    worksheet.update_cell(cell.row, header.index('yemek_zorlugu') + 1, edit_yemek_zorlugu)
                if edit_hazirlanma_suresi != recipe['hazirlanma_suresi']:
                    worksheet.update_cell(cell.row, header.index('hazirlanma_suresi') + 1, edit_hazirlanma_suresi)
                if edit_malzemeler != recipe.get('malzemeler', ''):
                    worksheet.update_cell(cell.row, header.index('malzemeler') + 1, edit_malzemeler)
                if edit_yapilisi != recipe.get('yapilisi', ''):
                    worksheet.update_cell(cell.row, header.index('yapilisi') + 1, edit_yapilisi)
                
                st.success("Tarif başarıyla güncellendi!")
                st.cache_data.clear()
                st.session_state.recipe_to_edit_id = None # Edit modundan çık
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Güncelleme sırasında bir hata oluştu: {e}")

    if st.button("İptal", key="cancel_edit_button"):
        st.session_state.recipe_to_edit_id = None
        st.rerun()

# --- ANA SAYFA GÖRÜNÜMÜ ---
def show_main_page():
    st.markdown("""
        <header>
            <h1>🌸 Ceren'in Defteri 🌸</h1>
        </header>
    """, unsafe_allow_html=True)
    
    all_recipes_df = fetch_all_recipes()
    
    selected_page = option_menu(
        menu_title=None, 
        options=["Tüm Tarifler", "⭐ Favorilerim", "Ne Pişirsem?", "Yeni Tarif Ekle"],
        icons=['card-list', 'star-fill', 'lightbulb', 'plus-circle'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
            "container": {"background-color": "var(--card-bg-color)", "border-radius": "12px", "box-shadow": "0 4px 12px rgba(0,0,0,0.05)", "padding": "0.5rem", "width": "fit-content", "margin": "0 auto 2rem auto", "border": "1px solid var(--border-light)"},
            "nav-link": {"font-weight": "600", "color": "var(--text-dark)"},
            "nav-link-selected": {"background-color": "var(--primary-green)", "color": "white"}
        }
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
        ingredient_search = st.text_input("Malzeme Ara...", placeholder="Aradığın malzemeyi yazarak listeyi kısalt...")
        
        selected_ingredients = []
        for category, ingredients in CATEGORIZED_INGREDIENTS.items():
            ingredients_to_show = [ing for ing in ingredients if ingredient_search.lower() in ing.lower()] if ingredient_search else ingredients
            if ingredients_to_show:
                with st.expander(category, expanded=bool(ingredient_search)):
                    cols = st.columns(4)
                    for i, ingredient in enumerate(ingredients_to_show):
                        with cols[i % 4]:
                            if st.checkbox(ingredient, key=f"ing_{ingredient}"):
                                selected_ingredients.append(ingredient)
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            find_recipe_button = st.button("🧑‍🍳 Bu Malzemelerle Tarif Bul", use_container_width=True, key="find_recipe_main")
        with col2:
            # AI_ENABLED değişkenini burada tanımlamanız veya dışarıdan almanız gerekir
            ai_enabled = False # Varsayılan olarak False, API anahtarınız varsa True yapın
            if "GOOGLE_API_KEY" in st.secrets:
                ai_enabled = True
                # genai.configure(api_key=st.secrets["GOOGLE_API_KEY"]) # API anahtarını yapılandır
            
            ai_recipe_button = st.button("🤖 Yapay Zekadan Tarif İste!", use_container_width=True, type="primary", disabled=not ai_enabled, key="ai_recipe_main")

        if find_recipe_button and selected_ingredients:
            filtered_df = all_recipes_df.copy()
            for ingredient in selected_ingredients:
                filtered_df = filtered_df[filtered_df['malzemeler'].str.contains(ingredient.lower(), case=False, na=False)]
            display_recipe_cards_final(filtered_df.sort_values(by='id', ascending=False))
        
        if ai_recipe_button and selected_ingredients:
            if ai_enabled:
                with st.spinner("Yapay zeka şefimiz sizin için özel bir tarif hazırlıyor..."):
                    # model = genai.GenerativeModel('gemini-1.5-flash')
                    # prompt = f"""Kullanıcı şu malzemeleri seçti: {', '.join(selected_ingredients)}. Bu malzemelerle hazırlanabilecek, Ceren'in Defteri tarzında (samimi, kısa girişli, kolay anlaşılır, başlığında emoji olan) tek bir tarif önerisi oluştur. Tarifin adı ve açıklamasında "Ceren'in Defteri'nden" ibaresi olsun. Tarife "Malzemeler:" ve "Yapılışı:" başlıklarını ekle. Tarif sonunda "Ceren" imzası bulunsun. Örneğin: Ceren'in Defteri'nden: Fındıklı Çikolatalı Sütlü Mucize Kek
                    # response = model.generate_content(prompt, stream=True)
                    # st.markdown("### 🤖 Yapay Zeka Şefin Önerisi")
                    # st.write_stream(chunk.text for chunk in response)
                    st.info("Yapay zeka özelliği şuan kapalı.") # API anahtarınız varsa bu satırı silin
            else:
                st.warning("Yapay zeka özelliği devre dışı. Lütfen GOOGLE_API_KEY sırrını yapılandırın.")

        if not selected_ingredients and (find_recipe_button or ai_recipe_button):
             st.warning("Lütfen önce en az bir malzeme seçin.")
        elif not selected_ingredients:
             st.info("Sonuçları görmek için yukarıdan malzeme seçin ve bir butona basın.")


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
                            new_row = [datetime.now().strftime("%Y%m%d%H%M%S"), insta_url, tarif_basligi, yapilisi, malzemeler, kategori, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), thumbnail_url, yemek_zorlugu, hazirlanma_suresi, "HAYIR"]
                            worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                            st.cache_data.clear()
                            st.success("Tarif başarıyla kaydedildi!")
                        else: st.error("Bu linkten kapak fotoğrafı alınamadı.")
                else: st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")

# --- ANA UYGULAMA YÖNLENDİRİCİSİ (ROUTER) ---
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