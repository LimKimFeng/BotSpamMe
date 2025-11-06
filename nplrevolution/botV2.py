import sys, re, time, random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ===== Utilities =====
def ask_url():
    """Meminta URL dari pengguna."""
    print("Masukkan URL Halaman Checkout: ", end="", flush=True)
    url = sys.stdin.readline().strip()
    if not url:
        raise ValueError("URL tidak boleh kosong.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def pick_dummy_data():
    """Memilih data dummy acak untuk mengisi form."""
    names = [
        "Andi Pratama", "Budi Santoso", "Cahyo Nugroho", "Deni Saputra", "Eko Wibowo",
        "Fajar Ramadhan", "Gilang Saputra", "Hendra Kurniawan", "Irfan Maulana", "Joko Susilo",
        "Joko", "Anies", "Prabowo", "Budi", "Shibal", "Anjing", "Nugroho", "Hai hai"
    ]
    n = random.choice(names)
    
    # Modifikasi: Hasilkan nomor 8xx (10-12 digit) karena +62 sudah ada di form
    phone = "8" + str(random.randint(111111111, 999999999)) 
    
    email = n.lower().replace(" ", "") + str(int(time.time()) % 10000) + "@example.com"
    return {"name": n, "phone": phone, "email": email}

# ===== One-shot flow =====
def do_order_once(browser, target, timeout_sec=90):
    """
    Menjalankan satu siklus pemesanan.
    timeout_sec adalah waktu maksimum dalam detik untuk menunggu elemen.
    """
    timeout_ms = timeout_sec * 1000  # Konversi ke milidetik untuk Playwright
    page = None
    try:
        page = browser.new_page()
        print(f"Membuka URL: {target}")
        page.goto(target, timeout=timeout_ms)
        
        # --- TAMBAHAN BARU SESUAI PERMINTAAN ---
        print("Memberi jeda 15 detik untuk load awal (sesuai permintaan)...")
        time.sleep(15)
        # --- AKHIR TAMBAHAN ---
        
        # Tetap menunggu elemen form pertama secara dinamis
        print("Menunggu form dimuat (wait_for_selector)...")
        page.wait_for_selector('#name', timeout=timeout_ms)
        print("Form terdeteksi. Mulai mengisi data...")

        # Mengisi Form
        data = pick_dummy_data()

        # Selektor diperbarui berdasarkan HTML baru
        print("Filling Name...")
        page.fill('#name', data["name"])  # Ganti dari #user_name
        
        print("Filling Email...")
        page.fill('#email', data["email"])  # Ganti dari #user_email
        
        print("Filling Phone...")
        page.fill('#phone', data["phone"])  # Ganti dari #user_phone (data phone sudah disesuaikan)

        print(f"Form terisi → Nama: {data['name']} | WA: {data['phone']} | Email: {data['email']}")

        # Menekan tombol submit (selektor diperbarui)
        print("Mencoba klik tombol 'Pesan!'...")
        page.click('button[type="submit"]')  # Ganti dari .submit-button

        # Memperpanjang waktu tunggu dan menunggu elemen yang menunjukkan berhasil
        print("Menunggu halaman sukses (indikator: 'Bayar Sebelum')...")
        
        # Indikator sukses baru berdasarkan HTML kedua
        page.wait_for_selector('p[data-testid="expiry-date"]', timeout=timeout_ms)
        
        print("✅ Checkout berhasil terdeteksi!")
        return True
    except PlaywrightTimeoutError:
        print(f"❌ Timeout setelah {timeout_sec} detik. Halaman sukses tidak terdeteksi.")
        return False
    except Exception as e:
        print(f"❌ Terjadi error: {e}")
        return False
    finally:
        if page:
            page.close()


# ===== Main: LOOP sampai Ctrl+C =====
if __name__ == "__main__":
    
    # Pengecekan untuk mode headless
    is_headless = False
    if "--headless" in sys.argv:
        is_headless = True
    
    print("="*30)
    print(f"Menjalankan bot dalam mode: {'HEADLESS' if is_headless else 'NON-HEADLESS (terlihat)'}")
    print("Tekan Ctrl+C untuk berhenti.")
    print("="*30)

    with sync_playwright() as p:
        try:
            browser = p.firefox.launch(headless=is_headless)
            target = ask_url()
        except Exception as e:
            print(f"Gagal memulai browser atau mendapatkan URL: {e}")
            sys.exit(1)

        total_runs = 0
        success_runs = 0
        failed_runs = 0

        try:
            while True:
                total_runs += 1
                print(f"\n=== Iterasi #{total_runs} ===")
                try:
                    # Pass timeout 90 detik ke fungsi
                    ok = do_order_once(browser, target, timeout_sec=90) 
                    if ok:
                        success_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"❌ Error iterasi #{total_runs}: {e}")
                    failed_runs += 1

                sleep_time = random.uniform(1.0, 3.0)
                print(f"Tidur selama {sleep_time:.1f} detik sebelum iterasi berikutnya...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n=== Dihentikan oleh pengguna (Ctrl+C) ===")
        except Exception as e:
            print(f"\n\n=== Terjadi error tak terduga: {e} ===")
        finally:
            print(f"\nRekap: total={total_runs}, sukses={success_runs}, gagal={failed_runs}")
            print("Menutup browser...")
            browser.close()
            print("Selesai.")


# Saya sudah membuat file `order_bot_modified.py` untuk Anda.

# **Cara Menjalankan:**

# 1.  **Mode Normal (Terlihat):**
#     ```bash
#     python order_bot_modified.py
#     ```
# 2.  **Mode Headless (Tidak Terlihat):**
#     ```bash
#     python order_bot_modified.py --headless
#     ```

# Semoga ini sesuai dengan kebutuhan Anda!