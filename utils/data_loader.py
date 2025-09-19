"""
Data Loading Utilities
Handles connection to Google Sheets and data processing
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
from typing import Tuple, Optional, List, Dict
from datetime import datetime




def get_google_credentials():
    """Get Google credentials from service account file"""
    try:
        # Path to service account credentials
        creds_path = "config/service_account.json"
        
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Service account file not found: {creds_path}")
        
        # Define the scope
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # Create credentials
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        
        return gspread.authorize(credentials)
    
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets: {str(e)}")
        return None

def test_connection() -> Tuple[bool, str]:
    """
    Test the connection to Google Sheets
    Returns: (success: bool, message: str)
    """
    try:
        # Test credentials
        gc = get_google_credentials()
        if gc is None:
            return False, "Failed to authenticate with Google"
        
        # Test sheet access
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Your Workout Log')
        try:
            spreadsheet = gc.open(sheet_name)
            worksheet = spreadsheet.sheet1  # Default to first sheet
            
            # Try to read just the header row
            header_row = worksheet.row_values(1)
            
            if not header_row:
                return False, f"Sheet '{sheet_name}' appears to be empty"
            
            return True, f"✅ Successfully connected to '{sheet_name}' with {len(header_row)} columns"
            
        except gspread.SpreadsheetNotFound:
            return False, f"❌ Sheet '{sheet_name}' not found or not shared with service account"
        except Exception as e:
            return False, f"❌ Error accessing sheet: {str(e)}"
    
    except Exception as e:
        return False, f"❌ Connection test failed: {str(e)}"

@st.cache_data(ttl=int(os.getenv('REFRESH_INTERVAL', 60)))
def load_workout_data() -> Optional[pd.DataFrame]:
    """
    Load workout data from Google Sheets with caching
    Returns: DataFrame or None if error
    """

    
    try:
        # Get credentials
        gc = get_google_credentials()
        if gc is None:
            return None
        
        # # Open the spreadsheet
        # sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Your Workout Log')
        # worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'Sheet1')
        # Open the spreadsheet
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Fitness Tracker')
        worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'master_tracker')

        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)

        data = worksheet.get_all_records()

        # Get all data
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame()  # Return empty DataFrame if no data
        
        df = pd.DataFrame(data)
        
        # Process the data
        # df = process_raw_data(df)
        df = clean_workout_data(df)
        
        return df        
   
    except Exception as e:
        st.error(f"Error loading workout data: {str(e)}")
        return None                     
        
    #     try:
    #         spreadsheet = gc.open(sheet_name)
            
    #         # Try to access specific worksheet, fall back to first sheet
    #         try:
    #             if worksheet_name == 'Sheet1' or worksheet_name == '':
    #                 worksheet = spreadsheet.sheet1
    #             else:
    #                 worksheet = spreadsheet.worksheet(worksheet_name)
    #         except gspread.WorksheetNotFound:
    #             st.warning(f"Worksheet '{worksheet_name}' not found, using first sheet")
    #             worksheet = spreadsheet.sheet1
            
    #     except gspread.SpreadsheetNotFound:
    #         st.error(f"Spreadsheet '{sheet_name}' not found or not accessible")
    #         return None
        
    #     # Get all data
    #     records = worksheet.get_all_records()
        
    #     if not records:
    #         st.warning("No data found in the spreadsheet")
    #         return pd.DataFrame()  # Return empty DataFrame
        
    #     # Convert to DataFrame
    #     df = pd.DataFrame(records)
        
    #     if df.empty:
    #         st.warning("No data found in the spreadsheet")
    #         return pd.DataFrame()
        
    #     # Basic data cleaning
    #     df = clean_workout_data(df)
        
    #     return df
    
    # except Exception as e:
    #     st.error(f"Error loading data: {str(e)}")
    #     return None

def clean_workout_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize workout data
    """
    if df.empty:
        return df
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Common column name standardizations (adapt based on your sheet structure)
    column_mapping = {
        'date': 'Date',
        'Date': 'Date',
        'workout': 'Workout',
        'Workout': 'Workout',
        'exercise': 'Movement',
        'movement': 'Movement',
        'Movement': 'Movement',
        'Exercise': 'Movement',
        'reps': 'Reps',
        'Reps': 'Reps',
        'sets': 'Sets',
        'Sets': 'Sets',
        'weight': 'Weight',
        'Weight': 'Weight'
    }
    
    # Rename columns that exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Convert data types where possible
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except:
            pass  # Keep as string if conversion fails
    
    # Convert numeric columns
    numeric_columns = ['Reps', 'Sets', 'Weight']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows where all key columns are NaN
    key_columns = ['Workout', 'Movement']
    existing_key_cols = [col for col in key_columns if col in df.columns]
    if existing_key_cols:
        df = df.dropna(subset=existing_key_cols, how='all')
    
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


# def get_data_summary(df: pd.DataFrame) -> dict:

#     """
#     Get basic summary statistics about the workout data
#     """
#     if df.empty:
#         return {
#             'total_records': 0,
#             'unique_workouts': 0,
#             'unique_movements': 0,
#             'date_range': 'No data',
#             'columns': []
#         }
    
#     summary = {
#         'total_records': len(df),
#         'unique_workouts': df['Workout'].nunique() if 'Workout' in df.columns else 0,
#         'unique_movements': df['Movement'].nunique() if 'Movement' in df.columns else 0,
#         'columns': list(df.columns)
#     }
    
#     # Date range
#     if 'Date' in df.columns and df['Date'].notna().any():
#         min_date = df['Date'].min()
#         max_date = df['Date'].max()
#         summary['date_range'] = f"{min_date} to {max_date}"
#     else:
#         summary['date_range'] = 'No date information'
    
#     return summary


