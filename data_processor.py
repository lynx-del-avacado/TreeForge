import pandas as pd
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

def validate_csv_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate the structure and content of the uploaded CSV."""
    
    validation_result = {
        'valid': True,
        'message': '',
        'warnings': []
    }
    
    # Check if DataFrame is empty
    if df.empty:
        validation_result['valid'] = False
        validation_result['message'] = "CSV file is empty"
        return validation_result
    
    # Check for required columns
    required_columns = ['name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        validation_result['valid'] = False
        validation_result['message'] = f"Missing required columns: {', '.join(missing_columns)}"
        return validation_result
    
    # Check for empty names
    if df['name'].isnull().any() or (df['name'] == '').any():
        empty_name_rows = df[df['name'].isnull() | (df['name'] == '')].index.tolist()
        validation_result['warnings'].append(f"Empty names found in rows: {empty_name_rows}")
    
    # Check for duplicate names
    duplicate_names = df[df['name'].duplicated()]['name'].tolist()
    if duplicate_names:
        validation_result['warnings'].append(f"Duplicate names found: {duplicate_names}")
    
    # Validate date formats if date columns exist
    date_columns = ['birth_date', 'death_date']
    for col in date_columns:
        if col in df.columns:
            invalid_dates = _validate_date_column(df, col)
            if invalid_dates:
                validation_result['warnings'].append(
                    f"Invalid date format in {col} for rows: {invalid_dates}. Expected format: YYYY-MM-DD"
                )
    
    # Check for circular references in parent-child relationships
    circular_refs = _check_circular_references(df)
    if circular_refs:
        validation_result['warnings'].append(f"Potential circular references detected: {circular_refs}")
    
    # Check for orphaned references
    orphaned_refs = _check_orphaned_references(df)
    if orphaned_refs:
        validation_result['warnings'].append(f"Parent references not found in data: {orphaned_refs}")
    
    return validation_result

def _validate_date_column(df: pd.DataFrame, column: str) -> List[int]:
    """Validate date format in a specific column."""
    invalid_rows = []
    
    for idx, date_value in df[column].items():
        if pd.isnull(date_value) or str(date_value).strip() == '':
            continue
        
        try:
            # Try to parse the date
            datetime.strptime(str(date_value), '%Y-%m-%d')
        except ValueError:
            try:
                # Try alternative formats
                datetime.strptime(str(date_value), '%Y/%m/%d')
            except ValueError:
                try:
                    datetime.strptime(str(date_value), '%m/%d/%Y')
                except ValueError:
                    invalid_rows.append(idx)
    
    return invalid_rows

def _check_circular_references(df: pd.DataFrame) -> List[str]:
    """Check for circular references in parent-child relationships."""
    circular_refs = []
    
    if 'parent' not in df.columns:
        return circular_refs
    
    # Create a mapping of child to parent
    relationships = {}
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        parent = str(row.get('parent', '')).strip()
        
        if parent and parent != '' and parent != 'nan':
            relationships[name] = parent
    
    # Check for circular references
    for child, parent in relationships.items():
        visited = set()
        current = parent
        
        while current and current in relationships:
            if current in visited:
                circular_refs.append(f"{child} -> {' -> '.join(visited)} -> {current}")
                break
            
            visited.add(current)
            current = relationships.get(current)
            
            # If we've found the original child, it's a circular reference
            if current == child:
                circular_refs.append(f"{child} -> {' -> '.join(visited)} -> {child}")
                break
    
    return circular_refs

def _check_orphaned_references(df: pd.DataFrame) -> List[str]:
    """Check for parent references that don't exist in the data."""
    orphaned_refs = []
    
    if 'parent' not in df.columns:
        return orphaned_refs
    
    # Get all names in the dataset
    all_names = set(df['name'].astype(str).str.strip())
    
    # Check each parent reference
    for _, row in df.iterrows():
        parent = str(row.get('parent', '')).strip()
        
        if parent and parent != '' and parent != 'nan' and parent not in all_names:
            orphaned_refs.append(parent)
    
    return list(set(orphaned_refs))  # Remove duplicates

def process_csv_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process and clean the CSV data for family tree creation."""
    
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Clean and standardize column names
    processed_df.columns = processed_df.columns.str.lower().str.strip()
    
    # Fill NaN values with appropriate defaults
    processed_df = processed_df.fillna('')
    
    # Clean name column
    processed_df['name'] = processed_df['name'].astype(str).str.strip()
    
    # Clean parent column
    if 'parent' in processed_df.columns:
        processed_df['parent'] = processed_df['parent'].astype(str).str.strip()
        processed_df['parent'] = processed_df['parent'].replace(['nan', 'NaN', 'None'], '')
    else:
        processed_df['parent'] = ''
    
    # Process date columns
    date_columns = ['birth_date', 'death_date']
    for col in date_columns:
        if col in processed_df.columns:
            processed_df[col] = _standardize_dates(processed_df[col])
    
    # Clean gender column
    if 'gender' in processed_df.columns:
        processed_df['gender'] = processed_df['gender'].astype(str).str.strip().str.upper()
        processed_df['gender'] = processed_df['gender'].replace(['NAN', 'NONE', ''], None)
    
    # Clean other text columns
    text_columns = ['spouse', 'occupation', 'notes']
    for col in text_columns:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].astype(str).str.strip()
            processed_df[col] = processed_df[col].replace(['nan', 'NaN', 'None'], '')
    
    # Remove rows with empty names
    processed_df = processed_df[processed_df['name'] != '']
    
    # Convert to list of dictionaries
    data = processed_df.to_dict('records')
    
    # Post-process each record
    for record in data:
        # Convert empty strings to None for certain fields
        for field in ['parent', 'birth_date', 'death_date', 'spouse', 'occupation', 'notes']:
            if field in record and record[field] == '':
                record[field] = None
        
        # Ensure parent is None if it's the same as the name (self-reference)
        if record.get('parent') == record['name']:
            record['parent'] = None
    
    return data

def _standardize_dates(date_series: pd.Series) -> pd.Series:
    """Standardize date formats to YYYY-MM-DD."""
    
    standardized_dates = []
    
    for date_value in date_series:
        if pd.isnull(date_value) or str(date_value).strip() == '' or str(date_value).lower() == 'nan':
            standardized_dates.append('')
            continue
        
        date_str = str(date_value).strip()
        standardized_date = _parse_date(date_str)
        standardized_dates.append(standardized_date if standardized_date else '')
    
    return pd.Series(standardized_dates)

def _parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats and return YYYY-MM-DD format."""
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',    # 2023-01-15
        '%Y/%m/%d',    # 2023/01/15
        '%m/%d/%Y',    # 01/15/2023
        '%d/%m/%Y',    # 15/01/2023
        '%Y-%m',       # 2023-01
        '%Y/%m',       # 2023/01
        '%Y',          # 2023
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            
            # For partial dates, pad with defaults
            if fmt in ['%Y-%m', '%Y/%m']:
                return f"{parsed_date.year:04d}-{parsed_date.month:02d}-01"
            elif fmt == '%Y':
                return f"{parsed_date.year:04d}-01-01"
            else:
                return f"{parsed_date.year:04d}-{parsed_date.month:02d}-{parsed_date.day:02d}"
        
        except ValueError:
            continue
    
    # If no format matches, return None
    return None

def export_family_data(family_tree, format_type: str = 'csv') -> str:
    """Export family tree data in various formats."""
    
    df = family_tree.to_dataframe()
    
    if format_type.lower() == 'csv':
        return df.to_csv(index=False)
    elif format_type.lower() == 'json':
        return df.to_json(orient='records', indent=2)
    else:
        raise ValueError(f"Unsupported export format: {format_type}")

def get_data_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate statistics about the family data."""
    
    stats = {
        'total_members': len(df),
        'with_birth_dates': df['birth_date'].notna().sum() if 'birth_date' in df.columns else 0,
        'with_death_dates': df['death_date'].notna().sum() if 'death_date' in df.columns else 0,
        'living_members': len(df) - (df['death_date'].notna().sum() if 'death_date' in df.columns else 0),
        'gender_distribution': df['gender'].value_counts().to_dict() if 'gender' in df.columns else {},
        'with_occupations': df['occupation'].notna().sum() if 'occupation' in df.columns else 0,
        'with_spouses': df['spouse'].notna().sum() if 'spouse' in df.columns else 0,
    }
    
    return stats
