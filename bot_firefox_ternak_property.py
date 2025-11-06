import sys, re, time, random, shutil, os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager  # <-- ganti ke firefox manager

SUCCESS_KEY = "terimakasih sudah melakukan order"

# ===== Utilities =====
def ask_url():
    print("Masukkan URL OO (contoh: https://ddaacademy.orderonline.id/AS-SeminarAkuisisiProperti-Medan): ", end="", flush=True)
    url = sys.stdin.readline().strip()
    if not url:
        raise ValueError("URL tidak boleh kosong.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url

def make_driver():
    opts = FirefoxOptions()
    # opts.add_argument("--headless")  # aktifkan kalau mau headless
    # Bahasa + kurangi fingerprint automation
    opts.set_preference("intl.accept_languages", "id-ID, id")
    opts.set_preference("dom.webdriver.enabled", False)

    # ===== Penting di Linux Mint/Snap: pastikan binary Firefox ketemu =====
    # coba deteksi otomatis lokasi firefox
    firefox_bin = shutil.which("firefox") or os.getenv("FIREFOX_BIN")
    if firefox_bin:
        opts.binary_location = firefox_bin
    # catatan: jika firefox via Snap, biasanya: /snap/bin/firefox
    # kalau manual: export FIREFOX_BIN=/path/ke/firefox

    service = FirefoxService(GeckoDriverManager().install())
    drv = webdriver.Firefox(service=service, options=opts)
    drv.set_page_load_timeout(45)
    drv.implicitly_wait(0)
    return drv

def open_url(driver, url):
    driver.get(url)
    WebDriverWait(driver, 25).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "form.orderonline-embed-form"))
    )

# ===== Data dummy =====
def pick_dummy_data():
    names = [
        "Andi Pratama","Budi Santoso","Cahyo Nugroho","Deni Saputra","Eko Wibowo",
        "Fajar Ramadhan","Gilang Saputra","Hendra Kurniawan","Irfan Maulana","Joko Susilo"
    ]
    n = random.choice(names)
    phone = "62" + str(random.randint(8111111111, 8999999999))
    email = n.lower().replace(" ", "") + str(int(time.time()) % 10000) + "@example.com"
    return {"name": n, "phone": phone, "email": email}

# ===== Helpers =====
def fill_text_optional(driver, wait, selector, value, must=False):
    try:
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))) if must \
             else WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    except TimeoutException:
        return False
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.clear()
        el.send_keys(value)
    except Exception:
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            el, value
        )
    return True

def choose_variation_if_any(driver, wait):
    try:
        radios = [r for r in driver.find_elements(By.CSS_SELECTOR, 'input.ooef-product-variation[type="radio"]') if r.is_displayed()]
        if radios:
            choice = random.choice(radios)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", choice)
            if not choice.is_selected():
                choice.click()
            return True
    except Exception:
        pass
    return False

def select2_pick_complete_district(driver, wait, keywords=None, max_wait_each=12):
    if keywords is None:
        keywords = ["Alalak"]

    sel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select[name="complete_district"]')))
    try:
        box = sel.find_element(
            By.XPATH,
            'following-sibling::span[contains(@class,"select2")]/span[@class="selection"]/span[contains(@class,"select2-selection--single")]'
        )
    except Exception:
        box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-selection.select2-selection--single")))

    def selected_ok():
        return driver.execute_script("const s=document.querySelector('select[name=\"complete_district\"]');return !!(s && s.value);")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
    box.click()
    for word in keywords:
        try:
            sf = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".select2-search__field")))
            sf.clear()
            q = word if len(word) >= 3 else (word + "   ")[:3]
            sf.send_keys(q)

            WebDriverWait(driver, max_wait_each).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".select2-results__option:not(.select2-results__message)")) > 0
            )
            opts = driver.find_elements(By.CSS_SELECTOR, ".select2-results__option:not(.select2-results__message)")
            if not opts:
                sf.send_keys("\u001b")
                box.click()
                continue

            target = opts[0]
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            target.click()

            if selected_ok():
                return True
            box.click()
        except Exception:
            try:
                driver.find_element(By.CSS_SELECTOR, ".select2-search__field").send_keys("\u001b")
            except Exception:
                pass
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
            box.click()
            continue

    # fallback: tanam option langsung
    implant = random.choice([
        "Jawa Barat, Kota Bandung, Andir",
        "Kalimantan Selatan, Kab. Barito Kuala, Alalak",
        "Jawa Barat, Kab. Sumedang, Cibugel",
    ])
    ok = driver.execute_script("""
        const text = arguments[0];
        const sel  = document.querySelector('select[name="complete_district"]');
        if (!sel) return false;
        let opt = null;
        for (const o of sel.options) {
          if ((o.textContent||'').trim() === text) { opt = o; break; }
        }
        if (!opt) { opt = document.createElement('option'); opt.value=text; opt.textContent=text; sel.appendChild(opt); }
        sel.value = opt.value;
        sel.dispatchEvent(new Event('change', {bubbles:true}));
        const r = document.querySelector('span.select2-selection__rendered[id^="select2-"][id$="-container"]');
        if (r) { r.textContent = text; r.title = text; }
        return true;
    """, implant)
    return bool(ok)

def is_whatsapp_url(u: str) -> bool:
    u = (u or "").lower()
    return ("wa.me" in u) or ("api.whatsapp.com" in u) or ("web.whatsapp.com" in u) or ("whatsapp.com" in u)

# ===== One-shot flow =====
def do_order_once(driver, target, timeout=60):
    wait = WebDriverWait(driver, timeout)
    open_url(driver, target)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.orderonline-embed-form")))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#field-name")))
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#field-phone")))

    choose_variation_if_any(driver, wait)

    data = pick_dummy_data()
    fill_text_optional(driver, wait, '#field-name',  data["name"], must=True)
    fill_text_optional(driver, wait, '#field-phone', data["phone"], must=True)
    email_filled = fill_text_optional(driver, wait, 'input[name="email"]', data["email"], must=False)
    print(f"Form terisi → Nama: {data['name']} | WA: {data['phone']} | Email: {data['email'] if email_filled else '(tidak ada field)'}")

    ok_city = select2_pick_complete_district(driver, wait)
    print(f"Kota/Kecamatan → {'OK' if ok_city else 'GAGAL'}")

    old_url = driver.current_url
    old_handles = driver.window_handles
    original_handle = driver.current_window_handle

    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#btn-complete-order, .ooef-submit-order")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    print("Klik tombol submit…")
    time.sleep(1.0)

    success = False
    try:
        WebDriverWait(driver, 25).until(
            lambda d: d.current_url != old_url or len(d.window_handles) != len(old_handles)
        )

        new_handles = driver.window_handles
        if len(new_handles) > len(old_handles):
            new_tab = list(set(new_handles) - set(old_handles))[0]
            driver.switch_to.window(new_tab)
            new_url = driver.current_url
            print(f"✅ SUCCESS (tab baru): {new_url}")

            if is_whatsapp_url(new_url):
                print("Menutup tab WhatsApp & kembali ke halaman asal…")
                driver.close()
                driver.switch_to.window(original_handle)
                driver.get(target)
            else:
                driver.switch_to.window(original_handle)
                driver.get(target)

            success = True

        else:
            new_url = driver.current_url
            print(f"✅ SUCCESS (url berubah):\n   {old_url}\n→  {new_url}")

            if is_whatsapp_url(new_url):
                print("Berpindah ke WhatsApp di tab yang sama → buka tab baru ke target & tutup tab ini…")
                driver.switch_to.new_window('tab')
                driver.get(target)
                try:
                    for h in driver.window_handles:
                        driver.switch_to.window(h)
                        if is_whatsapp_url(driver.current_url):
                            driver.close()
                    for h in driver.window_handles:
                        driver.switch_to.window(h)
                        if target.split('://',1)[-1].split('/')[0] in driver.current_url:
                            break
                except Exception:
                    pass
            else:
                driver.get(target)

            success = True

    except TimeoutException:
        print("❌ Belum terdeteksi perubahan URL/tab (submit mungkin gagal / tertahan).")

    return success

# ===== Main: LOOP sampai Ctrl+C =====
if __name__ == "__main__":
    driver = None
    total_runs = 0
    success_runs = 0
    failed_runs = 0
    try:
        target = ask_url()
        driver = make_driver()

        while True:
            total_runs += 1
            print(f"\n=== Iterasi #{total_runs} ===")
            try:
                ok = do_order_once(driver, target, timeout=70)
                if ok:
                    success_runs += 1
                else:
                    failed_runs += 1
            except TimeoutException as e:
                print(f"❌ Timeout iterasi #{total_runs}: {e}")
                failed_runs += 1
            except Exception as e:
                print(f"❌ Error iterasi #{total_runs}: {e}")
                failed_runs += 1

            time.sleep(random.uniform(1.0, 3.0))

    except KeyboardInterrupt:
        print("\n=== Dihentikan oleh pengguna (Ctrl+C) ===")
    finally:
        print(f"\nRekap: total={total_runs}, sukses={success_runs}, gagal={failed_runs}")
        if driver:
            driver.quit()
