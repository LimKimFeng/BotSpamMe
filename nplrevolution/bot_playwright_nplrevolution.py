import sys, re, time, random
import os  # <-- Diperlukan untuk cek file
import json # <-- Diperlukan untuk baca/tulis stats
from playwright.sync_api import sync_playwright

# Nama file untuk menyimpan statistik
STATS_FILE = "stats.json"

# ===== Utilities =====
def ask_url():
    print("Masukkan URL OO: ", end="", flush=True)
    url = sys.stdin.readline().strip()
    if not url:
        raise ValueError("URL tidak boleh kosong.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def pick_dummy_data():
    names = [
        "Andi Pratama", "Budi Santoso", "Cahyo Nugroho", "Deni Saputra", "Eko Wibowo",
        "Fajar Ramadhan", "Gilang Saputra", "Hendra Kurniawan", "Irfan Maulana", "Joko Susilo", "Joko", "Anies", "Prabowo", "Budi", "Shibal", "Anjing", "Nugroho", "Hai hai"
    ]
    n = random.choice(names)
    phone = "62" + str(random.randint(8111111111, 8999999999))
    email = n.lower().replace(" ", "") + str(int(time.time()) % 10000) + "@example.com"
    return {"name": n, "phone": phone, "email": email}

# ===== Fungsi untuk memuat stats =====
def load_stats():
    """Membaca stats dari file JSON."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
            total = stats.get('total_runs', 0)
            success = stats.get('success_runs', 0)
            failed = stats.get('failed_runs', 0)
            print(f"Melanjutkan dari stats sebelumnya:")
            print(f"Total={total}, Sukses={success}, Gagal={failed}")
            return total, success, failed
        except Exception as e:
            print(f"Gagal memuat stats.json ({e}). Memulai dari 0.")
            return 0, 0, 0
    else:
        print("File stats.json tidak ditemukan. Memulai dari 0.")
        return 0, 0, 0

# ===== Fungsi untuk menyimpan stats =====
def save_stats(total, success, failed):
    """Menyimpan stats ke file JSON."""
    print(f"\nMenyimpan stats ke {STATS_FILE}...")
    stats_data = {
        "total_runs": total,
        "success_runs": success,
        "failed_runs": failed
    }
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats_data, f, indent=4)
        print("Stats berhasil disimpan.")
    except Exception as e:
        print(f"Gagal menyimpan stats: {e}")

# ===== One-shot flow =====
def do_order_once(page, target, timeout=90): # <-- Menerima 'page'
    print(f"Membuka URL: {target}")
    page.goto(target)
    
    print("Menunggu 30 detik...")
    time.sleep(30)  # Tunggu selama 30 detik untuk memastikan halaman dimuat

    # Mengisi Form
    data = pick_dummy_data()

    print("Filling Name...")
    page.fill('#user_name', data["name"])  # Mengisi Nama Lengkap
    
    print("Filling Email...")
    page.fill('#user_email', data["email"])  # Mengisi Email
    
    print("Filling Phone...")
    page.fill('#user_phone', data["phone"])  # Mengisi Nomor WhatsApp

    print(f"Form terisi → Nama: {data['name']} | WA: {data['phone']} | Email: {data['email']}")

    # Menekan tombol submit
    print("Submit clicked!")
    page.click('.submit-button')  # Klik tombol submit

    time.sleep(3)  # Tunggu beberapa detik untuk memastikan halaman merespons

    # Memperpanjang waktu tunggu dan menunggu elemen yang menunjukkan berhasil
    try:
        # Tunggu hingga 30 detik untuk mendeteksi teks "Checkout berhasil"
        page.wait_for_selector('h2:text("Checkout berhasil")', timeout=30000)  # Waktu tunggu 30 detik
        print("✅ Checkout berhasil terdeteksi!")
        return True
    except Exception as e:
        print(f"❌ Checkout berhasil tidak terdeteksi. Error: {e}")
        return False


# ===== Main: LOOP sampai Ctrl+C =====
if __name__ == "__main__":
    with sync_playwright() as p:
        
        # --- Fitur 1: Pilihan Headless ---
        print("Jalankan mode headless? (tanpa UI browser) (y/n) [default: n]: ", end="", flush=True)
        headless_input = sys.stdin.readline().strip().lower()
        is_headless = headless_input == 'y'
        print(f"Mode headless: {'Aktif' if is_headless else 'Non-Aktif'}")

        browser = p.firefox.launch(headless=is_headless)  # Luncurkan browser Firefox
        target = ask_url()
        page = browser.new_page()

        # --- Fitur 2: Muat Stats ---
        total_runs, success_runs, failed_runs = load_stats()

        try:
            while True:
                # Iterasi dihitung berdasarkan total_runs yang sudah ada
                current_run_number = total_runs + 1
                print(f"\n=== Iterasi #{current_run_number} ===")
                try:
                    # Menggunakan 'page' yang sudah dibuat
                    ok = do_order_once(page, target, timeout=90) 
                    if ok:
                        success_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"❌ Error iterasi #{current_run_number}: {e}")
                    failed_runs += 1
                
                # Update total runs setelah iterasi selesai
                total_runs += 1

                time.sleep(random.uniform(1.0, 3.0))

        except KeyboardInterrupt:
            print("\n=== Dihentikan oleh pengguna (Ctrl+C) ===")
        finally:
            print(f"\nRekap: total={total_runs}, sukses={success_runs}, gagal={failed_runs}")
            
            # --- Fitur 2: Simpan Stats ---
            save_stats(total_runs, success_runs, failed_runs)
            
            browser.close()  # Tutup browser setelah selesai