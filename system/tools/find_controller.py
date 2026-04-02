#!/usr/bin/env python3
"""
Utility to find controller device path by name.
Searches /dev/input/event* devices and matches by device name.

Usage:
    python3 find_controller.py "Xbox Wireless Controller"
    python3 find_controller.py --list
    python3 find_controller.py --partial "Xbox"
"""

import sys
import os
import glob
from evdev import InputDevice


def list_all_devices():
    """List all input devices with their paths and names."""
    devices = []
    pattern = '/dev/input/event*'
    
    for path in sorted(glob.glob(pattern)):
        try:
            dev = InputDevice(path)
            devices.append((path, dev.name))
        except (OSError, PermissionError):
            continue
    
    return devices


def find_device_by_name(name, partial_match=False):
    """Find device path by exact or partial name match."""
    devices = list_all_devices()
    matches = []
    
    for path, dev_name in devices:
        if partial_match:
            if name.lower() in dev_name.lower():
                matches.append((path, dev_name))
        else:
            if name.lower() == dev_name.lower():
                matches.append((path, dev_name))
    
    return matches


def main():
    if len(sys.argv) < 2:
        print("Usage: find_controller.py <device_name>")
        print("       find_controller.py --list")
        print("       find_controller.py --partial <search_term>")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == '--list':
        print("Available input devices:")
        print("-" * 60)
        devices = list_all_devices()
        for path, name in devices:
            print(f"{path}: {name}")
    
    elif arg == '--partial':
        if len(sys.argv) < 3:
            print("Error: --partial requires a search term")
            sys.exit(1)
        
        search_term = sys.argv[2]
        matches = find_device_by_name(search_term, partial_match=True)
        
        if matches:
            print(f"Devices matching '{search_term}':")
            for path, name in matches:
                print(f"{path}: {name}")
        else:
            print(f"No devices found matching '{search_term}'")
            sys.exit(1)
    
    else:
        # Exact match search
        device_name = arg
        matches = find_device_by_name(device_name, partial_match=False)
        
        if matches:
            path, name = matches[0]
            print(path)
        else:
            print(f"Error: Device '{device_name}' not found", file=sys.stderr)
            
            # Suggest similar devices
            partial_matches = find_device_by_name(device_name, partial_match=True)
            if partial_matches:
                print("\nDid you mean one of these?", file=sys.stderr)
                for path, name in partial_matches:
                    print(f"  {path}: {name}", file=sys.stderr)
            
            sys.exit(1)


if __name__ == '__main__':
    main()
