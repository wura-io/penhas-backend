#!/usr/bin/env python3
"""
Create separate CSV files for each type of import error.
"""

import csv
from collections import defaultdict
from pathlib import Path

def analyze_and_create_error_files():
    """Analyze new-data.csv and create separate error files."""
    base_dir = Path(__file__).parent
    input_file = base_dir / 'new-data.csv'
    output_dir = base_dir / 'import-errors'
    
    output_dir.mkdir(exist_ok=True)
    
    # Group rows by error type
    error_groups = defaultdict(list)
    
    # Read the header first
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        
        for row_num, row in enumerate(reader, start=2):
            issues = []
            
            # Only categoria is required from the error-checked fields
            if not row.get('categoria', '').strip():
                issues.append('categoria')
            
            if issues:
                # Create a key for this error combination (sorted for consistency)
                # Use double underscore to separate field names to avoid confusion
                error_key = '__'.join(sorted(issues))
                error_groups[error_key].append((row_num, row))
    
    # Create a file for each error type
    print(f"Creating error files in {output_dir}...")
    print()
    
    for error_key, rows in sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True):
        filename = f"missing_{error_key}.csv"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for row_num, row in rows:
                writer.writerow(row)
        
        missing_fields = error_key.replace('__', ', ')
        print(f"  Created {filename}")
        print(f"    Missing fields: {missing_fields}")
        print(f"    Rows: {len(rows)} (original row numbers: {rows[0][0]} to {rows[-1][0]})")
        print()
    
    print(f"Total error files created: {len(error_groups)}")
    print(f"Total problematic rows: {sum(len(rows) for rows in error_groups.values())}")

if __name__ == '__main__':
    analyze_and_create_error_files()

