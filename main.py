import pyfiglet
import requests
import shutil
import subprocess
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkAnalyzer:
    def __init__(self):
        self.public_ip = self._get_self_ip()
        self.seen_ips = set()
        self.api_url = "http://ip-api.com/json/"

    def _get_self_ip(self):
        """Fetches the local machine's public IP to filter out self-traffic."""
        try:
            return requests.get('https://api.ipify.org', timeout=5).text
        except requests.RequestException:
            logging.warning("Could not fetch public IP. Filtering might be limited.")
            return "0.0.0.0"

    def fetch_geo_data(self, ip):
        """Retrieves geolocation and ISP data for a given IP address."""
        try:
            response = requests.get(f"{self.api_url}{ip}", timeout=5)
            if response.status_code == 429:
                return "Rate limit exceeded (429)"
            
            data = response.json()
            if data.get('status') == 'success':
                return f"[{data.get('country')}] {data.get('city')} | ISP: {data.get('isp')}"
            return f"Data unavailable: {data.get('message')}"
        except Exception as e:
            return f"Query error: {str(e)}"

    def start_capture(self, interface):
        """Initiates tshark subprocess to capture STUN packets."""
        display_filter = f"stun.type == 0x0101 && stun.att.ipv4 && stun.att.ipv4 != {self.public_ip}"
        
        cmd = [
            "sudo", "tshark", "-i", interface, "-f", "udp",
            "-Y", display_filter, "-T", "fields", "-e", "stun.att.ipv4", "-l"
        ]

        logging.info(f"Starting capture on interface {interface}...")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in iter(process.stdout.readline, ''):
                target_ip = line.strip().split(',')[0]
                if target_ip and target_ip not in self.seen_ips:
                    geo_info = self.fetch_geo_data(target_ip)
                    print(f"\n[+] NEW TARGET DETECTED: {target_ip}")
                    print(f"    Location: {geo_info}")
                    self.seen_ips.add(target_ip)
                    time.sleep(1) 
        except KeyboardInterrupt:
            logging.info("Capture stopped by user.")
            process.terminate()

if __name__ == "__main__":
    print(pyfiglet.figlet_format("Speech ip leaker"))
    print("Developed by aydogan60 | Network Security Tool\n")

    if not shutil.which("tshark"):
        logging.error("Tshark not found. Please install Wireshark/Tshark.")
        sys.exit(1)

    subprocess.run(["sudo", "tshark", "-D"])
    iface = input("\nSelect Interface Index: ")
    
    analyzer = NetworkAnalyzer()
    analyzer.start_capture(iface)