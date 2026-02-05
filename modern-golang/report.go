package main

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/go-pdf/fpdf"
	"github.com/joho/godotenv"
	"github.com/shirou/gopsutil/v3/disk"
)

func init() {
	// Load environment variables from .env file
	err := godotenv.Load()
	if err != nil {
		fmt.Println("⚠️  Warning: .env file not found")
	}
}

func getDiscordWebhookURL() string {
	webhookURL := os.Getenv("DISCORD_WEBHOOK_URL")
	if webhookURL == "" {
		fmt.Println("❌ ERROR: DISCORD_WEBHOOK_URL not found in .env file")
		os.Exit(1)
	}
	return webhookURL
}

func getStorageInfo() (totalGB, usedGB, percent float64) {
	d, err := disk.Usage("/")
	if err != nil {
		return 0.0, 0.0, 0.0
	}

	totalGB = float64(d.Total) / (1024 * 1024 * 1024)
	usedGB = float64(d.Used) / (1024 * 1024 * 1024)
	percent = (float64(d.Used) / float64(d.Total)) * 100

	return float64(int(totalGB*100)) / 100,
		float64(int(usedGB*100)) / 100,
		float64(int(percent*10)) / 10
}

func runReport() {
	fmt.Println("1. Membaca Data Log Harian...")

	// 1. BACA DATA LOG HARIAN
	filenameCSV := "daily_log_go.csv"
	dataRows := [][]string{}

	if _, err := os.Stat(filenameCSV); err == nil {
		file, err := os.Open(filenameCSV)
		if err != nil {
			fmt.Println("❌ Error: Tidak bisa membuka file CSV")
			return
		}
		defer file.Close()

		reader := csv.NewReader(file)
		records, err := reader.ReadAll()
		if err != nil {
			fmt.Println("❌ Error: Gagal membaca CSV:", err)
			return
		}

		// Skip header
		for i := 1; i < len(records); i++ {
			if len(records[i]) >= 7 {
				dataRows = append(dataRows, records[i])
			}
		}
	}

	// Hitung Rata-rata
	var avgCPU, avgTemp, avgRAM, avgPing, avgDL, avgUL float64
	storageTotal, storageUsed, storagePercent := getStorageInfo()

	if len(dataRows) > 0 {
		var totalCPU, totalTemp, totalRAM, totalPing, totalDL, totalUL float64

		for _, row := range dataRows {
			if cpu, err := strconv.ParseFloat(row[1], 64); err == nil {
				totalCPU += cpu
			}
			if temp, err := strconv.ParseFloat(row[2], 64); err == nil {
				totalTemp += temp
			}
			if ram, err := strconv.ParseFloat(row[3], 64); err == nil {
				totalRAM += ram
			}
			if ping, err := strconv.ParseFloat(row[4], 64); err == nil {
				totalPing += ping
			}
			if dl, err := strconv.ParseFloat(row[5], 64); err == nil {
				totalDL += dl
			}
			if ul, err := strconv.ParseFloat(row[6], 64); err == nil {
				totalUL += ul
			}
		}

		count := float64(len(dataRows))
		avgCPU = totalCPU / count
		avgTemp = totalTemp / count
		avgRAM = totalRAM / count
		avgPing = totalPing / count
		avgDL = totalDL / count
		avgUL = totalUL / count
	}

	// Setup File
	todayStr := time.Now().Format("2006-01-02")
	dynamicFilename := fmt.Sprintf("/tmp/Laporan_Server_Golang_%s.pdf", todayStr)

	// --- BUAT PDF ---
	pdf := fpdf.New("P", "mm", "A4", "")
	pdf.AddPage()

	// PENTING: Translator untuk menangani simbol derajat (°) agar tidak error/aneh
	tr := pdf.UnicodeTranslatorFromDescriptor("")

	// Judul
	pdf.SetFont("Arial", "B", 16)
	pdf.CellFormat(0, 10, "LAPORAN MONITORING SERVER (Golang)", "", 1, "C", false, 0, "")

	pdf.SetFont("Arial", "I", 10)
	pdf.CellFormat(0, 10, fmt.Sprintf("Tanggal: %s", todayStr), "", 1, "C", false, 0, "")
	pdf.Ln(5)

	// --- BAGIAN 1: RANGKUMAN ---
	// Background Abu-abu untuk Header
	pdf.SetFillColor(230, 230, 230)
	pdf.SetFont("Arial", "B", 12)
	// Border="1", Align="L", Fill=true
	pdf.CellFormat(0, 10, "1. Rangkuman Rata-rata (24 Jam)", "1", 1, "L", true, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "", 10)

	// Baris 1: Hardware (Pakai CellFormat dengan border "1")
	// Parameter CellFormat: (w, h, text, border, ln, align, fill, link, linkStr)
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("CPU: %.1f%%", avgCPU)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("Suhu: %.1f°C", avgTemp)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(70, 8, tr(fmt.Sprintf("RAM: %.2f GB", avgRAM)), "1", 1, "L", false, 0, "") // ln=1 (ganti baris)

	// Baris 2: Storage
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("Storage: %.1f/%.1f GB", storageUsed, storageTotal)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("Disk Usage: %.1f%%", storagePercent)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(70, 8, "", "1", 1, "L", false, 0, "")

	// Baris 3: Internet
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("Download: %.1f Mbps", avgDL)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(60, 8, tr(fmt.Sprintf("Upload: %.1f Mbps", avgUL)), "1", 0, "L", false, 0, "")
	pdf.CellFormat(70, 8, tr(fmt.Sprintf("Ping: %.0f ms", avgPing)), "1", 1, "L", false, 0, "")
	pdf.Ln(8)

	// --- BAGIAN 2: TABEL DETAIL ---
	pdf.SetFont("Arial", "B", 12)
	pdf.SetFillColor(230, 230, 230)
	pdf.CellFormat(0, 10, "2. Detail Per Jam", "1", 1, "L", true, 0, "")
	pdf.Ln(2)

	// Header Tabel
	pdf.SetFont("Arial", "B", 9)
	w_jam, w_cpu, w_suhu, w_ram, w_ping, w_dl, w_ul := 18.0, 18.0, 20.0, 25.0, 18.0, 30.0, 30.0

	// Gunakan CellFormat dengan Align="C" (Center) dan Border="1"
	pdf.CellFormat(w_jam, 8, "Jam", "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_cpu, 8, "CPU%", "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_suhu, 8, tr("Suhu°C"), "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_ram, 8, "RAM(GB)", "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_ping, 8, "Ping", "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_dl, 8, "DL(Mbps)", "1", 0, "C", false, 0, "")
	pdf.CellFormat(w_ul, 8, "UL(Mbps)", "1", 1, "C", false, 0, "")

	// Isi Tabel
	pdf.SetFont("Arial", "", 9)
	for _, row := range dataRows {
		pdf.CellFormat(w_jam, 8, row[0], "1", 0, "C", false, 0, "")
		pdf.CellFormat(w_cpu, 8, row[1]+"%", "1", 0, "C", false, 0, "")

		// Suhu Merah jika > 60°C
		if temp, err := strconv.ParseFloat(row[2], 64); err == nil && temp > 60 {
			pdf.SetTextColor(255, 0, 0)
		}
		pdf.CellFormat(w_suhu, 8, tr(row[2]+"°"), "1", 0, "C", false, 0, "")
		pdf.SetTextColor(0, 0, 0) // Reset Hitam

		pdf.CellFormat(w_ram, 8, row[3]+" GB", "1", 0, "C", false, 0, "")

		// Format Ping (hilangkan desimal jika ada)
		valPing := row[4]
		if p, err := strconv.ParseFloat(row[4], 64); err == nil {
			valPing = fmt.Sprintf("%.0f", p)
		}
		pdf.CellFormat(w_ping, 8, valPing, "1", 0, "C", false, 0, "")

		pdf.CellFormat(w_dl, 8, row[5]+" Mbps", "1", 0, "C", false, 0, "")
		pdf.CellFormat(w_ul, 8, row[6]+" Mbps", "1", 1, "C", false, 0, "")
	}

	// Output File
	err := pdf.OutputFileAndClose(dynamicFilename)
	if err != nil {
		fmt.Println("❌ Gagal membuat PDF:", err)
		return
	}

	// Kirim ke Discord
	fmt.Printf("3. Mengirim ke Discord: %s\n", dynamicFilename)
	sendToDiscordGolang(dynamicFilename, todayStr, avgRAM, avgTemp, avgDL, storagePercent)

	// Bersih-bersih
	os.Remove(dynamicFilename)
	// os.Remove(filenameCSV) // Optional: Hapus CSV jika mau reset harian
	fmt.Println("Selesai.")
}

func sendToDiscordGolang(filename, todayStr string, avgRAM, avgTemp, avgDL, storagePercent float64) {
	fmt.Println("🚀 Mengirim laporan ke Discord...")

	file, err := os.Open(filename)
	if err != nil {
		fmt.Println("❌ Gagal buka file PDF:", err)
		return
	}
	defer file.Close()

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	caption := fmt.Sprintf("📊 **Daily Report (%s)**\n💾 RAM: %.2fGB | 🌡️ Suhu: %.1f°C | 🚀 DL: %.1fMbps | 💿 Disk: %.1f%%",
		todayStr, avgRAM, avgTemp, avgDL, storagePercent)

	_ = writer.WriteField("content", caption)

	part, err := writer.CreateFormFile("file", fmt.Sprintf("Laporan_Golang_%s.pdf", todayStr))
	if err != nil {
		return
	}
	_, err = io.Copy(part, file)
	if err != nil {
		return
	}

	writer.Close()

	req, _ := http.NewRequest("POST", getDiscordWebhookURL(), body)
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("❌ Gagal mengirim ke Discord:", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 || resp.StatusCode == 204 {
		fmt.Println("✅ SUKSES! Laporan PDF terkirim dengan format tabel rapi.")
	} else {
		fmt.Printf("⚠️ Gagal kirim. Status: %d\n", resp.StatusCode)
	}
}
