#!/usr/bin/env python3
"""
Test script to verify timing metadata extraction from TIFF files
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tiffFunctions as tiffF

def test_timing_extraction():
    """Test the timing metadata extraction"""
    
    # Test the ImageJ timing parser directly
    print("Testing ImageJ timing parser...")
    
    # Sample ImageJ metadata strings (common formats)
    test_cases = [
        {
            'description': 'ImageJ=1.53c\nimages=50\nchannels=1\nslices=1\nframes=50\nhyperstack=true\nmode=grayscale\nunit=micron\nfinterval=0.5\nspacing=1.0\nloop=false',
            'frames': 50,
            'expected': {'Frame_Interval': '0.5 seconds', 'Frame_Rate': '2.0000 fps'}
        },
        {
            'description': 'ImageJ=1.52p\nimages=100\nframes=100\nfps=10\nunit=second\nloop=false',
            'frames': 100,
            'expected': {'ImageJ_fps': '10'}
        },
        {
            'description': 'ImageJ=1.54f\nchannels=1\nslices=1\nframes=30\ninterval=2.5\nunit=sec',
            'frames': 30,
            'expected': {'Frame_Interval': '2.5 seconds', 'Frame_Rate': '0.4000 fps'}
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print(f"Description: {test_case['description']}")
        
        # Parse timing info
        timing_info = tiffF._parseImageJTiming(test_case['description'], test_case['frames'])
        
        print("Extracted timing info:")
        for key, value in timing_info.items():
            print(f"  {key}: {value}")
        
        # Check if expected values are present
        for expected_key, expected_value in test_case['expected'].items():
            if expected_key in timing_info:
                print(f"✓ Found expected {expected_key}: {timing_info[expected_key]}")
            else:
                print(f"✗ Missing expected {expected_key}")

    print("\n" + "="*50)
    print("Timing extraction test completed!")
    print("="*50)

if __name__ == "__main__":
    test_timing_extraction()
