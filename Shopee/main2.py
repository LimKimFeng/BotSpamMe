import pandas as pd
import math
import sys
import os

def update_harga_shopee(input_file, output_file, persentase_kenaikan):
    """
    Membaca file CSV atau XLSX template Shopee, menaikkan harga produk sekian persen,
    dan menyimpannya ke file baru dengan format yang sama.
    """
    
    # --- Konfigurasi ---
    PRICE_COLUMN_INDEX = 6 
    HEADER_ROWS = 6
    # --- Selesai Konfigurasi ---

    # Tentukan ekstensi file untuk membaca dan menulis
    _ , file_extension = os.path.splitext(input_file)

    try:
        print(f"Membaca file '{input_file}'...")
        
        # 1. Baca file berdasarkan ekstensinya
        if file_extension == '.csv':
            df = pd.read_csv(input_file, header=None, keep_default_na=False, dtype=str)
        
        elif file_extension in ['.xlsx', '.xls']:
            # Ganti engine ke 'xlrd' karena 'openpyxl' sering error dengan format Shopee
            # Pastikan Anda sudah install: pip install xlrd
            # Jika 'xlrd' juga error, coba Solusi 1 (simpan sebagai CSV)
            df = pd.read_excel(input_file, header=None, keep_default_na=False, dtype=str, engine='xlrd')
        
        else:
            print(f"ERROR: Format file '{file_extension}' tidak didukung. Harap gunakan .csv atau .xlsx.")
            return

        print("File berhasil dibaca.")

    except FileNotFoundError:
        print(f"ERROR: File input '{input_file}' tidak ditemukan.")
        print("Pastikan nama file dan lokasinya sudah benar.")
        return
    except ImportError:
        print(f"ERROR: Library 'openpyxl' atau 'xlrd' dibutuhkan untuk membaca file .xlsx.")
        print("Silakan install terlebih dahulu dengan perintah:")
        print("pip install openpyxl xlrd")
        return
    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat membaca file: {e}")
        return

    # Hitung faktor pengali
    faktor_pengali = 1 + (persentase_kenaikan / 100.0)
    
    rows_processed = 0
    
    # 2. Iterasi melalui baris data (mulai dari baris setelah header)
    for i in range(HEADER_ROWS, len(df)):
        try:
            # Ambil harga saat ini sebagai string
            current_price_str = df.iat[i, PRICE_COLUMN_INDEX]
            
            # Cek apakah string harga tidak kosong dan bisa dikonversi ke angka
            current_price_numeric = pd.to_numeric(current_price_str, errors='coerce')

            if pd.notna(current_price_numeric):
                current_price = float(current_price_numeric)
                
                # 3. Hitung harga baru (kenaikan persen) dan bulatkan ke atas (ceil)
                #    Ini adalah harga 'kotor' sebelum pembulatan ratusan
                new_price_int = math.ceil(current_price * faktor_pengali)
                
                # 4. (BARU) Bulatkan ke ratusan terdekat
                #    Contoh: 32401 -> 32400 (sesuai permintaan)
                #    Contoh: 32450 -> 32500
                new_price_rounded = round(new_price_int, -2)
                
                # 5. Update nilai di DataFrame sebagai string (menggunakan harga yang sudah dibulatkan)
                df.iat[i, PRICE_COLUMN_INDEX] = str(new_price_rounded)
                rows_processed += 1
                
        except Exception as e:
            print(f"PERINGATAN: Gagal memproses baris {i+1}. Error: {e}. Baris ini dilewati.")
            pass

    # 5. Simpan ke file baru (sesuai format file input)
    try:
        if file_extension == '.csv':
            df.to_csv(output_file, index=False, header=False, encoding='utf-8')
        
        elif file_extension in ['.xlsx', '.xls']:
            df.to_excel(output_file, index=False, header=False, engine='openpyxl')

        print("\n--- PROSES SELESAI ---")
        print(f"Sebanyak {rows_processed} baris produk telah dinaikkan harganya sebesar {persentase_kenaikan}%.")
        print(f"File baru telah disimpan sebagai: {output_file}")

    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat menyimpan file: {e}")

# --- Fungsi Utama untuk Menjalankan Skrip ---
def main():
    print("--- Skrip Update Harga Massal Shopee ---")
    
    # 1. Tanya nama file input
    while True:
        # Mengubah prompt untuk menerima CSV atau XLSX
        input_file = input("Masukkan nama file CSV atau XLSX dari Shopee: ")
        if os.path.exists(input_file):
            break
        else:
            print(f"File '{input_file}' tidak ditemukan. Coba lagi.")

    # Ambil ekstensi file input untuk digunakan di file output
    _ , input_ext = os.path.splitext(input_file)

    # 2. Tanya persentase kenaikan
    while True:
        try:
            persentase = float(input("Masukkan persentase kenaikan (contoh: 10 untuk 10%): "))
            if persentase <= 0:
                print("Masukkan angka positif.")
            else:
                break
        except ValueError:
            print("Input tidak valid. Masukkan angka saja.")

    # 3. Tanya nama file output
    # Memberi contoh ekstensi file yang sesuai
    output_file = input(f"Masukkan nama untuk file BARU (contoh: harga_baru{input_ext}): ")
    
    # Cek apakah user mengetik ekstensi atau tidak
    _ , output_ext = os.path.splitext(output_file)
    if output_ext == "":
        # Jika tidak, tambahkan ekstensi yang sama dengan file input
        output_file += input_ext
        print(f"Ekstensi {input_ext} ditambahkan. Nama file: {output_file}")

    # 4. Jalankan fungsi update
    update_harga_shopee(input_file, output_file, persentase)

if __name__ == "__main__":
    main()