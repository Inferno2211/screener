#!/usr/bin/env python3
"""
Enhanced Quick Setup for EMA Screener
=====================================

Quickly setup enhanced EMA system using existing stock data
Calculates 50, 100, 200 day EMAs with band analysis

Author: Generated for trading analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from enhanced_ema_screener import EnhancedEMAScreener

def main():
    """Quick setup using existing data"""
    print("Enhanced EMA Screener Quick Setup")
    print("=================================")
    print("This will calculate 50/100/200 EMAs using existing stock data.")
    print()
    
    # Initialize enhanced screener
    screener = EnhancedEMAScreener()
    
    # Paths
    existing_data_dir = Path("stock_data")
    target_data_dir = screener.data_dir
    
    if not existing_data_dir.exists():
        print("❌ stock_data/ directory not found!")
        print("Please run the full setup first.")
        return
    
    # Get list of existing data files
    existing_files = list(existing_data_dir.glob("*_15yr_data.csv"))
    
    if not existing_files:
        print("❌ No existing stock data files found!")
        return
    
    print(f"✓ Found {len(existing_files)} existing stock data files")
    print("📊 Processing data and calculating enhanced EMAs...")
    print()
    
    successful_count = 0
    ema_count = 0
    
    # Process each file
    with tqdm(total=len(existing_files), desc="Processing enhanced EMAs") as pbar:
        for file_path in existing_files:
            # Extract symbol from filename
            symbol = file_path.stem.replace("_15yr_data", "")
            pbar.set_description(f"Processing {symbol}")
            
            try:
                # Read existing data
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                df.columns = df.columns.str.strip().str.strip('"').str.strip()
                
                # Clean BOM if present
                if len(df.columns) > 0 and 'ï»¿' in df.columns[0]:
                    df.columns = [df.columns[0].replace('ï»¿', '').replace('"', '').strip()] + list(df.columns[1:])
                
                # CRITICAL FIX: Get latest 1 year of data, ensuring proper date sorting
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df.sort_values('Date', ascending=True)  # Oldest to newest
                    df = df.tail(365)  # Get latest 365 days
                else:
                    df = df.tail(365)
                
                # Target file for enhanced system
                target_file = target_data_dir / f"{symbol}_1yr_data.csv"
                df.to_csv(target_file, index=False)
                successful_count += 1
                
                # Calculate enhanced EMAs
                ema_data = screener.calculate_stock_emas(symbol)
                if ema_data:
                    screener.update_ema_cache(symbol, ema_data)
                    ema_count += 1
                    pbar.set_postfix({
                        "EMAs": ema_count,
                        "50": f"{ema_data['EMA_50']:.0f}" if ema_data['EMA_50'] else "N/A",
                        "100": f"{ema_data['EMA_100']:.0f}" if ema_data['EMA_100'] else "N/A", 
                        "200": f"{ema_data['EMA_200']:.0f}" if ema_data['EMA_200'] else "N/A"
                    })
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
            
            pbar.update(1)
    
    print()
    print("🎉 Enhanced Quick Setup Complete!")
    print(f"✓ Processed {successful_count} stock files")
    print(f"✓ Calculated enhanced EMAs for {ema_count} stocks")
    print()
    
    if ema_count > 0:
        # Show sample of enhanced data
        df = screener.get_ema_data()
        if len(df) > 0:
            print("📊 Sample Enhanced EMA Data:")
            sample_cols = ['SYMBOL', 'EMA_50', 'EMA_100', 'EMA_200', 'LAST_CLOSE']
            available_cols = [col for col in sample_cols if col in df.columns]
            print(df[available_cols].head(5).to_string(index=False))
            print()
        
        print("🚀 Ready to launch enhanced web application!")
        print("   Run: python enhanced_ema_webapp.py")
        print("   Then open: http://localhost:5000")
        print()
        print("🎯 Features available:")
        print("   • 50/100/200 EMA toggles")
        print("   • Customizable band filtering (±2.5% default)")
        print("   • Dark mode toggle")
        print("   • Numbered stock rows")
        print("   • Advanced filtering and sorting")
    else:
        print("⚠️  No EMAs calculated. You may need to run full setup.")

if __name__ == "__main__":
    main() 