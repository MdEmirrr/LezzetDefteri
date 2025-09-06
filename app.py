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
from streamlit_lottie import st_lottie # Animasyonlar için eklendi

# --- GÖRSEL AYARLAR VE SABİT DEĞİŞKENLER ---

st.set_page_config(page_title="Ceren'in Defteri", layout="wide")

# Beğendiğiniz bir arka plan resminin linkini buraya yapıştırın.
# Telifsiz resimler için: unsplash.com, pexels.com
arka_plan_resmi = "https://images.unsplash.com/photo-1541172238217-86c2d0f353fd?q=80&w=2574&auto=format&fit=crop"

# --- YENİ STİL (CSS) ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Quicksand:wght@400;500;600&display=swap');

/* --- ARKA PLAN RESMİ --- */
.stApp {{
    background-image: url("{arka_plan_resmi}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* --- OKUNAKLILIK İÇİN YARI SAYDAM ARKA PLANLAR --- */
.recipe-card, div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stVerticalBlock"] > div[style*="border"] {{
    background-color: rgba(255, 255, 255, 0.88) !important;
    backdrop-filter: blur(5px);
}}

/* --- GENEL STİLLER --- */
.main .block-container {{ padding-top: 1rem !important; }}
h1 {{font-family: 'Dancing Script', cursive !important; color: #D988B9 !important; text-shadow: 1px 1px 3px #FFFFFF; text-align: center;}}
h2, h3, h5 {{font-family: 'Quicksand', sans-serif !important;color: #2F4F4F !important;}}
.recipe-card {{border: 1px solid #e9e9e9; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 2rem; overflow: hidden;}}
.card-image {{width: 100%; height: 250px; object-fit: cover;}}
.card-body {{ padding: 1rem; }}
.card-body .category-badge {{background-color: #FAE3FF; color: #B980F0; padding: 4px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: 600; margin-top: 10px; display: inline-block;}}
div[data-testid="stExpander"] > summary p {{color: #2F4F4F !important; font-weight: 600;}}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {{color: #333 !important;}}
</style>
""", unsafe_allow_html=True)

TUM_KATEGORILER = sorted(["Aperatif", "Atıştırmalık", "Bakliyat", "Balık & Deniz Ürünleri", "Çorba", "Dolma", "Etli Yemek", "Glutensiz", "Hamurişi", "Kahvaltılık", "Kebap", "Kızartma", "Köfte", "Makarna", "Meze", "Pilav", "Pratik", "Salata", "Sandviç", "Sebze", "Sokak Lezzetleri", "Sos", "Sulu Yemek", "Tatlı", "Tavuklu Yemek", "Vegan", "Vejetaryen", "Zeytinyağlı"])
CATEGORIZED_INGREDIENTS = { "Temel Gıdalar": ["Un", "Pirinç", "Bulgur", "Makarna", "Şeker", "Tuz", "Sıvı yağ", "Zeytinyağı", "Salça", "Sirke", "Maya"], "Süt & Süt Ürünleri": ["Süt", "Yoğurt", "Peynir", "Beyaz peynir", "Kaşar peyniri", "Lor peyniri", "Krema", "Tereyağı", "Yumurta"], "Et, Tavuk & Balık": ["Kıyma", "Kuşbaşı et", "Tavuk", "Sucuk", "Sosis", "Balık"], "Sebzeler": ["Soğan", "Sarımsak", "Domates", "Biber", "Patates", "Havuç", "Patlıcan", "Kabak", "Ispanak", "Marul", "Salatalık", "Limon", "Mantar"], "Bakliyat": ["Mercimek", "Nohut", "Fasulye", "Yeşil mercimek"], "Meyveler": ["Elma", "Muz", "Çilek", "Portakal"], "Kuruyemiş & Tatlı": ["Ceviz", "Fındık", "Badem", "Çikolata", "Kakao", "Bal", "Pekmez", "Vanilya"], "Baharatlar": ["Karabiber", "Nane", "Kekik", "Pul biber", "Kimyon", "Tarçın"] }

# --- VERİTABANI BAĞLANTISI (GOOGLE SHEETS) ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    worksheet = spreadsheet.worksheet("Sayfa1")
except Exception as e:
    st.error(f"Google E-Tablosu'na bağlanırken bir hata oluştu: {e}")
    st.info("`.streamlit/secrets.toml` dosyanızı, E-Tablo paylaşım ayarlarınızı ve Google Cloud projenizdeki API'lerin (Sheets ve Drive) etkin olduğunu kontrol edin.")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=10)
def fetch_all_recipes():
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df = df[df['id'] != ''].copy()
    return df

def get_instagram_thumbnail(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1',
            'accept-language': 'en-US,en;q=0.9'
        }
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_text = response.text
        
        script_tag = re.search(r'<script type="application/ld\+json">(.+?)</script>', html_text)
        if script_tag:
            json_data = json.loads(script_tag.group(1))
            thumbnail_url = json_data.get('thumbnailUrl') or json_data.get('image')
            if thumbnail_url:
                return thumbnail_url

        soup = BeautifulSoup(html_text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        if meta_tag and meta_tag.get('content'):
            return meta_tag['content']
            
        shared_data_script = re.search(r'window\._sharedData\s*=\s*(.*?);</script>', html_text)
        if shared_data_script:
            shared_data = json.loads(shared_data_script.group(1))
            media = shared_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
            thumbnail_url = media.get('display_url')
            if thumbnail_url:
                return thumbnail_url

    except Exception as e:
        st.error(f"Veri çekme sırasında bir hata oluştu. Hata: {e}")
        return None

    st.warning(f"Bu linkten kapak fotoğrafı otomatik olarak alınamadı. Link doğruysa, Instagram'ın güvenlik önlemleri engellemiş olabilir.")
    return None

def refresh_all_thumbnails():
    st.info("Eski tariflerin kapak fotoğrafları yenileniyor... Bu işlem yavaşlatılmıştır ve biraz zaman alabilir.")
    worksheet_data = worksheet.get_all_values()
    header = worksheet_data[0]
    try:
        url_col_index = header.index('url') + 1
        thumbnail_col_index = header.index('thumbnail_url') + 1
    except ValueError:
        st.error("'url' veya 'thumbnail_url' sütunları E-Tabloda bulunamadı!")
        return

    updated_count = 0
    for i in range(2, len(worksheet_data) + 1):
        row = worksheet_data[i-1]
        original_post_url = row[url_col_index - 1]
        if original_post_url:
            try:
                st.write(f"{i-1}. satırdaki tarif yenileniyor: {original_post_url}")
                new_thumbnail_url = get_instagram_thumbnail(original_post_url)
                if new_thumbnail_url:
                    worksheet.update_cell(i, thumbnail_col_index, new_thumbnail_url)
                    updated_count += 1
                    st.write(f"✅ Başarılı! Yeni kapak fotoğrafı bulundu.")
                    time.sleep(1.1)
                else:
                    st.write(f"❌ Bu link için yeni kapak fotoğrafı bulunamadı.")
            except Exception as e:
                st.warning(f"{i-1}. satır işlenirken bir hata oluştu: {e}")

    st.success(f"Yenileme tamamlandı! Toplam {updated_count} adet tarifin kapak fotoğrafı güncellendi.")
    st.cache_data.clear()
    st.rerun()

def display_recipe_cards(df):
    if df.empty:
        st.warning("Bu kriterlere uygun tarif bulunamadı.")
        return
    st.markdown(f"**{len(df)}** adet tarif bulundu.")
    st.write("")
    cols = st.columns(4)
    recipes_list = df.to_dict('records')
    for i, recipe in enumerate(reversed(recipes_list)):
        if pd.notna(recipe.get('thumbnail_url')) and recipe.get('thumbnail_url'):
            col = cols[i % 4]
            with col:
                st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
                st.markdown(f"""<a href="{recipe['url']}" target="_blank"><img src="{recipe['thumbnail_url']}" class="card-image"/></a>""", unsafe_allow_html=True)
                with st.container():
                    st.markdown(f"""<div class="card-body"><h3>{html.escape(str(recipe.get('baslik','')))}</h3><div class="category-badge">{html.escape(str(recipe.get('kategori','')))}</div></div>""", unsafe_allow_html=True)
                    with st.expander("Detayları Gör"):
                        st.markdown("---")
                        st.markdown("<h5>Malzemeler</h5>", unsafe_allow_html=True)
                        st.text(recipe.get('malzemeler') if pd.notna(recipe.get('malzemeler')) else "Eklenmemiş")
                        st.markdown("---")
                        st.markdown("<h5>Yapılışı</h5>", unsafe_allow_html=True)
                        st.write(recipe.get('yapilisi') if pd.notna(recipe.get('yapilisi')) else "Eklenmemiş")
                        st.markdown("---")
                        btn_cols = st.columns(2)
                        with btn_cols[0]:
                            if st.button("✏️ Düzenle", key=f"edit_{recipe['id']}", use_container_width=True):
                                st.session_state.recipe_to_edit_id = recipe['id']
                                st.rerun()
                        with btn_cols[1]:
                            if st.button("❌ Sil", key=f"delete_{recipe['id']}", use_container_width=True):
                                try:
                                    cell = worksheet.find(str(recipe['id']))
                                    worksheet.delete_rows(cell.row)
                                    st.cache_data.clear()
                                    st.rerun()
                                except gspread.CellNotFound:
                                    st.error("Tarif bulunamadı, sayfa yenileniyor.")
                                    st.cache_data.clear()
                                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- ANA UYGULAMA AKIŞI ---

if 'recipe_to_edit_id' not in st.session_state:
    st.session_state.recipe_to_edit_id = None

# Session state ile karşılama ekranını kontrol et
if 'show_main_app' not in st.session_state:
    st.session_state.show_main_app = False

# Eğer ana uygulama henüz gösterilmiyorsa, karşılama ekranını göster
if not st.session_state.show_main_app:
    st.markdown("<div style='text-align: center; margin-top: 5rem;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 5rem; font-family: \"Dancing Script\", cursive;'>Ceren'in Defteri</h1>", unsafe_allow_html=True)
    st.markdown("<h2>🌸 Lezzetli Anılara Hoş Geldin! 🌸</h2>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("✨ Defteri Aç ✨", use_container_width=True):
            st.session_state.show_main_app = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Eğer "Defteri Aç" butonuna basıldıysa, ana uygulamayı göster
else:
    if st.session_state.recipe_to_edit_id is not None:
        all_recipes_df = fetch_all_recipes()
        recipe_details_list = all_recipes_df[all_recipes_df['id'].astype(str) == str(st.session_state.recipe_to_edit_id)].to_dict('records')
        if recipe_details_list:
            recipe_details = recipe_details_list[0]
            st.markdown(f"## ✏️ Tarifi Düzenle: *{recipe_details['baslik']}*")
            with st.form("edit_main_form"):
                edit_baslik = st.text_input("Tarif Başlığı", value=recipe_details['baslik'])
                edit_kategori = st.selectbox("Kategori", TUM_KATEGORILER, index=TUM_KATEGORILER.index(recipe_details['kategori']) if recipe_details['kategori'] in TUM_KATEGORILER else 0)
                edit_malzemeler = st.text_area("Malzemeler", value=recipe_details['malzemeler'], height=200)
                edit_yapilisi = st.text_area("Yapılışı", value=recipe_details['yapilisi'], height=200)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Değişiklikleri Kaydet", use_container_width=True):
                        try:
                            cell = worksheet.find(str(st.session_state.recipe_to_edit_id))
                            worksheet.update_cell(cell.row, 3, edit_baslik)
                            worksheet.update_cell(cell.row, 4, edit_yapilisi)
                            worksheet.update_cell(cell.row, 5, edit_malzemeler)
                            worksheet.update_cell(cell.row, 6, edit_kategori)
                            st.success(f"Tarif güncellendi!")
                            st.session_state.recipe_to_edit_id = None
                            st.cache_data.clear()
                            st.rerun()
                        except gspread.CellNotFound:
                            st.error("Tarif bulunamadı, sayfa yenileniyor.")
                            st.session_state.recipe_to_edit_id = None
                            st.cache_data.clear()
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ İptal", use_container_width=True):
                        st.session_state.recipe_to_edit_id = None
                        st.rerun()
    else:
        st.markdown("<h1 style='font-family: \"Dancing Script\", cursive;'>🌸Ceren'in Defteri🌸</h1>", unsafe_allow_html=True)
        selected_page = option_menu(
            menu_title=None,
            options=["Tüm Tarifler", "Ne Pişirsem?", "Yeni Tarif Ekle"],
            icons=['card-list', 'lightbulb', 'plus-circle'],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"border-bottom": "2px solid #eee", "padding-bottom": "10px", "background-color": "transparent"},
                "nav-link": {"font-family": "'Quicksand', sans-serif", "font-weight": "600"},
                "nav-link-selected": {"background-color": "#FAE3FF", "color": "#B980F0"},
            }
        )

        if selected_page == "Tüm Tarifler":
            st.markdown("<h2>Tüm Tarifler</h2>", unsafe_allow_html=True)
            if st.button("Eski Kapak Fotoğraflarını Yenile"):
                refresh_all_thumbnails()
            all_recipes_df = fetch_all_recipes()
            selected_category = st.selectbox("Kategoriye göre filtrele:", ["Tümü"] + TUM_KATEGORILER)
            if selected_category != "Tümü":
                filtered_df = all_recipes_df[all_recipes_df['kategori'] == selected_category]
            else:
                filtered_df = all_recipes_df
            display_recipe_cards(filtered_df)
        
        elif selected_page == "Ne Pişirsem?":
            st.markdown("<h2>Ne Pişirsem?</h2>", unsafe_allow_html=True)
            st.markdown("### Elinizdeki malzemeleri seçin, size uygun tarifleri bulalım!")
            selected_ingredients = []
            categories = list(CATEGORIZED_INGREDIENTS.keys())
            num_columns = 4
            cols = st.columns(num_columns)
            for i, category_name in enumerate(categories):
                column = cols[i % num_columns]
                with column:
                    st.markdown(f"<h5>{category_name}</h5>", unsafe_allow_html=True)
                    for ingredient in CATEGORIZED_INGREDIENTS[category_name]:
                        if st.checkbox(ingredient, key=f"ing_{ingredient}"):
                            selected_ingredients.append(ingredient)
            st.markdown("---")
            if selected_ingredients:
                st.write("**Seçilen Malzemeler:**", ", ".join(selected_ingredients))
                all_recipes_df = fetch_all_recipes()
                filtered_list = []
                for index, row in all_recipes_df.iterrows():
                    recipe_ingredients_lower = str(row.get('malzemeler','')).lower()
                    if all(malzeme.lower() in recipe_ingredients_lower for malzeme in selected_ingredients):
                        filtered_list.append(row)
                if filtered_list:
                    display_recipe_cards(pd.DataFrame(filtered_list))
                else:
                    st.warning("Bu malzemelerle eşleşen tarif bulunamadı.")
            else:
                st.info("Sonuçları görmek için yukarıdaki listelerden malzeme seçin.")

        elif selected_page == "Yeni Tarif Ekle":
            lottie_cooking_url = "https://lottie.host/eda719a7-2483-4d7a-85b3-3a9a14732168/vSDb8x9LVZ.json"
            lottie_cooking_json = load_lottieurl(lottie_cooking_url)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                if lottie_cooking_json:
                    st_lottie(lottie_cooking_json, speed=1, height=200, key="cooking")
            with col2:
                st.markdown("<h2 style='padding-top: 50px;'>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)

            with st.form("new_recipe_page_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    insta_url = st.text_input("Instagram Reel Linki")
                    tarif_basligi = st.text_input("Tarif Başlığı")
                    kategori = st.selectbox("Kategori", TUM_KATEGORILER)
                with col2:
                    malzemeler = st.text_area("Malzemeler (Her satıra bir tane)", height=200)
                yapilisi = st.text_area("Yapılışı (Açıklama)", height=200)
                submitted_add = st.form_submit_button("✨ Tarifi Kaydet", use_container_width=True)
                if submitted_add:
                    if insta_url and tarif_basligi:
                        with st.spinner("İşleniyor..."):
                            thumbnail_url = get_instagram_thumbnail(insta_url)
                            if thumbnail_url:
                                new_row = [datetime.now().strftime("%Y%m%d%H%M%S"), insta_url, tarif_basligi, yapilisi, malzemeler, kategori, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), thumbnail_url]
                                worksheet.append_row(new_row, value_input_option='USER_ENTERED')
                                st.cache_data.clear()
                                st.success("Tarif başarıyla kaydedildi! 'Tüm Tarifler' sekmesinden görebilirsiniz.")
                            else:
                                st.error("Bu linkten kapak fotoğrafı alınamadı.")
                    else:
                        st.warning("Lütfen en azından Link ve Başlık alanlarını doldurun.")