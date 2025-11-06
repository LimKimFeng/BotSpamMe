import json, time, sys, os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SCREENSHOT_DIR = "screenshots"
URL = "https://almai.id/referral/scalpinghack"

# create folders
Path(SCREENSHOT_DIR).mkdir(exist_ok=True)


def ask_for_file(prompt_text, default_filename=None):
    """Prompt user for file path and validate existence."""
    while True:
        file_input = input(f"{prompt_text} ").strip().strip('"').strip("'")
        if not file_input and default_filename:
            file_input = default_filename
        if not file_input:
            print("❌ Tidak boleh kosong. Silakan masukkan nama file.")
            continue
        path = Path(file_input)
        if path.exists() and path.is_file():
            return path
        print(f"⚠️ File '{file_input}' tidak ditemukan. Coba lagi.")


def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Gagal membaca file JSON '{path}': {e}")
        sys.exit(1)


def save_progress(progress, progress_file):
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def dedupe_key(entry):
    if entry.get("email"):
        return entry["email"].lower().strip()
    return entry.get("whatsapp", "").strip()


def wait_and_click_ultimate(page):
    try:
        page.wait_for_timeout(1000)
        locator = page.locator("button:has-text('ULTIMATE')")
        if locator.count() == 0:
            locator = page.locator("text=ULTIMATE")
        locator.first.click(timeout=8000)
        return True
    except Exception as e:
        print("Warning: gagal klik ULTIMATE:", e)
        return False


def fill_and_submit(page, entry):
    try:
        page.locator("input[name='name']:visible").first.fill(entry["nama_lengkap"])
        page.locator("input[name='phone']:visible").first.fill(entry["whatsapp"])
        page.locator("input[name='email']:visible").first.fill(entry["email"])
        page.locator("input[name='password']:visible").first.fill(entry["password"])
        page.locator("input[name='password_confirmation']:visible").first.fill(entry["konfirmasi_password"])

        try:
            page.locator("input[name='terms']:visible").first.check()
        except:
            cb = page.locator("label:has-text('Saya telah membaca')").locator("..").locator("input[type='checkbox']:visible")
            if cb.count() > 0:
                cb.first.check()

        page.locator("button:has-text('Kirim'):visible").first.click()
        return True, None
    except Exception as e:
        return False, str(e)


def detect_otp(page, timeout=30000):
    start = time.time()
    elapsed = 0
    interval = 1.0
    while elapsed * 1000 < timeout:
        try:
            if page.locator("text=Verifikasi OTP").count() > 0:
                return True, "found_text_Verifikasi_OTP"
            if page.locator("input[name='token']").count() > 0:
                return True, "found_input_name_token"
            if page.locator("input[placeholder*='OTP']").count() > 0:
                return True, "found_placeholder_otp"
            if page.locator("text=Masukkan Kode OTP").count() > 0:
                return True, "found_text_masukkan_kode_otp"
            content = page.content()
            if "OTP" in content or "Masukkan Kode OTP" in content or "Verifikasi OTP" in content:
                return True, "found_in_html"
        except Exception:
            pass
        time.sleep(interval)
        elapsed = time.time() - start
    return False, None


def main(batch_mode=False):
    # === ASK FOR FILES ===
    print("=== PILIH FILE DATA DAN PROGRESS ===")
    data_file = ask_for_file("Masukkan nama/path file data JSON (contoh: data.json):", default_filename="data.json")
    progress_file = ask_for_file("Masukkan nama/path file progress JSON (contoh: progress.json):", default_filename="progress.json")

    data = load_json_file(data_file)
    progress = load_json_file(progress_file) if progress_file.exists() else {}

    total = len(data)
    print(f"✅ Loaded {total} records dari {data_file.name}. Progress file: {progress_file.name}")

    def launch_browser(p):
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        return browser, context, page

    with sync_playwright() as p:
        browser, context, page = launch_browser(p)

        for idx, entry in enumerate(data, start=1):
            key = dedupe_key(entry)
            if key in progress and progress[key].get("status") == "success":
                print(f"[{idx}/{total}] SKIP (already success) {entry.get('email') or entry.get('whatsapp')}")
                continue

            print("\n" + "="*60)
            print(f"[{idx}/{total}] READY: {entry.get('nama_lengkap')} | {entry.get('whatsapp')} | {entry.get('email')}")
            action = "Y"
            if not batch_mode:
                print("Pilihan: (Y) lanjut, (S) skip data ini, (X) stop & save progress")
                action = input("Masukkan pilihan [Y/S/X] (default Y): ").strip().upper() or "Y"
            if action == "S":
                progress.setdefault(key, {})["status"] = "skipped"
                progress[key]["meta"] = entry
                save_progress(progress, progress_file)
                continue
            if action == "X":
                print("User memilih berhenti. Menyimpan progress...")
                save_progress(progress, progress_file)
                break

            try:
                page.goto(URL, timeout=30000)
            except Exception as e:
                print("ERROR: gagal buka URL:", e)
                progress.setdefault(key, {})["status"] = "error"
                progress[key]["error"] = f"nav_error: {e}"
                save_progress(progress, progress_file)
                continue

            print("Menunggu 10 detik agar halaman load + modal muncul...")
            page.wait_for_timeout(10_000)

            clicked = wait_and_click_ultimate(page)
            if not clicked:
                print("Gagal klik ULTIMATE.")
                fname = f"{SCREENSHOT_DIR}/error_ult_{idx}.png"
                page.screenshot(path=fname)
                progress.setdefault(key, {})["status"] = "error"
                progress[key]["error"] = "click_ultimate_failed"
                progress[key]["screenshot"] = fname
                save_progress(progress, progress_file)
                continue

            print("Klik ULTIMATE -> tunggu 10 detik ...")
            page.wait_for_timeout(10_000)

            print("Akan mengisi data berikut:")
            print(json.dumps(entry, indent=2, ensure_ascii=False))

            ok, err = fill_and_submit(page, entry)
            if not ok:
                print("Gagal mengisi form:", err)
                fname = f"{SCREENSHOT_DIR}/fill_error_{idx}.png"
                page.screenshot(path=fname)
                progress.setdefault(key, {})["status"] = "error"
                progress[key]["error"] = f"fill_error: {err}"
                progress[key]["screenshot"] = fname
                save_progress(progress, progress_file)
                continue

            print("Form disubmit. Menunggu 30 detik untuk respon / OTP ...")
            otp_found, reason = detect_otp(page, timeout=30_000)
            if otp_found:
                print(f"✅ OTP detected (reason: {reason}) — restart browser session")
                progress.setdefault(key, {})["status"] = "otp_required"
                progress[key]["meta"] = entry
                progress[key]["otp_detected_reason"] = reason
                fname = f"{SCREENSHOT_DIR}/otp_{idx}.png"
                page.screenshot(path=fname)
                progress[key]["screenshot"] = fname
                save_progress(progress, progress_file)

                try:
                    context.close()
                    browser.close()
                except:
                    pass
                time.sleep(3)
                browser, context, page = launch_browser(p)
                continue
            else:
                print("Tidak menemukan OTP setelah 30s.")
                fname = f"{SCREENSHOT_DIR}/no_otp_{idx}.png"
                page.screenshot(path=fname)
                htmlfile = f"{SCREENSHOT_DIR}/no_otp_{idx}.html"
                with open(htmlfile, "w", encoding="utf-8") as fh:
                    fh.write(page.content())
                progress.setdefault(key, {})["status"] = "no_otp_detected"
                progress[key]["meta"] = entry
                progress[key]["screenshot"] = fname
                progress[key]["html_dump"] = htmlfile
                save_progress(progress, progress_file)

            print("Selesai record ini. Delay 2s sebelum record berikutnya.")
            page.wait_for_timeout(2000)

        print("Semua proses selesai. Menyimpan progress terakhir.")
        save_progress(progress, progress_file)
        context.close()
        browser.close()


if __name__ == "__main__":
    batch = False
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        batch = True
    main(batch_mode=batch)
