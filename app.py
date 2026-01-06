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

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Ceren'in Defteri", layout="wide", page_icon="🌸")

# --- CSS TASARIM (PROFESYONEL GÖRÜNÜM) ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

:root {{
    --primary-color: #8BC34A;
    --primary-hover: #7CB342;
    --bg-color: #FAFAF9;
    --card-bg: #FFFFFF;
    --text-main: #2C3E50;
    --text-sub: #7F8C8D;
    --shadow: 0 4px 20px rgba(0,0,0,0.06);
    --radius: 16px;
}}

.stApp {{ background-color: var(--bg-color); font-family: 'Plus Jakarta Sans', sans-serif; }}
div[data-testid="stAppViewContainer"] > .main {{ padding-top: 0rem; }}

/* HEADER */
header {{
    background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.1)), url("https://images.unsplash.com/photo-1490818387583-1baba5e638af?q=80&w=1932&auto=format&fit=crop");
    background-size: cover; background-position: center;
    padding: 3rem 1rem; text-align: center; margin-bottom: 2rem;
    border-radius: 0 0 24px 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}}
header h1 {{
    font-family: 'Dancing Script', cursive !important; color: white !important;
    font-size: 4.5rem; margin: 0; text-shadow: 0 4px 10px rgba(0,0,0,0.3);
}}
div[data-testid="stHeading"] {{ display: none; }}

/* SIDEBAR BUTONLARI */
.sidebar-btn {{
    width: 100%; border-radius: 12px; border: 2px solid var(--primary-color);
    background-color: white; color: var(--text-main); font-weight: 600;
    padding: 0.8rem; margin-bottom: 0.5rem; transition: all 0.3s;
    text-align: center; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
}}
.sidebar-btn:hover {{ background-color: var(--primary-color); color: white; transform: translateY(-2px); }}

/* KART TASARIMI */
.recipe-card-link {{ text-decoration: none; }}
.recipe-card {{ 
    background-color: var(--card-bg); border-radius: var(--radius);
    box-shadow: var(--shadow); border: 1px solid #F0F0F0;
    margin-bottom: 1.5rem; overflow: hidden; transition: all 0.3s ease;
    height: 420px; display: flex; flex-direction: column; 
}}
.recipe-card:hover {{ transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }}
.card-image {{ width: 100%; height: 250px; object-fit: cover; }}
.card-body {{ padding: 1.2rem; flex-grow: 1; display: flex; flex-direction: column; }}
.card-body h3 {{ 
    font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.1rem;
    color: var(--text-main); margin: 0 0 0.5rem 0; line-height: 1.4;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}}
.card-tag {{
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    background-color: #EEF7E8; color: var(--primary-color);
    font-size: 0.75rem; font-weight: 600; margin-bottom: 8px; width: fit-content;
}}
.card-metadata {{ 
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.85rem; color: var(--text-sub); margin-top: auto; padding-top: 1rem;
    border-top: 1px solid #F5F5F5;
}}

/* DETAY SAYFASI */
.detail-card {{ 
    padding: 2rem; background: white; border-radius: 24px; 
    box-shadow: var(--shadow); margin-bottom: 1rem;
}}
.detail-title {{ font-family: 'Dancing Script', cursive; font-size: 3.5rem; text-align: center; color: var(--text-main); }}

/* FORM ELEMANLARI */
.stTextInput>div>div>input, .stSelectbox>div>div, .stTextArea>div>div>textarea {{
    border-radius: 12px; border: 1px solid #E0E0E0; padding: 0.5rem;
}}
.stButton>button {{
    border-radius: 12px; font-weight: 600; padding: 0.5rem 2rem;
}}
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    
    if "spreadsheet_id" in st.secrets:
        spreadsheet = gc.open_by_key(st.secrets["spreadsheet_id"])
    else:
        spreadsheet = gc.open("Lezzet Defteri Veritabanı")
    
    worksheet_recipes = spreadsheet.worksheet("Sayfa1")
    
    try:
        worksheet_events = spreadsheet.worksheet("Etkinlikler")
    except:
        worksheet_events = None

except Exception as e:
    st.error(f"Veritabanı Bağlantı Hatası: {e}")
    st.stop()

# --- GELİŞMİŞ FOTOĞRAF ÇEKME (API DESTEKLİ) ---
def get_instagram_data_robust(link):
    """
    Önce RapidAPI'yi dener (Kesin çözüm), 
    Eğer API key yoksa veya bittiyse varsayılan resmi döndürür.
    """
    
    # 1. API Anahtarını Kontrol Et
    api_key = ""
    if "instagram" in st.secrets and "api_key" in st.secrets["instagram"]:
        api_key = st.secrets["instagram"]["api_key"]
    
    if not api_key:
        # API yoksa direkt varsayılan döndür, boşuna zaman harcama
        return None

    # 2. Linkten Shortcode'u al (p/ABC1234/ kısmını bulur)
    shortcode = None
    match = re.search(r'(?:p|reel|tv)/([A-Za-z0-9_-]+)', link)
    if match:
        shortcode = match.group(1)
    else:
        return None

    # 3. API'ye sor
    url = "https://instagram-scraper-2022.p.rapidapi.com/ig/post_details/"
    querystring = {"shortcode": shortcode}
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "instagram-scraper-2022.p.rapidapi.com"
    }

    try:
        # İstek at
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Fotoğrafı bulmaya çalış
            try:
                # Carousel (Kaydırmalı post) ise ilki
                if 'carousel_media' in data.get('data', {}):
                    return data['data']['carousel_media'][0]['image_versions2']['candidates'][0]['url']
                # Tekli post/reel ise
                else:
                    return data['data']['image_versions2']['candidates'][0]['url']
            except:
                pass
    except Exception:
        pass
    
    return None

def refresh_photos():
    """Tüm fotoğrafları yeniler (Hem tarif hem etkinlik)"""
    # İlerleme çubuğu
    progress_bar = st.progress(0)
    status = st.empty()
    status.info("Fotoğraflar taranıyor... Lütfen bekleyin.")
    
    # 1. Tarifler
    data = worksheet_recipes.get_all_records()
    head = [h.strip().lower() for h in worksheet_recipes.row_values(1)]
    thumb_idx = head.index('thumbnail_url') + 1
    
    count = 0
    total_ops = len(data)
    
    if worksheet_events:
        total_ops += len(worksheet_events.get_all_records())

    # Tarif Döngüsü
    for i, row in enumerate(data):
        # Sadece Instagram linki varsa ve fotoğraf yoksa veya eski linkse dene
        current_thumb = row.get('thumbnail_url', '')
        
        # Eğer fotoğraf yoksa veya link kırılmışsa (cdninstagram içeriyorsa genelde kırılır)
        if 'instagram.com' in row.get('url', ''):
            # API ile taze link al
            new_img = get_instagram_data_robust(row['url'])
            
            # Eğer API bulamazsa, şık bir varsayılan resim koyalım ki BOŞ GÖRÜNMESİN
            if not new_img:
               new_img = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000"
            
            # Her türlü güncelle (Kırık link yerine sağlam veya default gelsin)
            worksheet_recipes.update_cell(i + 2, thumb_idx, new_img)
            time.sleep(0.5) # API'yi boğmamak için bekleme

        progress_bar.progress((i+1) / (total_ops + 1))
        count += 1

    # 2. Etkinlikler
    if worksheet_events:
        data_ev = worksheet_events.get_all_records()
        head_ev = [h.strip().lower() for h in worksheet_events.row_values(1)]
        thumb_idx_ev = head_ev.index('thumbnail_url') + 1
        
        for j, row in enumerate(data_ev):
            if 'instagram.com' in row.get('url', ''):
                new_img = get_instagram_data_robust(row['url'])
                
                # Etkinlik için farklı varsayılan resim
                if not new_img:
                    new_img = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=1000"
                
                worksheet_events.update_cell(j + 2, thumb_idx_ev, new_img)
                time.sleep(0.5)
            
            # İlerlemeyi güncelle
            current_progress = (len(data) + j + 1) / (total_ops + 1)
            progress_bar.progress(min(current_progress, 1.0))
            
    status.success("İşlem Tamamlandı! Sayfa yenileniyor...")
    st.cache_data.clear()
    time.sleep(2)
    st.rerun()

# --- SIDEBAR TASARIMI ---
def build_sidebar():
    with st.sidebar:
        st.write("### 📌 Hızlı Ekle")
        
        c1, c2 = st.columns(2)
        add_recipe_clk = c1.button("🍳 Tarif", use_container_width=True, type="primary")
        add_event_clk = c2.button("🎉 Etkinlik", use_container_width=True, type="primary")
        
        if add_recipe_clk: st.session_state.page = "add_recipe"; st.rerun()
        if add_event_clk: st.session_state.page = "add_event"; st.rerun()

        st.write("---")
        st.write("### 🔍 Filtrele")
        
        # Sayfaya göre filtre göster
        df_r = fetch_data("recipes")
        df_e = fetch_data("events")
        
        search = st.text_input("Ara...", placeholder="Kek, Konser, İzmir...")
        
        filter_cat = []
        filter_time = (0, 120)
        
        # Eğer etkinlik sayfasındaysak etkinlik kategorileri, değilse yemek
        active_tab = st.session_state.get('active_tab', 'Tarifler')
        
        if active_tab == 'Tarifler' and not df_r.empty:
            cats = sorted(df_r['kategori'].unique())
            filter_cat = st.multiselect("Kategori", cats)
            min_t, max_t = int(df_r['hazirlanma_suresi'].min()), int(df_r['hazirlanma_suresi'].max())
            filter_time = st.slider("Süre (dk)", min_t, max_t if max_t > 0 else 120, (min_t, max_t if max_t > 0 else 120))
            
        elif active_tab == 'Etkinlikler' and not df_e.empty:
            cats = sorted(df_e['kategori'].unique())
            filter_cat = st.multiselect("Etkinlik Türü", cats)

        # Admin Paneli (En Altta)
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        with st.expander("⚙️ Yönetici & Ayarlar"):
            st.caption("Fotoğraflar görünmüyorsa yenileyin.")
            if st.button("🔄 Fotoğrafları Tamir Et", use_container_width=True):
                refresh_photos()

    return search, filter_cat, filter_time

# --- VERİ ÇEKME FONKSİYONLARI ---
@st.cache_data(ttl=600)
def fetch_data(sheet_type="recipes"):
    try:
        ws = worksheet_recipes if sheet_type == "recipes" else worksheet_events
        if not ws: return pd.DataFrame()
        
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty:
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            df = df[df['id'] != ''].copy()
            if 'hazirlanma_suresi' in df.columns:
                df['hazirlanma_suresi'] = pd.to_numeric(df['hazirlanma_suresi'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception: return pd.DataFrame()

# --- KART GÖSTERİMİ ---
def display_cards(df, type="recipe"):
    if df.empty:
        st.info("Henüz kayıt yok veya filtreye uygun sonuç bulunamadı.")
        return

    cols = st.columns(4)
    # Varsayılan görseller
    def_img_recipe = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000"
    def_img_event = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=1000"
    
    default_img = def_img_recipe if type == "recipe" else def_img_event

    for i, row in enumerate(df.to_dict('records')):
        with cols[i % 4]:
            img = row.get('thumbnail_url')
            # Eğer resim hücresi boşsa varsayılanı kullan
            if not img: img = default_img
            
            title = html.escape(str(row.get('baslik', '')).title())
            
            # Kart Detayları
            if type == "recipe":
                meta = f"""
                <span>⏱️ {row.get('hazirlanma_suresi',0)} dk</span>
                <span>🔥 {row.get('yemek_zorlugu','N/A')}</span>
                """
                badge = row.get('kategori', 'Genel')
            else:
                meta = f"""
                <span>📍 {row.get('konum','Unknown')}</span>
                <span>⭐ {row.get('puan','-')}/10</span>
                """
                badge = row.get('kategori', 'Etkinlik')

            st.markdown(f"""
            <a href="/?id={row['id']}&type={type}" target="_self" class="recipe-card-link">
                <div class="recipe-card">
                    <img src="{img}" class="card-image" onerror="this.src='{default_img}'">
                    <div class="card-body">
                        <div class="card-tag">{badge}</div>
                        <h3>{title}</h3>
                        <div class="card-metadata">{meta}</div>
                    </div>
                </div>
            </a>
            """, unsafe_allow_html=True)

# --- DETAY SAYFALARI ---
def show_detail(id, type):
    df = fetch_data("recipes" if type == "recipe" else "events")
    row = df[df['id'].astype(str) == str(id)].iloc[0]
    
    if st.button("⬅️ Geri Dön"): st.query_params.clear(); st.rerun()
    
    st.markdown(f"<div class='detail-title'>{row['baslik'].title()}</div>", unsafe_allow_html=True)
    
    # Detay sayfası varsayılan resimleri
    def_img = "https://images.unsplash.com/photo-1495521821757-a1efb6729352?q=80&w=1000"
    img_src = row.get('thumbnail_url', '')
    if not img_src: img_src = def_img
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.image(img_src, use_column_width=True)
        st.markdown(f"### 🔗 [Instagram'da Görüntüle]({row['url']})")
        
        if type == "recipe":
            st.info(f"⏱️ Süre: {row['hazirlanma_suresi']} dk | 🔥 Zorluk: {row['yemek_zorlugu']}")
        else:
            st.info(f"📍 Konum: {row['konum']} | ⭐ Puan: {row['puan']}/10")
            
    with col2:
        st.markdown("### 📝 Detaylar")
        if type == "recipe":
            st.markdown(f"**Malzemeler:**\n{row['malzemeler']}")
            st.markdown("---")
            st.markdown(f"**Yapılışı:**\n{row['yapilisi']}")
        else:
            st.markdown(row['aciklama'])
            st.markdown(f"**🗓️ Tarih:** {row.get('tarih', '-')}")

    # SİLME BUTONU
    st.write("---")
    with st.expander("🔴 Kaydı Sil"):
        if st.button("Evet, Sil", type="primary"):
            ws = worksheet_recipes if type == "recipe" else worksheet_events
            cell = ws.find(str(id))
            ws.delete_rows(cell.row)
            st.cache_data.clear()
            st.success("Silindi!"); time.sleep(1); st.query_params.clear(); st.rerun()

# --- EKLEME SAYFALARI ---
def page_add_recipe():
    st.markdown("## 🍳 Yeni Tarif Ekle")
    with st.form("add_recipe"):
        c1, c2 = st.columns(2)
        with c1:
            url = st.text_input("Instagram Linki")
            baslik = st.text_input("Başlık")
            kat = st.selectbox("Kategori", ["Ana Yemek", "Tatlı", "Kahvaltılık", "Çorba", "Salata", "Atıştırmalık"])
            zorluk = st.select_slider("Zorluk", ["Basit", "Orta", "Zor"])
            sure = st.number_input("Süre (dk)", 30)
        with c2:
            malz = st.text_area("Malzemeler", height=150)
            yap = st.text_area("Yapılışı", height=150)
        
        if st.form_submit_button("Kaydet", use_container_width=True):
            if not url or not baslik: st.warning("Link ve Başlık zorunludur."); return
            
            with st.spinner("Kaydediliyor..."):
                img = get_instagram_data_robust(url) or "https://images.unsplash.com/photo-1495521821757-a1efb6729352"
                row = [datetime.now().strftime("%Y%m%d%H%M%S"), url, baslik, yap, malz, kat, datetime.now().strftime("%Y-%m-%d"), img, zorluk, sure, "HAYIR"]
                worksheet_recipes.append_row(row)
                st.cache_data.clear(); st.success("Eklendi!"); time.sleep(1); st.session_state.page="home"; st.rerun()

def page_add_event():
    if not worksheet_events:
        st.error("⚠️ Google Sheet dosyanızda 'Etkinlikler' sayfası bulunamadı. Lütfen oluşturun.")
        return

    st.markdown("## 🎉 Yeni Etkinlik / Mekan Ekle")
    with st.form("add_event"):
        c1, c2 = st.columns(2)
        with c1:
            url = st.text_input("Instagram Linki (Reel/Post)")
            baslik = st.text_input("Etkinlik/Mekan Adı")
            konum = st.text_input("Konum (Semt/Şehir)")
            kat = st.selectbox("Tür", ["Mekan Keşfi", "Konser", "Gezi", "Tiyatro", "Sergi", "Diğer"])
        with c2:
            aciklama = st.text_area("Açıklama / Notlar", height=150)
            puan = st.slider("Puanım", 1, 10, 8)
            tarih_inp = st.date_input("Gidilen Tarih")
        
        if st.form_submit_button("Kaydet", use_container_width=True):
            if not url or not baslik: st.warning("Link ve Başlık zorunludur."); return
            
            with st.spinner("Kaydediliyor..."):
                img = get_instagram_data_robust(url) or "https://images.unsplash.com/photo-1492684223066-81342ee5ff30"
                row = [datetime.now().strftime("%Y%m%d%H%M%S"), url, baslik, aciklama, konum, kat, str(tarih_inp), img, puan]
                worksheet_events.append_row(row)
                st.cache_data.clear(); st.success("Eklendi!"); time.sleep(1); st.session_state.page="home"; st.rerun()

# --- ANA UYGULAMA ---
def main():
    if 'page' not in st.session_state: st.session_state.page = "home"
    
    # Query Params Kontrolü (Linkten geliyorsa)
    qp = st.query_params
    if "id" in qp and "type" in qp:
        show_detail(qp["id"], qp["type"])
        return

    # Sayfa Yönlendirmeleri
    if st.session_state.page == "add_recipe":
        if st.button("⬅️ İptal"): st.session_state.page = "home"; st.rerun()
        page_add_recipe()
        return
    elif st.session_state.page == "add_event":
        if st.button("⬅️ İptal"): st.session_state.page = "home"; st.rerun()
        page_add_event()
        return

    # Ana Sayfa Akışı
    st.markdown("<header><h1>Ceren'in Defteri</h1></header>", unsafe_allow_html=True)
    
    # Menü ve Filtreler
    search, f_cat, f_time = build_sidebar()
    
    selected = option_menu(None, ["Tarifler", "Etkinlikler", "Favoriler"], 
        icons=['egg-fried', 'ticket-perforated', 'star'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={"nav-link-selected": {"background-color": "#8BC34A"}})
    
    st.session_state.active_tab = selected # Filtreler için aktif sekmeyi kaydet

    if selected == "Tarifler":
        df = fetch_data("recipes")
        if not df.empty:
            if search: df = df[df['baslik'].str.contains(search, case=False, na=False)]
            if f_cat: df = df[df['kategori'].isin(f_cat)]
            df = df[df['hazirlanma_suresi'].between(f_time[0], f_time[1])]
            display_cards(df.sort_values('id', ascending=False), "recipe")
            
    elif selected == "Etkinlikler":
        if not worksheet_events:
            st.warning("Henüz etkinlik veritabanı oluşturulmamış. Google Sheet'te 'Etkinlikler' sayfasını açın.")
        else:
            df = fetch_data("events")
            if not df.empty:
                if search: df = df[df['baslik'].str.contains(search, case=False, na=False)]
                if f_cat: df = df[df['kategori'].isin(f_cat)]
                display_cards(df.sort_values('id', ascending=False), "event")
            else:
                st.info("Henüz hiç etkinlik eklenmemiş. Yanda '🎉 Etkinlik' butonuna basarak ekle!")
                
    elif selected == "Favoriler":
        df = fetch_data("recipes")
        if not df.empty:
            favs = df[df['favori'] == 'EVET']
            display_cards(favs, "recipe")

if __name__ == "__main__":
    main()
