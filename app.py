import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SRAL Disiplin Takip", page_icon="🛡️")

# --- GOOGLE SHEETS BAĞLANTISI ---
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"]).sheet1

# --- ÖĞRENCİ VERİSİNİ YÜKLE ---
@st.cache_data
def load_students():
    # Excel'i oku ve sütun isimlerindeki boşlukları temizle
    data = pd.read_excel("ogrenciler.xlsx")
    data.columns = [str(c).strip() for c in data.columns]
    return data

try:
    df = load_students()
except Exception as e:
    st.error(f"Excel dosyası okunamadı: {e}")
    st.stop()

# --- ARAYÜZ ---
st.title("🛡️ SRAL Disiplin Takip")

with st.sidebar:
    st.header("⚙️ Giriş Yapan")
    ogretmen_ad = st.text_input("Öğretmen Ad Soyad")
    ders_saati = st.selectbox("Ders Saati", list(range(1, 10)))

st.subheader("🔍 Öğrenci Sorgula")
# Numarayı metin olarak alıyoruz (bazı Excel'lerde sayı, bazılarında metin olduğu için en güvenlisi)
ogr_no_input = st.text_input("Öğrenci Numarasını Yazın ve Enter'a Basın")

if ogr_no_input:
    # Numarayı Excel'de ara (Sütun adının 'Öğrenci No' olduğunu varsayıyoruz)
    # Eğer Excel'de sadece 'No' yazıyorsa aşağıdaki kısmı ['No'] yapın
    ogrenci_res = df[df['Öğrenci No'].astype(str) == str(ogr_no_input)]
    
    if not ogrenci_res.empty:
        # Excel'deki 'Ad Soyad' ve 'Sınıf' sütunlarını al
        ad_soyad = ogrenci_res.iloc[0]['Ad Soyad']
        sinif = ogrenci_res.iloc[0]['Sınıf']
        
        st.success(f"👤 **{ad_soyad}** | 🏫 **{sinif}**")
        
        # 4 ANA BAŞLIKLI İHLAL SEÇİMİ
        ihlaller = st.multiselect(
            "İhlal Türlerini Seçiniz (Birden fazla seçilebilir):",
            ["Saç-Sakal", "Kıyafet", "Makyaj", "Takı"]
        )
        notlar = st.text_input("Ek Not:")
        
        if st.button("SİSTEME KAYDET"):
            if not ogretmen_ad:
                st.error("Lütfen önce adınızı girin!")
            elif not ihlaller:
                st.error("En az bir ihlal seçmelisiniz!")
            else:
                try:
                    sheet = connect_to_gsheet()
                    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
                    # Veriyi Google Sheets'e gönder
                    sheet.append_row([
                        tarih, ogretmen_ad, ders_saati, ogr_no_input, ad_soyad, sinif, ", ".join(ihlaller), notlar
                    ])
                    st.balloons()
                    st.success("Veri başarıyla Google Tabloya işlendi.")
                except Exception as e:
                    st.error(f"Kayıt sırasında hata oluştu: {e}")
    else:
        st.error("❌ Bu numaralı bir öğrenci bulunamadı. Lütfen Excel dosyanızı kontrol edin.")
