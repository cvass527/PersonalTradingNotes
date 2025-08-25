#!/usr/bin/env python3

# Simple test to debug the monthly summary without running the full dash app
import sys
import os
sys.path.append('.')

from ui.monthly_summary import MonthlySummaryComponents
from datetime import datetime

def test_monthly_summary():
    print("Testing MonthlySummaryComponents...")
    
    try:
        ms = MonthlySummaryComponents()
        print("✓ MonthlySummaryComponents created successfully")
        
        # Test with current month
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        
        print(f"Testing with current month: {year}-{month}")
        
        # Test the data gathering method directly
        monthly_data = ms._get_monthly_data(year, month)
        print(f"Monthly data result: {monthly_data}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monthly_summary()