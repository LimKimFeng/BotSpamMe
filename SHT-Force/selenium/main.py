import sys
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

URL = "https://healingtransformation.orderonline.id/webinar-self-healing-transformation"

def pick_dummy():
    """Membuat data dummy untuk formulir."""
    
    # Data Nama, Telepon, Email
    names = ["Andi Pratama", "Budi Santoso", "Cahyo Nugroho", "Deni Saputra", "Eko Wibowo",
             "Fajar Ramadhan", "Gilang Saputra", "Hendra Kurniawan", "Irfan Maulana", "Joko Susilo"]
    n = random.choice(names)
    phone = "62" + str(random.randint(8111111111, 8999999999))
    email = n.lower().replace(" ", "") + str(int(time.time()) % 10000) + "@example.com"
    
    # Data Catatan Pemesanan (20 kata/frasa acak)
    notes_list = [
        "Mohon konfirmasi jika sudah diproses", "Packing aman ya", "Segera dikirim", "Terima kasih",
        "Semoga berjalan lancar", "Ditunggu akses webinarnya", "Tolong cek kembali data saya",
        "Pembayaran sudah lunas", "Saya peserta dari luar kota", "Apakah ada grup WA?",
        "Sangat antusias!", "Butuh invoice", "Atas nama perusahaan", "Hadiah untuk teman",
        "Semoga bermanfaat", "Jangan lupa reminder", "Transfer via BCA", "OK", "Sip", "Mantap"
    ]
    
    # Data Alamat Lengkap (15 alamat acak)
    address_list = [
        "Jl. Merdeka No. 17, RT 01 RW 02, Jakarta Pusat",
        "Jl. Sudirman Kav. 25, Apartemen Senopati, Unit 8A, Jakarta Selatan",
        "Jl. Diponegoro No. 112, Surabaya",
        "Jl. Gajah Mada No. 33, Semarang",
        "Jl. Pahlawan No. 45, Bandung",
        "Jl. Imam Bonjol No. 5, Medan",
        "Jl. Teuku Umar No. 88, Denpasar",
        "Jl. Ahmad Yani No. 1, Yogyakarta",
        "Jl. Asia Afrika No. 155, Bandung",
        "Jl. Gatot Subroto No. 20, Makassar",
        "Jl. Siliwangi No. 76, Bogor",
        "Perumahan Griya Indah, Blok C2 No. 5, Bekasi",
        "Jl. Raya Bintaro Sektor 3, Tangerang Selatan",
        "Jl. Kemerdekaan No. 9, Palembang",
        "Jl. Pemuda No. 101, Semarang"
    ]
    
    # Data Lokasi dari gambar (sesuai permintaan)
    location_options = [
        {"province": "Kalimantan Barat", "city": "Kab. Kapuas Hulu", "district": "Boyan Tanjung"},
        {"province": "Kalimantan Barat", "city": "Kab. Bengkayang", "district": "Jagoi Babang"},
        {"province": "Kalimantan Barat", "city": "Kota Pontianak", "district": "Pontianak Kota"},
        {"province": "Kalimantan Barat", "city": "Kab. Bengkayang", "district": "Lembah Bawang"},
        {"province": "Kalimantan Barat", "city": "Kota Pontianak", "district": "Pontianak Timur"},
        {"province": "Kalimantan Barat", "city": "Kab. Bengkayang", "district": "Tujuh Belas"},
    ]
    selected_location = random.choice(location_options)

    return {
        "name": n,
        "phone": phone,
        "email": email,
        "notes": random.choice(notes_list),
        "address": random.choice(address_list),
        "location": selected_location
    }

def make_driver():
    """Inisialisasi Chrome WebDriver."""
    opts = ChromeOptions()
    # opts.add_argument("--headless=new") 
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_argument("--lang=id-ID")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    
    print("Menginstal/Menyiapkan ChromeDriver...")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(0) # Kita akan gunakan explicit wait
    print("Driver siap.")
    return driver

def fill_field_with_delay(driver, wait, selector, value, delay_sec=5):
    """Mengisi field input dan memberikan jeda."""
    try:
        field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        field.clear()
        field.send_keys(value)
        print(f"Field '{selector}' diisi: {value}")
        time.sleep(delay_sec)
        return True
    except TimeoutException:
        print(f"Field opsional '{selector}' tidak ditemukan. Dilewati.")
        return False
    except Exception as e:
        print(f"Gagal mengisi field '{selector}': {e}")
        return False

# --- FUNGSI DROPDOWN BARU: Menggunakan metode pencarian Select2 ---
def select_select2_with_search(driver, wait, select_name, item_text, delay_sec=5):
    """
    Fungsi untuk memilih dropdown Select2 dengan mengetik di kotak pencarian.
    Ini adalah strategi yang benar berdasarkan HTML Select2.
    """
    print(f"Memilih dropdown Select2 [name='{select_name}'] untuk: {item_text}...")
    try:
        # 1. Tentukan selector untuk 'kotak' Select2 yang terlihat
        # Kita cari <select> berdasarkan nama, lalu cari <span> berikutnya yang merupakan kontainer Select2
        trigger_xpath = f"//select[@name='{select_name}']/following-sibling::span[contains(@class, 'select2-container')]"
        trigger_box = wait.until(EC.element_to_be_clickable((By.XPATH, trigger_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger_box)
        
        # 2. Klik kotak tersebut untuk memicu dropdown
        trigger_box.click()
        
        # 3. Tunggu kotak pencarian muncul, lalu ketik
        # Kotak pencarian ini ada di body, bukan di dalam 'trigger_box'
        search_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input.select2-search__field")))
        search_field.send_keys(item_text)
        
        # 4. Tunggu hasil pencarian (elemen <li>) muncul dan klik
        # Kita gunakan normalize-space() untuk mencocokkan teks tanpa peduli spasi
        result_xpath = f"//li[contains(@class, 'select2-results__option') and normalize-space(text())='{item_text}']"
        target_option = wait.until(EC.element_to_be_clickable((By.XPATH, result_xpath)))
        
        target_option.click()
        
        print(f"Berhasil memilih: {item_text}")
        time.sleep(delay_sec)
        return True
        
    except Exception as e:
        print(f"Gagal memilih dropdown Select2 [name='{select_name}'] untuk '{item_text}': {e}")
        # Ambil screenshot di sini agar lebih jelas
        driver.save_screenshot("error_dropdown_select2.png")
        print("Screenshot kegagalan dropdown disimpan.")
        return False

def main():
    driver = None
    try:
        dummy = pick_dummy()
        
        TARGET_PROVINCE = dummy["location"]["province"]
        TARGET_CITY = dummy["location"]["city"]
        TARGET_DISTRICT = dummy["location"]["district"]

        driver = make_driver()
        wait = WebDriverWait(driver, 30) # Timeout utama 30 detik

        print(f"Mencoba mendaftar dengan data:\n{dummy}\n")
        
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.orderonline-embed-form")))

        # --- Mengisi Data Kontak ---
        fill_field_with_delay(driver, wait, "#field-name", dummy["name"])
        fill_field_with_delay(driver, wait, "#field-phone", dummy["phone"])
        
        short_wait = WebDriverWait(driver, 3)
        fill_field_with_delay(driver, short_wait, "#field-email", dummy["email"])
        fill_field_with_delay(driver, short_wait, "#field-notes", dummy["notes"])
        fill_field_with_delay(driver, short_wait, "#field-address", dummy["address"])
        
        # --- Mengisi Dropdown (Logika Select2 Search) ---
        
        # 1. Pilih Provinsi
        if not select_select2_with_search(driver, wait, 
                "province",         # Atribut 'name'
                TARGET_PROVINCE):   # Teks yang dicari
            raise Exception("Gagal memilih Provinsi")

        # 2. Pilih Kota/Kabupaten
        # Tidak perlu 'wait' di sini, karena fungsi select_... sudah 'wait'
        if not select_select2_with_search(driver, wait, 
                "city",             # Atribut 'name'
                TARGET_CITY):       # Teks yang dicari
            raise Exception("Gagal memilih Kota/Kabupaten")

        # 3. Pilih Kecamatan
        if not select_select2_with_search(driver, wait, 
                "district",         # Atribut 'name'
                TARGET_DISTRICT):   # Teks yang dicari
             raise Exception("Gagal memilih Kecamatan")


        # --- reCAPTCHA: Klik, lalu tunggu penyelesaian manual ---
        print("Mencoba klik checkbox reCAPTCHA...")
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')))
            wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))).click()
            driver.switch_to.default_content()
            
            print("Checkbox reCAPTCHA diklik.")
            time.sleep(5) 

            print("Silakan selesaikan reCAPTCHA (Saya bukan robot) jika diminta. Skrip menunggu sampai token terisi…")
            WebDriverWait(driver, 180).until(
                lambda d: d.execute_script("return document.querySelector('#g-recaptcha-response')?.value?.length > 0")
            )
            print("reCAPTCHA terdeteksi terselesaikan ✅")
        
        except TimeoutException:
            print("⚠️ reCAPTCHA belum terselesaikan dalam batas waktu 3 menit.")
            raise
        except Exception as e:
            print(f"Gagal mengklik reCAPTCHA: {e}")
            raise

        # --- Submit ---
        print("Mengklik tombol 'Beli Sekarang'...")
        old_handles = driver.window_handles
        original_handle = driver.current_window_handle
        
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-complete-order")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        submit_button.click()
        
        try:
            WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(len(old_handles) + 1))
            new_handle = [h for h in driver.window_handles if h != original_handle][0]
            driver.switch_to.window(new_handle)
            
            print("✅ SUCCESS (tab baru terbuka):", driver.current_url)
            if "whatsapp.com" in driver.current_url or "wa.me" in driver.current_url:
                print("Halaman WhatsApp terdeteksi, menutup tab baru...")
                driver.close()
                driver.switch_to.window(original_handle)
                
        except TimeoutException:
            try:
                WebDriverWait(driver, 10).until(EC.url_changes(URL))
                print("✅ SUCCESS (URL berubah di tab yang sama):", driver.current_url)
            except TimeoutException:
                 print("✅ SUCCESS (Tidak ada redirect, submit berhasil di halaman yang sama)")
        
        print("Proses selesai. Menutup browser dalam 10 detik.")
        time.sleep(10)

    except Exception as e:
        print("\n--- Terjadi Kesalahan ---")
        print(str(e))
        print("Skrip dihentikan.")
        if driver:
            try:
                driver.save_screenshot("error_screenshot.png")
                print("Screenshot error disimpan sebagai 'error_screenshot.png'")
            except:
                pass 
            
    finally:
        if driver:
            driver.quit()
            print("Browser ditutup.")

if __name__ == "__main__":
    main()

