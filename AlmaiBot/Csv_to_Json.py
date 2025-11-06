import csv
import json
import os
import sys
import re

COMMON_NAME_KEYS = ['name', 'full name', 'nama', 'nama_lengkap', 'nama lengkap']
COMMON_EMAIL_KEYS = ['email', 'e-mail', 'alamat email']
COMMON_PHONE_KEYS = ['phone', 'phone number', 'phone_number', 'hp', 'handphone', 'whatsapp', 'nohp', 'no_hp', 'telephone', 'tel']

def normalize_header(h):
    return re.sub(r'[^a-z0-9]', '', h.strip().lower())

def guess_columns(headers):
    norm = {h: normalize_header(h) for h in headers}
    name_col = email_col = phone_col = None
    for h in headers:
        nh = norm[h]
        if any(k.replace(' ', '') == nh for k in COMMON_NAME_KEYS) and name_col is None:
            name_col = h
        if any(k.replace('-', '').replace(' ', '') == nh for k in COMMON_EMAIL_KEYS) and email_col is None:
            email_col = h
        if any(k.replace('_','') == nh for k in COMMON_PHONE_KEYS) and phone_col is None:
            phone_col = h
    # fallback heuristics if not found
    if not name_col:
        for h in headers:
            if 'name' in h.lower() or 'nama' in h.lower():
                name_col = h
                break
    if not email_col:
        for h in headers:
            if 'email' in h.lower() or 'e-mail' in h.lower():
                email_col = h
                break
    if not phone_col:
        # try common positions from screenshot: columns C (index 2), D (3), E (4) — but we can't assume index.
        for h in headers:
            if any(s in h.lower() for s in ['phone', 'hp', 'whatsapp', 'no', 'tel']):
                phone_col = h
                break
    return name_col, email_col, phone_col

def normalize_phone(raw):
    if raw is None:
        return ''
    s = str(raw).strip()
    if s == '':
        return ''
    # remove spaces, parentheses, dashes, plus signs
    s = re.sub(r'[()\s\-\+\.]', '', s)
    # if starts with 0 and length plausible, convert to 62...
    if s.startswith('0'):
        s = '62' + s[1:]
    # if starts with '8' and length plausible (Indo mobile without leading 0), add 62
    if s.startswith('8') and len(s) >= 8 and not s.startswith('62'):
        s = '62' + s
    return s

def read_csv_with_sniffer(path):
    with open(path, 'rb') as fb:
        sample = fb.read(2048)
    # try utf-8 first, fallback to latin1
    try_enc = ['utf-8', 'latin-1', 'cp1252']
    for enc in try_enc:
        try:
            text_sample = sample.decode(enc)
            break
        except Exception:
            text_sample = None
    if text_sample is None:
        enc = 'utf-8'
    else:
        enc = enc
    with open(path, 'r', encoding=enc, errors='replace') as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows

def main():
    print("=== CSV → JSON konversi (skema: nama_lengkap, whatsapp, email, password, konfirmasi_password) ===")
    csv_path = input("Masukkan path file CSV (contoh: orders.csv): ").strip()
    if not os.path.isfile(csv_path):
        print("File tidak ditemukan:", csv_path)
        sys.exit(1)

    print("Membaca file:", csv_path)
    headers, rows = read_csv_with_sniffer(csv_path)
    if not headers:
        print("Gagal mendeteksi header pada CSV.")
        sys.exit(1)
    print("Header terdeteksi:", headers)

    name_col, email_col, phone_col = guess_columns(headers)
    print("Kolom tebakan:")
    print(" - name  =>", name_col)
    print(" - email =>", email_col)
    print(" - phone =>", phone_col)
    # jika ada kolom yang belum ditemukan, beritahu user dan tanyakan nama kolom manual
    if not name_col:
        name_col = input("Kolom untuk 'name' tidak terdeteksi. Masukkan nama header kolom yang berisi nama: ").strip()
    if not email_col:
        email_col = input("Kolom untuk 'email' tidak terdeteksi. Masukkan nama header kolom yang berisi email: ").strip()
    if not phone_col:
        phone_col = input("Kolom untuk 'phone' tidak terdeteksi. Masukkan nama header kolom yang berisi nomor telepon/WA: ").strip()

    out_name = input("Mau simpan hasil JSON dengan nama file apa? (contoh: hasil.json): ").strip()
    if out_name == '':
        out_name = 'hasil.json'
    # ensure extension
    if not out_name.lower().endswith('.json'):
        out_name += '.json'

    total = len(rows)
    converted = 0
    skipped = 0
    dup_count = 0
    seen_keys = set()
    results = []
    print("\nMulai konversi ...")
    for i, r in enumerate(rows, start=1):
        # show small progress per 50 rows or final
        if i % 50 == 1:
            print(f"  memproses baris {i}/{total} ...")

        # fetch values safely
        name = (r.get(name_col) or r.get(name_col.strip()) or '').strip() if name_col else ''
        email = (r.get(email_col) or r.get(email_col.strip()) or '').strip() if email_col else ''
        phone = (r.get(phone_col) or r.get(phone_col.strip()) or '').strip() if phone_col else ''

        # some CSVs might have comma-separated multiple columns in single header; handle basic cases
        # normalize phone
        whatsapp_norm = normalize_phone(phone)

        # decide key for dedupe: prefer whatsapp then email
        key = whatsapp_norm if whatsapp_norm else (email.lower() if email else '')
        if not key:
            # can't dedupe or identify row, skip
            skipped += 1
            continue
        if key in seen_keys:
            dup_count += 1
            continue
        seen_keys.add(key)

        # if name or email missing, we still include row but we can flag -- here we include but keep empty
        entry = {
            "nama_lengkap": name,
            "whatsapp": whatsapp_norm,
            "email": email,
            "password": "12345678",
            "konfirmasi_password": "12345678"
        }
        results.append(entry)
        converted += 1

    # write json
    with open(out_name, 'w', encoding='utf-8') as fo:
        json.dump(results, fo, ensure_ascii=False, indent=2)

    # summary
    print("\n=== Selesai ===")
    print(f"Total baris sumber  : {total}")
    print(f"Berhasil dikonversi : {converted}")
    print(f"Dilewati (tanpa key) : {skipped}")
    print(f"Duplikat terdeteksi  : {dup_count}")
    print(f"File JSON tersimpan di: {os.path.abspath(out_name)}")
    print(f"Total objek JSON     : {len(results)}")
    print("Contoh 3 entri pertama (jika ada):")
    for e in results[:3]:
        print(json.dumps(e, ensure_ascii=False))
    print("\nKalau mau: kamu bisa jalankan lagi dengan file berbeda, atau buka file JSON untuk verifikasi.")

if __name__ == '__main__':
    main()
