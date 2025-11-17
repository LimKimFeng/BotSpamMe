import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_user_input(prompt, choices):
    """Meminta input dari pengguna dan memvalidasinya."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in choices:
            return choice
        print(f"Input tidak valid. Pilihan yang tersedia: {', '.join(choices)}")

# --- 1. Dapatkan Pengaturan dari Pengguna ---
print("--- 🤖 Setup Otomatisasi Penilaian Kantin ---")
print("Skrip ini akan berjalan terus menerus. Tekan Ctrl+C di terminal untuk berhenti.")

is_headless = get_user_input("Jalankan dalam mode headless? (y/n): ", ['y', 'n'])
kepuasan = get_user_input("Pilih tingkat kepuasan (puas/tidak): ", ['puas', 'tidak'])
q1_answer = get_user_input("Jawaban 'Porsi Cukup'? (y/n): ", ['y', 'n'])
q2_answer = get_user_input("Jawaban 'Rasa Enak'? (y/n): ", ['y', 'n'])

print("\n--- 🚀 Pengaturan Selesai. Memulai Otomatisasi ---")
print(f"Mode: {'Headless' if is_headless == 'y' else 'Tampil'}")
print(f"Kepuasan: {'Puas' if kepuasan == 'puas' else 'Tidak Puas'}")
print(f"Porsi Cukup: {'Ya' if q1_answer == 'y' else 'Tidak'}")
print(f"Rasa Enak: {'Ya' if q2_answer == 'y' else 'Tidak'}")

# --- 2. Setup Selenium WebDriver ---
chrome_options = Options()
if is_headless == 'y':
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

# Menggunakan webdriver-manager untuk mengelola driver secara otomatis
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
except ValueError:
    print("\n[PERHATIAN] Tidak dapat mengunduh ChromeDriver.")
    print("Pastikan Anda memiliki koneksi internet atau ChromeDriver sudah ada di PATH.")
    sys.exit(1)
    
wait = WebDriverWait(driver, 10) # Timeout 10 detik
url = "https://cktc.web.id/kantin/rating2/"

try:
    print(f"\nMembuka website: {url}...")
    driver.get(url)
    print("Menunggu 5 detik (sesuai permintaan)...")
    time.sleep(5)
    
    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n--- 🔄 Memulai Loop Ke-{loop_count} ---")
        
        # --- 3. Pilih Kepuasan (Puas / Tidak Puas) ---
        if kepuasan == 'puas':
            puas_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='1']")))
            driver.execute_script("arguments[0].click();", puas_btn) # Klik via JS agar lebih stabil
            print("Memilih: 😊 Puas")
        else:
            tidak_puas_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='0']")))
            driver.execute_script("arguments[0].click();", tidak_puas_btn)
            print("Memilih: 😞 Tidak Puas")
            
            # Isi feedback (wajib jika tidak puas)
            try:
                feedback_box = wait.until(EC.visibility_of_element_located((By.ID, "feedback")))
                feedback_box.send_keys("Saran dan kritik (otomatis)")
                print("Mengisi feedback wajib.")
            except Exception as e:
                print(f"Error saat mengisi feedback: {e}")

        # --- 4. Isi Pertanyaan Detail ---
        # Pertanyaan 1 (question_5): Porsi
        # q1_value = '1' if q1_answer == 'y' else '0'
        # q1_xpath = f"//input[@name='question_5' and @value='{q1_value}']"
        # q1_radio = wait.until(EC.element_to_be_clickable((By.XPATH, q1_xpath)))
        # driver.execute_script("arguments[0].click();", q1_radio)
        # print(f"Porsi Cukup? -> {'Ya' if q1_answer == 'y' else 'Tidak'}")

        # Pertanyaan 2 (question_6): Rasa
        # q2_value = '1' if q2_answer == 'y' else '0'
        # q2_xpath = f"//input[@name='question_6' and @value='{q2_value}']"
        # q2_radio = wait.until(EC.element_to_be_clickable((By.XPATH, q2_xpath)))
        # driver.execute_script("arguments[0].click();", q2_radio)
        # print(f"Rasa Enak? -> {'Ya' if q2_answer == 'y' else 'Tidak'}")
        
        # --- 5. Submit Form ---
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        driver.execute_script("arguments[0].click();", submit_btn)
        print("Formulir telah disubmit.")

        # --- 6. Tunggu dan Tutup Modal ---
        print("Menunggu 5 detik setelah submit (sesuai permintaan)...")
        time.sleep(5)
        
        tutup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tutup Browser')]")))
        driver.execute_script("arguments[0].click();", tutup_btn)
        print("Modal ditutup, halaman akan me-reload.")
        
        # Tunggu halaman reload selesai sebelum loop berikutnya
        # Kita tunggu tombol 'Puas' muncul lagi sebagai indikator halaman siap
        print("Menunggu halaman siap untuk loop berikutnya...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-value='1']")))

except KeyboardInterrupt:
    print("\n\n--- 🛑 Proses dihentikan oleh pengguna (Ctrl+C) ---")
except Exception as e:
    print(f"\n--- ❌ Terjadi Error ---")
    print(e)
    print("Silakan cek apakah struktur website berubah atau ada masalah koneksi.")
finally:
    if 'driver' in locals():
        driver.quit()
    print("Browser Selenium telah ditutup.")    