import subprocess
import time
import os

# --- KONFIGURASI ---
TERMINAL_PROGRAM = "gnome-terminal"  # Ganti jika perlu (konsole, xterm)
PROJECT_PATH = "~/Documents/BotSpamMe/"
SCRIPT_NAME = "tzuchi-V2.py"
# --- SELESAI KONFIGURASI ---

# 1. Tanyakan jumlah terminal
while True:
    try:
        terminal_count = int(input("Berapa banyak terminal yang ingin dibuka? (angka): "))
        if terminal_count > 0:
            break
        else:
            print("Masukkan angka lebih dari 0.")
    except ValueError:
        print("Input tidak valid. Masukkan angka.")

print(f"\n--- 🤖 Mempersiapkan {terminal_count} Terminal Tes Lokal ---")
print("Skrip akan berjalan otomatis. Tutup setiap terminal secara manual untuk berhenti.")

# 2. Siapkan perintah sederhana
full_project_path = os.path.expanduser(PROJECT_PATH)

# Perintahnya sekarang jauh lebih simpel:
# 1. Pindah ke direktori
# 2. Aktifkan venv
# 3. Jalankan skrip (tidak perlu 'pipe' input lagi)
shell_command = (
    f"cd {full_project_path} && "
    f"source venv/bin/activate && "
    f"python3 {SCRIPT_NAME}; "
    f"echo 'Skrip tes lokal selesai atau crash. Tekan Enter untuk menutup.' && read"
)

# 3. Buka terminal baru sebanyak yang diminta
for i in range(terminal_count):
    print(f"Membuka terminal ke-{i+1}...")
    
    if TERMINAL_PROGRAM == "gnome-terminal":
        terminal_cmd = [TERMINAL_PROGRAM, '--', 'bash', '-c', shell_command]
    elif TERMINAL_PROGRAM == "konsole":
        terminal_cmd = [TERMINAL_PROGRAM, '-e', 'bash', '-c', shell_command]
    elif TERMINAL_PROGRAM == "xterm":
        terminal_cmd = [TERMINAL_PROGRAM, '-e', 'bash', '-c', shell_command]
    else:
        print(f"Program terminal '{TERMINAL_PROGRAM}' tidak didukung.")
        continue

    subprocess.Popen(terminal_cmd)
    
    # Beri jeda agar sistem Anda tidak kaget
    time.sleep(1)

print("\n--- ✅ Semua terminal tes telah diluncurkan ---")
print("Anda bisa menutup terminal peluncur ini.")