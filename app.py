import streamlit as st
import gspread
import pandas as pd
from google.oauth2 import service_account # Önemli kütüphane
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import html
from streamlit_option_menu import option_menu
import json
import re
import time
import random
import google.generativeai as genai

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

:root {{
    --primary-green: #8BC34A;
    --secondary-green: #A5D6A7;
    --background-cream: #FFF8E1;
    --card-bg-color: #FFFFFF;
    --text-dark: #36454F;
    --text-light: #6A7B8E;
    --border-light: #E0E0E0;
    --button-hover: #7CB342;
}}

.stApp {{ background-color: var(--background-cream); font-family: 'Quicksand', sans-serif; }}
div[data-testid="stAppViewContainer"] > .main {{ padding-top: 0rem; }}

header {{
    background-image: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.1)),
                      url("https://plus.unsplash.com/premium_photo-1663099777846-62e0c092ce0b?q=80&w=1349&auto=format&fit=crop");
    background-size: cover;
    background-position: center 35%;
    padding: 3rem 1rem;
    border-bottom: 2px solid var(--primary-green);
    text-align: center;
    margin-bottom: 2rem;
}}
header h1 {{
    font-family: 'Dancing Script', cursive !important;
    color: var(--card-bg-color) !important;
    font-size: 4.5rem;
    text-shadow: 2px 2px 5px rgba(0,0,0,0.6);
    margin: 0;
}}
div[data-testid="stHeading"] {{ display: none; }}
div[data-testid="stSidebar"] {{ background-color: var(--secondary-green) !important; }}
div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p {{ color: var(--text-dark) !important; }}

nav.st-emotion-cache-19rxjzo {{
    background-color: var(--card-bg-color);
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin: 0 auto 2rem auto;
    padding: 0.5rem;
    width: fit-content;
    border: 1px solid var(--border-light);
}}
.st-emotion-cache-1nm7f8b {{ background-color: var(--primary-green) !important; border-radius: 8px; }}
.st-emotion-cache-1nm7f8b p {{ color: white !important; font-weight: 600; }}

.recipe-card-link {{ text-decoration: none; }}
.recipe-card {{ 
    background-color: var(--card-bg-color) !important; 
    border-radius: 12px; border: 1px solid var(--border-light); 
    box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
    margin-bottom: 1.5rem; overflow: hidden; 
    transition: all 0.3s ease; 
    height: 440px; 
    display: flex; flex-direction: column; 
}}
.recipe-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
.card-image {{ width: 100%; height: 280px; object-fit: cover; display: block; flex-shrink: 0; }}
.card-body {{ padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{ font-weight: 700; font-size: 1.1rem; color: var(--text-dark) !important; margin: 0 0 0.5rem 0; line-height: 1.3; height: 2.6em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
.card-metadata {{ display: flex; flex-direction: row; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #777; margin-top: auto; padding-top: 0.5rem; border-top: 1px solid var(--border-light); }}
.stButton > button {{ background-color: var(--primary-green); color: white; border-radius: 8px; border: none; padding: 0.7rem 1.2rem; font-weight: 600; transition: background-color 0.2s ease; }}
.stButton > button:hover {{ background-color: var(--button-hover); }}
.detail-page-title {{ font-family: 'Dancing Script', cursive !important; font-size: 3.5rem; text-align: center; margin-bottom: 1rem; color: var(--text-dark); }}
.detail-card {{ padding: 1.5rem; height: 100%; background-color: var(--card-bg-color); border-radius: 12px; border: 1px solid var(--border-light); }}
.detail-card img {{ width: 100%; border-radius: 8px; object-fit: cover; height: 450px; }}
.detail-card h5 {{ border-bottom: 2px solid var(--border-light); padding-bottom: 8px; margin-top: 0; }}
.detail-card-text {{ white-space: pre-wrap; font-size: 0.9rem; line-height: 1.7; }}
</style>
""", unsafe_allow_html=True)

CATEGORIZED_INGREDIENTS = {
    "Süt & Süt Ürünleri 🥛": ["Süt", "Yoğurt", "Peynir", "Kaşar peyniri", "Krema", "Tereyağı", "Yumurta"],
    "Et, Tavuk & Balık 🥩": ["Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Balık"],
    "Sebzeler 🥕": ["Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar"],
    "Bakliyat & Tahıl 🍚": ["Un", "Pirinç", "Bulgur", "Makarna", "Mercimek", "Nohut", "Fasulye", "Maya"],
    "Temel Gıdalar & Soslar 🧂": ["Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke"],
    "Kuruyemiş & Tatlı 🍫": ["Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal"],
    "Baharatlar 🌿": ["Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Toz biber"]
}

# --- GEMINI API KURULUMU ---
if "general" in st.secrets and "gemini_api_key" in st.secrets["general"]:
    genai.configure(api_key=st.secrets["general"]["gemini_api_key"])

def parse_recipe_with_ai(text_content):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Sen uzman bir aşçısın. Aşağıdaki Instagram gönderisi metnini analiz et.
    Bana SADECE geçerli bir JSON formatında şu bilgileri ver.
    {{
        "baslik": "Yemeğin adı (kısa, baş harfleri büyük)",
        "malzemeler": "Malzemeleri alt alta maddeler halinde string olarak yaz",
        "yapilisi": "Yapılış adımlarını anlaşılır bir paragraf olarak yaz",
        "sure": "Tahmini hazırlama süresi (sadece sayı, dakika cinsinden, örn: 30)",
        "zorluk": "Basit, Orta veya Zor",
        "kategori": "Ana Yemek, Tatlı, Kahvaltılık, Çorba, Salata, Atıştırmalık"
    }}
    Analiz edilecek metin: {text_content}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        st.error(f"AI Analizi başarısız oldu: {e}")
        return None

# --- VERİTABANI BAĞLANTISI (DÜZELTİLMİŞ) ---
try:
    # Secrets dosyasından veriyi dictionary olarak al
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Scopes tanımla
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Service Account objesi oluştur
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    
    # Gspread ile yetkilendir
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
    
except Exception as e:
    st.error(f"⚠️ Bağlantı Hatası: {e}")
    st.info("Lütfen .streamlit/secrets.toml dosyanızın formatını kontrol edin.")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
def refresh_all_thumbnails():
    st.info("Kapak fotoğrafları yenileniyor...")
    all_recipes_df = pd.DataFrame(worksheet.get_all_records())
    all_recipes_df.columns = [col.strip().lower().replace(' ', '_') for col in all_recipes_df.columns]
    
    updated_count = 0
    total_rows = len(all_recipes_df)
    progress_bar = st.progress(0, text="Başlıyor...")

    for index, row in all_recipes_df.iterrows():
        progress_bar.progress((index + 1) / total_rows, text=f"{index+1}/{total_rows} işleniyor")
        original_post_url = row.get('url')
        current_thumbnail_url = row.get('thumbnail_url')
        recipe_id = str(row.get('id'))

        if original_post_url and recipe_id:
            try:
                new_thumbnail_url = get_instagram_thumbnail(original_post_url)
                if new_thumbnail_url and new_thumbnail_url != current_thumbnail_url:
                    cell = worksheet.find(recipe_id)
                    if cell:
                        header = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)]
                        thumbnail_col_index = header.index('thumbnail_url') + 1
                        worksheet.update_cell(cell.row, thumbnail_col_index, new_thumbnail_url)
                        updated_count += 1
                        time.sleep(1.1)
            except Exception:
                pass

    progress_bar.empty()
    st.success(f"Tamamlandı! {updated_count} fotoğraf güncellendi.")
    st.cache_data.clear()
    st.rerun()

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
    clean_url = url.split("?")[0]
    headers = { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1' }
    try:
        response = requests.get(clean_url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        if meta_tag and meta_tag.get('content'):
            return meta_tag.get('content')
        return None
    except Exception:
        return None

def build_sidebar(df):
    with st.sidebar:
        st.markdown("<h2>Filtrele</h2>", unsafe_allow_html=True)
        search_query = st.text_input("Tarif Ara...", placeholder="Örn: Kek")
        st.write("---")
        all_categories = sorted(df['kategori'].unique())
        selected_categories = st.multiselect("Yemek Türü", options=all_categories)
        st.write("---")
        min_süre = int(df['hazirlanma_suresi'].min())
        max_süre = int(df['hazirlanma_suresi'].max()) if df['hazirlanma_suresi'].max() > 0 else 120
        selected_süre_aralığı = st.slider("Hazırlanma Süresi (dk)", min_süre, max_süre, (min_süre, max_süre))
        
        st.markdown("---")
        if st.button("🔄 Fotoğrafları Düzelt"):
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
        st.warning("Tarif bulunamadı.")
        return
    st.markdown(f"**{len(df)}** tarif bulundu.")
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
                            <span><b>{recipe.get('yemek_zorlugu', 'N/A')}</b></span>
                            <span><b>{recipe.get('hazirlanma_suresi', 0)} dk</b></span>
                        </div>
                    </div>
                </div>
            </a>""", unsafe_allow_html=True)

def show_recipe_detail(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty: st.error("Bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0]

    col_b1, col_b2, col_b3, col_b4 = st.columns([2, 2, 2, 6])
    with col_b1:
        if st.button("⬅️ Geri"): st.query_params.clear(); st.rerun()
    with col_b2:
        is_favorite = recipe.get('favori') == 'EVET'
        if st.button("⭐ Çıkar" if is_favorite else "⭐ Ekle"):
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
    with col1: st.markdown(f"""<a href="{recipe['url']}" target="_blank"><div class="detail-card"><img src="{recipe['thumbnail_url']}"></div></a>""", unsafe_allow_html=True)
    with col2: st.markdown(f"""<div class="detail-card"><h5>Malzemeler</h5><div class="detail-card-text">{recipe.get('malzemeler', '')}</div></div>""", unsafe_allow_html=True)
    with col3: st.markdown(f"""<div class="detail-card"><h5>Yapılışı</h5><div class="detail-card-text">{recipe.get('yapilisi', '')}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander("🔴 Tarifi Sil"):
        if st.button("Evet, Sil", type="primary"):
            cell = worksheet.find(str(recipe['id']))
            worksheet.delete_rows(cell.row)
            st.cache_data.clear(); st.success("Silindi."); time.sleep(1); st.query_params.clear(); st.rerun()

def show_edit_form(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty: st.error("Hata"); st.stop()
    recipe = recipe_df.iloc[0].to_dict()

    st.markdown(f"<h2>✏️ Düzenle: {recipe['baslik']}</h2>", unsafe_allow_html=True)
    with st.form("edit_recipe_form"):
        edit_insta_url = st.text_input("Instagram Linki", value=recipe['url'])
        edit_baslik = st.text_input("Başlık", value=recipe['baslik'])
        cat_ops = sorted(df['kategori'].unique())
        edit_kategori = st.selectbox("Kategori", options=cat_ops, index=cat_ops.index(recipe['kategori']) if recipe['kategori'] in cat_ops else 0)
        zorluk_ops = ["Basit", "Orta", "Zor"]
        edit_zorluk = st.selectbox("Zorluk", options=zorluk_ops, index=zorluk_ops.index(recipe.get('yemek_zorlugu')) if recipe.get('yemek_zorlugu') in zorluk_ops else 0)
        edit_sure = st.number_input("Süre (dk)", value=int(recipe.get('hazirlanma_suresi', 15)))
        edit_malz = st.text_area("Malzemeler", value=recipe.get('malzemeler', ''), height=200)
        edit_yap = st.text_area("Yapılışı", value=recipe.get('yapilisi', ''), height=200)

        col1, col2 = st.columns(2)
        with col1: sub = st.form_submit_button("💾 Kaydet", use_container_width=True)
        with col2: 
            if st.form_submit_button("❌ İptal", use_container_width=True):
                st.session_state.recipe_to_edit_id = None; st.rerun()
        
        if sub:
            cell = worksheet.find(str(recipe['id']))
            head = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)]
            worksheet.update_cell(cell.row, head.index('baslik')+1, edit_baslik.title())
            worksheet.update_cell(cell.row, head.index('url')+1, edit_insta_url)
            worksheet.update_cell(cell.row, head.index('kategori')+1, edit_kategori)
            worksheet.update_cell(cell.row, head.index('yemek_zorlugu')+1, edit_zorluk)
            worksheet.update_cell(cell.row, head.index('hazirlanma_suresi')+1, edit_sure)
            worksheet.update_cell(cell.row, head.index('malzemeler')+1, edit_malz)
            worksheet.update_cell(cell.row, head.index('yapilisi')+1, edit_yap)
            st.success("Güncellendi!"); st.cache_data.clear(); st.session_state.recipe_to_edit_id = None; time.sleep(1); st.rerun()

# --- ANA SAYFA ---
def show_main_page():
    st.markdown("""<header><h1>🌸 Ceren'in Defteri 🌸</h1></header>""", unsafe_allow_html=True)
    all_recipes_df = fetch_all_recipes()
    selected_page = option_menu(menu_title=None, options=["Tüm Tarifler", "⭐ Favorilerim", "Ne Pişirsem?", "Yeni Tarif Ekle"], icons=['card-list', 'star-fill', 'lightbulb', 'plus-circle'], menu_icon="cast", default_index=0, orientation="horizontal")

    if selected_page == "Tüm Tarifler":
        filtered = build_sidebar(all_recipes_df)
        display_recipe_cards_final(filtered.sort_values(by='id', ascending=False))
        
    elif selected_page == "⭐ Favorilerim":
        favs = all_recipes_df[all_recipes_df['favori'] == 'EVET']
        display_recipe_cards_final(favs.sort_values(by='id', ascending=False))
        
    elif selected_page == "Ne Pişirsem?":
        st.markdown("<h2>Ne Pişirsem?</h2>", unsafe_allow_html=True)
        search = st.text_input("Malzeme Ara...")
        selected_ings = []
        for cat, ings in CATEGORIZED_INGREDIENTS.items():
            to_show = [i for i in ings if search.lower() in i.lower()] if search else ings
            if to_show:
                with st.expander(cat, expanded=bool(search)):
                    cols = st.columns(4)
                    for i, ing in enumerate(to_show):
                        with cols[i%4]:
                            if st.checkbox(ing, key=f"ing_{ing}"): selected_ings.append(ing)
        
        col1, col2 = st.columns(2)
        with col1: find_btn = st.button("🧑‍🍳 Tarif Bul", use_container_width=True)
        with col2: ai_btn = st.button("🤖 AI'dan İste", use_container_width=True, disabled=True) # AI chat özelliği kapalı

        if find_btn and selected_ings:
            filtered = all_recipes_df.copy()
            for ing in selected_ings: filtered = filtered[filtered['malzemeler'].str.contains(ing.lower(), case=False, na=False)]
            display_recipe_cards_final(filtered)

    elif selected_page == "Yeni Tarif Ekle":
        st.markdown("<h2>✨ Yeni Tarif Ekle (AI Asistan)</h2>", unsafe_allow_html=True)
        if 'ai_form_data' not in st.session_state: st.session_state.ai_form_data = {}

        with st.container():
            c1, c2 = st.columns([3, 1])
            with c1: insta_caption = st.text_area("Instagram Açıklaması:", height=100)
            with c2: 
                st.write(""); st.write("")
                if st.button("✨ AYRIŞTIR", type="primary", use_container_width=True):
                    if insta_caption:
                        with st.spinner("Okunuyor..."):
                            res = parse_recipe_with_ai(insta_caption)
                            if res: st.session_state.ai_form_data = res; st.success("Tamam!")
                            else: st.error("Hata")
        
        st.write("---")
        data = st.session_state.ai_form_data
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1:
                baslik = st.text_input("Başlık", value=data.get('baslik', ''))
                url = st.text_input("Instagram Linki")
                thumb = st.text_input("Manuel Resim Linki")
                kats = ["Ana Yemek", "Tatlı", "Kahvaltılık", "Çorba", "Salata", "Atıştırmalık"]
                kat = st.selectbox("Kategori", options=kats, index=kats.index(data.get('kategori')) if data.get('kategori') in kats else 0)
                zors = ["Basit", "Orta", "Zor"]
                zor = st.selectbox("Zorluk", options=zors, index=zors.index(data.get('zorluk')) if data.get('zorluk') in zors else 0)
                sure = st.number_input("Süre", value=int(data.get('sure', 15)))
            with c2:
                malz = st.text_area("Malzemeler", value=data.get('malzemeler', ''), height=250)
                yap = st.text_area("Yapılışı", value=data.get('yapilisi', ''), height=250)
            
            if st.form_submit_button("💾 Kaydet", use_container_width=True):
                if baslik and (url or thumb):
                    final_thumb = "https://images.unsplash.com/photo-1495521821757-a1efb6729352"
                    if url: 
                        s = get_instagram_thumbnail(url)
                        if s: final_thumb = s
                        elif thumb: final_thumb = thumb
                    elif thumb: final_thumb = thumb
                    
                    row = [datetime.now().strftime("%Y%m%d%H%M%S"), url, baslik.title(), yap, malz, kat, datetime.now().strftime("%Y-%m-%d"), final_thumb, zor, sure, "HAYIR"]
                    worksheet.append_row(row, value_input_option='USER_ENTERED')
                    st.success("Kaydedildi!"); st.balloons(); st.session_state.ai_form_data = {}; time.sleep(2); st.rerun()
                else: st.warning("Başlık ve Link girin.")

# --- ROUTER ---
if 'recipe_to_edit_id' not in st.session_state: st.session_state.recipe_to_edit_id = None
all_recipes_df = fetch_all_recipes()
if st.session_state.recipe_to_edit_id: show_edit_form(st.session_state.recipe_to_edit_id, all_recipes_df)
elif "id" in st.query_params: show_recipe_detail(st.query_params.get("id"), all_recipes_df)
else: show_main_page()