import sys
import random
import time
import asyncio
import json  # <- Ditambahkan untuk membaca file JSON
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

URL = "https://healingtransformation.orderonline.id/webinar-self-healing-transformation"

def pick_dummy(phone_mode, phone_list=None):
    """
    Membuat data dummy untuk formulir.
    phone_mode: 'random' atau 'file'
    phone_list: List nomor telepon jika mode 'file'
    """
    
    # Data Nama, Telepon, Email
    names = ["Andi Pratama", "Budi Santoso", "Cahyo Nugroho", "Deni Saputra", "Eko Wibowo",
             "Fajar Ramadhan", "Gilang Saputra", "Hendra Kurniawan", "Irfan Maulana", "Joko Susilo"]
    n = random.choice(names)
    
    # --- LOGIKA NOMOR TELEPON DIMODIFIKASI ---
    phone = ""
    if phone_mode == 'file' and phone_list:
        phone = random.choice(phone_list)
        print(f"Menggunakan nomor dari file: {phone}")
    else:
        if phone_mode == 'file' and not phone_list:
            print("Mode file dipilih tapi list kosong. Beralih ke random.")
        phone = "62" + str(random.randint(8111111111, 8999999999))
        print(f"Menggunakan nomor random: {phone}")
    # --- AKHIR MODIFIKASI ---

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

async def fill_field_with_delay(page, selector, value, delay_sec=5, optional=False):
    """Mengisi field input dan memberikan jeda."""
    try:
        # Tentukan timeout: 3 detik untuk opsional, 30 detik untuk wajib
        timeout = 3000 if optional else 30000
        
        locator = page.locator(selector)
        await locator.scroll_into_view_if_needed()
        await locator.fill(value, timeout=timeout)
        
        print(f"Field '{selector}' diisi: {value}")
        await page.wait_for_timeout(delay_sec * 1000) # Konversi detik ke milidetik
        return True
    except PWTimeout:
        print(f"Field opsional '{selector}' tidak ditemukan. Dilewati.")
        return False
    except Exception as e:
        print(f"Gagal mengisi field '{selector}': {e}")
        return False

# --- FUNGSI DROPDOWN: Menggunakan metode pencarian Select2 ---
async def select_select2_with_search(page, select_name, item_text, delay_sec=5):
    """
    Fungsi untuk memilih dropdown Select2 dengan mengetik di kotak pencarian.
    """
    print(f"Memilih dropdown Select2 [name='{select_name}'] untuk: {item_text}...")
    try:
        # 1. Tentukan locator untuk 'kotak' Select2 yang terlihat
        trigger_xpath = f"//select[@name='{select_name}']/following-sibling::span[contains(@class, 'select2-container')]"
        trigger_box = page.locator(trigger_xpath)
        
        await trigger_box.scroll_into_view_if_needed()
        
        # 2. Klik kotak tersebut untuk memicu dropdown
        await trigger_box.click()
        
        # 3. Tunggu kotak pencarian muncul, lalu ketik
        search_field = page.locator("input.select2-search__field")
        # 'fill' lebih cepat dan andal daripada 'type'
        await search_field.fill(item_text)
        
        # 4. Tunggu hasil pencarian (elemen <li>) muncul dan klik
        result_xpath = f"//li[contains(@class, 'select2-results__option') and normalize-space(text())='{item_text}']"
        target_option = page.locator(result_xpath)
        
        await target_option.click()
        
        print(f"Berhasil memilih: {item_text}")
        await page.wait_for_timeout(delay_sec * 1000)
        return True
        
    except Exception as e:
        print(f"Gagal memilih dropdown Select2 [name='{select_name}'] untuk '{item_text}': {e}")
        await page.screenshot(path="error_dropdown_select2.png")
        print("Screenshot kegagalan dropdown disimpan.")
        return False

def log_success_to_json(filename, data_to_log, attempt_count):
    """Mencatat data sukses ke file JSON."""
    if not filename:
        print("Nama file progress tidak disediakan, logging dilewati.")
        return

    try:
        # Coba baca data yang ada
        with open(filename, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
    except FileNotFoundError:
        progress_data = []  # Buat list baru jika file tidak ada
    except json.JSONDecodeError:
        print(f"WARNING: File {filename} korup, akan ditimpa.")
        progress_data = [] # Timpa jika file korup
    
    # Pastikan data adalah list
    if not isinstance(progress_data, list):
        print(f"WARNING: Data di {filename} bukan list, akan ditimpa.")
        progress_data = []

    # Siapkan data baru
    log_entry = {
        "attempt": attempt_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data": data_to_log
    }
    
    # Tambahkan data baru
    progress_data.append(log_entry)

    # Tulis kembali ke file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=4, ensure_ascii=False)
        print(f"Berhasil mencatat sukses ke {filename}")
    except IOError as e:
        print(f"ERROR: Gagal menulis ke file progress {filename}: {e}")
    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat menulis JSON: {e}")


async def run_single_attempt(page, attempt_count, phone_mode, phone_list=None, progress_filename=None):
    """
    Menjalankan satu kali percobaan pendaftaran pada Halaman (Page) yang sudah ada.
    """
    # Hapus: context = None
    # Hapus: page = None
    try:
        # Panggil pick_dummy dengan parameter baru
        dummy = pick_dummy(phone_mode, phone_list)
        
        TARGET_PROVINCE = dummy["location"]["province"]
        TARGET_CITY = dummy["location"]["city"]
        TARGET_DISTRICT = dummy["location"]["district"]

        print(f"\n--- Percobaan #{attempt_count} ---")
        print(f"Mencoba mendaftar dengan data:\n{dummy}\n")
        
        # --- PERUBAHAN: Hapus pembuatan konteks/halaman baru ---
        # context = await browser.new_context(...)
        # page = await context.new_page()
        
        # --- PERUBAHAN: Mulai dengan navigasi di halaman yang ada ---
        print(f"Menavigasi ke URL: {URL}")
        await page.goto(URL, wait_until="domcontentloaded")

        # --- INJEKSI JAVASCRIPT: Mematikan WA Validator ---
        print("Mencoba mematikan WhatsApp Validator...")
        try:
            await page.evaluate(
                """
                if (window.myProduct && window.myProduct.global_setting && window.myProduct.global_setting.anti_spam) {
                    window.myProduct.global_setting.anti_spam.whatsapp_validator = false;
                    console.log('WhatsApp Validator dinonaktifkan.');
                } else {
                    console.log('Variabel myProduct tidak ditemukan untuk dimodifikasi.');
                }
                """
            )
            print("Injeksi JS untuk mematikan validator telah dieksekusi.")
        except Exception as e:
            print(f"Gagal menginjeksi JS untuk validator: {e}")
            # Kita lanjut saja, mungkin tidak fatal
        
        await page.wait_for_selector("form.orderonline-embed-form")

        # --- Mengisi Data Kontak ---
        await fill_field_with_delay(page, "#field-name", dummy["name"])
        await fill_field_with_delay(page, "#field-phone", dummy["phone"])
        
        await fill_field_with_delay(page, "#field-email", dummy["email"], optional=True)
        await fill_field_with_delay(page, "#field-notes", dummy["notes"], optional=True)
        await fill_field_with_delay(page, "#field-address", dummy["address"], optional=True)
        
        # --- Mengisi Dropdown (Logika Select2 Search) ---
        
        # 1. Pilih Provinsi
        if not await select_select2_with_search(page, "province", TARGET_PROVINCE):
            raise Exception("Gagal memilih Provinsi")

        # 2. Pilih Kota/Kabupaten
        if not await select_select2_with_search(page, "city", TARGET_CITY):
            raise Exception("Gagal memilih Kota/Kabupaten")

        # 3. Pilih Kecamatan
        if not await select_select2_with_search(page, "district", TARGET_DISTRICT):
             raise Exception("Gagal memilih Kecamatan")

        # --- reCAPTCHA: Menunggu penyelesaian manual ---
        # print("Mencoba klik checkbox reCAPTCHA...") # <- Dihapus
        try:
            # # Locator spesifik untuk frame yang 'visible' (size=normal)
            # frame = page.frame_locator('iframe[title="reCAPTCHA"][src*="size=normal"]') # <- Dihapus
            
            # # Klik checkbox di dalam frame
            # await frame.locator('#recaptcha-anchor').click() # <- Dihapus
            
            # print("Checkbox reCAPTCHA diklik.") # <- Dihapus
            # await page.wait_for_timeout(5000) # Tunggu 5 detik setelah klik # <- Dihapus

            # Tunggu sampai token terisi (penyelesaian manual)
            print("Silakan selesaikan reCAPTCHA (Saya bukan robot) secara manual. Skrip menunggu sampai token terisi…")
            await page.wait_for_function(
                "document.querySelector('#g-recaptcha-response')?.value?.length > 0",
                timeout=180000 # Timeout 3 menit
            )
            print("reCAPTCHA terdeteksi terselesaikan ✅")
        
        except PWTimeout:
            print("⚠️ reCAPTCHA belum terselesaikan dalam batas waktu 3 menit.")
            raise
        except Exception as e:
            print(f"Gagal mengklik reCAPTCHA: {e}")
            raise

        # --- Submit ---
        print("Mengklik tombol 'Beli Sekarang'...")
        
        try:
            # Mulai "mendengarkan" popup SEBELUM mengklik
            async with page.expect_popup(timeout=20000) as popup_info:
                await page.locator("#btn-complete-order").click()
            
            # --- KASUS 1: POPUP MUNCUL (WA) ---
            new_page = await popup_info.value
            await new_page.wait_for_load_state()
            
            print(f"✅ SUCCESS (tab baru terbuka): {new_page.url}")
            if "whatsapp.com" in new_page.url or "wa.me" in new_page.url:
                print("Halaman WhatsApp terdeteksi, menutup tab baru...")
                await new_page.close()

            # Log sukses dan selesaikan
            print(f"--- Percobaan #{attempt_count} SUKSES ---")
            log_success_to_json(progress_filename, dummy)
            
        except PWTimeout:
            # --- KASUS 2: TIDAK ADA POPUP ---
            print("Tidak ada popup terdeteksi, mengecek perubahan URL di tab yang sama...")
            try:
                # Coba tunggu URL berubah
                await page.wait_for_url(lambda url: url != URL, timeout=10000)
                
                # --- KASUS 2a: URL BERUBAH ---
                print(f"✅ SUCCESS (URL berubah di tab yang sama): {page.url}")
                
                # Log sukses dan selesaikan
                print(f"--- Percobaan #{attempt_count} SUKSES ---")
                log_success_to_json(progress_filename, dummy)

            except PWTimeout:
                # --- KASUS 2b: URL TIDAK BERUBAH (GAGAL) ---
                 print(f"❌ GAGAL: Submit diklik, tapi URL tidak berubah. (Captcha mungkin salah?)")
                 print(f"--- Percobaan #{attempt_count} GAGAL ---")
                 # Lempar exception agar ditangkap oleh blok try...except luar
                 # Ini akan memicu screenshot error dan melanjutkan ke loop berikutnya
                 raise Exception("Submit gagal, URL tidak berubah atau Captcha salah")
        
        # HAPUS log sukses dari sini, karena sudah dipindah ke atas
        # print(f"--- Percobaan #{attempt_count} SUKSES ---")
        # log_success_to_json(progress_filename, dummy)

    except Exception as e:
        print(f"\n--- Terjadi Kesalahan pada Percobaan #{attempt_count} ---")
        print(str(e))
        if "page" in locals() and page:
            try:
                # Simpan screenshot error dengan nama unik
                error_filename = f"error_attempt_{attempt_count}.png"
                await page.screenshot(path=error_filename)
                print(f"Screenshot error disimpan sebagai '{error_filename}'")
            except:
                pass 
            
    finally:
        # --- PERUBAHAN BESAR: Jangan tutup konteks ---
        # if context:
        #     await context.close()
        #     print("Konteks halaman ditutup.")
        print("Percobaan selesai, bersiap untuk loop berikutnya...") # Pesan baru

def get_phone_config():
    """
    Fungsi untuk menanyakan user dan memuat data telepon jika perlu.
    """
    phone_mode_input = ''
    phone_list = []
    mode_str = 'random' # Default
    
    # --- PERTANYAAN FILE PROGRESS DIPINDAHKAN KE ATAS ---
    print("\n--- Pengaturan File Progress ---")
    progress_filename_input = input("Masukkan nama file JSON untuk log progress (default: 'progress.json'): ")
    progress_filename = progress_filename_input.strip() or "progress.json"
    print(f"Progress akan dicatat di: {progress_filename}")
    # --- AKHIR PERUBAHAN ---

    while phone_mode_input not in ['1', '2']:
        phone_mode_input = input(
            "\n--- Pengaturan Sumber Telepon ---\n" # Menambahkan header
            "Pilih sumber nomor telepon:\n"
            " (1) Buat nomor random (default)\n"
            " (2) Ambil dari file JSON\n" # <-- Dibuat lebih generik
            "Pilihan [1/2]: "
        ) or '1' # Default ke '1' jika user menekan Enter

    if phone_mode_input == '2':
        try:
            # --- MODIFIKASI: Tanya nama file ---
            json_path_input = input("Masukkan nama file JSON untuk nomor telepon (default: 'nomor.json'): ") # Dibuat lebih jelas
            json_path = json_path_input.strip() or "nomor.json" # Ambil input, default ke 'nomor.json'
            # --- AKHIR MODIFIKASI ---
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            phone_list = data["semua_nomor_unik"]
            
            if not phone_list:
                print(f"File JSON '{json_path}' ditemukan tapi list 'semua_nomor_unik' kosong.")
                raise ValueError("List nomor kosong")
            
            print(f"Berhasil memuat {len(phone_list)} nomor dari {json_path}.")
            mode_str = 'file'
            
        except FileNotFoundError:
            print(f"ERROR: File '{json_path}' tidak ditemukan.")
            print("Beralih ke mode random.")
            mode_str = 'random'
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"ERROR: Gagal memproses file JSON ({e}).")
            print("Pastikan format file benar dan memiliki key 'semua_nomor_unik'.")
            print("Beralih ke mode random.")
            mode_str = 'random'
    else:
        print("Mode random dipilih.")
        mode_str = 'random'
        
    # --- BAGIAN INI SUDAH DIPINDAHKAN KE ATAS ---
    # print("\n--- Pengaturan File Progress ---")
    # progress_filename_input = input("Masukkan nama file JSON untuk log progress (default: 'progress.json'): ")
    # progress_filename = progress_filename_input.strip() or "progress.json"
    # print(f"Progress akan dicatat di: {progress_filename}")
    # --- AKHIR TAMBAHAN ---
        
    return mode_str, phone_list, progress_filename

async def main():
    """
    Fungsi utama untuk meluncurkan browser SATU KALI
    dan menjalankan loop pendaftaran tak terbatas.
    """
    
    # --- PENGATURAN AWAL (DILAKUKAN SEKALI) ---
    print("--- Pengaturan Awal ---")
    phone_mode, phone_list, progress_filename = get_phone_config()
    print("------------------------")
    
    browser = None
    attempt_count = 0
    try:
        async with async_playwright() as p:
            # Menyiapkan argumen browser, termasuk anti-deteksi
            launch_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                # '--window-size=800,1080' # <-- DIHAPUS: Biarkan user mengatur manual
            ]
            
            print("Meluncurkan browser (NON-HEADLESS)...")
            browser = await p.chromium.launch(
                headless=False, # Diubah ke False agar browser terlihat
                channel="chrome",  # Mencoba menggunakan Chrome terinstal
                args=launch_args
            )
            
            # --- PERUBAHAN: Buat Konteks & Halaman SEKALI di sini ---
            print("Membuat konteks dan halaman browser...")
            context = await browser.new_context(
                locale="id-ID",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
                # HAPUS: device_scale_factor=0.25
            )
            page = await context.new_page()
            
            print("\n=======================================================")
            print("Halaman browser telah terbuka.")
            print("Silakan atur ZOOM dan UKURAN WINDOW secara manual SEKARANG.")
            print("Skrip akan dimulai dalam 10 detik...")
            print("=======================================================\n")
            await asyncio.sleep(10) # Jeda 10 detik untuk setup manual
            
            # --- MULAI LOOPING ---
            while True:
                attempt_count += 1
                # Teruskan 'page' yang sudah ada, bukan 'browser'
                await run_single_attempt(page, attempt_count, phone_mode, phone_list, progress_filename)
                
                # Jeda acak antar percobaan (misal: 5 sampai 15 detik)
                delay = random.uniform(5.0, 15.0)
                print(f"Menunggu {delay:.1f} detik sebelum percobaan berikutnya...")
                await asyncio.sleep(delay)
            # --- AKHIR LOOPING ---

    except KeyboardInterrupt:
        print("\n--- Looping dihentikan oleh pengguna (Ctrl+C) ---")
    except Exception as e:
        print(f"\n--- Terjadi Kesalahan Fatal (Browser mungkin crash) ---")
        print(str(e))
            
    finally:
        if browser:
            await browser.close()
            print("Browser ditutup.")

if __name__ == "__main__":
    # Pindahkan import asyncio ke atas jika belum ada
    asyncio.run(main())