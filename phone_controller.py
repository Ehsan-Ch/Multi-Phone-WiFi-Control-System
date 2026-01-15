import subprocess
import json
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class PhoneController:
    def __init__(self):
        self.devices = []
        self.scan_devices()
    
    def scan_devices(self):
        """Scan for all connected Android devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            self.devices = []
            for line in lines:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    self.devices.append(device_id)
            print(f"Found {len(self.devices)} device(s): {self.devices}")
            return self.devices
        except Exception as e:
            print(f"Error scanning devices: {e}")
            return []
    
    def execute_command(self, device_id: str, command: str) -> Dict:
        """Execute ADB command on specific device"""
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'device_id': device_id,
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'device_id': device_id,
                'success': False,
                'error': 'Command timeout'
            }
        except Exception as e:
            return {
                'device_id': device_id,
                'success': False,
                'error': str(e)
            }
    
    def execute_all(self, command: str, parallel: bool = True) -> List[Dict]:
        """Execute command on all devices"""
        if not self.devices:
            print("No devices connected!")
            return []
        
        results = []
        
        if parallel:
            with ThreadPoolExecutor(max_workers=len(self.devices)) as executor:
                futures = {
                    executor.submit(self.execute_command, device_id, command): device_id
                    for device_id in self.devices
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for device_id in self.devices:
                results.append(self.execute_command(device_id, command))
        
        return results
    
    def tap(self, device_id: str, x: int, y: int):
        """Tap on screen coordinates"""
        return self.execute_command(device_id, f'input tap {x} {y}')
    
    def tap_all(self, x: int, y: int):
        """Tap on all devices"""
        return self.execute_all(f'input tap {x} {y}')
    
    def swipe(self, device_id: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe on screen"""
        return self.execute_command(
            device_id,
            f'input swipe {x1} {y1} {x2} {y2} {duration}'
        )
    
    def swipe_all(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe on all devices"""
        return self.execute_all(f'input swipe {x1} {y1} {x2} {y2} {duration}')
    
    def input_text(self, device_id: str, text: str):
        """Input text (requires keyboard to be open)"""
        # Escape special characters
        text = text.replace(' ', '%s').replace('&', '\\&')
        return self.execute_command(device_id, f'input text "{text}"')
    
    def input_text_all(self, text: str):
        """Input text on all devices"""
        text = text.replace(' ', '%s').replace('&', '\\&')
        return self.execute_all(f'input text "{text}"')
    
    def press_key(self, device_id: str, keycode: str):
        """Press a key (HOME, BACK, MENU, etc.)"""
        return self.execute_command(device_id, f'input keyevent {keycode}')
    
    def press_key_all(self, keycode: str):
        """Press key on all devices"""
        return self.execute_all(f'input keyevent {keycode}')
    
    def get_screen_info(self, device_id: str) -> Dict:
        """Get screen dimensions - uses override size if available (for coordinate mapping)"""
        import re
        
        # Get wm size output
        result = self.execute_command(device_id, 'wm size')
        if result['success']:
            output = result['output'].strip()
            
            # IMPORTANT: Use "Override size" if available, because that's what Android uses for input coordinates!
            # If Android has display scaling enabled, input coordinates must match the override size, not physical size
            override_match = re.search(r'Override size:\s*(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if override_match:
                width = int(override_match.group(1))
                height = int(override_match.group(2))
                return {'width': width, 'height': height, 'is_override': True}
            
            # If no override, use physical size
            physical_match = re.search(r'Physical size:\s*(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if physical_match:
                width = int(physical_match.group(1))
                height = int(physical_match.group(2))
                return {'width': width, 'height': height, 'is_override': False}
            
            # Fallback: use any size found
            match = re.search(r'(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return {'width': width, 'height': height, 'is_override': False}
        
        # Alternative: Try using dumpsys window displays
        result = self.execute_command(device_id, 'dumpsys window displays')
        if result['success']:
            output = result['output']
            # Look for mDisplayWidth and mDisplayHeight
            width_match = re.search(r'mDisplayWidth=(\d+)', output)
            height_match = re.search(r'mDisplayHeight=(\d+)', output)
            if width_match and height_match:
                width = int(width_match.group(1))
                height = int(height_match.group(2))
                return {'width': width, 'height': height}
        
        return {'width': 0, 'height': 0}
    
    def install_app(self, device_id: str, apk_path: str) -> Dict:
        """Install APK on device"""
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'install', apk_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                'device_id': device_id,
                'success': 'Success' in result.stdout,
                'output': result.stdout
            }
        except Exception as e:
            return {
                'device_id': device_id,
                'success': False,
                'error': str(e)
            }
    
    def install_app_all(self, apk_path: str) -> List[Dict]:
        """Install APK on all devices"""
        results = []
        with ThreadPoolExecutor(max_workers=len(self.devices)) as executor:
            futures = {
                executor.submit(self.install_app, device_id, apk_path): device_id
                for device_id in self.devices
            }
            for future in as_completed(futures):
                results.append(future.result())
        return results
    
    def launch_app(self, device_id: str, package_name: str, activity_name: str):
        """Launch an app"""
        return self.execute_command(
            device_id,
            f'am start -n {package_name}/{activity_name}'
        )
    
    def launch_app_all(self, package_name: str, activity_name: str):
        """Launch app on all devices"""
        return self.execute_all(f'am start -n {package_name}/{activity_name}')
    
    def take_screenshot(self, device_id: str, save_path: str = None):
        """Take screenshot"""
        if save_path is None:
            save_path = f'screenshot_{device_id}.png'
        try:
            subprocess.run(
                ['adb', '-s', device_id, 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
                check=True
            )
            subprocess.run(
                ['adb', '-s', device_id, 'pull', '/sdcard/screenshot.png', save_path],
                check=True
            )
            return {'device_id': device_id, 'success': True, 'path': save_path}
        except Exception as e:
            return {'device_id': device_id, 'success': False, 'error': str(e)}
    
    def get_device_info(self, device_id: str) -> Dict:
        """Get device information"""
        info = {}
        commands = {
            'model': 'getprop ro.product.model',
            'brand': 'getprop ro.product.brand',
            'android_version': 'getprop ro.build.version.release',
            'serial': 'getprop ro.serialno'
        }
        for key, cmd in commands.items():
            result = self.execute_command(device_id, cmd)
            if result['success']:
                info[key] = result['output'].strip()
        return info


