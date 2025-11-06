import sys, re, time, random, shutil, os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager

SUCCESS_KEY = "terimakasih sudah melakukan order"

# ===== Utilities =====
def ask_url():
    print("Masukkan URL OO: ", end="", flush=True)
    url = sys.stdin.readline().strip()
    if not url:
        raise ValueError("URL tidak boleh kosong.")
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def make_driver():
    opts = FirefoxOptions()
    opts.set_preference("intl.accept_languages", "id-ID, id")  # Set language to Indonesian (id-ID)

    service = FirefoxService(GeckoDriverManager().install())
    drv = webdriver.Firefox(service=service, options=opts)
    
    # Increase timeout values
    drv.set_page_load_timeout(90)  # Increased timeout to 90 seconds
    drv.implicitly_wait(20)  # Increased implicit wait to 20 seconds
    
    return drv

def open_url(driver, url):
    driver.get(url)
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "form.checkout"))
    )

# ===== Data dummy =====
def pick_dummy_data():
    names = [
        "Andi Pratama", "Budi Santoso", "Cahyo Nugroho", "Deni Saputra", "Eko Wibowo",
        "Fajar Ramadhan", "Gilang Saputra", "Hendra Kurniawan", "Irfan Maulana", "Joko Susilo", "Joko", "Anies", "Prabowo", "Budi", "Shibal", "Anjing", "Nugroho", "Hai hai"
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

def is_thank_you_page(driver):
    """Check if the 'Thank You' page is loaded by looking for the thank you confirmation element."""
    try:
        # Looking for a unique element indicating a 'Thank You' page (e.g., a specific header or message)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".thankyou")))
        return True
    except TimeoutException:
        return False

# ===== One-shot flow =====
def do_order_once(driver, target, timeout=90):
    wait = WebDriverWait(driver, timeout)
    open_url(driver, target)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.checkout")))

    # Filling out necessary form fields only
    data = pick_dummy_data()

    # Mengisi Nama Lengkap
    fill_text_optional(driver, wait, '#user_name', data["name"], must=True)
    # Mengisi Email
    fill_text_optional(driver, wait, '#user_email', data["email"], must=True)
    # Mengisi Nomor WhatsApp
    fill_text_optional(driver, wait, '#user_phone', data["phone"], must=True)

    print(f"Form terisi → Nama: {data['name']} | WA: {data['phone']} | Email: {data['email']}")

    # No need to interact with other fields (like quantity, product selection)

    old_url = driver.current_url
    old_handles = driver.window_handles
    original_handle = driver.current_window_handle

    # Mengklik tombol submit (submit-button)
    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".submit-button")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)

    print("Klik tombol submit…")
    time.sleep(1.0)

    success = False
    try:
        # Wait for 30 seconds after submit to ensure page loads
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".thankyou")))

        if is_thank_you_page(driver):
            print("✅ Halaman Terima Kasih terdeteksi!")
            # Kembali ke halaman checkout
            driver.close()  # Tutup tab baru
            driver.switch_to.window(original_handle)
            driver.get(target)  # Kembali ke halaman checkout

            success = True
        else:
            print("❌ Halaman Terima Kasih tidak ditemukan.")
    except TimeoutException:
        print("❌ Timeout: Halaman tidak ditemukan dalam waktu yang ditentukan.")

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
                ok = do_order_once(driver, target, timeout=90)
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
