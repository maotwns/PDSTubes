from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
import random

options = Options()
options.add_argument('--lang=id')
options.add_argument("accept-language=id-ID,id")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

srclink = ["https://www.google.com/maps/search/masjid+bandung/@-6.9025568,107.6189005,14z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoKLDEwMDc5MjA2OUgBUAM%3D",
            "https://www.google.com/maps/search/gereja+katolik+bandung/@-6.9025568,107.6189005,14z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoKLDEwMDc5MjA2OUgBUAM%3D",
            "https://www.google.com/maps/search/gereja+protestan+bandung/@-6.9025568,107.6189005,14z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoKLDEwMDc5MjA2OUgBUAM%3D",
            "https://www.google.com/maps/search/vihara+di+bandung/@-6.9182535,107.5934633,17z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoKLDEwMDc5MjA2OUgBUAM%3D",
            "https://www.google.com/maps/search/pura+di+bandung/@-6.9182535,107.5934633,14z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI2MDExMy4wIKXMDSoKLDEwMDc5MjA2OUgBUAM%3D"]

data = []

for s in srclink:

    driver.get(s)
    time.sleep(5)

    # Scroll 
    feed = driver.find_element(By.XPATH, '//div[@role="feed"]')

    prev_count = 0
    links = set()

    while True:
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight",
            feed
        )
        time.sleep(2)

        tempat = driver.find_elements(By.XPATH, '//div[@role="article"]')
        curr_count = len(tempat)

        print(f"Jumlah tempat: {curr_count}")

        cards = driver.find_elements(By.XPATH, '//a[contains(@href,"/maps/place")]')
        for c in cards:
            links.add(c.get_attribute("href")
                    )
        if curr_count == prev_count:
            print("Semua tempat sudah terload")
            break

        prev_count = curr_count

    print("Total link:", len(links))




    seen_names = set()

    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] Ambil data") 

        driver.get(link)
        time.sleep(random.uniform(3, 5))

        #nama

        try:
            nama = driver.find_element(By.TAG_NAME, "h1").text
        except:
            nama = "Unknown"

        if not nama or nama in seen_names:
            continue
        seen_names.add(nama)

        body = driver.find_element(By.TAG_NAME, "body").text

        #tipe
        try:
            tipe = driver.find_element(By.CLASS_NAME, "DkEaL").text
        except:
            tipe = "Unknown"

        #alamat
        try:
            alamat = wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'Io6YTe')
            )
        ).text
        except:
            alamat = None

        #Jam
        try:
            jam = driver.find_element(By.XPATH, '//td[@role="text"]').get_attribute("aria-label")
        except:
            jam = None


        #tlp
        try:
            telp = driver.find_element(
                By.XPATH, '//*[contains(@data-item-id,"phone") or contains(@data-item-id,"call")]'
            ).text
            Tstatus = "Ada"
        except:
            telp = None
            Tstatus = "Tidak Ada "

        #web
        try:
            website = driver.find_element(
                By.XPATH, '//a[contains(@data-item-id,"authority")]'
            ).get_attribute("href")
            wstt = "Tersedia"
        except:
            website = None
            wstt = "Tidak Tersedia"

        # rating
        body = driver.find_element(By.TAG_NAME, "body").text

        rate_match = re.search(r'\b\d[.,]\d\b', body)
        rating = rate_match.group() if rate_match else None

        review_match = re.search(r'\(([\d\.]+)\)', body)
        review = review_match.group(1) if review_match else None

        #latlong
        try:
            latlon = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', driver.current_url)
            latitude = latlon.group(1)
            longitude = latlon.group(2)
        except:
            latitude = longitude = None

        #masukttg

        try:
            tentang_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[.//div[text()="Tentang"]]')
            ))
            tentang_btn.click()
            time.sleep(2)
        except:
            pass


        try:
        # scroll biar bagian aksesibilitas kelihatan
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(2)

            spans = driver.find_elements(
                By.XPATH, '//h2[contains(text(),"Aksesibilitas")]/following-sibling::ul//span[@aria-label]'
            )
            akses_list = [s.get_attribute("aria-label") for s in spans]
            akses_str = " | ".join(akses_list)
            stta = "Aksesibilitas Tersedia"
        except:
            akses_list = []
            akses_str = None
            stta = "Aksesibilitas Tidak Tersedia"



        #save
        data.append({
            "nama_tempat": nama,
            "type_place": tipe,
            "alamat": alamat,
            "jam_operasional": jam,
            "rating": rating,
            "jumlah_review": review,
            "telepon": telp,
            "stt_tlp": Tstatus,
            "website": wstt,
            "latitude": latitude,
            "longitude": longitude,
            "Ketersediaan Akses": stta,
            "aksesibilitas": akses_list
        })

df = pd.DataFrame(data)
df.to_csv("DataBandung.csv", index=False)

print("Selesai. Data tersimpan.")




