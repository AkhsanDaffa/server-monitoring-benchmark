import re
import csv
import sys

def parse_benchmark_log(input_file, output_csv):
    # Regex untuk menangkap data penting dari output 'time -v'
    patterns = {
        "user_time": r"User time \(seconds\): ([\d\.]+)",
        "sys_time": r"System time \(seconds\): ([\d\.]+)",
        "cpu_usage": r"Percent of CPU this job got: (\d+)%",
        "wall_time": r"Elapsed \(wall clock\) time.*: ([\d:\.]+)",
        "max_ram_kb": r"Maximum resident set size \(kbytes\): (\d+)",
        "page_faults": r"Minor \(reclaiming a frame\) page faults: (\d+)"
    }

    data_rows = []
    current_entry = {}

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Memisahkan setiap blok eksekusi (karena ada banyak run)
    # Kita split berdasarkan "Command being timed"
    blocks = content.split("Command being timed")

    for block in blocks:
        if not block.strip():
            continue
            
        entry = {}
        found_data = False
        
        for key, pattern in patterns.items():
            match = re.search(pattern, block)
            if match:
                entry[key] = match.group(1)
                found_data = True
        
        if found_data:
            # Konversi RAM ke MB biar enak dibaca
            if 'max_ram_kb' in entry:
                entry['max_ram_mb'] = round(int(entry['max_ram_kb']) / 1024, 2)
            
            data_rows.append(entry)

    # Tulis ke CSV
    if data_rows:
        headers = ["user_time", "sys_time", "cpu_usage", "wall_time", "max_ram_kb", "max_ram_mb", "page_faults"]
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"✅ Sukses! Data bersih tersimpan di: {output_csv}")
        print(f"📊 Total data ditemukan: {len(data_rows)} baris")
    else:
        print("❌ Tidak ada data yang cocok ditemukan di log.")

# Cara pakai
if __name__ == "__main__":
    # Ganti nama file sesuai log asli Anda
    parse_benchmark_log("bench_go.log", "clean_benchmark_go.csv")