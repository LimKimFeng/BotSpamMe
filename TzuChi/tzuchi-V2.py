import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path # Untuk menangani path file

# --- 1. PENGATURAN TES (Langsung isi di sini) ---
IS_HEADLESS = 'n'       # 'y' untuk headless, 'n' untuk tampil
KEPUASAN = 'tidak'      # 'puas' atau 'tidak'
Q1_ANSWER = 'n'         # 'y' atau 'n' untuk Porsi
Q2_ANSWER = 'y'         # 'y' atau 'n' untuk Rasa
# ------------------------------------------------

print("--- 🚀 Memulai Otomatisasi Tes Lokal ---")
print(f"Mode: {'Headless' if IS_HEADLESS == 'y' else 'Tampil'}")
print(f"Kepuasan: {'Puas' if KEPUASAN == 'puas' else 'Tidak Puas'}")
print(f"Porsi Cukup: {'Ya' if Q1_ANSWER == 'y' else 'Tidak'}")
print(f"Rasa Enak: {'Ya' if Q2_ANSWER == 'y' else 'Tidak'}")

# --- 2. Setup Selenium WebDriver ---
chrome_options = Options()
if IS_HEADLESS == 'y':
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
except ValueError:
    print("\n[PERHATIAN] Tidak dapat mengunduh ChromeDriver.")
    sys.exit(1)
    
wait = WebDriverWait(driver, 10)

# --- INI BAGIAN PENTINGNYA ---
# Arahkan ke file 'test.html' lokal Anda
local_html_path = Path(os.path.realpath(__file__)).parent / "test2.html"
url = local_html_path.as_uri() # Mengubah path file menjadi URL (misal: file://...)

try:
    print(f"\nMembuka file lokal: {url}...")
    driver.get(url)
    print("Menunggu 5 detik...")
    time.sleep(5)
    
    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n--- 🔄 Memulai Loop Ke-{loop_count} ---")
        
        # --- 3. Pilih Kepuasan (Puas / Tidak Puas) ---
        if KEPUASAN == 'puas':
            puas_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='1']")))
            driver.execute_script("arguments[0].click();", puas_btn)
            print("Memilih: 😊 Puas")
        else:
            tidak_puas_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='0']")))
            driver.execute_script("arguments[0].click();", tidak_puas_btn)
            print("Memilih: 😞 Tidak Puas")
            
            try:
                feedback_box = wait.until(EC.visibility_of_element_located((By.ID, "feedback")))
                feedback_box.send_keys("Saran dan kritik (otomatis)")
                print("Mengisi feedback wajib.")
            except Exception as e:
                print(f"Error saat mengisi feedback: {e}")

        # --- 4. Isi Pertanyaan Detail ---
        # (Saya mengaktifkan kembali kode ini, di skrip Anda sebelumnya ini ter-comment)
        
        # Pertanyaan 1 (question_5): Porsi
        q1_value = '1' if Q1_ANSWER == 'y' else '0'
        q1_xpath = f"//input[@name='question_5' and @value='{q1_value}']"
        q1_radio = wait.until(EC.element_to_be_clickable((By.XPATH, q1_xpath)))
        driver.execute_script("arguments[0].click();", q1_radio)
        print(f"Porsi Cukup? -> {'Ya' if Q1_ANSWER == 'y' else 'Tidak'}")

        # Pertanyaan 2 (question_6): Rasa
        q2_value = '1' if Q2_ANSWER == 'y' else '0'
        q2_xpath = f"//input[@name='question_6' and @value='{q2_value}']"
        q2_radio = wait.until(EC.element_to_be_clickable((By.XPATH, q2_xpath)))
        driver.execute_script("arguments[0].click();", q2_radio)
        print(f"Rasa Enak? -> {'Ya' if Q2_ANSWER == 'y' else 'Tidak'}")
        
        # --- 5. Submit Form ---
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        driver.execute_script("arguments[0].click();", submit_btn)
        print("Formulir telah disubmit.")

        # --- 6. Tunggu dan Tutup Modal ---
        print("Menunggu 5 detik setelah submit...")
        time.sleep(5)
        
        tutup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tutup Browser')]")))
        driver.execute_script("arguments[0].click();", tutup_btn)
        print("Modal ditutup, halaman akan me-reload.")
        
        print("Menunggu halaman siap untuk loop berikutnya...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='1']")))

except KeyboardInterrupt:
    print("\n\n--- 🛑 Proses dihentikan oleh pengguna (Ctrl+C) ---")
except Exception as e:
    print(f"\n--- ❌ Terjadi Error ---")
    print(e)
finally:
    if 'driver' in locals():
        driver.quit()
    print("Browser Selenium telah ditutup.")