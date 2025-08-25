#!/usr/bin/env python3

# Simple test to check data directory and files
import os
import sys
sys.path.append('.')

from config import DATA_DIR
from datetime import datetime

def test_data_access():
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}")
    
    if os.path.exists(DATA_DIR):
        files = os.listdir(DATA_DIR)
        print(f"Files in DATA_DIR: {files}")
        
        # Test for current month files
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        
        print(f"Looking for files in {year}-{month:02d}")
        
        for day in range(1, 32):  # Check first 31 days
            date_str = f"{year}-{month:02d}-{day:02d}"
            file_path = os.path.join(DATA_DIR, f'{date_str}.csv')
            if os.path.exists(file_path):
                print(f"Found: {date_str}.csv")
                
    else:
        print("❌ DATA_DIR does not exist!")

if __name__ == "__main__":
    test_data_access()