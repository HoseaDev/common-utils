#!/usr/bin/env python3
import subprocess
import time
import string
import itertools
import argparse
from typing import Iterator, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Lock
import math
import os
from datetime import datetime


def check_whois_installed():
    """检查whois命令是否已安装"""
    try:
        subprocess.run(['which', 'whois'], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print("错误: 未找到whois命令")
        print("\n请安装whois:")
        print("Ubuntu/Debian: sudo apt-get install whois")
        print("CentOS/RHEL:   sudo yum install whois")
        print("Alpine:        apk add whois")
        return False


class DomainChecker:
    def __init__(self, tld: str = "xyz", sleep_time: float = 1.0, num_threads: int = 4):
        """
        Initialize the domain checker
        
        Args:
            tld: Top-level domain (e.g., 'xyz', 'com')
            sleep_time: Time to sleep between checks to avoid rate limiting
            num_threads: Number of worker threads to use
        """
        
        if num_threads > 10:
            num_threads = 10
        self.tld = tld.strip('.')
        self.sleep_time = sleep_time
        self.num_threads = num_threads
        self.print_lock = Lock()  # Lock for synchronized printing
        
        # Create log directory and files
        self.log_dir = "domains_log"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.available_file = os.path.join(self.log_dir, f"available_domains_{timestamp}.txt")
        self.registered_file = os.path.join(self.log_dir, f"registered_domains_{timestamp}.txt")
        
        # Create files with headers
        with open(self.available_file, 'w') as f:
            f.write(f"Available Domains (TLD: .{self.tld})\n")
            f.write("=" * 50 + "\n")
        
        with open(self.registered_file, 'w') as f:
            f.write(f"Registered Domains (TLD: .{self.tld})\n")
            f.write("=" * 50 + "\n")

    def write_to_file(self, domain: str, is_available: bool):
        """Write domain status to appropriate file"""
        target_file = self.available_file if is_available else self.registered_file
        with self.print_lock:
            with open(target_file, 'a') as f:
                f.write(f"{domain}\n")

    def generate_sequence(self, start: str, end: str) -> Iterator[str]:
        """
        Generate a sequence of strings between start and end
        
        Args:
            start: Starting string/number
            end: Ending string/number
            
        Yields:
            Sequential strings between start and end
        """
        # If both start and end are numeric
        if start.isdigit() and end.isdigit():
            # Determine padding length
            pad_length = max(len(start), len(end))
            start_num = int(start)
            end_num = int(end)
            
            for num in range(start_num, end_num + 1):
                yield str(num).zfill(pad_length)
        
        # If both are alphabetic
        elif start.isalpha() and end.isalpha() and len(start) == len(end):
            # Convert to list of characters for manipulation
            start_chars = list(start.lower())
            end_chars = list(end.lower())
            
            # Generate all possible combinations
            current = start_chars[:]
            while current <= end_chars:
                yield ''.join(current)
                # Increment string
                for i in range(len(current) - 1, -1, -1):
                    if current[i] < 'z':
                        current[i] = chr(ord(current[i]) + 1)
                        break
                    current[i] = 'a'
        else:
            raise ValueError("Start and end must both be either numeric or alphabetic with same length")

    def check_domain(self, domain: str) -> tuple[str, bool]:
        """
        Check if a domain is available
        
        Args:
            domain: Domain name to check
            
        Returns:
            tuple: (domain, availability_status)
        """
        try:
            result = subprocess.run(['whois', domain], 
                                 capture_output=True, 
                                 text=True)
            is_available = "DOMAIN NOT FOUND" in result.stdout
            
            # Write result to appropriate file
            self.write_to_file(domain, is_available)
            
            # Also print progress to console
            with self.print_lock:
                print(f"Checked: {domain}")
            
            time.sleep(self.sleep_time)  # Rate limiting per thread
            return domain, is_available
        except subprocess.SubprocessError:
            with self.print_lock:
                print(f"Error checking domain {domain}")
            return domain, False

    def check_domains_worker(self, domains: list[str]) -> list[tuple[str, bool]]:
        """
        Worker function to check a batch of domains
        
        Args:
            domains: List of domains to check
            
        Returns:
            list: List of (domain, availability_status) tuples
        """
        results = []
        for domain in domains:
            full_domain = f"{domain}.{self.tld}"
            result = self.check_domain(full_domain)
            results.append(result)
        return results

    def check_domains(self, start: str, end: str):
        """
        Check availability for a range of domains using multiple threads
        
        Args:
            start: Starting string/number
            end: Ending string/number
        """
        print(f"Results will be saved in:\n- {self.available_file}\n- {self.registered_file}")
        
        # Generate all domains first
        domains = list(self.generate_sequence(start, end))
        total_domains = len(domains)
        print(f"Total domains to check: {total_domains}")
        
        # Calculate batch size for each thread
        batch_size = math.ceil(total_domains / self.num_threads)
        
        # Split domains into batches
        domain_batches = [
            domains[i:i + batch_size]
            for i in range(0, total_domains, batch_size)
        ]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit all batches to the thread pool
            future_to_batch = {
                executor.submit(self.check_domains_worker, batch): i
                for i, batch in enumerate(domain_batches)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    with self.print_lock:
                        print(f"Error in batch {batch_num}: {e}")

        # Print summary
        available_count = sum(1 for _, available in results if available)
        print(f"\nScan complete!")
        print(f"Available domains: {available_count}")
        print(f"Registered domains: {len(results) - available_count}")
        print(f"Results have been saved to the files in {self.log_dir}/")
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Check domain availability')
    parser.add_argument('start', help='Starting sequence (e.g., "000000" or "aaa")')
    parser.add_argument('end', help='Ending sequence (e.g., "999999" or "zzz")')
    parser.add_argument('--tld', default='xyz', help='Top-level domain (default: xyz)')
    parser.add_argument('--sleep', type=float, default=1.0,
                       help='Sleep time between checks in seconds (default: 1.0)')
    parser.add_argument('--threads', type=int, default=4,
                       help='Number of worker threads (default: 4)')

    args = parser.parse_args()

    # 检查whois命令是否已安装
    if not check_whois_installed():
        exit(1)

    checker = DomainChecker(
        tld=args.tld,
        sleep_time=args.sleep,
        num_threads=args.threads
    )
    
    try:
        checker.check_domains(args.start, args.end)
    except KeyboardInterrupt:
        print("\nDomain checking interrupted by user")
        print("Partial results have been saved to files")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
