import psutil
import speedtest
import requests
from fpdf import FPDF
from datetime import datetime
import os
import csv
import time
import argparse
import statistics

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("❌ ERROR: DISCORD_WEBHOOK_URL not found in .env file")
    exit(1)
LOG_FILE = "/opt/monitoring/daily_log.csv"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read()) / 1000.0
    except:
        return 0.0

def get_storage_info():
    try:
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        percent = (disk.used / disk.total) * 100
        return round(total_gb, 2), round(used_gb, 2), round(percent, 1)
    except:
        return 0.0, 0.0, 0.0

def run_speedtest():
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Percobaan Speedtest ke-{attempt}...")
            # secure=True pakai HTTPS (lebih aman tapi kadang sensitif jam/cert)
            # Kalau masih error terus, coba ganti secure=False
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()

            ping = st.results.ping
            dl = st.download() / 1_000_000
            ul = st.upload() / 1_000_000

            return round(ping, 1), round(dl, 2), round(ul, 2)

        except Exception as e:
            error_msg = f"{datetime.now()} - Gagal Percobaan {attempt}: {str(e)}\n"
            print(error_msg)

            # Jika ini percobaan terakhir, baru catat ke log permanent
            if attempt == max_retries:
                with open("/opt/monitoring/error_log.txt", "a") as f:
                    f.write(f"{datetime.now()} - ERROR FINAL Speedtest: {str(e)}\n")
                return 0, 0, 0

            # Jika belum menyerah, tunggu 15 detik sebelum coba lagi
            time.sleep(15)

def log_data():
    print("Mencatat data harian... (Mohon tunggu Speedtest)")
    timestamp = datetime.now().strftime("%H:%M")

    cpu = psutil.cpu_percent(interval=1)
    temp = get_cpu_temp()
    ram = psutil.virtual_memory()

    ping, dl, ul = run_speedtest()

    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Jam", "CPU_%", "Suhu_C", "RAM_GB", "Ping_ms", "DL_Mbps", "UL_Mbps"])

        writer.writerow([
            timestamp,
            round(cpu, 1),
            round(temp, 1),
            round(ram.used/(1024**3), 2),  # Hanya GB yang digunakan
            ping,
            dl,
            ul
        ])

    print(f"Data jam {timestamp} berhasil dicatat (DL: {dl} Mbps).")

def generate_report():
    print("1. Membaca Data Log Harian...")
    data_rows = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='r') as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) >= 8:
                    data_rows.append(row)

    avg_cpu, avg_temp, avg_ram = 0, 0, 0
    avg_ping, avg_dl, avg_ul = 0, 0, 0

    storage_total, storage_used, storage_percent = get_storage_info()

    if data_rows:
        # Index CSV baru: 0=Jam, 1=CPU, 2=Suhu, 3=RAM, 4=Ping, 5=DL, 6=UL
        avg_cpu = statistics.mean([float(r[1]) for r in data_rows])
        avg_temp = statistics.mean([float(r[2]) for r in data_rows])
        avg_ram = statistics.mean([float(r[3]) for r in data_rows])
        avg_ping = statistics.mean([float(r[4]) for r in data_rows])
        avg_dl = statistics.mean([float(r[5]) for r in data_rows])
        avg_ul = statistics.mean([float(r[6]) for r in data_rows])

    # Setup Nama File Tanggal
    today_str = datetime.now().strftime('%Y-%m-%d')
    dynamic_filename = f"/tmp/Laporan_Server_{today_str}.pdf"

    # --- BUAT PDF ---
    pdf = FPDF()
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Laporan Harian Server (Raspi 4)", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Tanggal: {today_str}", ln=True, align='C')
    pdf.ln(5)

    # BAGIAN 1: RANGKUMAN (UPDATE: Tambah Avg Speed)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Rangkuman Rata-rata (24 Jam)", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", size=10)

    # Baris 1: Hardware (Format praktis)
    pdf.cell(60, 8, f"CPU: {avg_cpu:.1f}%", border=1)
    pdf.cell(60, 8, f"Suhu: {avg_temp:.1f}°C", border=1)
    pdf.cell(70, 8, f"RAM: {avg_ram:.2f} GB", border=1, ln=True)

    # Baris 2: Storage (INFO BARU - hanya di rangkuman)
    pdf.cell(60, 8, f"Storage: {storage_used}/{storage_total} GB", border=1)
    pdf.cell(60, 8, f"Disk Usage: {storage_percent}%", border=1)
    pdf.cell(70, 8, "", border=1, ln=True)

    # Baris 3: Internet
    pdf.cell(60, 8, f"Download: {avg_dl:.1f} Mbps", border=1)
    pdf.cell(60, 8, f"Upload: {avg_ul:.1f} Mbps", border=1)
    pdf.cell(70, 8, f"Ping: {avg_ping:.0f} ms", border=1, ln=True)
    pdf.ln(8)

    # BAGIAN 2: TABEL DETAIL (UPDATE: Tambah Kolom Speed)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Detail Per Jam", ln=True, fill=True)
    pdf.ln(2)

    # Header Tabel
    pdf.set_font("Arial", 'B', 9)

    # Layout baru untuk format praktis
    # Jam(18), CPU(18), Suhu(20), RAM(25), Ping(18), DL(30), UL(30) = Total 159mm
    w_jam=18; w_cpu=18; w_suhu=20; w_ram=25; w_ping=18; w_dl=30; w_ul=30

    pdf.cell(w_jam, 8, "Jam", 1, 0, 'C')
    pdf.cell(w_cpu, 8, "CPU%", 1, 0, 'C')
    pdf.cell(w_suhu, 8, "Suhu°C", 1, 0, 'C')
    pdf.cell(w_ram, 8, "RAM(GB)", 1, 0, 'C')
    pdf.cell(w_ping, 8, "Ping", 1, 0, 'C')
    pdf.cell(w_dl, 8, "DL(Mbps)", 1, 0, 'C')
    pdf.cell(w_ul, 8, "UL(Mbps)", 1, 1, 'C') # 1,1 artinya ganti baris

    # Isi Tabel dengan format praktis
    pdf.set_font("Arial", size=9)
    for row in data_rows:
        # row baru: [0:Jam, 1:CPU, 2:Suhu, 3:RAM(GB), 4:Ping, 5:DL, 6:UL]
        pdf.cell(w_jam, 8, row[0], 1, 0, 'C')
        pdf.cell(w_cpu, 8, f"{row[1]}%", 1, 0, 'C')

        # Suhu Merah jika > 60°C
        if float(row[2]) > 60: pdf.set_text_color(255, 0, 0)
        pdf.cell(w_suhu, 8, f"{row[2]}°", 1, 0, 'C')
        pdf.set_text_color(0, 0, 0) # Reset Hitam

        pdf.cell(w_ram, 8, f"{row[3]} GB", 1, 0, 'C')
        pdf.cell(w_ping, 8, f"{float(row[4]):.0f}", 1, 0, 'C')
        pdf.cell(w_dl, 8, f"{row[5]} Mbps", 1, 0, 'C')
        pdf.cell(w_ul, 8, f"{row[6]} Mbps", 1, 1, 'C')

    # Output File
    pdf.output(dynamic_filename)

    # Kirim ke Discord
    print(f"3. Mengirim ke Discord: {dynamic_filename}")

    with open(dynamic_filename, "rb") as f:
        # Caption Discord dengan format praktis
        caption = f"📊 **Daily Report ({today_str})**\n💾 RAM: {avg_ram:.2f}GB | 🌡️ Suhu: {avg_temp:.1f}°C | 🚀 DL: {avg_dl:.1f}Mbps | 💿 Disk: {storage_percent}%"
        files = {"file": (f"Laporan_{today_str}.pdf", f)}
        requests.post(DISCORD_WEBHOOK_URL, data={"content": caption}, files=files)

    # Bersih-bersih
    if os.path.exists(dynamic_filename): os.remove(dynamic_filename)
    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
    print("Selesai.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', action='store_true')
    parser.add_argument('--report', action='store_true')
    args = parser.parse_args()

    if args.log: log_data()
    elif args.report: generate_report()
