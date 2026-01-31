import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SRAL Disiplin Takip", page_icon="🛡️")

def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"]).sheet1

@st.cache_data
def load_students():
    # Excel'i oku ve başlıkları temizle
    data = pd.read_excel("ogrenciler.xlsx")
    # Sütun isimlerinin başındaki ve sonundaki boşlukları temizle
    data.columns = [str(c).strip() for c in data.columns]
    return data

try:
    df = load_students()
except Exception as e:
    st.error(f"Excel dosyası okunamadı: {e}")
    st.stop()

st.title("🛡️ SRAL Disiplin Takip")

with st.sidebar:
    st.header("⚙️ Giriş Yapan")
    ogretmen_ad = st.text_input("Öğretmen Ad Soyad")
    ders_saati = st.selectbox("Ders Saati", list(range(1, 10)))

st.subheader("🔍 Öğrenci Sorgula")
ogr_no_input = st.text_input("Öğrenci Numarasını Yazın ve Enter'a Basın")

if ogr_no_input:
    # 1. ADIM: Numarayı bul (İçinde 'No' geçen sütun)
    no_col = [c for c in df.columns if 'No' in c][0]
    ogrenci_res = df[df[no_col].astype(str) == str(ogr_no_input)]
    
    if not ogrenci_res.empty:
        # 2. ADIM: İsim sütununu otomatik bul (İçinde 'Ad' geçen ilk sütun)
        # Bu kısım 'Ad Soyad', 'Adı Soyadı' veya 'Ad' sütununu otomatik yakalar
        try:
            name_col = [c for c in df.columns if 'Ad' in c][0]
            ad_soyad = ogrenci_res.iloc[0][name_col]
            
            # 3. ADIM: Sınıf sütununu otomatik bul
            class_col = [c for c in df.columns if 'Sınıf' in c or 'Şube' in c][0]
            sinif = ogrenci_res.iloc[0][class_col]
        except Exception:
            st.error("Excel'de 'Ad Soyad' veya 'Sınıf' sütunu bulunamadı!")
            st.stop()
        
        st.success(f"👤 **{ad_soyad}** | 🏫 **{sinif}**")
        
        ihlaller = st.multiselect(
            "İhlal Türlerini Seçiniz:",
            ["Saç-Sakal", "Kıyafet", "Makyaj", "Takı"]
        )
        notlar = st.text_input("Ek Not:")
        
        if st.button("SİSTEME KAYDET"):
            if not ogretmen_ad:
                st.error("Lütfen adınızı girin!")
            elif not ihlaller:
                st.error("En az bir ihlal seçmelisiniz!")
            else:
                try:
                    sheet = connect_to_gsheet()
                    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
                    sheet.append_row([
                        tarih, ogretmen_ad, ders_saati, ogr_no_input, ad_soyad, sinif, ", ".join(ihlaller), notlar
                    ])
                    st.balloons()
                    st.success("Veri başarıyla Google Tabloya işlendi.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
    else:
        st.error("❌ Bu numaralı bir öğrenci bulunamadı.")
