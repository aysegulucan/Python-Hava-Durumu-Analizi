import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import sys
import io
import matplotlib.dates as mdates
import calendar # Ayları isimlendirmek için eklendi

# --- 0. RAPORLAMA (LOGGING) SİSTEMİNİ AYARLAMA ---
log_dosyasi = "hava_durumu_raporu.txt"

# Eski logger'ları temizle
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Yeni, "insan okuyacak" seviyede logger'ı ayarla
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Sadece mesajı bas
    encoding='utf-8',
    handlers=[
        logging.FileHandler(log_dosyasi, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Ekrana da bas
    ]
)

logging.info("="*60)
logging.info("--- HAVA DURUMU VERİ ANALİZİ RAPORU (MÜNİH) ---")
logging.info("="*60)
logging.info(f"Rapor Dosyası: {log_dosyasi}\n")

try:
    # --- AŞAMA 1: VERİ YÜKLEME VE HAZIRLIK ---
    logging.info("--- AŞAMA 1: VERİ YÜKLEME VE HAZIRLIK ---")
    
    # 1.1: Veriyi Yükle
    # Bu kod, 'munich.csv' dosyasının script ile aynı klasörde olmasını bekler.
    veri_dosyasi = "munich.csv"
    try:
        df = pd.read_csv(veri_dosyasi, delimiter=';')
    except FileNotFoundError:
        logging.error(f"[HATA] '{veri_dosyasi}' dosyası bulunamadı.")
        logging.error("Lütfen 'munich.csv' dosyasının script ile aynı klasörde olduğundan emin olun.")
        sys.exit()

    logging.info(f"Başarılı: '{veri_dosyasi}' yüklendi.")

    # 1.2: Sütun Adlarını Temizle
    df.columns = ['time', 'precipitation_mm', 'snowfall_cm']
    logging.info("Başarılı: Sütun adları temizlendi (örn: 'time', 'precipitation_mm').")

    # 1.3: Tarih Formatını Düzelt
    df['time'] = pd.to_datetime(df['time'])
    logging.info("Başarılı: 'time' sütunu tarih formatına çevrildi.")

    # 1.4: Eksik Verileri Temizle
    original_rows = len(df)
    # Sadece yağış verisi (ana analiz konumuz) boş olanları at
    df = df.dropna(subset=['precipitation_mm']) 
    cleaned_rows = len(df)
    logging.info(f"Başarılı: Eksik veriler ({original_rows - cleaned_rows} satır) temizlendi.")
    logging.info(f"Analiz edilecek {cleaned_rows} geçerli veri satırı kaldı.")


    # --- AŞAMA 2: KEŞİFSEL VERİ ANALİZİ (EDA) ---
    logging.info("\n--- AŞAMA 2: TEMEL ANALİZ (İKLİMSEL TRENDLER) ---")

    start_date = df['time'].min().strftime('%Y-%m-%d')
    end_date = df['time'].max().strftime('%Y-%m-%d')
    logging.info(f"Analiz Periyodu: {start_date} ile {end_date} arası.")

    total_precipitation = df['precipitation_mm'].sum()
    total_snowfall = df['snowfall_cm'].sum()
    logging.info(f"\nToplam Değerler:")
    logging.info(f"  Toplam Yağış: {total_precipitation:.2f} mm")
    logging.info(f"  Toplam Kar Yağışı: {total_snowfall:.2f} cm")

    max_precipitation_day = df.loc[df['precipitation_mm'].idxmax()]
    logging.info(f"\nAykırı Olaylar (En Yoğun Gün):")
    logging.info(f"  En yağışlı gün: {max_precipitation_day['time'].strftime('%Y-%m-%d')}")
    logging.info(f"  Yağış miktarı: {max_precipitation_day['precipitation_mm']} mm")

    df['month'] = df['time'].dt.month
    monthly_precipitation = df.groupby('month')['precipitation_mm'].sum()
    logging.info(f"\nAylık Toplam Yağış (Mevsimsel Kalıp):")
    logging.info(monthly_precipitation.to_string(name="Toplam Yağış (mm)"))
    logging.info("(Detaylar için 'monthly_precipitation_pattern.png' grafiğine bakınız.)")


    # --- AŞAMA 3: VERİ GÖRSELLEŞTİRME ---
    logging.info("\n--- AŞAMA 3: GÖRSELLEŞTİRME ---")
    plt.style.use('seaborn-v0_8-whitegrid')

    # 1. Günlük Yağış Trendi (Time Series)
    plt.figure(figsize=(14, 7))
    plt.plot(df['time'], df['precipitation_mm'], color='blue', alpha=0.7, linestyle='-', marker='o', markersize=4)
    plt.title('Günlük Yağış Trendi (Münih, 2024)', fontsize=16, pad=20)
    plt.xlabel('Tarih', fontsize=12)
    plt.ylabel('Günlük Yağış (mm)', fontsize=12)
    
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.axvline(max_precipitation_day['time'], color='red', linestyle='--', label=f"En Yağışlı Gün ({max_precipitation_day['time'].strftime('%m-%d')}: {max_precipitation_day['precipitation_mm']} mm)")
    plt.legend()
    
    plt.tight_layout()
    plt.savefig("daily_precipitation_trend.png")
    logging.info("Grafik oluşturuldu: 'daily_precipitation_trend.png'")
    plt.close()

    # 2. Aylık Yağış Kalıbı (Bar Chart)
    plt.figure(figsize=(12, 7))
    sns.barplot(x=monthly_precipitation.index, y=monthly_precipitation.values, palette="Blues_d")
    plt.title('Aylara Göre Toplam Yağış (Mevsimsel Kalıp)', fontsize=16, pad=20)
    plt.xlabel('Ay', fontsize=12)
    plt.ylabel('Toplam Yağış (mm)', fontsize=12)
    
    # X eksenindeki ayları sayı (3, 4, 5) yerine isim (Mar, Apr, May) yap
    plt.xticks(ticks=range(0, len(monthly_precipitation.index)), labels=[calendar.month_abbr[i] for i in monthly_precipitation.index])

    plt.tight_layout()
    plt.savefig("monthly_precipitation_pattern.png")
    logging.info("Grafik oluşturuldu: 'monthly_precipitation_pattern.png'")
    plt.close()


    # --- AŞAMA 4: RAPORLAMA (ÖZET) ---
    logging.info("\n--- AŞAMA 4: YÖNETİCİ ÖZETİ ---")
    logging.info(f"Analiz, {start_date} ile {end_date} arasındaki {cleaned_rows} günlük Münih hava durumu verisini kapsamaktadır.")
    logging.info(f"Bu dönemde toplam {total_precipitation:.2f} mm yağış kaydedilmiştir.")
    logging.info(f"En yoğun yağış {max_precipitation_day['time'].strftime('%Y-%m-%d')} tarihinde {max_precipitation_day['precipitation_mm']} mm olarak ölçülmüştür.")
    logging.info("Aylık analiz, yağışların özellikle Mayıs (May) ve Haziran (Jun) aylarında yoğunlaştığını göstermektedir (Bkz: 'monthly_precipitation_pattern.png').")


    logging.info("\n\n" + "="*60)
    logging.info("--- HAVA DURUMU ANALİZ RAPORU TAMAMLANDI ---")
    logging.info("="*60)

except Exception as e:
    logging.error(f"\n!!! ANALİZ SIRASINDA BEKLENMEDİK BİR HATA OLUŞTU !!!")
    logging.error(f"Hata Detayı: {e}")
    import traceback
    logging.error(f"Traceback: {traceback.format_exc()}")
finally:
    # Logger'ı düzgünce kapat
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
