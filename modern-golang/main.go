package main

import (
        "flag"
        "fmt"
        "os"
)

func main() {
        // Definisikan Flag (Argumen baris perintah)
        // Contoh: ./monitor-app --report
        reportMode := flag.Bool("report", false, "Generate PDF Report from CSV")
        logMode := flag.Bool("log", false, "Run Monitoring & Log to CSV")

        flag.Parse()

        // Logika Percabangan
        if *reportMode {
                // Jika ada flag --report, jalankan fungsi dari report.go
                runReport()
        } else if *logMode {
                // Jika ada flag --log, jalankan fungsi dari monitor.go
                runMonitor()
        } else {
                // Jika tidak ada flag apa-apa
                fmt.Println("⚠️  Harap gunakan argumen:")
                fmt.Println("   ./monitor-app --log     (Untuk mencatat data)")
                fmt.Println("   ./monitor-app --report  (Untuk membuat PDF)")
                os.Exit(1)
        }
}