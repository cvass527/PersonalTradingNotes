#!/usr/bin/env python3

# Simple test to check if monthly summary HTML generation works
import sys
import os
sys.path.append('.')

def test_monthly_summary_basic():
    print("Testing basic monthly summary HTML generation...")
    
    try:
        # Test the HTML generation without dash dependencies
        from datetime import datetime
        
        year = 2025
        month = 8
        
        # Create a simple monthly summary without dash
        from dash import html
        
        summary = html.Div([
            html.H3(f"August {year} Trading Summary", style={'color': '#2c3e50'}),
            html.P("Found 15 trading days in August 2025"),
            html.P("Total P&L: $1,500.00 (mock data)", style={'color': 'green', 'fontSize': '18px'}),
            html.P("This is a basic test to see if Dash HTML components work")
        ], style={'padding': '20px'})
        
        print("✅ Basic HTML generation works!")
        print("✅ Dash import successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error in basic test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monthly_summary_full():
    print("\nTesting full monthly summary component...")
    
    try:
        from ui.monthly_summary import MonthlySummaryComponents
        
        ms = MonthlySummaryComponents()
        print("✅ MonthlySummaryComponents created")
        
        # Test just the data gathering part
        monthly_data = ms._get_monthly_data(2025, 8)
        print(f"✅ Data gathering works: {len(monthly_data)} days found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Monthly Summary Debug Test ===\n")
    
    basic_ok = test_monthly_summary_basic()
    
    if basic_ok:
        full_ok = test_monthly_summary_full()
        
        if full_ok:
            print("\n🎉 All tests passed! Monthly summary should work.")
        else:
            print("\n⚠️  Basic test passed but full component failed.")
    else:
        print("\n❌ Basic test failed. Check dependencies.")