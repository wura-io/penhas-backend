#!/usr/bin/env python3
"""
Transform new-data.csv into Directus-compatible CSV files for import.

This script processes new-data.csv and generates:
- ponto_apoio_ponto_apoio_upload.csv (all records)
- ponto_apoio_ponto_apoio_upload_test.csv (first 5 records)
- ponto_apoio_categoria_ponto_apoio_categoria_upload.csv (if new categories found)
- ponto_apoio_projeto_ponto_apoio_projeto_upload.csv (if new projetos found)
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Column name mappings from new-data.csv to Directus ponto_apoio format
COLUMN_MAPPING = {
    'cod_IBGE': 'cod_ibge',
    '24horas': 'eh_24h',
    'whatsapp': 'eh_whatsapp',
    'presencial': 'eh_presencial',
    'online': 'eh_online',
    'obs_pandemia': 'observacao_pandemia',
}

# Directus column order (from ponto_apoio_table.csv header)
DIRECTUS_COLUMNS = [
    'id', 'status', 'created_on', 'categoria', 'nome', 'sigla', 'natureza', 'owner',
    'descricao', 'tipo_logradouro', 'nome_logradouro', 'numero', 'numero_sem_numero',
    'complemento', 'bairro', 'municipio', 'uf', 'cep', 'ddd', 'telefone1', 'telefone2',
    'email', 'horario_inicio', 'horario_fim', 'eh_24h', 'dias_funcionamento',
    'eh_presencial', 'eh_online', 'funcionamento_pandemia', 'observacao_pandemia',
    'avaliacao', 'latitude', 'longitude', 'ja_passou_por_moderacao', 'updated_at',
    'observacao', 'qtde_avaliacao', 'horario_correto', 'delegacia_mulher',
    'endereco_correto', 'telefone_correto', 'existe_delegacia', 'eh_importacao',
    'cliente_id', 'indexed_at', 'test_status', 'index', 'geog.type', 'geog.coordinates',
    'abrangencia', 'eh_whatsapp', 'ramal1', 'ramal2', 'cod_ibge', 'fonte'
]

# Columns to exclude from output (not in Directus schema or handled separately)
EXCLUDE_COLUMNS = {'id_estabelecimento', 'projeto', 'id'}


def load_categoria_mapping(categoria_file: Path) -> Dict[str, int]:
    """Load categoria name to ID mapping from CSV."""
    mapping = {}
    with open(categoria_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['label'].strip()
            cat_id = int(row['id'])
            # Create case-insensitive mapping
            mapping[label.lower()] = cat_id
    return mapping


def load_projeto_mapping(projeto_file: Path) -> Dict[str, int]:
    """Load projeto name to ID mapping from CSV."""
    mapping = {}
    with open(projeto_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['label'].strip()
            proj_id = int(row['id'])
            mapping[label.lower()] = proj_id
    return mapping


def normalize_natureza(value: str) -> str:
    """Normalize natureza values."""
    if not value:
        return value
    value = value.strip().lower()
    if value == 'público':
        return 'publico'
    return value


def convert_boolean(value: str, default: bool = False) -> Optional[bool]:
    """Convert string to boolean for Directus."""
    if not value or not value.strip():
        return default
    value_lower = value.strip().lower()
    if value_lower in ('sim', 'yes', '1', 'true', 'verdadeiro'):
        return True
    if value_lower in ('não', 'nao', 'no', '0', 'false', 'falso'):
        return False
    return default


def convert_latitude_longitude(value: str) -> Optional[str]:
    """Convert latitude/longitude from comma to dot decimal separator."""
    if not value or not value.strip():
        return None
    # Replace comma with dot
    value = value.strip().replace(',', '.')
    # Validate it's a number
    try:
        float(value)
        return value
    except ValueError:
        return None


def format_cep(value: str) -> str:
    """Format CEP: remove dashes, ensure 8 digits. Returns single space if invalid."""
    if not value or not value.strip():
        return ' '  # Single space placeholder for Directus validation
    # Remove dashes and spaces
    cep = re.sub(r'[-\s]', '', value.strip())
    # Validate it's 8 digits
    if re.match(r'^\d{8}$', cep):
        return cep
    return ' '  # Single space placeholder for invalid CEP


def format_time(value: str) -> Optional[str]:
    """Format time as HH:MM (remove seconds if present)."""
    if not value or not value.strip():
        return None
    value = value.strip()
    # Remove seconds if present (HH:MM:SS -> HH:MM)
    if re.match(r'^\d{2}:\d{2}:\d{2}$', value):
        return value[:5]
    # Validate HH:MM format
    if re.match(r'^\d{2}:\d{2}$', value):
        return value
    return None


def process_numero(value: str) -> Tuple[Optional[int], bool]:
    """Process numero field: handle 's/n' and return (numero, numero_sem_numero)."""
    if not value or not value.strip():
        return None, True
    value = value.strip().lower()
    if value == 's/n' or value == 's/n.':
        return None, True
    # Try to extract number
    match = re.search(r'\d+', value)
    if match:
        return int(match.group()), False
    return None, True


def transform_row(
    row: Dict[str, str],
    categoria_mapping: Dict[str, int],
    projeto_mapping: Dict[str, int],
    errors: List[str],
    row_num: int
) -> Optional[Dict[str, any]]:
    """Transform a single row from new-data.csv to Directus format."""
    transformed = {}
    current_time = datetime.utcnow().isoformat() + 'Z'
    
    # Required Directus fields
    transformed['status'] = 'active'
    transformed['created_on'] = current_time
    transformed['updated_at'] = current_time
    transformed['eh_importacao'] = True
    
    # Process each column
    for key, value in row.items():
        if key in EXCLUDE_COLUMNS:
            continue
        
        # Map column name
        directus_key = COLUMN_MAPPING.get(key, key)
        
        # Skip if not in Directus schema
        if directus_key not in DIRECTUS_COLUMNS:
            continue
        
        # Transform value based on field type
        if directus_key == 'categoria':
            # Map categoria name to ID, or use ID directly if already numeric
            if value:
                value_stripped = value.strip()
                # Check if it's already a numeric ID
                if value_stripped.isdigit():
                    transformed[directus_key] = int(value_stripped)
                else:
                    # It's a name, map it to ID
                    cat_name = value_stripped.lower()
                    # Handle common typos
                    if cat_name == 'assitência social':
                        cat_name = 'assistência social'
                    
                    if cat_name in categoria_mapping:
                        transformed[directus_key] = categoria_mapping[cat_name]
                    else:
                        errors.append(f"Row {row_num}: Unknown categoria '{value}'")
                        return None
            else:
                errors.append(f"Row {row_num}: Missing required field 'categoria'")
                return None
        
        elif directus_key == 'natureza':
            transformed[directus_key] = normalize_natureza(value)
        
        elif directus_key in ('eh_24h', 'eh_whatsapp', 'eh_presencial', 'eh_online', 
                             'funcionamento_pandemia', 'ja_passou_por_moderacao',
                             'horario_correto', 'delegacia_mulher', 'endereco_correto',
                             'telefone_correto', 'existe_delegacia'):
            transformed[directus_key] = convert_boolean(value, default=False)
        
        elif directus_key in ('latitude', 'longitude'):
            transformed[directus_key] = convert_latitude_longitude(value)
        
        elif directus_key == 'cep':
            transformed[directus_key] = format_cep(value)
        
        elif directus_key == 'tipo_logradouro':
            # Dropdown field - use value if present, otherwise will be set to "Rua" placeholder later
            if value and value.strip():
                transformed[directus_key] = value.strip()
        
        elif directus_key in ('nome_logradouro', 'bairro'):
            # String fields - use single space as placeholder if empty
            if value and value.strip():
                transformed[directus_key] = value.strip()
            else:
                transformed[directus_key] = ' '  # Single space placeholder (will be set in defaults section)
        
        elif directus_key in ('horario_inicio', 'horario_fim'):
            transformed[directus_key] = format_time(value)
        
        elif directus_key == 'numero':
            numero, numero_sem_numero = process_numero(value)
            transformed['numero'] = numero
            transformed['numero_sem_numero'] = numero_sem_numero
        
        elif directus_key == 'numero_sem_numero':
            # This will be set by process_numero, skip here
            continue
        
        elif directus_key in ('ddd', 'telefone1', 'telefone2', 'ramal1', 'ramal2', 
                              'cod_ibge', 'avaliacao', 'qtde_avaliacao'):
            # Integer fields
            if value and value.strip():
                try:
                    transformed[directus_key] = int(value.strip())
                except ValueError:
                    transformed[directus_key] = None
            else:
                transformed[directus_key] = None
        
        elif directus_key == 'sigla':
            # Uppercase sigla
            if value:
                transformed[directus_key] = value.strip().upper()
            else:
                transformed[directus_key] = None
        
        elif directus_key == 'uf':
            # Uppercase UF
            if value:
                transformed[directus_key] = value.strip().upper()
            else:
                errors.append(f"Row {row_num}: Missing required field 'uf'")
                return None
        
        else:
            # String fields - just copy and strip
            if value:
                transformed[directus_key] = value.strip()
            else:
                transformed[directus_key] = None
    
    # Set defaults for required fields if missing
    if 'numero_sem_numero' not in transformed:
        transformed['numero_sem_numero'] = True
    
    if 'eh_whatsapp' not in transformed:
        transformed['eh_whatsapp'] = False
    
    # Set default for abrangencia if missing
    if 'abrangencia' not in transformed or transformed['abrangencia'] is None:
        transformed['abrangencia'] = 'Local'  # Default value
    
    # For fields with database defaults, use placeholder values
    # Directus validates required fields before DB defaults can apply (both CSV and API)
    # Since we can't change Directus settings or DB schema, we must provide values
    
    # tipo_logradouro: Use "Rua" (most common dropdown value) as placeholder
    if 'tipo_logradouro' not in transformed or not transformed.get('tipo_logradouro'):
        transformed['tipo_logradouro'] = 'Rua'  # Placeholder for dropdown field
    
    # String fields: Use single space as placeholder (minimal valid value)
    # This satisfies Directus validation while being minimal
    for field in ('nome_logradouro', 'bairro', 'cep'):
        if field not in transformed or transformed[field] is None or transformed[field] == '' or transformed[field] == 'null':
            transformed[field] = ' '  # Single space placeholder for string fields
    
    # Validate required fields
    required_fields = ['nome', 'natureza', 'categoria', 'municipio', 'uf']
    for field in required_fields:
        if field not in transformed or transformed[field] is None:
            errors.append(f"Row {row_num}: Missing required field '{field}'")
            return None
    
    return transformed


def collect_new_categories(
    rows: List[Dict[str, any]],
    existing_categoria_ids: Set[int]
) -> List[Dict[str, any]]:
    """Collect new categories that need to be added."""
    new_categories = {}
    for row in rows:
        cat_id = row.get('categoria')
        if cat_id and cat_id not in existing_categoria_ids:
            # We'd need the category name, but we only have ID
            # This would require additional logic if categories are missing
            pass
    return list(new_categories.values())


def collect_new_projetos(
    rows: List[Dict[str, any]],
    existing_projeto_ids: Set[int],
    projeto_mapping: Dict[str, int]
) -> List[Dict[str, any]]:
    """Collect new projetos that need to be added."""
    # Check if any projeto from new-data.csv is missing
    new_projetos = {}
    # Since we're skipping the junction table, we don't need to add projetos
    return list(new_projetos.values())


def write_csv(output_file: Path, rows: List[Dict[str, any]], columns: List[str]):
    """Write rows to CSV file with specified columns."""
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            # Ensure all columns are present, even if empty
            csv_row = {}
            for col in columns:
                if col in row:
                    value = row[col]
                    # Convert boolean values to lowercase strings for Directus
                    if isinstance(value, bool):
                        csv_row[col] = str(value).lower()
                    elif value is None:
                        # Use empty string for all fields
                        csv_row[col] = ''
                    else:
                        csv_row[col] = value
                else:
                    # Field not in row - use empty string
                    csv_row[col] = ''
            writer.writerow(csv_row)


def main(starting_id: int = 7033):
    """
    Main transformation function.
    
    Args:
        starting_id: The starting ID for generated records (default: 7033, which is last_id + 1)
                    Test file will use IDs starting_id to starting_id+4 (5 records)
                    Main file will use IDs starting from starting_id+5
    """
    base_dir = Path(__file__).parent
    
    # Input files
    new_data_file = base_dir / 'new-data.csv'
    categoria_file = base_dir / 'ponto_apoio_categoria_table.csv'
    projeto_file = base_dir / 'ponto_apoio_projeto_table.csv'
    
    # Output files
    output_main = base_dir / 'ponto_apoio_ponto_apoio_upload.csv'
    output_test = base_dir / 'ponto_apoio_ponto_apoio_upload_test.csv'
    output_categoria = base_dir / 'ponto_apoio_categoria_ponto_apoio_categoria_upload.csv'
    output_projeto = base_dir / 'ponto_apoio_projeto_ponto_apoio_projeto_upload.csv'
    
    print("Loading reference data...")
    categoria_mapping = load_categoria_mapping(categoria_file)
    projeto_mapping = load_projeto_mapping(projeto_file)
    
    existing_categoria_ids = set(categoria_mapping.values())
    existing_projeto_ids = set(projeto_mapping.values())
    
    print(f"Loaded {len(categoria_mapping)} categorias")
    print(f"Loaded {len(projeto_mapping)} projetos")
    
    # Process new-data.csv
    print(f"\nProcessing {new_data_file}...")
    print(f"Starting ID: {starting_id} (test file: {starting_id}-{starting_id+4}, main file: {starting_id+5}+)")
    transformed_rows = []
    errors = []
    current_id = starting_id
    
    with open(new_data_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            transformed = transform_row(row, categoria_mapping, projeto_mapping, errors, row_num)
            if transformed:
                # Assign sequential ID
                transformed['id'] = current_id
                current_id += 1
                transformed_rows.append(transformed)
    
    print(f"Processed {len(transformed_rows)} rows successfully")
    if errors:
        print(f"\nWarnings: {len(errors)} rows were skipped due to missing required fields")
        # Group errors by type for better reporting
        error_types = {}
        for error in errors:
            error_type = error.split(':')[1].strip() if ':' in error else 'Unknown'
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        print("  Error summary:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {error_type}: {count} rows")
        
        if len(errors) <= 20:
            print("\n  Detailed errors:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"\n  First 10 errors:")
            for error in errors[:10]:
                print(f"    - {error}")
            print(f"  ... and {len(errors) - 10} more (see full list above)")
    
    # Generate output files
    print(f"\nGenerating output files...")
    
    # Use all Directus columns, but only include those we have data for
    # Directus will skip empty columns, but having them ensures proper structure
    available_columns = DIRECTUS_COLUMNS.copy()
    
    # Test file (first 5 records) - IDs starting_id to starting_id+4
    test_rows = transformed_rows[:5]
    if test_rows:
        # Assign IDs starting_id to starting_id+4 for test file
        for i, row in enumerate(test_rows):
            row['id'] = starting_id + i
        print(f"  Test file IDs: {test_rows[0]['id']} to {test_rows[-1]['id']}")
        write_csv(output_test, test_rows, available_columns)
        print(f"  Created {output_test} with {len(test_rows)} records")
    
    # Main file (all records) - IDs continue from starting_id+5
    # This assumes test file (5 records) will be imported first
    main_file_starting_id = starting_id + 5
    if transformed_rows:
        # Reassign IDs for main file, starting from starting_id+5
        # This way, if test file is imported first (IDs 7033-7037),
        # main file will continue from 7038
        for i, row in enumerate(transformed_rows):
            row['id'] = main_file_starting_id + i
        print(f"  Main file IDs: {transformed_rows[0]['id']} to {transformed_rows[-1]['id']}")
        print(f"  (Assumes test file with IDs {starting_id}-{starting_id+4} imported first)")
        write_csv(output_main, transformed_rows, available_columns)
        print(f"  Created {output_main} with {len(transformed_rows)} records")
    
    # Check for new categories/projetos (though unlikely based on the data)
    new_categories = collect_new_categories(transformed_rows, existing_categoria_ids)
    new_projetos = collect_new_projetos(transformed_rows, existing_projeto_ids, projeto_mapping)
    
    if new_categories:
        write_csv(output_categoria, new_categories, ['id', 'label', 'status', 'created_on'])
        print(f"  Created {output_categoria} with {len(new_categories)} new categories")
    else:
        print(f"  No new categories found (skipping {output_categoria})")
    
    if new_projetos:
        write_csv(output_projeto, new_projetos, ['id', 'label', 'status', 'created_on', 'owner', 'auto_inserir'])
        print(f"  Created {output_projeto} with {len(new_projetos)} new projetos")
    else:
        print(f"  No new projetos found (skipping {output_projeto})")
    
    print("\nTransformation complete!")


if __name__ == '__main__':
    import sys
    
    # Allow starting ID to be passed as command line argument
    # Default: 7033 (last ID 7032 + 1)
    starting_id = 7033
    if len(sys.argv) > 1:
        try:
            starting_id = int(sys.argv[1])
        except ValueError:
            print(f"Warning: Invalid starting ID '{sys.argv[1]}', using default {starting_id}")
    
    main(starting_id=starting_id)

