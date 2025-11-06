import sys, re, time, random
from playwright.sync_api import sync_playwright

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

# ===== One-shot flow =====
def do_order_once(browser, target, timeout=90):
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
        print("❌ Checkout berhasil tidak terdeteksi.")
        return False


# ===== Main: LOOP sampai Ctrl+C =====
if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # Luncurkan browser Firefox
        target = ask_url()
        page = browser.new_page()

        total_runs = 0
        success_runs = 0
        failed_runs = 0

        try:
            while True:
                total_runs += 1
                print(f"\n=== Iterasi #{total_runs} ===")
                try:
                    ok = do_order_once(browser, target, timeout=90)
                    if ok:
                        success_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"❌ Error iterasi #{total_runs}: {e}")
                    failed_runs += 1

                time.sleep(random.uniform(1.0, 3.0))

        except KeyboardInterrupt:
            print("\n=== Dihentikan oleh pengguna (Ctrl+C) ===")
        finally:
            print(f"\nRekap: total={total_runs}, sukses={success_runs}, gagal={failed_runs}")
            browser.close()  # Tutup browser setelah selesai
