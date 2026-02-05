package main

import (
        "encoding/csv"
        "fmt"
        "log"
        "math"
        "os"
        "strconv"
        "strings"
        "time"

        "github.com/shirou/gopsutil/v3/cpu"
        "github.com/shirou/gopsutil/v3/disk"
        "github.com/shirou/gopsutil/v3/mem"
        "github.com/showwin/speedtest-go/speedtest"
)

func getCPUTemp() float64 {
        data, err := os.ReadFile("/sys/class/thermal/thermal_zone0/temp")
        if err != nil {
                return 0.0
        }

        tempStr := strings.TrimSpace(string(data))
        temp, err := strconv.ParseFloat(tempStr, 64)
        if err != nil {
                return 0.0
        }

        return temp / 1000.0 // Convert milidegree to Celcius
}

func runMonitor() {
        v, _ := mem.VirtualMemory()
        c, _ := cpu.Percent(time.Second, false)
        d, _ := disk.Usage("/")
        cpuTemp := getCPUTemp()

        var downloadSpeed, uploadSpeed float64
        var pingLatency int64

        st := speedtest.New()
        serverList, err := st.FetchServers()
        if err == nil {
                targets, _ := serverList.FindServer([]int{})
                if len(targets) > 0 {
                        for _, s := range targets {
                                s.PingTest(nil)
                                s.DownloadTest()
                                s.UploadTest()

                                pingLatency = s.Latency.Milliseconds()
                                downloadSpeed = float64(s.DLSpeed) * 8 / 1000000
                                uploadSpeed = float64(s.ULSpeed) * 8 / 1000000
                        }
                }
        }

        // Bersihkan layar terminal biar enak dilihat
        fmt.Print("\033[H\033[2J")
        fmt.Println("⚡ MONITORING SERVER V2 (GOLANG) ⚡")
        fmt.Println("==================================================")

        ramUsed := float64(v.Used) / math.Pow(1024, 3)
        ramTotal := float64(v.Total) / math.Pow(1024, 3)
        diskUsed := float64(d.Used) / math.Pow(1024, 3)
        diskTotal := float64(d.Total) / math.Pow(1024, 3)

        fmt.Printf("🖥️  CPU Load    : %.2f%%\n", c[0])
        fmt.Printf("🌡️  CPU Temp     : %.1f°C\n", cpuTemp)
        fmt.Printf("🧠 RAM Usage    : %.2f / %.2f GB (%.1f%%)\n", ramUsed, ramTotal, v.UsedPercent)
        fmt.Printf("💾 Disk Usage   : %.2f / %.2f GB (%.1f%%)\n", diskUsed, diskTotal, d.UsedPercent)
        fmt.Println("--------------------------------------------------")
        fmt.Printf("📡 Ping         : %d ms\n", pingLatency)
        fmt.Printf("⬇️  Download     : %.2f Mbps\n", downloadSpeed)
        fmt.Printf("⬆️  Upload       : %.2f Mbps\n", uploadSpeed)
        fmt.Println("==================================================")

        // Nama file kita bedakan dulu biar tidak menimpa log Python
        filename := "daily_log_go.csv"

        // Buka file dengan mode: APPEND (tambah bawah), CREATE (bikin kalau belum ada), WRONLY (tulis saja)
        file, err := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
        if err != nil {
                log.Fatalf("Gagal membuka file CSV: %s", err)
        }
        defer file.Close()

        writer := csv.NewWriter(file)
        defer writer.Flush()

        // Cek apakah file kosong? Kalau kosong, tulis Header dulu
        fileInfo, _ := file.Stat()
        if fileInfo.Size() == 0 {
                header := []string{"Jam", "CPU_%", "Suhu_C", "RAM_GB", "Ping_ms", "DL_Mbps", "UL_Mbps"}
                writer.Write(header)
        }

        // Siapkan data baris baru (format sama dengan Python)
        jam := time.Now().Format("15:04")
        record := []string{
                jam,
                fmt.Sprintf("%.1f", c[0]),  // CPU_%
                fmt.Sprintf("%.1f", cpuTemp),  // Suhu_C
                fmt.Sprintf("%.2f", ramUsed),  // RAM_GB
                fmt.Sprintf("%.1f", float64(pingLatency)),  // Ping_ms
                fmt.Sprintf("%.2f", downloadSpeed),  // DL_Mbps
                fmt.Sprintf("%.2f", uploadSpeed),  // UL_Mbps
        }

        // Tulis data
        if err := writer.Write(record); err != nil {
                log.Fatalln("Gagal menulis record ke CSV:", err)
        }

        fmt.Printf("✅ Data berhasil disimpan ke %s\n", filename)
}