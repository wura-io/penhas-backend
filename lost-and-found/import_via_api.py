#!/usr/bin/env python3
"""
Import ponto_apoio data via Directus API instead of CSV.

This bypasses CSV validation and allows database defaults to be applied.
"""

import csv
import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Optional

def load_csv_data(csv_file: Path) -> List[Dict]:
    """Load data from CSV file."""
    rows = []
    # Fields that should be omitted when empty (to allow DB defaults)
    omit_when_empty = {'nome_logradouro', 'bairro', 'cep'}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean row: omit empty fields that have DB defaults
            cleaned_row = {}
            for key, value in row.items():
                # Skip empty strings and null strings
                if value == '' or value == 'null':
                    # For fields with DB defaults, omit them entirely
                    if key in omit_when_empty:
                        continue
                    # For other fields, keep empty strings
                    cleaned_row[key] = ''
                else:
                    cleaned_row[key] = value
            rows.append(cleaned_row)
    return rows

def import_via_api(
    csv_file: Path,
    directus_url: str,
    access_token: str,
    collection: str = 'ponto_apoio',
    batch_size: int = 100,
    dry_run: bool = False
):
    """
    Import CSV data via Directus API.
    
    Args:
        csv_file: Path to CSV file
        directus_url: Directus instance URL (e.g., 'https://directus.example.com')
        access_token: Directus access token
        collection: Collection name (default: 'ponto_apoio')
        batch_size: Number of items to import per batch
        dry_run: If True, only validate without importing
    """
    rows = load_csv_data(csv_file)
    
    print(f"Loaded {len(rows)} rows from {csv_file}")
    
    if dry_run:
        print("\n[DRY RUN] Would import the following data:")
        print(json.dumps(rows[:2], indent=2, ensure_ascii=False))
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    endpoint = f"{directus_url.rstrip('/')}/items/{collection}"
    
    # Import in batches
    success_count = 0
    error_count = 0
    errors = []
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(rows) + batch_size - 1) // batch_size
        
        print(f"\nImporting batch {batch_num}/{total_batches} ({len(batch)} items)...")
        
        # Directus supports bulk import via POST with array
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=batch,
                timeout=60
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                batch_success = len(result.get('data', []))
                success_count += batch_success
                print(f"  ✓ Successfully imported {batch_success} items")
            else:
                error_msg = response.text
                print(f"  ✗ Error: {response.status_code}")
                print(f"    {error_msg}")
                errors.append(f"Batch {batch_num}: {error_msg}")
                error_count += len(batch)
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            errors.append(f"Batch {batch_num}: {str(e)}")
            error_count += len(batch)
    
    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  Total rows: {len(rows)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Import CSV data via Directus API')
    parser.add_argument('csv_file', type=Path, help='Path to CSV file')
    parser.add_argument('--url', required=True, help='Directus URL (e.g., https://directus.example.com)')
    parser.add_argument('--token', required=True, help='Directus access token')
    parser.add_argument('--collection', default='ponto_apoio', help='Collection name (default: ponto_apoio)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (validate only)')
    
    args = parser.parse_args()
    
    if not args.csv_file.exists():
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    import_via_api(
        args.csv_file,
        args.url,
        args.token,
        args.collection,
        args.batch_size,
        args.dry_run
    )

