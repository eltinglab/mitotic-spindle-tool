#!/usr/bin/env python3
"""
Test script for TIFF metadata functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tiffFunctions as tiffF
from PIL import Image
import numpy as np

def create_test_tiff():
    """Create a simple test TIFF file with metadata"""
    # Create a simple test image
    test_array = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    test_image = Image.fromarray(test_array, mode='L')
    
    # Add some metadata
    test_image.save('test_metadata.tif', format='TIFF', 
                   description="Test TIFF for metadata extraction",
                   software="Mitotic Spindle Tool Test",
                   resolution=(300, 300),
                   resolution_unit=2)  # inches
    
    return 'test_metadata.tif'

def test_metadata_extraction():
    """Test the metadata extraction function"""
    print("Testing TIFF metadata extraction...")
    
    # Create test file
    test_file = create_test_tiff()
    
    try:
        # Test metadata extraction
        metadata = tiffF.getTiffMetadata(test_file)
        
        print("\nExtracted metadata:")
        print("-" * 40)
        for key, value in sorted(metadata.items()):
            print(f"{key}: {value}")
        
        print(f"\nFound {len(metadata)} metadata entries")
        
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nCleaned up test file: {test_file}")
            
        return True
        
    except Exception as e:
        print(f"Error testing metadata extraction: {e}")
        return False

if __name__ == "__main__":
    success = test_metadata_extraction()
    if success:
        print("\n✅ Metadata extraction test passed!")
    else:
        print("\n❌ Metadata extraction test failed!")
        sys.exit(1)
