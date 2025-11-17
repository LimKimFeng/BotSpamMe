import sys, re, time, random, csv, datetime, os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- KONFIGURASI NAMA FILE ---
LOG_FILE = 'order_log.csv'
REPORT_FILE = 'laporan_order.html'
# ---------------------------

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
    phone = "8" + str(random.randint(111111111, 999999999)) 
    email = n.lower().replace(" ", "") + str(int(time.time()) % 10000) + "@example.com"
    return {"name": n, "phone": phone, "email": email}

# ===== One-shot flow =====
def do_order_once(browser, target, timeout_sec=90):
    """
    Menjalankan satu siklus pemesanan.
    Mengembalikan dictionary berisi status, data, dan pesan error.
    """
    timeout_ms = timeout_sec * 1000  # Timeout umum untuk load
    page = None
    data = pick_dummy_data() # Ambil data dulu, jadi bisa di-log meski gagal
    
    try:
        page = browser.new_page()
        print(f"Membuka URL: {target}")
        page.goto(target, timeout=timeout_ms)
        
        # Jeda 20 detik untuk load awal (sesuai permintaan sebelumnya)
        print("Memberi jeda 20 detik untuk load awal...")
        time.sleep(20)
        
        print("Menunggu form dimuat (wait_for_selector)...")
        page.wait_for_selector('#name', timeout=timeout_ms)
        print("Form terdeteksi. Mulai mengisi data...")

        # Mengisi Form
        print(f"Data: {data['name']} | {data['phone']} | {data['email']}")
        page.fill('#name', data["name"])
        page.fill('#email', data["email"])
        page.fill('#phone', data["phone"])

        print("Mencoba klik tombol 'Pesan!'...")
        page.click('button[type="submit"]')

        # --- PERUBAHAN: Menunggu URL berubah ATAU elemen sukses muncul ---
        print("Menunggu halaman sukses (URL berubah ATAU deteksi 'Status Pembayaran' / 'Order ID')...")
        print(f"URL Asal: {target}")

        # --- PERBAIKAN: JavaScript predicate DIBUAT LEBIH AMAN ---
        # Menambahkan pengecekan 'document.body' untuk menghindari error 'null'
        # saat halaman sedang transisi.
        js_predicate = f"""
        () => {{
            const urlChanged = window.location.href !== "{target}";

            // PERBAIKAN: Cek dulu apakah 'document.body' ada
            const bodyContent = document.body ? document.body.innerText : "";
            
            const elementFound = bodyContent.includes("Status Pembayaran") || bodyContent.includes("Order ID");
            
            return urlChanged || elementFound;
        }}
        """
        
        # Menunggu tanpa batas waktu sampai salah satu kondisi terpenuhi
        page.wait_for_function(js_predicate, timeout=0) 
        
        print(f"✅ Halaman sukses terdeteksi! URL Sekarang: {page.url}")
        return {"status": "Success", "data": data, "error": None}

    except PlaywrightTimeoutError as e:
        # Timeout ini HANYA berlaku untuk load awal (goto) atau
        # deteksi form awal (wait_for_selector('#name')).
        error_msg = f"Timeout {timeout_sec}s: Gagal load form awal atau halaman. ({str(e)})"
        print(f"❌ {error_msg}")
        return {"status": "Failed", "data": data, "error": error_msg}
    except Exception as e:
        print(f"❌ Terjadi error: {e}")
        return {"status": "Failed", "data": data, "error": str(e)}
    finally:
        if page:
            page.close()

# ===== HTML Report Generator =====
def generate_html_report(log_file, report_file, total, success, failed):
    """Membaca file CSV dan membuat laporan HTML statis."""
    if not os.path.exists(log_file):
        print(f"File log {log_file} tidak ditemukan. Laporan tidak dibuat.")
        return

    log_entries = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            log_entries = list(reader)
    except Exception as e:
        print(f"Gagal membaca file log: {e}")
        return

    # Membangun baris tabel HTML
    table_rows_html = ""
    for entry in reversed(log_entries): # Tampilkan data terbaru di atas
        status_color = "text-green-600" if entry.get('status') == 'Success' else "text-red-600"
        error_msg = entry.get('error_message', '-')
        if not error_msg:
            error_msg = '-'
        
        table_rows_html += f"""
        <tr class="hover:bg-gray-50">
            <td class="px-4 py-3 text-sm text-gray-700">{entry.get('timestamp', 'N/A')}</td>
            <td class="px-4 py-3 text-sm font-semibold {status_color}">{entry.get('status', 'N/A')}</td>
            <td class="px-4 py-3 text-sm text-gray-900">{entry.get('name', 'N/A')}</td>
            <td class="px-4 py-3 text-sm text-gray-700">{entry.get('phone', 'N/A')}</td>
            <td class="px-4 py-3 text-sm text-gray-700">{entry.get('email', 'N/A')}</td>
            <td class="px-4 py-3 text-sm text-gray-500">{error_msg}</td>
        </tr>
        """

    # Template HTML lengkap dengan Tailwind CSS
    html_content = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Laporan Bot Order</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; }}
        </style>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="container mx-auto max-w-7xl bg-white shadow-lg rounded-lg p-6">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Laporan Bot Order</h1>
            <p class="text-gray-600 mb-6">Dibuat pada: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

            <!-- Ringkasan Statistik -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                    <h2 class="text-sm font-medium text-blue-700">Total Iterasi</h2>
                    <p class="text-3xl font-bold text-blue-900">{total}</p>
                </div>
                <div class="bg-green-50 border border-green-200 p-4 rounded-lg">
                    <h2 class="text-sm font-medium text-green-700">Sukses</h2>
                    <p class="text-3xl font-bold text-green-900">{success}</p>
                </div>
                <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                    <h2 class="text-sm font-medium text-red-700">Gagal</h2>
                    <p class="text-3xl font-bold text-red-900">{failed}</p>
                </div>
            </div>

            <!-- Tabel Log -->
            <h2 class="text-2xl font-semibold text-gray-800 mb-4">Detail Log</h2>
            <div class="overflow-x-auto rounded-lg border border-gray-200">
                <table class="min-w-full divide-y divide-gray-200 bg-white">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nama</th>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Telepon</th>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                            <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    # Menulis file HTML
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Laporan HTML berhasil dibuat di: {report_file}")
    except Exception as e:
        print(f"Gagal membuat laporan HTML: {e}")


# ===== Main: LOOP sampai Ctrl+C =====
if __name__ == "__main__":
    
    # Pengecekan untuk mode headless
    is_headless = "--headless" in sys.argv
    
    print("="*30)
    print(f"Menjalankan bot dalam mode: {'HEADLESS' if is_headless else 'NON-HEADLESS (terlihat)'}")
    print(f"Log akan disimpan di: {LOG_FILE}")
    print(f"Laporan akan dibuat di: {REPORT_FILE} (saat dihentikan)")
    print("Tekan Ctrl+C untuk berhenti.")
    print("="*30)

    # Inisialisasi file CSV dengan header
    fieldnames = ['timestamp', 'status', 'name', 'phone', 'email', 'error_message']
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            print(f"File log baru dibuat: {LOG_FILE}")
        except IOError as e:
            print(f"Gagal membuat file log {LOG_FILE}: {e}. Keluar.")
            sys.exit(1)
    else:
        print(f"Melanjutkan log di file: {LOG_FILE}")


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

        # Membaca statistik sebelumnya jika file log sudah ada
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_runs += 1
                    if row['status'] == 'Success':
                        success_runs += 1
                    else:
                        failed_runs += 1
            print(f"Melanjutkan dari: {total_runs} iterasi, {success_runs} sukses, {failed_runs} gagal.")
        except Exception as e:
            print(f"Gagal membaca log sebelumnya (mungkin file baru): {e}")
            total_runs = 0
            success_runs = 0
            failed_runs = 0


        try:
            while True:
                total_runs += 1
                print(f"\n=== Iterasi #{total_runs} ===")
                result = {"status": "Failed", "data": {}, "error": "Unknown error"} # Default
                try:
                    result = do_order_once(browser, target, timeout_sec=90) 
                    if result["status"] == "Success":
                        success_runs += 1
                    else:
                        failed_runs += 1
                except Exception as e:
                    print(f"❌ Error iterasi #{total_runs}: {e}")
                    failed_runs += 1
                    result = {"status": "Failed", "data": pick_dummy_data(), "error": str(e)}

                # Mencatat ke CSV
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = {
                    'timestamp': now,
                    'status': result['status'],
                    'name': result['data'].get('name', '-'),
                    'phone': result['data'].get('phone', '-'),
                    'email': result['data'].get('email', '-'),
                    'error_message': result['error'] if result['error'] else ''
                }
                
                try:
                    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow(log_entry)
                except IOError as e:
                    print(f"Peringatan: Gagal menulis ke file log: {e}")

                sleep_time = random.uniform(1.0, 3.0)
                print(f"Tidur selama {sleep_time:.1f} detik...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n=== Dihentikan oleh pengguna (Ctrl+C) ===")
        except Exception as e:
            print(f"\n\n=== Terjadi error tak terduga: {e} ===")
        finally:
            print("\nMenutup browser...")
            browser.close()
            
            # --- Membuat Laporan HTML saat Selesai ---
            print("Membuat laporan HTML akhir...")
            generate_html_report(LOG_FILE, REPORT_FILE, total_runs, success_runs, failed_runs)
            
            print("\n=== REKAP AKHIR (Total Sesi) ===")
            print(f"Total Iterasi : {total_runs}")
            print(f"Sukses        : {success_runs}")
            print(f"Gagal         : {failed_runs}")
            print(f"Log tersimpan di: {LOG_FILE}")
            print(f"Laporan tersimpan di: {REPORT_FILE}")
            print("Selesai.")