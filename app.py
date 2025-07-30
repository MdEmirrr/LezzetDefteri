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
TUM_KATEGORILER = sorted(["Aperatif", "Atıştırmalık", "Bakliyat", "Balık & Deniz Ürünleri", "Çorba", "Dolma", "Et", "Glutensiz", "Hamurişi", "Kahvaltılık", "Kebap", "Kızartma", "Köfte", "Makarna", "Meze", "Pilav", "Pratik", "Salata", "Sandviç", "Sebze",  "Sos",  "Tatlı", "Tavuk", "Pizza", "İçecek",  ])
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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find('meta', property='og:image')
        return meta_tag['content'] if meta_tag else None
    except requests.exceptions.RequestException:
        return None

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
                st.markdown(
                     f"""<a href="{recipe['url']}" target="_blank">
                            <img src="{recipe['thumbnail_url']}" class="card-image"/>
                        </a>""",
                     unsafe_allow_html=True,
                 )
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

# --- ANA UYGULAMA AKIŞI ---
if 'recipe_to_edit_id' not in st.session_state:
    st.session_state.recipe_to_edit_id = None
st.markdown("<h1 style='font-family: \"Dancing Script\", cursive;'>🌸Ceren'in Defteri🌸</h1>", unsafe_allow_html=True)

selected_page = option_menu(
    menu_title=None,
    options=["Tüm Tarifler", "Ne Pişirsem?", "Yeni Tarif Ekle"],
    icons=['card-list', 'lightbulb', 'plus-circle'],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={ "container": {"border-bottom": "2px solid #eee", "padding-bottom": "10px"}, "nav-link": {"font-family": "'Quicksand', sans-serif", "font-weight":"600"}, "nav-link-selected": {"background-color": "#D1E7DD", "color": "#2F4F4F"}, }
)

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
    if selected_page == "Tüm Tarifler":
        st.markdown("<h2>Tüm Tarifler</h2>", unsafe_allow_html=True)
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
        st.markdown("<h2>Yeni Bir Tarif Ekle</h2>", unsafe_allow_html=True)
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