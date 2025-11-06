import sys, re, time, random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------- Utilities ----------
def ask_url():
    print("Masukkan URL Target: ", end="", flush=True)
    url = sys.stdin.readline().strip()
    if not url:
        raise ValueError("URL tidak boleh kosong.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url

def make_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    drv.set_page_load_timeout(30)
    return drv

def open_url(driver, url):
    driver.get(url)
    # Tunggu captcha muncul
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#captcha-text"))
    )

def wait_captcha_and_read(driver, length=4, mode='alnum', timeout=10):
    """Ambil teks captcha di layar"""
    if mode == 'digits':
        pattern = re.compile(r'^\d{' + str(int(length)) + r'}$')
    else:  # default alnum
        pattern = re.compile(r'^[A-Za-z0-9]{' + str(int(length)) + r'}$')

    wait = WebDriverWait(driver, timeout, poll_frequency=0.5)

    def _check_and_match(d):
        txt = d.execute_script(
            "return document.getElementById('captcha-text')?.textContent?.trim() || '';"
        )
        if not txt:
            return None
        txt_norm = txt.upper()
        return txt_norm if pattern.fullmatch(txt_norm) else None

    return wait.until(_check_and_match)

def input_captcha(driver, code: str, timeout=10):
    wait = WebDriverWait(driver, timeout)
    inputs = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.kode-input"))
    )
    if len(inputs) < len(code):
        raise ValueError(f"Jumlah input ({len(inputs)}) < panjang kode ({len(code)})")

    for i, ch in enumerate(code):
        try:
            inputs[i].clear()
            inputs[i].send_keys(ch)
        except Exception:
            driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                inputs[i], ch
            )

def submit_gate_form(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit-button"))
    )
    button.click()
    # tunggu gate hilang
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#gate-form-container")))
    # tunggu input muncul
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'form.orderonline-embed-form'))
    )
    return True

# ---------- Isi Form ----------


def input_order(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)
    # tunggu form siap
    form = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.orderonline-embed-form")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", form)
    
    # data dummy
    dummy_data = []

    names = [
        "Cornel Imut",
        "Cornel Ganteng",
        "Cornel Bot",
        "Cornel Ini",
        "Cornel Senang",
        "Hapus saja",
        "Maafkan Cornel",
        "Sorry Elda",
        "Hehe",
        "Cornel Imoy"
    ]

    nowtag = str(int(time.time()) % 10000)  # biar email unik per run
    for n in names:
        phone = "62" + str(random.randint(8111111111, 8999999999))  # nomor random 62...
        email = n.lower().replace(" ", "") + nowtag + "@example.com"
        dummy_data.append({"name": n, "phone": phone, "email": email})

    # Pilih 1 set secara random
    data = random.choice(dummy_data)

    name, phone, email = data["name"], data["phone"], data["email"]
    
    # isi field
    def fill(selector, value):
        fld = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", fld)
        try:
            fld.clear()
            fld.send_keys(value)
        except Exception:
            driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                fld, value
            )
    
    # isi field
    fill('input[name="name"]', name)
    fill('input[name="phone"]', phone)
    fill('input[name="email"]', email)
    
    print(f"Form terisi -> Name: {name} | WA: {phone} | Email: {email}")
    
    # klik submit
    old_url = driver.current_url
    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ooef-submit-order")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    submit_btn.click()
    print("Klik Tombol Beli Sekarang")
    
    # kalau sukses
    key = "terimakasih sudah melakukan order"
    success = False
    try:
        WebDriverWait(driver, 20).until(EC.url_changes(old_url))
        # cek teks
        WebDriverWait(driver, 20).until(lambda d: key in d.page_source.lower())
        success = True
    except TimeoutException:
        success = False
    
    if success:
        print("✅Success melakukan order.")
    else:
        print("❌Belum berhasil melakukan order.")
    
    return success
    

# ---------- Main ----------
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
                open_url(driver, target)
                captcha = wait_captcha_and_read(driver, length=4, mode='alnum', timeout=10)
                print("CAPTCHA terbaca:", captcha)

                input_captcha(driver, captcha)
                print("Captcha berhasil diisi.")

                if submit_gate_form(driver):
                    print("Tombol submit berhasil diklik. ✅ Form berhasil disubmit!")

                ok = input_order(driver, timeout=30)
                if ok:
                    success_runs += 1
                else:
                    failed_runs += 1
                    
            except TimeoutException as e:
                print(f"❌ TimeoutException pada iterasi #{total_runs}: {e}")
                failed_runs += 1
            except Exception as e:
                print(f"❌ Exception pada iterasi #{total_runs}: {e}")
                failed_runs += 1
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print(f"\n=== Dihentikan oleh pengguna ===")
        
    finally:
        print(f"\nRekap: total={total_runs}, sukses={success_runs}, gagal={failed_runs}")
        if driver:
            driver.quit()
