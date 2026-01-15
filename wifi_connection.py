import subprocess
import time
import socket
import re
from typing import List, Dict

class WiFiADBManager:
    def __init__(self):
        self.devices = []
        self.master_device = None
        self.slave_devices = []
    
    def get_usb_devices(self) -> List[str]:
        """Get devices connected via USB (for initial WiFi setup)"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                check=True
            )
            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            return devices
        except Exception as e:
            print(f"Error getting USB devices: {e}")
            return []
    
    def get_device_ip(self, device_id: str) -> str:
        """Get device IP address"""
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'ip', 'addr', 'show', 'wlan0'],
                capture_output=True,
                text=True,
                check=True
            )
            # Extract IP from output
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error getting IP for {device_id}: {e}")
        return None
    
    def connect_device_wifi(self, device_id: str, port: int = 5555) -> bool:
        """Connect device via WiFi"""
        ip = self.get_device_ip(device_id)
        if not ip:
            print(f"Could not get IP for device {device_id}")
            return False
        
        try:
            # Enable TCP/IP on device
            subprocess.run(
                ['adb', '-s', device_id, 'tcpip', str(port)],
                check=True,
                capture_output=True
            )
            time.sleep(2)
            
            # Connect via WiFi
            result = subprocess.run(
                ['adb', 'connect', f'{ip}:{port}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if 'connected' in result.stdout.lower():
                print(f"[OK] Connected {device_id} via WiFi at {ip}:{port}")
                return True
            else:
                print(f"[FAIL] Failed to connect {device_id}")
                return False
        except Exception as e:
            print(f"Error connecting {device_id} via WiFi: {e}")
            return False
    
    def connect_all_wifi(self, port: int = 5555):
        """Connect all USB devices to WiFi"""
        usb_devices = self.get_usb_devices()
        if not usb_devices:
            print("No USB devices found! Connect phones via USB first.")
            return []
        
        print(f"Found {len(usb_devices)} USB device(s). Connecting via WiFi...")
        connected = []
        
        for device_id in usb_devices:
            if self.connect_device_wifi(device_id, port):
                connected.append(device_id)
            time.sleep(1)
        
        return connected
    
    def get_wifi_devices(self) -> List[str]:
        """Get all devices connected via WiFi"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                check=True
            )
            wifi_devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    if ':' in device_id:  # WiFi devices have IP:PORT format
                        wifi_devices.append(device_id)
            return wifi_devices
        except Exception as e:
            print(f"Error getting WiFi devices: {e}")
            return []
    
    def set_master_device(self, device_id: str):
        """Set master device (the one you'll control)"""
        self.master_device = device_id
        print(f"Master device set to: {device_id}")
    
    def set_slave_devices(self, device_ids: List[str]):
        """Set slave devices (will mirror master actions)"""
        self.slave_devices = device_ids
        print(f"Slave devices set: {device_ids}")
    
    def disconnect_all(self):
        """Disconnect all WiFi devices"""
        devices = self.get_wifi_devices()
        for device in devices:
            try:
                subprocess.run(['adb', 'disconnect', device], check=True)
                print(f"Disconnected {device}")
            except:
                pass


# Quick setup function
def setup_wifi_connection():
    """Interactive setup for WiFi connection"""
    manager = WiFiADBManager()
    
    print("=== WiFi ADB Setup ===\n")
    print("Step 1: Connect all phones via USB")
    print("Step 2: Enable USB Debugging on all phones")
    print("Step 3: Make sure all phones are on the same WiFi network\n")
    
    input("Press Enter when all phones are connected via USB...")
    
    # Connect all devices via WiFi
    connected = manager.connect_all_wifi()
    
    if connected:
        print(f"\n[OK] Successfully connected {len(connected)} device(s) via WiFi")
        print("\nYou can now disconnect USB cables!")
        
        # Get WiFi devices
        wifi_devices = manager.get_wifi_devices()
        print(f"\nWiFi devices: {wifi_devices}")
        
        if len(wifi_devices) >= 2:
            # Set first as master, rest as slaves
            manager.set_master_device(wifi_devices[0])
            manager.set_slave_devices(wifi_devices[1:])
            print(f"\nMaster: {wifi_devices[0]}")
            print(f"Slaves: {wifi_devices[1:]}")
    else:
        print("\n✗ No devices connected. Check USB connection and try again.")


if __name__ == "__main__":
    setup_wifi_connection()


