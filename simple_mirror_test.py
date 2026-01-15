"""
Simple test to verify mirroring works - bypasses window detection
"""
import subprocess
import sys
from screen_mirror_controller import ScreenMirrorController

def main():
    print("=" * 60)
    print("  Simple Mirror Test - Direct Command Test")
    print("=" * 60)
    print()
    
    # Get devices
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
        
        if len(devices) < 2:
            print("ERROR: Need at least 2 devices")
            print(f"Found: {devices}")
            return
        
        master = devices[0]
        slaves = devices[1:]
        
        print(f"Master: {master}")
        print(f"Slaves: {slaves}")
        print()
        
        # Create controller
        controller = ScreenMirrorController(master, slaves)
        
        # Test 1: Simple tap
        print("Test 1: Sending tap(500, 1000) to all slaves...")
        controller.mirror_tap(500, 1000)
        print()
        
        input("Press Enter to continue to next test...")
        
        # Test 2: Home button
        print("Test 2: Sending HOME key to all slaves...")
        controller.mirror_key("KEYCODE_HOME")
        print()
        
        input("Press Enter to continue to next test...")
        
        # Test 3: Swipe
        print("Test 3: Sending swipe to all slaves...")
        controller.mirror_swipe(500, 1500, 500, 500, 300)
        print()
        
        print("=" * 60)
        print("Tests complete!")
        print("=" * 60)
        print("\nIf these tests worked, the issue is with input capture.")
        print("If these tests didn't work, check:")
        print("  1. Slave devices are connected: adb devices")
        print("  2. Devices have proper permissions")
        print("  3. ADB is working: adb -s DEVICE shell echo test")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

