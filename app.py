import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SRAL Disiplin Takip", page_icon="📝", layout="centered")

# --- GOOGLE SHEETS BAĞLANTISI ---
def connect_to_gsheet():
    # Streamlit Secrets üzerinden bağlantı bilgilerini alıyoruz
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Secrets içine yazdığınız Sheet ID ile dosyayı açar
    return client.open_by_key(st.secrets["sheet_id"]).sheet1

# --- ÖĞRENCİ VERİSİNİ YÜKLE (Dosya 2) ---
@st.cache_data
def load_students():
    return pd.read_excel("ogrenciler.xlsx")

try:
    df_ogrenci = load_students()
except Exception as e:
    st.error("Hata: 'ogrenciler.xlsx' dosyası bulunamadı!")
    st.stop()

# --- ARAYÜZ BAŞLANGIÇ ---
st.title("🛡️ SRAL Disiplin Takip Sistemi")
st.info("Öğretmenler için hızlı kılık-kıyafet ve ihlal kayıt ekranı.")

# --- YAN MENÜ (ÖĞRETMEN BİLGİLERİ) ---
with st.sidebar:
    st.header("⚙️ Sorumlu Girişi")
    ogretmen_ad = st.text_input("Adınız Soyadınız", placeholder="Örn: Ahmet Yılmaz")
    ders_saati = st.selectbox("Ders Saati", [1, 2, 3, 4, 5, 6, 7, 8])
    st.divider()
    st.write("v1.0 - Sıdıka Rodop Anadolu Lisesi")

# --- ANA EKRAN (GİRİŞ ALANI) ---
st.subheader("🔍 Öğrenci Sorgulama")
ogr_no = st.number_input("Öğrenci Numarasını Giriniz", min_value=1, step=1, value=None)

if ogr_no:
    # Numaraya göre öğrenciyi bul
    ogrenci_res = df_ogrenci[df_ogrenci['Öğrenci No'] == ogr_no]
    
    if not ogrenci_res.empty:
        ad_soyad = ogrenci_res.iloc[0]['Ad Soyad']
        sinif = ogrenci_res.iloc[0]['Sınıf']
        
        # Bilgileri ekrana yazdır
        st.success(f"✅ **Öğrenci:** {ad_soyad} | **Sınıf:** {sinif}")
        
        # İhlal detayları
        ihlal_turleri = st.multiselect(
            "Yapılan İhlalleri Seçiniz:",
            ["Kılık Kıyafet (Serbest Kıyafet)", "Saç-Sakal İhlali", "Takı-Aksesuar", "Makyaj/Oje", "Geç Kalma", "Diğer"]
        )
        notlar = st.text_input("Varsa ek notunuz:")
        
        # KAYDET BUTONU
        if st.button("KAYDI TAMAMLA VE GÖNDER"):
            if not ogretmen_ad:
                st.warning("Lütfen önce sol menüden adınızı giriniz!")
            elif not ihlal_turleri:
                st.warning("En az bir ihlal seçmelisiniz!")
            else:
                with st.spinner("Veri işleniyor..."):
                    try:
                        sheet = connect_to_gsheet()
                        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
                        # Google Sheets'e yeni satır ekle
                        sheet.append_row([
                            tarih, ogretmen_ad, ders_saati, ogr_no, ad_soyad, sinif, ", ".join(ihlal_turleri), notlar
                        ])
                        st.balloons()
                        st.success(f"{ad_soyad} için kayıt başarıyla oluşturuldu.")
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")
    else:
        st.error("❌ Bu numaralı bir öğrenci listede bulunamadı!")

# --- İDARE RAPORLAMA ---
st.divider()
if st.checkbox("📊 İdare Paneli (Rapor Al)"):
    admin_pass = st.text_input("Yetkili Şifresi", type="password")
    if admin_pass == "sral2024": # Bu şifreyi kendinize göre değiştirebilirsiniz
        try:
            sheet = connect_to_gsheet()
            data = pd.DataFrame(sheet.get_all_records())
            
            st.write("### Haftalık İhlal Özet Listesi")
            st.dataframe(data)
            
            # Limit aşımı analizi
            limit = st.slider("İhlal Sayısı Limiti", 1, 10, 3)
            counts = data['Ad Soyad'].value_counts()
            limit_asanlar = counts[counts >= limit]
            
            st.warning(f"⚠️ **{limit} ve Üzeri İhlal Yapan Öğrenciler:**")
            st.write(limit_asanlar)
        except:
            st.info("Henüz sistemde kayıtlı veri yok.")
