from wifi_connection import WiFiADBManager
from screen_mirror_controller import MasterSlaveController
import time
import sys

def main():
    print("=" * 60)
    print("  Multi-Phone WiFi Control System")
    print("=" * 60)
    print()
    
    manager = WiFiADBManager()
    
    # Step 1: Setup WiFi connection
    print("Step 1: WiFi Connection Setup")
    print("-" * 60)
    wifi_devices = manager.get_wifi_devices()
    
    if not wifi_devices:
        print("No WiFi devices found. Setting up...")
        print("\nPlease connect phones via USB first, then press Enter...")
        input()
        manager.connect_all_wifi()
        time.sleep(3)
        wifi_devices = manager.get_wifi_devices()
    
    if not wifi_devices:
        print("ERROR: No devices connected!")
        print("Make sure:")
        print("  1. Phones are connected via USB")
        print("  2. USB Debugging is enabled")
        print("  3. Phones are on the same WiFi network")
        return
    
    print(f"\n[OK] Found {len(wifi_devices)} WiFi device(s):")
    for i, device in enumerate(wifi_devices, 1):
        print(f"  {i}. {device}")
    
    # Step 2: Select master and slaves
    print("\n" + "-" * 60)
    print("Step 2: Select Master Device")
    print("-" * 60)
    
    if len(wifi_devices) < 2:
        print("ERROR: Need at least 2 devices (1 master + 1 slave)")
        return
    
    print(f"\nSelect master device (1-{len(wifi_devices)}):")
    print("(Press Enter to use first device as master)")
    try:
        user_input = input("Enter number: ").strip()
        if not user_input:
            # Default: first device is master
            choice = 0
        else:
            choice = int(user_input) - 1
        if choice < 0 or choice >= len(wifi_devices):
            raise ValueError
        master = wifi_devices[choice]
        slaves = [d for d in wifi_devices if d != master]
        if not user_input:
            print(f"Using default: {master} as master")
    except (ValueError, IndexError):
        # Default: first device is master
        master = wifi_devices[0]
        slaves = wifi_devices[1:]
        print(f"Invalid input. Using default: {master} as master")
    
    print(f"\n[OK] Master: {master}")
    print(f"[OK] Slaves: {slaves}")
    
    # Step 3: Check dependencies
    print("\n" + "-" * 60)
    print("Step 3: Checking Dependencies")
    print("-" * 60)
    
    try:
        import pynput
        import win32gui
        deps_ok = True
    except ImportError:
        deps_ok = False
        print("[WARNING] Required dependencies not installed!")
        print("For automatic input mirroring, please install:")
        print("  pip install pynput pywin32")
        print("  OR run: py setup_dependencies.py")
        print("\nContinuing without automatic mirroring...")
        print("(You can still use manual mirror functions)")
        input("\nPress Enter to continue...")
    
    # Step 4: Start screen mirroring and control
    print("\n" + "-" * 60)
    print("Step 4: Starting Screen Mirror & Control")
    print("-" * 60)
    
    controller = MasterSlaveController(master, slaves)
    
    try:
        if controller.start():
            print("\n" + "=" * 60)
            print("SYSTEM READY!")
            print("=" * 60)
            print("\nA window showing your master phone screen should appear.")
            if deps_ok:
                print("[OK] Automatic input mirroring is ACTIVE!")
                print("Click/tap on the master phone window - actions will mirror to all slaves!")
            else:
                print("[WARNING] Automatic input mirroring is NOT active (dependencies missing)")
                print("Install pynput and pywin32 for automatic mirroring")
            print("\nPress Ctrl+C to stop...")
            
            # Keep running
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\nStopping...")
        controller.stop()
        print("Done!")


if __name__ == "__main__":
    main()

