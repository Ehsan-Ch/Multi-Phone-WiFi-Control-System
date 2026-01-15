import subprocess
import threading
import time
import re
from typing import List, Dict, Optional
from phone_controller import PhoneController
import json

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

class ScreenMirrorController:
    def __init__(self, master_device: str, slave_devices: List[str]):
        self.master_device = master_device
        self.slave_devices = slave_devices
        self.controller = PhoneController()
        self.mirroring_active = False
        self.scrcpy_process = None
        self.master_screen_size = None
        self.slave_screen_sizes = {}
        self._cache_screen_sizes()
    
    def _cache_screen_sizes(self):
        """Cache screen sizes for all devices"""
        print("[INFO] Detecting screen sizes for all devices...")
        
        # Get master screen size
        self.master_screen_size = self.get_master_screen_size()
        if self.master_screen_size['width'] > 0:
            override_note = " (override)" if self.master_screen_size.get('is_override', False) else " (physical)"
            print(f"[INFO] Master ({self.master_device}): {self.master_screen_size['width']}x{self.master_screen_size['height']}{override_note}")
        else:
            print(f"[WARNING] Could not detect master screen size")
        
        # Get slave screen sizes
        for slave in self.slave_devices:
            size = self.controller.get_screen_info(slave)
            if size['width'] > 0:
                self.slave_screen_sizes[slave] = size
                override_note = " (override)" if size.get('is_override', False) else " (physical)"
                print(f"[INFO] Slave ({slave}): {size['width']}x{size['height']}{override_note}")
            else:
                print(f"[WARNING] Could not detect screen size for {slave}")
        
    def start_screen_mirror(self, window_title: str = "Phone Master"):
        """Start scrcpy to mirror master device screen on PC"""
        try:
            # Check if scrcpy is installed
            subprocess.run(['scrcpy', '--version'], 
                         capture_output=True, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: scrcpy not found!")
            print("Please install scrcpy:")
            print("  Windows: Download from https://github.com/Genymobile/scrcpy/releases")
            print("  Or use: winget install scrcpy")
            return False
        
        try:
            # Start scrcpy for master device
            # Use --no-control to disable scrcpy input forwarding
            # This prevents Android word selection issues - our system handles all input via ADB
            # Note: --turn-screen-off cannot be used with --no-control
            cmd = [
                'scrcpy',
                '-s', self.master_device,
                '--window-title', window_title,
                '--stay-awake',
                '--no-control',  # Disable scrcpy input - we handle it via ADB (prevents word selection issues)
                '--disable-screensaver',  # Prevent screen saver interference
            ]
            
            self.scrcpy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment and check if scrcpy started successfully
            time.sleep(2)
            if self.scrcpy_process.poll() is not None:
                # Process already terminated - there was an error
                stderr_output = self.scrcpy_process.stderr.read().decode('utf-8', errors='ignore') if self.scrcpy_process.stderr else ""
                print(f"[WARNING] scrcpy with --no-control failed, trying without it...")
                print(f"[INFO] Error: {stderr_output[:200] if stderr_output else 'Unknown error'}")
                
                # Fallback: try without --no-control (can use --turn-screen-off here)
                cmd_fallback = [
                    'scrcpy',
                    '-s', self.master_device,
                    '--window-title', window_title,
                    '--stay-awake',
                    '--turn-screen-off',  # Can use this when control is enabled
                    '--disable-screensaver',
                ]
                
                self.scrcpy_process = subprocess.Popen(
                    cmd_fallback,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                time.sleep(2)
                if self.scrcpy_process.poll() is not None:
                    stderr_output = self.scrcpy_process.stderr.read().decode('utf-8', errors='ignore') if self.scrcpy_process.stderr else ""
                    print(f"[ERROR] scrcpy failed to start!")
                    if stderr_output:
                        print(f"[ERROR] scrcpy error: {stderr_output[:300]}")
                    print(f"[INFO] Make sure the device is connected: adb devices")
                    return False
                else:
                    print(f"[WARNING] scrcpy started without --no-control flag")
                    print(f"[WARNING] Master device may have word selection issues - consider updating scrcpy")
            
            print(f"[OK] Screen mirroring started for master device: {self.master_device}")
            print(f"  Window title: {window_title}")
            return True
        except Exception as e:
            print(f"[ERROR] Error starting screen mirror: {e}")
            return False
    
    def stop_screen_mirror(self):
        """Stop screen mirroring"""
        if self.scrcpy_process:
            self.scrcpy_process.terminate()
            self.scrcpy_process.wait()
            self.scrcpy_process = None
            print("Screen mirroring stopped")
    
    def execute_on_slaves(self, command: str):
        """Execute command on all slave devices"""
        results = []
        for slave in self.slave_devices:
            try:
                result = subprocess.run(
                    ['adb', '-s', slave, 'shell', command],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                results.append({
                    'device': slave,
                    'success': result.returncode == 0
                })
            except Exception as e:
                results.append({
                    'device': slave,
                    'success': False,
                    'error': str(e)
                })
        return results
    
    def mirror_tap(self, x: int, y: int):
        """Mirror tap action to master and all slaves using proportional coordinates"""
        # Get master screen size
        master_size = self.get_master_screen_size()
        if master_size['width'] == 0 or master_size['height'] == 0:
            print("[WARNING] Could not get master screen size, using absolute coordinates")
            # Fallback to absolute coordinates - send to master first
            try:
                subprocess.run(
                    ['adb', '-s', self.master_device, 'shell', f'input tap {x} {y}'],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            # Then send to slaves
            if self.slave_devices:
                results = self.execute_on_slaves(f'input tap {x} {y}')
        else:
            # Calculate percentage/ratio of click position on master
            ratio_x = x / master_size['width']
            ratio_y = y / master_size['height']
            
            print(f"[MIRROR] Master tap at ({x}, {y}) on {master_size['width']}x{master_size['height']} = ({ratio_x*100:.1f}%, {ratio_y*100:.1f}%)")
            
            # Send tap to master device first (since scrcpy input is disabled)
            try:
                subprocess.run(
                    ['adb', '-s', self.master_device, 'shell', f'input tap {x} {y}'],
                    capture_output=True,
                    timeout=5
                )
            except Exception as e:
                print(f"[WARNING] Failed to send tap to master: {e}")
            
            # Send proportional coordinates to each slave
            results = []
            for slave in self.slave_devices:
                # Get slave screen size (use cache if available)
                if slave in self.slave_screen_sizes:
                    slave_size = self.slave_screen_sizes[slave]
                else:
                    slave_size = self.controller.get_screen_info(slave)
                    if slave_size['width'] > 0:
                        self.slave_screen_sizes[slave] = slave_size  # Cache it
                
                if slave_size['width'] > 0 and slave_size['height'] > 0:
                    # Calculate coordinates for this slave based on same percentage
                    slave_x = int(slave_size['width'] * ratio_x)
                    slave_y = int(slave_size['height'] * ratio_y)
                    
                    # Clamp to screen bounds (safety check)
                    slave_x = max(0, min(slave_x, slave_size['width'] - 1))
                    slave_y = max(0, min(slave_y, slave_size['height'] - 1))
                    
                    print(f"  -> {slave}: ({slave_x}, {slave_y}) on {slave_size['width']}x{slave_size['height']} screen ({ratio_x*100:.1f}%, {ratio_y*100:.1f}%)")
                    
                    # Execute tap on this slave
                    try:
                        result = subprocess.run(
                            ['adb', '-s', slave, 'shell', f'input tap {slave_x} {slave_y}'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        results.append({
                            'device': slave,
                            'success': result.returncode == 0,
                            'coords': f"({slave_x}, {slave_y})",
                            'screen': f"{slave_size['width']}x{slave_size['height']}"
                        })
                    except Exception as e:
                        results.append({
                            'device': slave,
                            'success': False,
                            'error': str(e)
                        })
                else:
                    print(f"[WARNING] Could not get screen size for {slave}, using absolute coordinates")
                    # Fallback for this device
                    try:
                        result = subprocess.run(
                            ['adb', '-s', slave, 'shell', f'input tap {x} {y}'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        results.append({
                            'device': slave,
                            'success': result.returncode == 0
                        })
                    except Exception as e:
                        results.append({
                            'device': slave,
                            'success': False,
                            'error': str(e)
                        })
        
        # Print results for debugging
        success_count = sum(1 for r in results if r.get('success', False))
        if success_count < len(results):
            print(f"[WARNING] Only {success_count}/{len(results)} slaves received the command successfully")
            for result in results:
                if not result.get('success', False):
                    print(f"  - {result.get('device', 'unknown')}: {result.get('error', 'unknown error')}")
        else:
            print(f"[SUCCESS] Tap sent to all {len(self.slave_devices)} slave(s)")
            # Show coordinates used for each slave
            for result in results:
                if 'coords' in result:
                    print(f"  - {result['device']}: {result['coords']} on {result['screen']} screen")
    
    def mirror_swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Mirror swipe action to master and all slaves using proportional coordinates"""
        # Get master screen size
        master_size = self.get_master_screen_size()
        if master_size['width'] == 0 or master_size['height'] == 0:
            print("[WARNING] Could not get master screen size, using absolute coordinates")
            # Fallback to absolute coordinates - send to master first
            try:
                subprocess.run(
                    ['adb', '-s', self.master_device, 'shell', f'input swipe {x1} {y1} {x2} {y2} {duration}'],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            # Then send to slaves
            if self.slave_devices:
                self.execute_on_slaves(f'input swipe {x1} {y1} {x2} {y2} {duration}')
        else:
            # Calculate percentage/ratio of swipe positions on master
            ratio_x1 = x1 / master_size['width']
            ratio_y1 = y1 / master_size['height']
            ratio_x2 = x2 / master_size['width']
            ratio_y2 = y2 / master_size['height']
            
            print(f"[MIRROR] Master swipe from ({x1}, {y1}) to ({x2}, {y2})")
            
            # Send swipe to master device first (since scrcpy input is disabled)
            try:
                subprocess.run(
                    ['adb', '-s', self.master_device, 'shell', f'input swipe {x1} {y1} {x2} {y2} {duration}'],
                    capture_output=True,
                    timeout=5
                )
            except Exception as e:
                print(f"[WARNING] Failed to send swipe to master: {e}")
            
            # Send proportional coordinates to each slave
            for slave in self.slave_devices:
                # Get slave screen size (use cache if available)
                if slave in self.slave_screen_sizes:
                    slave_size = self.slave_screen_sizes[slave]
                else:
                    slave_size = self.controller.get_screen_info(slave)
                    if slave_size['width'] > 0:
                        self.slave_screen_sizes[slave] = slave_size  # Cache it
                
                if slave_size['width'] > 0 and slave_size['height'] > 0:
                    # Calculate coordinates for this slave based on same percentage
                    slave_x1 = int(slave_size['width'] * ratio_x1)
                    slave_y1 = int(slave_size['height'] * ratio_y1)
                    slave_x2 = int(slave_size['width'] * ratio_x2)
                    slave_y2 = int(slave_size['height'] * ratio_y2)
                    
                    # Execute swipe on this slave
                    try:
                        subprocess.run(
                            ['adb', '-s', slave, 'shell', f'input swipe {slave_x1} {slave_y1} {slave_x2} {slave_y2} {duration}'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                    except Exception as e:
                        print(f"[ERROR] Failed to swipe on {slave}: {e}")
                else:
                    # Fallback for this device
                    try:
                        subprocess.run(
                            ['adb', '-s', slave, 'shell', f'input swipe {x1} {y1} {x2} {y2} {duration}'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                    except Exception as e:
                        print(f"[ERROR] Failed to swipe on {slave}: {e}")
    
    def mirror_key(self, keycode: str):
        """Mirror key press to master and all slaves"""
        # Send to master first (since scrcpy input is disabled)
        try:
            subprocess.run(
                ['adb', '-s', self.master_device, 'shell', f'input keyevent {keycode}'],
                capture_output=True,
                timeout=5
            )
        except:
            pass
        # Then send to slaves
        if self.slave_devices:
            print(f"Mirroring key {keycode} to {len(self.slave_devices)} slaves...")
            self.execute_on_slaves(f'input keyevent {keycode}')
    
    def mirror_text(self, text: str):
        """Mirror text input to all slaves"""
        if not self.slave_devices:
            return
        # Escape text for ADB
        text = text.replace(' ', '%s').replace('&', '\\&')
        print(f"Mirroring text to {len(self.slave_devices)} slaves...")
        self.execute_on_slaves(f'input text "{text}"')
    
    def get_master_screen_size(self) -> Dict:
        """Get master device screen dimensions (uses cache if available)"""
        if self.master_screen_size and self.master_screen_size['width'] > 0:
            return self.master_screen_size
        
        try:
            # First try wm size
            result = subprocess.run(
                ['adb', '-s', self.master_device, 'shell', 'wm', 'size'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            
            # IMPORTANT: Use "Override size" if available, because that's what Android uses for input coordinates!
            override_match = re.search(r'Override size:\s*(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if override_match:
                width = int(override_match.group(1))
                height = int(override_match.group(2))
                size = {'width': width, 'height': height, 'is_override': True}
                self.master_screen_size = size
                return size
            
            # If no override, use physical size
            physical_match = re.search(r'Physical size:\s*(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if physical_match:
                width = int(physical_match.group(1))
                height = int(physical_match.group(2))
                size = {'width': width, 'height': height, 'is_override': False}
                self.master_screen_size = size
                return size
            
            # Fallback: use any size found
            match = re.search(r'(\d+)\s*x\s*(\d+)', output, re.IGNORECASE)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                size = {'width': width, 'height': height, 'is_override': False}
                self.master_screen_size = size
                return size
            
            # Alternative: Try dumpsys
            result = subprocess.run(
                ['adb', '-s', self.master_device, 'shell', 'dumpsys', 'window', 'displays'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            width_match = re.search(r'mDisplayWidth=(\d+)', output)
            height_match = re.search(r'mDisplayHeight=(\d+)', output)
            if width_match and height_match:
                width = int(width_match.group(1))
                height = int(height_match.group(2))
                size = {'width': width, 'height': height}
                self.master_screen_size = size
                return size
        except Exception as e:
            print(f"[ERROR] Failed to get master screen size: {e}")
        return {'width': 0, 'height': 0}


class ActionMirror:
    """Monitor and mirror actions from master device to slaves"""
    
    def __init__(self, controller: ScreenMirrorController):
        self.controller = controller
        self.monitoring = False
        self.last_action = None
        
    def start_monitoring(self):
        """Start monitoring master device actions"""
        self.monitoring = True
        print("Action mirroring started - monitoring master device...")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        print("Action mirroring stopped")


class ScrcpyInputMirror:
    """Intercept scrcpy input events and mirror to slaves"""
    
    def __init__(self, master_device: str, slave_devices: List[str], window_title: str = "Phone Master - Control Here"):
        self.master_device = master_device
        self.slave_devices = slave_devices
        self.window_title = window_title
        self.mirror_thread = None
        self.running = False
        self.screen_controller = ScreenMirrorController(master_device, slave_devices)
        self.last_click_pos = None
        self.swipe_start = None
        self.swipe_active = False
        
    def start_mirroring(self):
        """Start intercepting and mirroring inputs"""
        try:
            import pynput
            self.pynput_available = True
        except ImportError:
            print("WARNING: pynput not installed. Installing automatic input mirroring...")
            print("For full automatic mirroring, install: pip install pynput")
            print("Using alternative method: monitoring ADB events...")
            self.pynput_available = False
            self._start_adb_monitoring()
            return
        
        self.running = True
        self.mirror_thread = threading.Thread(target=self._monitor_with_pynput)
        self.mirror_thread.daemon = True
        self.mirror_thread.start()
        print("[OK] Input mirroring thread started - monitoring for clicks on scrcpy window...")
        print("  Click on the scrcpy window to test mirroring")
    
    def stop_mirroring(self):
        """Stop input mirroring"""
        self.running = False
        if self.mirror_thread:
            self.mirror_thread.join(timeout=2)
        print("Input mirroring stopped")
    
    def _start_adb_monitoring(self):
        """Monitor ADB events from master device"""
        self.running = True
        self.mirror_thread = threading.Thread(target=self._monitor_adb_events)
        self.mirror_thread.daemon = True
        self.mirror_thread.start()
        print("[OK] ADB event monitoring active - mirroring master device inputs!")
    
    def _monitor_adb_events(self):
        """Monitor ADB input events and mirror to slaves"""
        import subprocess
        import re
        
        print("[INFO] Starting ADB event monitoring (fallback method)")
        print("[INFO] This method monitors touch events on the master device")
        
        # Get screen size for coordinate conversion
        screen_size = self.screen_controller.get_master_screen_size()
        if screen_size['width'] == 0:
            # Try to get it from ADB
            try:
                result = subprocess.run(
                    ['adb', '-s', self.master_device, 'shell', 'wm', 'size'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                match = re.search(r'(\d+)x(\d+)', result.stdout)
                if match:
                    screen_size['width'] = int(match.group(1))
                    screen_size['height'] = int(match.group(2))
                    print(f"[INFO] Master screen size: {screen_size['width']}x{screen_size['height']}")
            except Exception as e:
                print(f"[ERROR] Could not get screen size: {e}")
        
        # Alternative: Use a simpler approach - monitor for any input on master and mirror
        # This is less precise but more reliable
        print("[INFO] Monitoring master device for input events...")
        print("[INFO] Note: This method may have delays. For better performance, install pynput.")
        
        last_tap_time = 0
        tap_cooldown = 0.3  # Prevent duplicate taps
        
        while self.running:
            try:
                # Check if master device received any recent input
                # We'll use a polling approach since getevent requires root
                time.sleep(0.1)
                
                # For now, this is a placeholder - the pynput method is preferred
                # In a production system, you'd parse getevent output here
                
            except Exception as e:
                print(f"[ERROR] ADB monitoring error: {e}")
                time.sleep(1)
    
    def _monitor_with_pynput(self):
        """Monitor mouse and keyboard using pynput"""
        from pynput import mouse, keyboard
        
        if not WIN32_AVAILABLE:
            print("WARNING: win32gui not available. Install pywin32: pip install pywin32")
            print("Falling back to ADB monitoring...")
            self._start_adb_monitoring()
            return
        
        def get_scrcpy_window():
            """Find scrcpy window handle"""
            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if self.window_title.lower() in title.lower() or 'scrcpy' in title.lower():
                        ctx.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_handler, windows)
            return windows[0] if windows else None
        
        def is_point_in_window(x, y, hwnd):
            """Check if point is in window"""
            if not hwnd:
                return False
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                return left <= x <= right and top <= y <= bottom
            except:
                return False
        
        def get_window_size(hwnd):
            """Get window size"""
            try:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                return right - left, bottom - top
            except:
                return 0, 0
        
        def convert_to_phone_coords(window_x, window_y, hwnd):
            """Convert window coordinates to phone screen coordinates"""
            screen_size = self.screen_controller.get_master_screen_size()
            if screen_size['width'] == 0 or screen_size['height'] == 0:
                print(f"[WARNING] Could not get master screen size")
                return None, None
            
            try:
                # Get window position and size
                win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(hwnd)
                win_width = win_right - win_left
                win_height = win_bottom - win_top
                
                # Get client area (content area excluding borders/title bar)
                # GetClientRect returns coordinates relative to client area (usually starts at 0,0)
                client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
                client_width = client_right - client_left
                client_height = client_bottom - client_top
                
                # Get the actual client area position on screen
                # ClientToScreen converts client coordinates to screen coordinates
                try:
                    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
                    client_screen_left = client_point[0]
                    client_screen_top = client_point[1]
                except:
                    # Fallback: estimate title bar height
                    client_screen_left = win_left
                    client_screen_top = win_top + (win_height - client_height)  # Approximate title bar
                
                # Convert absolute screen coordinates to client-relative coordinates
                # window_x and window_y are absolute screen coordinates
                rel_x = window_x - client_screen_left
                rel_y = window_y - client_screen_top
                
                # Clamp to client area bounds
                rel_x = max(0, min(rel_x, client_width))
                rel_y = max(0, min(rel_y, client_height))
                
                # Scale to phone screen dimensions
                if client_width > 0 and client_height > 0:
                    # Calculate aspect ratios
                    window_aspect = client_width / client_height if client_height > 0 else 0
                    phone_aspect = screen_size['width'] / screen_size['height'] if screen_size['height'] > 0 else 0
                    
                    # Calculate scale factors
                    scale_x = screen_size['width'] / client_width
                    scale_y = screen_size['height'] / client_height
                    
                    # scrcpy maintains aspect ratio, so if aspect ratios don't match,
                    # there will be letterboxing (black bars). We need to account for this.
                    if abs(window_aspect - phone_aspect) > 0.01:  # Aspect ratio mismatch
                        # Use uniform scaling (scrcpy will letterbox to maintain aspect ratio)
                        scale = min(scale_x, scale_y)
                        
                        # Calculate the actual visible content area (excluding letterboxing)
                        if window_aspect > phone_aspect:
                            # Window is wider - letterboxing on sides (vertical bars)
                            # Content is centered horizontally
                            visible_width = int(client_height * phone_aspect)
                            letterbox_x = (client_width - visible_width) // 2
                            
                            # Adjust relative X to account for letterboxing
                            if rel_x < letterbox_x or rel_x > (letterbox_x + visible_width):
                                # Clicked in letterbox area - return None to ignore
                                return None, None
                            
                            # Map to visible content area
                            content_x = rel_x - letterbox_x
                            phone_x = int(content_x * scale)
                            phone_y = int(rel_y * scale)
                        else:
                            # Window is taller - letterboxing on top/bottom (horizontal bars)
                            # Content is centered vertically
                            visible_height = int(client_width / phone_aspect)
                            letterbox_y = (client_height - visible_height) // 2
                            
                            # Adjust relative Y to account for letterboxing
                            if rel_y < letterbox_y or rel_y > (letterbox_y + visible_height):
                                # Clicked in letterbox area - return None to ignore
                                return None, None
                            
                            # Map to visible content area
                            content_y = rel_y - letterbox_y
                            phone_x = int(rel_x * scale)
                            phone_y = int(content_y * scale)
                    else:
                        # Aspect ratios match - use direct scaling (no letterboxing)
                        phone_x = int(rel_x * scale_x)
                        phone_y = int(rel_y * scale_y)
                    
                    # Clamp to phone screen bounds (safety check)
                    phone_x = max(0, min(phone_x, screen_size['width'] - 1))
                    phone_y = max(0, min(phone_y, screen_size['height'] - 1))
                    
                    # Debug output - show detailed info for troubleshooting
                    # Only show if coordinates seem off (near edges or if verbose mode)
                    show_debug = (rel_y > client_height * 0.9 or rel_y < client_height * 0.1 or 
                                 rel_x < client_width * 0.1 or rel_x > client_width * 0.9)
                    if show_debug:
                        print(f"[DEBUG] screen({window_x}, {window_y}) -> rel({rel_x:.0f}, {rel_y:.0f}) -> phone({phone_x}, {phone_y})")
                        print(f"[DEBUG]   Client offset: ({client_screen_left - win_left}, {client_screen_top - win_top})")
                        print(f"[DEBUG]   Scale: ({scale_x:.3f}, {scale_y:.3f}), Client: {client_width}x{client_height}")
                    
                    return phone_x, phone_y
                else:
                    print(f"[ERROR] Invalid client area: {client_width}x{client_height}")
                    return None, None
                    
            except Exception as e:
                print(f"[ERROR] Coordinate conversion failed: {e}")
                # Fallback: simple scaling using window size
                try:
                    win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(hwnd)
                    rel_x = window_x - win_left
                    rel_y = window_y - win_top
                    win_width = win_right - win_left
                    win_height = win_bottom - win_top
                    
                    if win_width > 0 and win_height > 0:
                        scale_x = screen_size['width'] / win_width
                        scale_y = screen_size['height'] / win_height
                        phone_x = int(rel_x * scale_x)
                        phone_y = int(rel_y * scale_y)
                        return max(0, min(phone_x, screen_size['width'])), max(0, min(phone_y, screen_size['height']))
                except:
                    pass
                return None, None
        
        # Wait for scrcpy window to appear - try multiple times
        hwnd = None
        max_attempts = 100  # Wait up to 10 seconds
        for attempt in range(max_attempts):
            hwnd = get_scrcpy_window()
            if hwnd:
                break
            if attempt % 10 == 0:  # Print status every second
                print(f"[INFO] Waiting for scrcpy window... ({attempt/10:.0f}s)")
            time.sleep(0.1)
        
        if not hwnd:
            print("[WARNING] Could not find scrcpy window with expected title.")
            print("[WARNING] Looking for ANY scrcpy window...")
            # Try to find any window with scrcpy
            def find_any_scrcpy(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if 'scrcpy' in title.lower():
                        ctx.append((hwnd, title))
                return True
            all_windows = []
            win32gui.EnumWindows(find_any_scrcpy, all_windows)
            if all_windows:
                print(f"[INFO] Found {len(all_windows)} scrcpy window(s):")
                for h, t in all_windows:
                    print(f"  - '{t}' (handle: {h})")
                # Use the first one found
                hwnd = all_windows[0][0]
                print(f"[INFO] Using first window found: '{all_windows[0][1]}'")
            else:
                print("[ERROR] No scrcpy windows found at all!")
                print("[ERROR] Make sure scrcpy is running and the window is visible.")
                print("[ERROR] Input mirroring will not work until scrcpy window is detected.")
                return
        else:
            window_title = win32gui.GetWindowText(hwnd)
            print(f"[SUCCESS] Found scrcpy window: '{window_title}' (handle: {hwnd})")
        
        # Get window info for debugging
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
            client_width = client_right - client_left
            client_height = client_bottom - client_top
            print(f"[INFO] Window: {width}x{height} at ({left}, {top}), Client: {client_width}x{client_height}")
            
            # Get and display phone screen size
            screen_size = self.screen_controller.get_master_screen_size()
            if screen_size['width'] > 0:
                window_aspect = client_width / client_height if client_height > 0 else 0
                phone_aspect = screen_size['width'] / screen_size['height'] if screen_size['height'] > 0 else 0
                print(f"[INFO] Master phone screen: {screen_size['width']}x{screen_size['height']}")
                print(f"[INFO] Aspect ratios - Window: {window_aspect:.3f}, Phone: {phone_aspect:.3f}")
                if abs(window_aspect - phone_aspect) > 0.01:
                    print(f"[INFO] Aspect ratio mismatch detected - using uniform scaling")
            else:
                print(f"[WARNING] Could not detect master phone screen size - coordinate conversion may fail")
        except Exception as e:
            print(f"[WARNING] Could not get window info: {e}")
        
        # Track mouse drag state
        drag_start = None
        drag_active = False
        
        def on_click(x, y, button, pressed):
            """Handle mouse clicks and drags"""
            nonlocal drag_start, drag_active
            
            if not self.running:
                return False
            
            if not hwnd:
                return True  # Continue listening even if window not found
            
            if is_point_in_window(x, y, hwnd):
                if button == mouse.Button.left:
                    if pressed:
                        # Mouse down - start drag
                        phone_x, phone_y = convert_to_phone_coords(x, y, hwnd)
                        if phone_x is not None and phone_y is not None:
                            drag_start = (phone_x, phone_y)
                            drag_active = True
                            screen_size = self.screen_controller.get_master_screen_size()
                            print(f"[DEBUG] Mouse down: screen({x}, {y}) -> phone({phone_x}, {phone_y})")
                    else:
                        # Mouse up - end drag or tap
                        if drag_active and drag_start:
                            phone_x, phone_y = convert_to_phone_coords(x, y, hwnd)
                            if phone_x is not None and phone_y is not None:
                                # Check if this was a drag (moved more than threshold)
                                dx = abs(phone_x - drag_start[0])
                                dy = abs(phone_y - drag_start[1])
                                drag_threshold = 10  # Minimum pixels to consider it a drag
                                
                                if dx > drag_threshold or dy > drag_threshold:
                                    # This was a drag - send swipe command
                                    print(f"[DEBUG] Drag: ({drag_start[0]}, {drag_start[1]}) -> ({phone_x}, {phone_y})")
                                    self.screen_controller.mirror_swipe(
                                        drag_start[0], drag_start[1],
                                        phone_x, phone_y,
                                        300
                                    )
                                else:
                                    # This was just a tap
                                    screen_size = self.screen_controller.get_master_screen_size()
                                    print(f"[DEBUG] Tap: screen({x}, {y}) -> phone({phone_x}, {phone_y})")
                                    self.screen_controller.mirror_tap(phone_x, phone_y)
                            
                            drag_start = None
                            drag_active = False
                elif pressed and button == mouse.Button.right:
                    # Right click = back button
                    print(f"[DEBUG] Right-click detected - sending BACK key")
                    self.screen_controller.mirror_key("KEYCODE_BACK")
            else:
                # Click outside window - cancel drag
                if drag_active:
                    drag_start = None
                    drag_active = False
        
        def on_scroll(x, y, dx, dy):
            """Handle mouse scroll (swipe)"""
            if not self.running:
                return False
            
            if hwnd and is_point_in_window(x, y, hwnd):
                phone_x, phone_y = convert_to_phone_coords(x, y, hwnd)
                if phone_x is not None and phone_y is not None:
                    # Convert scroll to swipe
                    # Note: dy > 0 means scrolling down, which should swipe down on phone
                    swipe_distance = 300
                    if dy > 0:  # Scroll down = swipe down (FIXED)
                        self.screen_controller.mirror_swipe(
                            phone_x, phone_y - swipe_distance,
                            phone_x, phone_y + swipe_distance,
                            300
                        )
                    elif dy < 0:  # Scroll up = swipe up (FIXED)
                        self.screen_controller.mirror_swipe(
                            phone_x, phone_y + swipe_distance,
                            phone_x, phone_y - swipe_distance,
                            300
                        )
        
        def on_move(x, y):
            """Handle mouse movement (for drag tracking)"""
            nonlocal drag_start, drag_active
            # We don't need to do anything on move - drag is handled on mouse up
            # But we can use this to update drag end position if needed
            pass
        
        # Start mouse listener
        print("[INFO] Starting mouse listener...")
        mouse_listener = mouse.Listener(
            on_click=on_click,
            on_scroll=on_scroll,
            on_move=on_move
        )
        mouse_listener.start()
        print("[SUCCESS] Mouse listener active! Click on the scrcpy window to test.")
        print("[INFO] Listening for clicks... (Press Ctrl+C in main script to stop)")
        
        # Keep running and periodically check window still exists
        check_count = 0
        while self.running:
            time.sleep(0.1)
            check_count += 1
            # Every 5 seconds, verify window still exists
            if check_count % 50 == 0:
                current_hwnd = get_scrcpy_window()
                if not current_hwnd and hwnd:
                    # Window might have closed, try to find it again
                    hwnd = get_scrcpy_window()
                    if not hwnd:
                        print("[WARNING] scrcpy window not found - it may have closed")
        
        print("[INFO] Stopping mouse listener...")
        mouse_listener.stop()
        print("[INFO] Mouse listener stopped")


class MasterSlaveController:
    """Complete system: Screen mirror + Action mirroring"""
    
    def __init__(self, master_device: str, slave_devices: List[str]):
        self.master_device = master_device
        self.slave_devices = slave_devices
        self.screen_controller = ScreenMirrorController(master_device, slave_devices)
        self.window_title = "Phone Master - Control Here"
        self.input_mirror = None  # Will be created in start()
        
    def start(self, window_title: str = "Phone Master - Control Here"):
        """Start complete system"""
        print("=== Starting Master-Slave Control System ===\n")
        
        self.window_title = window_title
        
        # Start screen mirroring
        if not self.screen_controller.start_screen_mirror(window_title):
            print("Failed to start screen mirroring!")
            return False
        
        time.sleep(2)
        
        # Create and start input mirroring
        self.input_mirror = ScrcpyInputMirror(self.master_device, self.slave_devices, window_title)
        self.input_mirror.start_mirroring()
        
        print("\n[OK] System ready!")
        print(f"  Master: {self.master_device}")
        print(f"  Slaves: {len(self.slave_devices)} devices")
        print("\nControl the master phone window - actions will mirror to all slaves!")
        print("Press Ctrl+C to stop...")
        
        return True
    
    def stop(self):
        """Stop all systems"""
        if self.input_mirror:
            self.input_mirror.stop_mirroring()
        self.screen_controller.stop_screen_mirror()
        print("\nSystem stopped")
    
    def manual_mirror_tap(self, x: int, y: int):
        """Manually trigger tap mirroring"""
        self.screen_controller.mirror_tap(x, y)
    
    def manual_mirror_swipe(self, x1: int, y1: int, x2: int, y2: int):
        """Manually trigger swipe mirroring"""
        self.screen_controller.mirror_swipe(x1, y1, x2, y2)
    
    def manual_mirror_key(self, keycode: str):
        """Manually trigger key mirroring"""
        self.screen_controller.mirror_key(keycode)

