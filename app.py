import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import html
from streamlit_option_menu import option_menu
import json
import re
import time

# --- GÖRSEL AYARLAR VE STİL ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

:root {{
    --primary-color: #8BC34A;
    --background-cream: #FDF5E6;
    --card-bg-color: #FFFFFF;
    --text-dark: #36454F;
    --text-light: #6A7B8E;
    --border-light: #E0E0E0;
    --link-color: #2196F3;
}}

.stApp {{ background-color: var(--background-cream); font-family: 'Quicksand', sans-serif; }}
div[data-testid="stAppViewContainer"] > .main {{ padding-top: 0rem; }}

header {{
    background-image: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.1)),
                      url("https://plus.unsplash.com/premium_photo-1663099777846-62e0c092ce0b?q=80&w=1349&auto=format&fit=crop");
    background-size: cover;
    background-position: center 35%;
    padding: 2.5rem 1rem;
    text-align: center;
    margin-bottom: 2rem;
}}
header h1 {{
    font-family: 'Dancing Script', cursive !important;
    color: var(--card-bg-color) !important;
    font-size: 4rem;
    text-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    margin: 0;
}}
div[data-testid="stHeading"] {{ display: none; }}

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
.card-image {{ 
    width: 100%; 
    height: 280px; 
    object-fit: cover; 
    display: block; 
    flex-shrink: 0; 
}}
.card-body {{ padding: 1rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{ 
    font-family: 'Quicksand', sans-serif; 
    font-weight: 700; font-size: 1.1rem; color: var(--text-dark) !important; margin: 0 0 0.5rem 0; 
    line-height: 1.3; 
    height: auto; 
    min-height: 2.6em; 
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box; 
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}}
.card-metadata {{ 
    display: flex; flex-direction: row; justify-content: space-between; 
    align-items: center; font-size: 0.9rem; 
    color: var(--text-light); 
    margin-top: auto; padding-top: 0.75rem; 
    border-top: 1px solid var(--border-light);
}}
.stButton > button {{
    background-color: var(--primary-color);
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.7rem 1.2rem;
    font-weight: 600;
}}
.stButton > button:hover {{ background-color: #7CB342; }}

/* Form stilleri */
.stTextInput>div>div>input, .stSelectbox>div>div, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {{
    background-color: var(--card-bg-color);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    color: var(--text-dark);
}}

.detail-page-title {{ font-family: 'Dancing Script', cursive !important; font-size: 3.5rem; text-align: center; margin-bottom: 1rem; color: var(--text-dark); }}
.detail-card {{ padding: 1.5rem; height: 100%; background-color: var(--card-bg-color); border-radius: 12px; border: 1px solid var(--border-light); }}
.detail-card img {{ width: 100%; border-radius: 8px; object-fit: cover; height: 450px; }}
.detail-card h5 {{ border-bottom: 2px solid var(--border-light); padding-bottom: 8px; margin-top: 0; color: var(--text-dark); }}
.detail-card-text {{ white-space: pre-wrap; font-size: 0.9rem; line-height: 1.7; color: var(--text-dark); }}
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS BAĞLANTISI ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    
    if "spreadsheet_id" in st.secrets:
        spreadsheet = gc.open_by_key(st.secrets["spreadsheet_id"])
    else:
        spreadsheet = gc.open("Lezzet Defteri Veritabanı")
        
    worksheet = spreadsheet.worksheet("Sayfa1")
    
except Exception as e:
    st.error(f"Veritabanı Bağlantı Hatası: {e}")
    st.info("Lütfen secrets.toml dosyanızı kontrol edin.")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
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
    try:
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty:
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            df = df[df['id'] != ''].copy()
            if 'hazirlanma_suresi' in df.columns:
                df['hazirlanma_suresi'] = pd.to_numeric(df['hazirlanma_suresi'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Veri okuma hatası: {e}")
        return pd.DataFrame()

def get_instagram_thumbnail(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1'}
        response = requests.get(url, headers=headers, timeout=10)
        html_text = response.text
        script_tag = re.search(r'<script type="application/ld\+json">(.+?)</script>', html_text)
        if script_tag:
            json_data = json.loads(script_tag.group(1))
            thumbnail_url = json_data.get('thumbnailUrl') or json_data.get('image')
            if thumbnail_url: return thumbnail_url
    except Exception: 
        pass
    return None

def build_sidebar(df):
    with st.sidebar:
        st.markdown("<h2>Filtrele</h2>", unsafe_allow_html=True)
        search_query = st.text_input("Tarif Adıyla Ara...", placeholder="Örn: Kek")
        
        # --- YENİ EKLENEN FOTOĞRAF TAMİR BUTONU ---
        st.write("---")
        with st.expander("🔧 Yönetici Paneli"):
            st.info("Fotoğraflar görünmüyorsa bu butona basarak hepsini yenileyebilirsiniz.")
            if st.button("Fotoğrafları Yenile / Tamir Et"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Tüm verileri çek
                all_data = worksheet.get_all_records()
                total_rows = len(all_data)
                updated_count = 0
                
                # Sütun başlıklarını bul
                headers = [h.strip().lower().replace(' ', '_') for h in worksheet.row_values(1)]
                url_idx = headers.index('url') + 1
                thumb_idx = headers.index('thumbnail_url') + 1
                
                for i, row in enumerate(all_data):
                    # Progress bar güncelle
                    progress = (i + 1) / total_rows
                    progress_bar.progress(progress)
                    status_text.text(f"İşleniyor: {i+1}/{total_rows}")
                    
                    current_url = row.get('url', '')
                    # Sadece Instagram linki varsa işlem yap
                    if 'instagram.com' in current_url:
                        new_thumb = get_instagram_thumbnail(current_url)
                        if new_thumb:
                            # Hücreyi güncelle (Satır numarası i+2 çünkü header var ve index 0'dan başlar)
                            worksheet.update_cell(i + 2, thumb_idx, new_thumb)
                            updated_count += 1
                        time.sleep(1) # Instagram engellemesin diye azıcık bekle
                
                status_text.success(f"İşlem Tamamlandı! {updated_count} fotoğraf yenilendi.")
                st.cache_data.clear()
                time.sleep(2)
                st.rerun()
        # ------------------------------------------

        st.write("---")
        
        if not df.empty:
            all_categories = sorted(df['kategori'].unique())
            selected_categories = st.multiselect("Yemek Türü", options=all_categories)
            
            min_süre = int(df['hazirlanma_suresi'].min())
            max_süre = int(df['hazirlanma_suresi'].max()) if df['hazirlanma_suresi'].max() > 0 else 120
            selected_süre_aralığı = st.slider("Hazırlanma Süresi (dk)", min_süre, max_süre, (min_süre, max_süre))
        else:
            selected_categories = []
            selected_süre_aralığı = (0, 120)
    
    if df.empty: return df
    
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
    
    default_img = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000&auto=format&fit=crop"
    
    cols = st.columns(4)
    for i, recipe in enumerate(df.to_dict('records')):
        col = cols[i % 4]
        with col:
            img_src = recipe['thumbnail_url'] if recipe['thumbnail_url'] else default_img
            
            st.markdown(f"""
            <a href="/?id={recipe['id']}" target="_self" class="recipe-card-link">
                <div class="recipe-card">
                    <img src="{img_src}" class="card-image" onerror="this.onerror=null; this.src='{default_img}';">
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
    if recipe_df.empty: st.error("Aradığınız tarif bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0]
    
    if st.button("⬅️ Tüm Tariflere Geri Dön"):
        st.query_params.clear(); st.rerun()

    st.markdown(f"<h1 class='detail-page-title'>{recipe['baslik'].title()}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    default_img = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000&auto=format&fit=crop"
    img_src = recipe['thumbnail_url'] if recipe['thumbnail_url'] else default_img

    col1, col2, col3 = st.columns([2, 2, 2], gap="large")
    with col1:
        st.markdown(f"""
        <a href="{recipe['url']}" target="_blank" title="Instagram'da gör">
            <div class="detail-card">
                <img src="{img_src}" alt="{recipe['baslik']}" onerror="this.onerror=null; this.src='{default_img}';">
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class="detail-card"><h5>Malzemeler</h5><div class="detail-card-text">{recipe.get('malzemeler', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class="detail-card"><h5>Yapılışı</h5><div class="detail-card-text">{recipe.get('yapilisi', 'Eklenmemiş')}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander("🔴 Tarifi Kalıcı Olarak Sil"):
        st.warning("Bu işlem geri alınamaz.")
        if st.button("Evet, Bu Tarifi Sil", type="primary", key="delete_confirm_button"):
            cell = worksheet.find(str(recipe['id']))
            worksheet.delete_rows(cell.row)
            st.cache_data.clear()
            st.success("Silindi.")
            time.sleep(2)
            st.query_params.clear()
            st.rerun()

def show_edit_form(recipe_id, df):
    recipe_df = df[df['id'].astype(str) == str(recipe_id)]
    if recipe_df.empty: st.error("Bulunamadı."); st.stop()
    recipe = recipe_df.iloc[0].to_dict()

    st.markdown(f"<h2>✏️ Tarifi Düzenle: *{recipe['baslik'].title()}*</h2>", unsafe_allow_html=True)
    with st.form("edit_recipe_form"):
        edit_insta_url = st.text_input("Instagram Reel Linki", value=recipe['url'])
        edit_baslik = st.text_input("Tarif Başlığı", value=recipe['baslik'].title())
        
        kategori_options = sorted(df['kategori'].unique())
        try:
            kategori_index = kategori_options.index(recipe['kategori'])
        except:
            kategori_index = 0
            
        edit_kategori = st.selectbox("Kategori", options=kategori_options, index=kategori_index)
        
        zorluk_options = ["Basit", "Orta", "Zor"]
        try:
            zorluk_index = zorluk_options.index(recipe.get('yemek_zorlugu'))
        except:
            zorluk_index = 0
            
        edit_yemek_zorlugu = st.selectbox("Yemek Zorluğu", options=zorluk_options, index=zorluk_index)
        edit_hazirlanma_suresi = st.number_input("Süre (dk)", min_value=1, value=int(recipe.get('hazirlanma_suresi', 30)))
        edit_malzemeler = st.text_area("Malzemeler", value=recipe.get('malzemeler', ''), height=200)
        edit_yapilisi = st.text_area("Yapılışı", value=recipe.get('yapilisi', ''), height=200)
        
        col1, col2 = st.columns(2)
        with col1: submitted_edit = st.form_submit_button("💾 Kaydet", use_container_width=True)
        with col2: 
            if st.form_submit_button("❌ İptal", use_container_width=True):
                st.session_state.recipe_to_edit_id = None
                st.rerun()
                
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
                
                st.success("Güncellendi!")
                st.cache_data.clear()
                st.session_state.recipe_to_edit_id = None
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")

# --- ANA SAYFA ---
def show_main_page():
    st.markdown("""<header><h1> Ceren'in Defteri </h1></header>""", unsafe_allow_html=True)
    
    all_recipes_df = fetch_all_recipes()
    
    selected_page = option_menu(
        menu_title=None, 
        options=["Tüm Tarifler", "⭐ Favorilerim", "Ne Pişirsem?", "Yeni Tarif Ekle"],
        icons=['card-list', 'star-fill', 'lightbulb', 'plus-circle'], 
        menu_icon="cast", 
        default_index=0, 
        orientation="horizontal"
    )

    if selected_page == "Tüm Tarifler":
        filtered_recipes = build_sidebar(all_recipes_df)
        display_recipe_cards_final(filtered_recipes.sort_values(by='id', ascending=False))

    elif selected_page == "⭐ Favorilerim":
        st.markdown("<h2>⭐ Favori Tariflerim</h2>", unsafe_allow_html=True)
        if not all_recipes_df.empty:
            favorites_df = all_recipes_df[all_recipes_df['favori'] == 'EVET']
            display_recipe_cards_final(favorites_df.sort_values(by='id', ascending=False))

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
                            
        if st.button("🧑‍🍳 Tarif Bul", use_container_width=True) and selected_ings:
             filtered = all_recipes_df.copy()
             for ing in selected_ings: 
                 filtered = filtered[filtered['malzemeler'].str.contains(ing.lower(), case=False, na=False)]
             display_recipe_cards_final(filtered)

    elif selected_page == "Yeni Tarif Ekle":
        st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
        with st.form("new_recipe_page_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                insta_url = st.text_input("Instagram Reel Linki")
                tarif_basligi = st.text_input("Tarif Başlığı")
                kategori = st.selectbox("Kategori", ["Ana Yemek", "Tatlı", "Kahvaltılık", "Çorba", "Salata", "Atıştırmalık"])
                yemek_zorlugu = st.selectbox("Zorluk", ["Basit", "Orta", "Zor"])
                hazirlanma_suresi = st.number_input("Süre (dk)", min_value=1, value=30)
                
            with col2:
                malzemeler = st.text_area("Malzemeler", height=150)
                yapilisi = st.text_area("Yapılışı", height=150)

            submitted_add = st.form_submit_button("✨ Tarifi Kaydet", use_container_width=True)
            
            if submitted_add:
                if insta_url and tarif_basligi:
                    with st.spinner("Kaydediliyor..."):
                        thumbnail_url = get_instagram_thumbnail(insta_url)
                        if not thumbnail_url:
                            thumbnail_url = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000&auto=format&fit=crop"
                        
                        new_row = [
                            datetime.now().strftime("%Y%m%d%H%M%S"), 
                            insta_url, 
                            tarif_basligi.title(), 
                            yapilisi, 
                            malzemeler, 
                            kategori, 
                            datetime.now().strftime("%Y-%m-%d"), 
                            thumbnail_url, 
                            yemek_zorlugu, 
                            hazirlanma_suresi, 
                            "HAYIR"
                        ]
                        
                        try:
                            worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                            st.cache_data.clear()
                            st.success("Tarif başarıyla kaydedildi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Hata: {e}")
                else: st.warning("Lütfen Link ve Başlık girin.")

# --- ROUTER ---
if 'recipe_to_edit_id' not in st.session_state: st.session_state.recipe_to_edit_id = None
all_recipes_df = fetch_all_recipes()

if st.session_state.recipe_to_edit_id: show_edit_form(st.session_state.recipe_to_edit_id, all_recipes_df)
elif "id" in st.query_params: show_recipe_detail(st.query_params.get("id"), all_recipes_df)
else: show_main_page()
