"""
Enhanced data loading utilities for dynamic workout analysis
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Optional, Tuple
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=int(os.getenv('REFRESH_INTERVAL', '300')))  # Cache for 5 minutes default
def load_workout_data() -> Optional[pd.DataFrame]:
    """
    Load workout data from Google Sheets with caching
    Returns processed DataFrame or None if loading fails
    """
    try:
        # Get credentials and connect to Google Sheets
        success, client_or_message = get_google_sheets_client()
        
        if not success:
            st.error(f"Failed to connect to Google Sheets: {client_or_message}")
            return None
            
        client = client_or_message
        
        # Open the spreadsheet
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Fitness Tracker')
        worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'master_tracker')
        
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get all data
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame()  # Return empty DataFrame if no data
        
        df = pd.DataFrame(data)
        
        # Process the data
        df = process_raw_data(df)
        
        return df
        
    except Exception as e:
        st.error(f"Error loading workout data: {str(e)}")
        return None

def get_google_sheets_client() -> Tuple[bool, any]:
    """
    Get authenticated Google Sheets client
    Returns (success, client_or_error_message)
    """
    try:
        # Define the scope
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Get credentials from Streamlit secrets or environment
        if 'GOOGLE_SHEETS_CREDENTIALS' in st.secrets:
            # Using Streamlit secrets (recommended for deployment)
            creds_dict = st.secrets['GOOGLE_SHEETS_CREDENTIALS']
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        else:
            # Using service account file (for local development)
            creds_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
            if os.path.exists(creds_file):
                credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
            else:
                return False, "No credentials found. Please configure GOOGLE_SHEETS_CREDENTIALS or credentials file."
        
        # Create the client
        client = gspread.authorize(credentials)
        return True, client
        
    except Exception as e:
        return False, str(e)

def process_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw data from Google Sheets into standardized format
    """
    if df.empty:
        return df
    
    # Standardize column names (handle case variations)
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'date' in col_lower:
            column_mapping[col] = 'Date'
        elif 'workout' in col_lower and 'type' not in col_lower:
            column_mapping[col] = 'Workout'
        elif 'start' in col_lower and 'time' in col_lower:
            column_mapping[col] = 'Start_Time'
        elif 'end' in col_lower and 'time' in col_lower:
            column_mapping[col] = 'End_Time'
    
    df = df.rename(columns=column_mapping)
    
    # Convert date columns
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Convert time columns
    for time_col in ['Start_Time', 'End_Time']:
        if time_col in df.columns:
            df[time_col] = pd.to_datetime(df[time_col], format='%H:%M', errors='coerce')
    
    # Clean up empty rows
    df = df.dropna(how='all')
    
    # Remove rows where essential columns are empty
    if 'Workout' in df.columns:
        df = df[df['Workout'].notna() & (df['Workout'] != '')]
    
    return df

def get_unique_workouts(df: pd.DataFrame) -> List[str]:
    """
    Extract unique workout types from the dataset
    """
    if df.empty or 'Workout' not in df.columns:
        return []
    
    workouts = df['Workout'].dropna().unique()
    # Filter out empty strings and sort
    workouts = [w for w in workouts if w and str(w).strip()]
    return sorted(workouts)

def extract_movements_from_workout(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract individual movements from workout sessions
    Handles dynamic column structure for movements, weights, reps, and sets
    """
    if df.empty:
        return pd.DataFrame()
    
    movements_data = []
    
    # Find movement columns (movement_1, movement_2, etc.)
    movement_columns = [col for col in df.columns if 'movement_' in col.lower()]
    
    for idx, row in df.iterrows():
        session_id = idx
        date = row.get('Date', pd.NaT)
        workout_type = row.get('Workout', 'Unknown')
        
        # Extract movements for this session
        for movement_col in movement_columns:
            movement_num = movement_col.lower().replace('movement_', '')
            
            movement_name = row.get(movement_col, None)
            if pd.isna(movement_name) or str(movement_name).strip() == '':
                continue
                
            # Look for corresponding weight, rep, and set columns
            weight_col = f'weight_{movement_num}'
            rep_col = f'rep_{movement_num}'
            set_col = f'set_{movement_num}'
            
            # Alternative naming conventions
            alt_weight_cols = [f'weights_{movement_num}', f'wt_{movement_num}']
            alt_rep_cols = [f'reps_{movement_num}', f'repetitions_{movement_num}']
            alt_set_cols = [f'sets_{movement_num}']
            
            # Find the actual column names (case insensitive)
            def find_column(target_cols):
                for target in target_cols:
                    for col in df.columns:
                        if col.lower() == target.lower():
                            return col
                return None
            
            weight_col = find_column([weight_col] + alt_weight_cols)
            rep_col = find_column([rep_col] + alt_rep_cols)
            set_col = find_column([set_col] + alt_set_cols)
            
            weight = row.get(weight_col, 0) if weight_col else 0
            reps = row.get(rep_col, 0) if rep_col else 0
            sets = row.get(set_col, 0) if set_col else 0
            
            # Convert to numeric, handle errors
            try:
                weight = float(weight) if pd.notna(weight) and str(weight).strip() != '' else 0
                reps = float(reps) if pd.notna(reps) and str(reps).strip() != '' else 0
                sets = float(sets) if pd.notna(sets) and str(sets).strip() != '' else 0
            except (ValueError, TypeError):
                weight, reps, sets = 0, 0, 0
            
            # Only add if we have at least some meaningful data
            if weight > 0 or reps > 0 or sets > 0:
                movements_data.append({
                    'session_id': session_id,
                    'date': date,
                    'workout_type': workout_type,
                    'movement': str(movement_name).strip(),
                    'weight': weight,
                    'reps': reps,
                    'sets': sets,
                    'movement_number': movement_num
                })
    
    if not movements_data:
        return pd.DataFrame()
    
    movements_df = pd.DataFrame(movements_data)
    
    # Clean up the dataframe
    movements_df = movements_df[movements_df['movement'] != '']
    movements_df = movements_df.sort_values(['date', 'session_id', 'movement_number'])
    
    return movements_df

def get_data_summary(df: pd.DataFrame) -> Dict:
    """
    Get summary statistics about the dataset
    """
    if df.empty:
        return {
            'total_records': 0,
            'unique_workouts': 0,
            'date_range': 'No data',
            'columns': []
        }
    
    summary = {
        'total_records': len(df),
        'unique_workouts': len(get_unique_workouts(df)),
        'columns': list(df.columns)
    }
    
    # Date range
    if 'Date' in df.columns and df['Date'].notna().any():
        min_date = df['Date'].min().strftime('%Y-%m-%d')
        max_date = df['Date'].max().strftime('%Y-%m-%d')
        summary['date_range'] = f"{min_date} to {max_date}"
    else:
        summary['date_range'] = 'No date information'
    
    # Movement analysis
    movements_df = extract_movements_from_workout(df)
    if not movements_df.empty:
        summary['unique_movements'] = movements_df['movement'].nunique()
        summary['total_movement_entries'] = len(movements_df)
    else:
        summary['unique_movements'] = 0
        summary['total_movement_entries'] = 0
    
    return summary

def test_connection() -> Tuple[bool, str]:
    """
    Test the Google Sheets connection
    Returns (success, message)
    """
    try:
        success, client_or_message = get_google_sheets_client()
        
        if not success:
            return False, f"Authentication failed: {client_or_message}"
        
        client = client_or_message
        
        # Try to open the spreadsheet
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Fitness Tracker')
        spreadsheet = client.open(sheet_name)
        
        # Try to access the worksheet
        worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'master_tracker')
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get a small sample of data
        sample_data = worksheet.get('A1:E2')
        
        return True, f"✅ Successfully connected to '{sheet_name}' sheet, '{worksheet_name}' worksheet. Found {len(sample_data)} rows in sample."
        
    except gspread.SpreadsheetNotFound:
        return False, f"❌ Spreadsheet '{os.getenv('GOOGLE_SHEET_NAME')}' not found. Check the sheet name and sharing permissions."
    
    except gspread.WorksheetNotFound:
        return False, f"❌ Worksheet '{os.getenv('GOOGLE_SHEET_WORKSHEET')}' not found in the spreadsheet."
    
    except Exception as e:
        return False, f"❌ Connection test failed: {str(e)}"

def validate_data_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that the data has the expected structure
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    if df.empty:
        issues.append("Dataset is empty")
        return False, issues
    
    # Check for essential columns
    if 'Workout' not in df.columns:
        issues.append("Missing 'Workout' column - unable to identify workout types")
    
    if 'Date' not in df.columns:
        issues.append("Missing 'Date' column - unable to track progress over time")
    
    # Check for movement columns
    movement_columns = [col for col in df.columns if 'movement_' in col.lower()]
    if not movement_columns:
        issues.append("No movement columns found (expected format: movement_1, movement_2, etc.)")
    
    # Check data quality
    if 'Workout' in df.columns:
        empty_workouts = df['Workout'].isna().sum()
        if empty_workouts > 0:
            issues.append(f"{empty_workouts} rows have empty workout types")
    
    if 'Date' in df.columns:
        invalid_dates = df['Date'].isna().sum()
        if invalid_dates > 0:
            issues.append(f"{invalid_dates} rows have invalid or empty dates")
    
    # Check for movements data
    movements_df = extract_movements_from_workout(df)
    if movements_df.empty:
        issues.append("No valid movement data could be extracted from the dataset")
    
    is_valid = len(issues) == 0
    return is_valid, issues

# Utility functions for data filtering and analysis
def filter_data_by_date_range(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Filter dataframe by date range"""
    if 'Date' not in df.columns:
        return df
    
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    return df[mask]

def get_workout_frequency(df: pd.DataFrame, period: str = 'M') -> pd.Series:
    """
    Get workout frequency over time
    period: 'D' for daily, 'W' for weekly, 'M' for monthly, 'Q' for quarterly
    """
    if 'Date' not in df.columns or df.empty:
        return pd.Series()
    
    return df.groupby(df['Date'].dt.to_period(period)).size()

def calculate_workout_metrics(movements_df: pd.DataFrame) -> Dict:
    """Calculate various workout metrics from movements data"""
    if movements_df.empty:
        return {}
    
    metrics = {
        'total_volume': (movements_df['weight'] * movements_df['reps'] * movements_df['sets']).sum(),
        'total_reps': movements_df['reps'].sum(),
        'total_sets': movements_df['sets'].sum(),
        'avg_weight_per_movement': movements_df.groupby('movement')['weight'].mean().to_dict(),
        'max_weight_per_movement': movements_df.groupby('movement')['weight'].max().to_dict(),
        'total_sessions': movements_df['session_id'].nunique(),
        'movements_per_session': len(movements_df) / movements_df['session_id'].nunique() if movements_df['session_id'].nunique() > 0 else 0
    }
    
    return metrics