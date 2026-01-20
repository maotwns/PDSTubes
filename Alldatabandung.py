from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import pandas as pd
import re
import random

# --- KONFIGURASI ---
# List link pencarian (Search Query)
search_urls = [
    "https://www.google.com/maps/search/Masjid+di+kabupaten+cianjur/@-7.0391398,106.8224775,10z/data=!3m1!4b1!5m1!1e4?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoASAFQAw%3D%3D",
    "https://www.google.com/maps/search/Gereja+kristen+di+kabupaten+cianjur/@-6.7703377,107.0686369,12z/data=!3m1!4b1!5m1!1e4?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoASAFQAw%3D%3D",
    "https://www.google.com/maps/search/Gereja+katolik+di+kabupaten+cianjur/@-6.8021539,106.9330353,10z/data=!3m1!4b1!5m1!1e4?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoASAFQAw%3D%3D",
    "https://www.google.com/maps/search/Vihara+di+kabupaten+cianjur/@-6.8005669,106.93303,10z/data=!3m1!4b1!5m1!1e4?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoASAFQAw%3D%3D",
    "https://www.google.com/maps/search/Pura+di+kabupaten+cianjur/@-6.7989798,106.9330246,10z/data=!3m1!4b1!5m1!1e4?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoASAFQAw%3D%3D"
]

def init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless=new') 
    
    # Strategi 'eager' biar gak nunggu loading gambar kelamaan
    options.page_load_strategy = 'eager'
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_argument('--lang=id')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(120) 
    return driver

# ==========================================
# STEP 1: KUMPULKAN LINK DARI SEMUA SEARCH URL
# ==========================================
all_links = set()
driver = init_driver(headless=True)
wait = WebDriverWait(driver, 30)

print(f"--- Step 1: Mengumpulkan link tempat dari {len(search_urls)} sumber ---")

for idx, url in enumerate(search_urls):
    print(f"\n[Search {idx+1}/{len(search_urls)}] Membuka: {url}...")
    try:
        driver.get(url)
        
        # Tunggu panel hasil (feed) muncul
        try:
            feed = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        except:
            print(f"  -> Gagal load feed di link ke-{idx+1}, skip.")
            continue

        # Logic Scrolling
        prev_len = 0
        scroll_attempts = 0
        while True:
            # Scroll panel hasil ke bawah
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(3) 
            
            # Ambil link tempat
            cards = driver.find_elements(By.XPATH, '//a[contains(@href,"/maps/place")]')
            for card in cards:
                all_links.add(card.get_attribute("href"))
            
            curr_len = len(all_links)
            print(f"  -> Terkumpul total: {curr_len} link unik")

            # Cek mentok
            if len(cards) == prev_len:
                scroll_attempts += 1
                if scroll_attempts >= 3: # Coba 3x scroll kalau gak nambah, berarti mentok
                    print("  -> Sudah mentok bawah.")
                    break
            else:
                scroll_attempts = 0
            
            prev_len = len(cards)

    except Exception as e:
        print(f"  -> Error di search url ini: {e}")
        # Restart driver jika crash
        try: driver.current_url
        except: driver = init_driver(headless=True)

links_list = list(all_links)
print(f"\nTOTAL LINK FINAL: {len(links_list)}")
driver.quit() # Tutup driver sesi 1

# ==========================================
# STEP 2: SCRAPING DETAIL (FULL COLUMNS)
# ==========================================
data_hasil = []
seen_names = set()

# Buka driver baru buat sesi detail
driver = init_driver(headless=True)

print("\n--- Step 2: Mulai Scraping Detail ---")
for i, link in enumerate(links_list):
    print(f"[{i+1}/{len(links_list)}] Processing...")
    
    try:
        # Auto-Heal: Cek browser crash
        try: driver.current_url
        except: driver = init_driver(headless=True)

        try:
            driver.get(link)
        except TimeoutException:
            driver.execute_script("window.stop();")

        # Tunggu element h1 (Nama Tempat)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except:
            print("  -> Timeout nunggu judul, skip.")
            continue
            
        time.sleep(2) # Jeda dikit

        # --- EXTRAKSI DATA ---
        try: nama = driver.find_element(By.TAG_NAME, "h1").text
        except: nama = "Unknown"
        
        if nama in seen_names: 
            print("  -> Duplikat, skip.")
            continue
        seen_names.add(nama)

        try: tipe = driver.find_element(By.CLASS_NAME, "DkEaL").text
        except: tipe = "Unknown"
        
        try: alamat = driver.find_element(By.CLASS_NAME, 'Io6YTe').text
        except: alamat = None

        try: jam = driver.find_element(By.XPATH, '//td[@role="text"]').get_attribute("aria-label")
        except: jam = None

        # Ambil body text sekali untuk Regex
        try: full_text = driver.find_element(By.TAG_NAME, "body").text
        except: full_text = ""
        
        rate_match = re.search(r'\b\d[.,]\d\b', full_text)
        rating = rate_match.group() if rate_match else None
        review_match = re.search(r'\(([\d\.]+)\)', full_text)
        review = review_match.group(1) if review_match else None

        # Telepon
        try:
            telepon = driver.find_element(By.XPATH, '//*[contains(@data-item-id,"phone") or contains(@data-item-id,"call")]').text
            stt_tlp = "Ada"
        except:
            telepon = None
            stt_tlp = "Tidak Ada"

        # Website
        try:
            website = driver.find_element(By.XPATH, '//a[contains(@data-item-id,"authority")]').get_attribute("href")
        except:
            website = None

        # Lat Long
        try:
            latlon = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', driver.current_url)
            lat, lon = latlon.groups()
        except: lat = lon = None

        # Aksesibilitas
        akses_list = []
        stta = "Aksesibilitas Tidak Tersedia"
        try:
            tentang_btn = driver.find_elements(By.XPATH, '//button[.//div[text()="Tentang"]]')
            if tentang_btn:
                driver.execute_script("arguments[0].click();", tentang_btn[0])
                time.sleep(2.5)
                spans = driver.find_elements(By.XPATH, '//h2[contains(text(),"Aksesibilitas")]/following-sibling::ul//span[@aria-label]')
                akses_list = [s.get_attribute("aria-label") for s in spans]
                if akses_list: stta = "Aksesibilitas Tersedia"
        except: pass

        # Append Data
        data_hasil.append({
            "nama_tempat": nama,
            "type_place": tipe,
            "alamat": alamat,
            "jam_operasional": jam,
            "rating": rating,
            "jumlah_review": review,
            "telepon": telepon,
            "stt_tlp": stt_tlp,
            "website": website,
            "latitude": lat,
            "longitude": lon,
            "Ketersediaan Akses": stta,
            "aksesibilitas": " | ".join(akses_list)
        })
        print(f"  -> Sukses: {nama}")

    except Exception as e:
        print(f"  -> Gagal: {str(e)[:50]}")
        continue

# 3. EXPORT KE CSV
driver.quit()
if data_hasil:
    df = pd.DataFrame(data_hasil)
    cols = ["nama_tempat", "type_place", "alamat", "jam_operasional", "rating", "jumlah_review", 
            "telepon", "stt_tlp", "website", "latitude", "longitude", "Ketersediaan Akses", "aksesibilitas"]
    df = df[cols] 
    df.to_csv("DataMasjid_Full_Cirebon.csv", index=False)
    print(f"\n🎉 SELESAI! {len(data_hasil)} data tersimpan di DataMasjid_Full_Cirebon.csv")
else:
    print("\nZonk, nggak ada data.")