#!/usr/bin/env python3
"""
Server Monitoring Benchmark Log Parser - Enhanced Version
Converts all raw /usr/bin/time -v logs to analysis-ready CSV files

Author: Benchmark Analysis Team
Date: February 9, 2026
Version: 2.0 - Enhanced with multi-day processing
"""

import re
import csv
import os
import datetime as dt
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class BenchmarkLogParser:
    def __init__(self):
        """Initialize parser with regex patterns and file paths"""
        self.base_dir = Path(__file__).parent.parent
        self.raw_logs_dir = self.base_dir / "benchmark-results" / "raw-logs"
        self.analysis_dir = self.base_dir / "benchmark-results" / "analysis"
        
        # Create analysis directory if it doesn't exist
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced regex patterns for comprehensive data extraction
        self.patterns = {
            'max_rss_kb': r'Maximum resident set size \(kbytes\):\s+(\d+)',
            'user_time_sec': r'User time \(seconds\):\s+([\d.]+)',
            'system_time_sec': r'System time \(seconds\):\s+([\d.]+)',
            'cpu_percent': r'Percent of CPU this job got:\s+(\d+)%',
            'elapsed_time': r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s+([\d:.]+)',
            'minor_page_faults': r'Minor \(reclaiming a frame\) page faults:\s+(\d+)',
            'major_page_faults': r'Major \(requiring I/O\) page faults:\s+(\d+)',
            'voluntary_context_switches': r'Voluntary context switches:\s+(\d+)',
            'involuntary_context_switches': r'Involuntary context switches:\s+(\d+)',
            'file_system_inputs': r'File system inputs:\s+(\d+)',
            'file_system_outputs': r'File system outputs:\s+(\d+)',
            'socket_messages_sent': r'Socket messages sent:\s+(\d+)',
            'socket_messages_received': r'Socket messages received:\s+(\d+)',
            'signals_delivered': r'Signals delivered:\s+(\d+)',
            'page_size_bytes': r'Page size \(bytes\):\s+(\d+)',
            'exit_status': r'Exit status:\s+(\d+)'
        }
        
        # Timestamp pattern for log entries
        self.timestamp_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})'
        
        # Command patterns for application detection
        self.go_command_pattern = r'"\.\/monitor-app --log"'
        self.python_command_pattern = r'"\/opt\/monitoring\/env\/bin\/python3.*monitor_server\.py --log"'
        
    def extract_timestamp(self, text: str, execution_id: int, day: str) -> str:
        """Extract timestamp from log block or generate one"""
        lines = text.split('\n')
        for line in lines:
            match = re.search(self.timestamp_pattern, line)
            if match:
                return match.group(1)
        
        # Generate timestamp based on execution_id and day
        base_dates = {
            'day1': datetime(2026, 2, 5, 7, 0, 0),   # Feb 5, 2026 07:00
            'day2': datetime(2026, 2, 6, 7, 0, 0),   # Feb 6, 2026 07:00
            'day3': datetime(2026, 2, 7, 7, 0, 0)    # Feb 7, 2026 07:00
        }
        
        base_date = base_dates.get(day, datetime(2026, 2, 5, 7, 0, 0))
        # Add hours based on execution_id (assuming hourly execution)
        hours_offset = execution_id - 1
        # Add proper datetime handling
        new_datetime = base_date.replace(hour=7) + dt.timedelta(hours=hours_offset)
        return new_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    def convert_elapsed_to_seconds(self, elapsed_str: str) -> float:
        """Convert elapsed time string to seconds"""
        if not elapsed_str or ':' not in elapsed_str:
            return 0.0
            
        parts = elapsed_str.split(':')
        if len(parts) == 2:  # mm:ss format
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:  # h:mm:ss format
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        else:
            return 0.0
    
    def determine_day_from_filename(self, filename: str) -> str:
        """Extract day information from filename"""
        if 'day1' in filename:
            return 'day1'
        elif 'day2' in filename:
            return 'day2'
        elif 'day3' in filename:
            return 'day3'
        else:
            return 'day1'  # Default to day1
    
    def parse_execution_block(self, block: str, app_type: str, execution_id: int, day: str) -> Optional[Dict]:
        """Parse a single execution block from log"""
        data = {
            'execution_id': execution_id,
            'application': app_type,
            'day': day,
            'timestamp': self.extract_timestamp(block, execution_id, day)
        }
        
        # Extract all metrics using regex patterns
        for metric, pattern in self.patterns.items():
            match = re.search(pattern, block, re.MULTILINE)
            if match:
                value = match.group(1)
                try:
                    # Convert to appropriate type
                    if metric == 'elapsed_time':
                        data[metric] = value  # Keep as string for conversion
                    elif 'time' in metric:
                        data[metric] = float(value)
                    elif 'percent' in metric:
                        data[metric] = int(value)
                    elif 'exit_status' in metric:
                        data[metric] = int(value)
                    else:
                        data[metric] = int(value)
                except ValueError:
                    data[metric] = 0
            else:
                data[metric] = 0
        
        # Convert elapsed time to seconds
        elapsed_time_value = data.get('elapsed_time')
        if elapsed_time_value:
            data['elapsed_sec'] = self.convert_elapsed_to_seconds(elapsed_time_value)
        else:
            data['elapsed_sec'] = 0.0
        
        # Calculate derived metrics
        memory_kb = data.get('max_rss_kb', 0)
        elapsed_sec = data.get('elapsed_sec', 0)
        
        if memory_kb > 0:
            data['max_rss_mb'] = round(memory_kb / 1024, 2)
            data['memory_efficiency_score'] = round(1000000 / memory_kb, 2)  # Higher is better
        else:
            data['max_rss_mb'] = 0.0
            data['memory_efficiency_score'] = 0
        
        if memory_kb > 0 and elapsed_sec > 0:
            data['efficiency_ratio'] = round(memory_kb / elapsed_sec, 2)
        else:
            data['efficiency_ratio'] = 0
        
        # Calculate performance score (0-100, higher is better)
        memory_kb = data.get('max_rss_kb', 0)
        if memory_kb > 0:
            memory_score = min(100, 100 * 1024 / memory_kb)  # Based on 1MB as baseline
        else:
            memory_score = 0
            
        cpu_score = max(0, 100 - data.get('cpu_percent', 100))
        speed_score = max(0, 100 - min(data.get('elapsed_sec', 100), 60))
        
        data['performance_score'] = round(
            memory_score * 0.4 + cpu_score * 0.3 + speed_score * 0.3, 2
        )
        
        return data
    
    def split_into_execution_blocks(self, content: str, app_type: str) -> List[str]:
        """Split log content into individual execution blocks"""
        if app_type == 'golang':
            command_pattern = self.go_command_pattern
        else:
            command_pattern = self.python_command_pattern
        
        # Split by "Command being timed:" pattern (more robust)
        sections = re.split(r'Command being timed:', content)
        blocks = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Extract command line to identify valid blocks
            lines = section.split('\n')
            if len(lines) > 5:  # Minimum lines for a valid execution block
                # Add back the "Command being timed:" prefix for consistency
                block = "Command being timed:" + section
                blocks.append(block)
        
        return blocks
    
    def process_log_file(self, file_path: Path) -> Tuple[List[Dict], str]:
        """Process a single log file and return parsed data with app type"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return [], 'unknown'
        
        # Determine application type
        if 'golang' in file_path.name.lower() or 'go_' in file_path.name.lower():
            app_type = 'golang'
        elif 'python' in file_path.name.lower() or 'py_' in file_path.name.lower():
            app_type = 'python'
        else:
            app_type = 'unknown'
        
        # Determine day from filename
        day = self.determine_day_from_filename(file_path.name)
        
        # Split into execution blocks
        blocks = self.split_into_execution_blocks(content, app_type)
        
        # Parse each block
        parsed_data = []
        for i, block in enumerate(blocks, 1):
            parsed = self.parse_execution_block(block, app_type, i, day)
            if parsed:
                parsed_data.append(parsed)
        
        print(f"✅ {file_path.name}: {len(parsed_data)} measurements ({app_type})")
        return parsed_data, app_type
    
    def find_log_files(self) -> List[Path]:
        """Find all benchmark log files in the raw logs directory"""
        if not self.raw_logs_dir.exists():
            print(f"❌ Directory not found: {self.raw_logs_dir}")
            return []
        
        # Look for benchmark log files
        log_files = []
        for pattern in ['bench_go_day*.log', 'bench_py_day*.log', 'bench_go.log', 'bench_py.log']:
            log_files.extend(self.raw_logs_dir.glob(pattern))
        
        return sorted(log_files)
    
    def write_golang_csv(self, data: List[Dict]) -> None:
        """Write Golang data to CSV"""
        if not data:
            print("❌ No Golang data to write")
            return
        
        columns = [
            'execution_id', 'timestamp', 'day', 'application',
            'max_rss_kb', 'max_rss_mb', 'elapsed_sec', 'user_time_sec', 
            'system_time_sec', 'cpu_percent', 'minor_page_faults', 
            'major_page_faults', 'voluntary_context_switches', 
            'involuntary_context_switches', 'file_system_outputs', 
            'file_system_inputs', 'socket_messages_sent', 
            'socket_messages_received', 'exit_status', 'efficiency_ratio',
            'memory_efficiency_score', 'performance_score'
        ]
        
        output_path = self.analysis_dir / 'golang_metrics.csv'
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            
            print(f"✅ Golang CSV created: {len(data)} rows -> {output_path}")
            
        except Exception as e:
            print(f"❌ Error writing Golang CSV: {e}")
    
    def write_python_csv(self, data: List[Dict]) -> None:
        """Write Python data to CSV"""
        if not data:
            print("❌ No Python data to write")
            return
        
        # Same columns as Golang for consistency
        columns = [
            'execution_id', 'timestamp', 'day', 'application',
            'max_rss_kb', 'max_rss_mb', 'elapsed_sec', 'user_time_sec', 
            'system_time_sec', 'cpu_percent', 'minor_page_faults', 
            'major_page_faults', 'voluntary_context_switches', 
            'involuntary_context_switches', 'file_system_outputs', 
            'file_system_inputs', 'socket_messages_sent', 
            'socket_messages_received', 'exit_status', 'efficiency_ratio',
            'memory_efficiency_score', 'performance_score'
        ]
        
        output_path = self.analysis_dir / 'python_metrics.csv'
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)
            
            print(f"✅ Python CSV created: {len(data)} rows -> {output_path}")
            
        except Exception as e:
            print(f"❌ Error writing Python CSV: {e}")
    
    def write_combined_summary(self, go_data: List[Dict], py_data: List[Dict]) -> None:
        """Write combined summary CSV with daily statistics"""
        summary_data = []
        
        # Group data by day
        go_by_day = {}
        py_by_day = {}
        
        for row in go_data:
            day = row['day']
            if day not in go_by_day:
                go_by_day[day] = []
            go_by_day[day].append(row)
        
        for row in py_data:
            day = row['day']
            if day not in py_by_day:
                py_by_day[day] = []
            py_by_day[day].append(row)
        
        # Generate summary for each day
        all_days = sorted(set(go_by_day.keys()) | set(py_by_day.keys()))
        
        for day in all_days:
            go_day_data = go_by_day.get(day, [])
            py_day_data = py_by_day.get(day, [])
            
            # Go statistics
            go_stats = self.calculate_day_statistics(go_day_data)
            
            # Python statistics
            py_stats = self.calculate_day_statistics(py_day_data)
            
            # Calculate efficiency metrics
            memory_efficiency = py_stats['avg_memory_kb'] / go_stats['avg_memory_kb'] if go_stats['avg_memory_kb'] > 0 else 0
            cpu_improvement = ((py_stats['avg_cpu_percent'] - go_stats['avg_cpu_percent']) / py_stats['avg_cpu_percent'] * 100) if py_stats['avg_cpu_percent'] > 0 else 0
            speed_improvement = ((py_stats['avg_elapsed_sec'] - go_stats['avg_elapsed_sec']) / py_stats['avg_elapsed_sec'] * 100) if py_stats['avg_elapsed_sec'] > 0 else 0
            
            summary_row = {
                'day': day,
                'go_measurements': go_stats['count'],
                'go_avg_memory_kb': round(go_stats['avg_memory_kb'], 2),
                'go_min_memory_kb': go_stats['min_memory_kb'],
                'go_max_memory_kb': go_stats['max_memory_kb'],
                'go_memory_variance_kb': go_stats['memory_variance_kb'],
                'go_avg_cpu_percent': round(go_stats['avg_cpu_percent'], 2),
                'go_avg_elapsed_sec': round(go_stats['avg_elapsed_sec'], 2),
                'go_avg_performance_score': round(go_stats['avg_performance_score'], 2),
                'py_measurements': py_stats['count'],
                'py_avg_memory_kb': round(py_stats['avg_memory_kb'], 2),
                'py_min_memory_kb': py_stats['min_memory_kb'],
                'py_max_memory_kb': py_stats['max_memory_kb'],
                'py_memory_variance_kb': py_stats['memory_variance_kb'],
                'py_avg_cpu_percent': round(py_stats['avg_cpu_percent'], 2),
                'py_avg_elapsed_sec': round(py_stats['avg_elapsed_sec'], 2),
                'py_avg_performance_score': round(py_stats['avg_performance_score'], 2),
                'memory_efficiency_ratio': round(memory_efficiency, 2),
                'cpu_improvement_percent': round(cpu_improvement, 2),
                'speed_improvement_percent': round(speed_improvement, 2)
            }
            
            summary_data.append(summary_row)
        
        # Write summary CSV
        columns = [
            'day', 'go_measurements', 'go_avg_memory_kb', 'go_min_memory_kb', 
            'go_max_memory_kb', 'go_memory_variance_kb', 'go_avg_cpu_percent',
            'go_avg_elapsed_sec', 'go_avg_performance_score', 'py_measurements',
            'py_avg_memory_kb', 'py_min_memory_kb', 'py_max_memory_kb',
            'py_memory_variance_kb', 'py_avg_cpu_percent', 'py_avg_elapsed_sec',
            'py_avg_performance_score', 'memory_efficiency_ratio',
            'cpu_improvement_percent', 'speed_improvement_percent'
        ]
        
        output_path = self.analysis_dir / 'combined_summary.csv'
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                writer.writerows(summary_data)
            
            print(f"✅ Combined summary created: {len(summary_data)} days -> {output_path}")
            
        except Exception as e:
            print(f"❌ Error writing combined summary: {e}")
    
    def calculate_day_statistics(self, data: List[Dict]) -> Dict:
        """Calculate statistics for a day's data"""
        if not data:
            return {
                'count': 0, 'avg_memory_kb': 0, 'min_memory_kb': 0,
                'max_memory_kb': 0, 'memory_variance_kb': 0,
                'avg_cpu_percent': 0, 'avg_elapsed_sec': 0,
                'avg_performance_score': 0
            }
        
        memory_values = [row.get('max_rss_kb', 0) for row in data]
        cpu_values = [row.get('cpu_percent', 0) for row in data]
        elapsed_values = [row.get('elapsed_sec', 0) for row in data]
        performance_values = [row.get('performance_score', 0) for row in data]
        
        return {
            'count': len(data),
            'avg_memory_kb': sum(memory_values) / len(memory_values),
            'min_memory_kb': min(memory_values),
            'max_memory_kb': max(memory_values),
            'memory_variance_kb': max(memory_values) - min(memory_values),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'avg_elapsed_sec': sum(elapsed_values) / len(elapsed_values),
            'avg_performance_score': sum(performance_values) / len(performance_values)
        }
    
    def run_parser(self):
        """Main execution method"""
        print("🚀 Starting Enhanced Log Parser v2.0")
        print(f"📁 Input directory: {self.raw_logs_dir}")
        print(f"📁 Output directory: {self.analysis_dir}")
        print()
        
        # Find all log files
        log_files = self.find_log_files()
        
        if not log_files:
            print("❌ No log files found!")
            return
        
        print(f"📄 Found {len(log_files)} log files:")
        for file in log_files:
            print(f"   - {file.name}")
        print()
        
        # Process all files
        all_go_data = []
        all_py_data = []
        
        for file_path in log_files:
            print(f"🔄 Processing {file_path.name}...")
            data, app_type = self.process_log_file(file_path)
            
            if app_type == 'golang':
                all_go_data.extend(data)
            elif app_type == 'python':
                all_py_data.extend(data)
        
        print(f"\n📊 Total measurements found:")
        print(f"   🐹 Golang: {len(all_go_data)} measurements")
        print(f"   🐍 Python: {len(all_py_data)} measurements")
        print()
        
        # Write CSV files
        print("📈 Writing CSV files...")
        
        if all_go_data:
            self.write_golang_csv(all_go_data)
        
        if all_py_data:
            self.write_python_csv(all_py_data)
        
        if all_go_data and all_py_data:
            self.write_combined_summary(all_go_data, all_py_data)
        
        print(f"\n🎉 Parsing completed successfully!")
        print(f"📁 Output files created in: {self.analysis_dir}")
        print()
        print("📋 Generated files:")
        if all_go_data:
            print("   ✅ golang_metrics.csv - Individual Go measurements")
        if all_py_data:
            print("   ✅ python_metrics.csv - Individual Python measurements")
        if all_go_data and all_py_data:
            print("   ✅ combined_summary.csv - Daily statistics & comparisons")
        print()
        print("🚀 Ready for visualization and analysis!")


def main():
    """Main entry point"""
    parser = BenchmarkLogParser()
    parser.run_parser()


if __name__ == "__main__":
    main()