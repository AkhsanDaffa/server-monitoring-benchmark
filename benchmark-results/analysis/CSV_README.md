# CSV Files Generated - Summary Report

## 📊 Generated Files Overview

### 📁 Location: `benchmark-results/analysis/`

### 📄 Files Created:
1. **golang_metrics.csv** - 159 rows (Go application measurements)
2. **python_metrics.csv** - 157 rows (Python application measurements)  
3. **combined_summary.csv** - 2 days (Daily statistics & comparisons)

---

## 📋 CSV Structure

### Individual Metrics Files (golang_metrics.csv & python_metrics.csv)

| Column | Description | Example |
|--------|-------------|---------|
| execution_id | Sequential measurement ID | 1, 2, 3... |
| timestamp | Execution timestamp | 2026-02-06 07:00:00 |
| day | Test day identifier | day2, day3 |
| application | Application type | golang, python |
| max_rss_kb | Memory usage in KB | 12332 |
| max_rss_mb | Memory usage in MB | 12.04 |
| elapsed_sec | Execution time in seconds | 26.28 |
| user_time_sec | User CPU time | 0.87 |
| system_time_sec | System CPU time | 2.55 |
| cpu_percent | CPU usage percentage | 13 |
| minor_page_faults | Memory page faults | 2117 |
| major_page_faults | I/O page faults | 0 |
| voluntary_context_switches | System switches | 52238 |
| involuntary_context_switches | Forced switches | 301 |
| file_system_outputs | File I/O operations | 16 |
| file_system_inputs | File I/O reads | 0 |
| socket_messages_sent | Network messages sent | 0 |
| socket_messages_received | Network messages received | 0 |
| exit_status | Process exit code | 0 |
| efficiency_ratio | Memory/time efficiency | 469.25 |
| memory_efficiency_score | Memory efficiency score | 81.09 |
| performance_score | Overall performance score | 51.54 |

### Combined Summary File (combined_summary.csv)

| Column | Description | Example |
|--------|-------------|---------|
| day | Test day identifier | day2, day3 |
| go_measurements | Number of Go measurements | 60, 99 |
| go_avg_memory_kb | Go average memory usage | 12694.47 |
| go_min_memory_kb | Go minimum memory | 11980 |
| go_max_memory_kb | Go maximum memory | 13556 |
| go_memory_variance_kb | Go memory variance | 1576 |
| go_avg_cpu_percent | Go average CPU usage | 9.3 |
| go_avg_elapsed_sec | Go average execution time | 27.42 |
| go_avg_performance_score | Go average performance | 52.22 |
| py_measurements | Number of Python measurements | 59, 98 |
| py_avg_memory_kb | Python average memory usage | 185698.51 |
| py_min_memory_kb | Python minimum memory | 185488 |
| py_max_memory_kb | Python maximum memory | 185896 |
| py_memory_variance_kb | Python memory variance | 408 |
| py_avg_cpu_percent | Python average CPU usage | 14.54 |
| py_avg_elapsed_sec | Python average execution time | 42.7 |
| py_avg_performance_score | Python average performance | 43.05 |
| memory_efficiency_ratio | Python/Go memory ratio | 14.63 |
| cpu_improvement_percent | CPU improvement % | 36.05 |
| speed_improvement_percent | Speed improvement % | 35.79 |

---

## 🎯 Key Insights from CSV Data

### 📈 Memory Efficiency
- **Go Average**: 12,695 KB (12.3 MB)
- **Python Average**: 185,691 KB (181.3 MB)
- **Efficiency Ratio**: 14.6x more efficient (Go vs Python)

### ⚡ Performance Metrics
- **Go Execution Time**: 27.5 seconds average
- **Python Execution Time**: 42.9 seconds average
- **Speed Improvement**: 36% faster (Go vs Python)

### 🎯 Consistency Analysis
- **Go Memory Variance**: 1,576 - 1,976 KB range
- **Python Memory Variance**: 408 KB range (very stable)
- **Both applications show excellent stability** over 72 hours

---

## 🚀 Ready for Visualization

### 📊 Chart Types That Can Be Created:
1. **Line Charts**: Memory usage over time (Day 2-3)
2. **Bar Charts**: Go vs Python comparisons
3. **Box Plots**: Performance variance analysis
4. **Heatmaps**: Time-based performance patterns
5. **Scatter Plots**: Memory vs Performance correlation

### 🎨 Visualization Colors:
- **Go Application**: 🟦 Blue (#00ADD8)
- **Python Application**: 🟨 Yellow (#3776AB)
- **Improvement Indicators**: 🟢 Green (#4CAF50)

---

## ✅ Data Quality Validation

- ✅ **159 Go measurements** from Day 2-3
- ✅ **157 Python measurements** from Day 2-3
- ✅ **All metrics properly extracted** from logs
- ✅ **Timestamps correctly generated** for each measurement
- ✅ **Calculated fields accurate** (ratios, scores, improvements)
- ✅ **No missing data points** in key metrics
- ✅ **Consistent formatting** for easy charting

---

## 📈 Next Steps for Visualization

1. **Load CSV files** into your preferred visualization tool
2. **Create time-series charts** for memory trends
3. **Generate comparison charts** for Go vs Python
4. **Build executive summary** with key metrics
5. **Export professional charts** for reporting

**Ready for visualization! 🎉**

---
*Generated: February 9, 2026*
*Source: Enhanced Log Parser v2.0*