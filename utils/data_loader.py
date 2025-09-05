"""
Enhanced Data Loading Utilities
Handles connection to Google Sheets, data processing, and workout discovery
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
from typing import Tuple, Optional, List, Dict
import numpy as np

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
        
        # Open the spreadsheet
        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Your Workout Log')
        worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'master_tracker')  # Updated default
        
        try:
            spreadsheet = gc.open(sheet_name)
            
            # Try to access specific worksheet, fall back to first sheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                st.warning(f"Worksheet '{worksheet_name}' not found, using first sheet")
                worksheet = spreadsheet.sheet1
            
        except gspread.SpreadsheetNotFound:
            st.error(f"Spreadsheet '{sheet_name}' not found or not accessible")
            return None
        
        # Get all data
        records = worksheet.get_all_records()
        
        if not records:
            st.warning("No data found in the spreadsheet")
            return pd.DataFrame()  # Return empty DataFrame
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        if df.empty:
            st.warning("No data found in the spreadsheet")
            return pd.DataFrame()
        
        # Basic data cleaning
        df = clean_workout_data(df)
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def clean_workout_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize workout data with enhanced movement processing
    """
    if df.empty:
        return df
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Standard column name mapping
    column_mapping = {
        'date': 'Date',
        'Date': 'Date',
        'workout': 'Workout',
        'Workout': 'Workout',
        'start_time': 'Start_Time'
    }
    
    # Rename columns that exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Convert date columns
    if 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except:
            pass
    
    if 'Start_Time' in df.columns:
        try:
            df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
        except:
            pass
    
    # Clean movement columns (remove #REF! errors)
    movement_cols = [col for col in df.columns if col.startswith('movement_')]
    weight_cols = [col for col in df.columns if col.startswith('weight_')]
    rep_cols = [col for col in df.columns if col.startswith('rep_')]
    set_cols = [col for col in df.columns if col.startswith('set_')]
    
    # Replace #REF! with NaN
    for col in movement_cols + weight_cols + rep_cols + set_cols:
        if col in df.columns:
            df[col] = df[col].replace('#REF!', np.nan)
    
    # Convert numeric columns
    for col in weight_cols + rep_cols + set_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows where workout type is missing
    if 'Workout' in df.columns:
        df = df.dropna(subset=['Workout'])
        df = df[df['Workout'].str.strip() != '']
    
    return df

def get_unique_workouts(df: pd.DataFrame) -> List[str]:
    """
    Get list of unique workout types from the dataframe
    """
    if df.empty or 'Workout' not in df.columns:
        return []
    
    unique_workouts = df['Workout'].dropna().unique()
    # Sort for consistent ordering
    return sorted([w for w in unique_workouts if w and str(w).strip()])

def get_workout_data(df: pd.DataFrame, workout_type: str) -> pd.DataFrame:
    """
    Filter dataframe for a specific workout type
    """
    if df.empty or 'Workout' not in df.columns:
        return pd.DataFrame()
    
    return df[df['Workout'] == workout_type].copy()

def extract_movements_from_workout(workout_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and normalize movement data from the wide format into long format
    Returns a dataframe with one row per movement per workout session
    """
    if workout_df.empty:
        return pd.DataFrame()
    
    movements_list = []
    
    for idx, row in workout_df.iterrows():
        # Base information for this workout session
        base_info = {
            'session_id': idx,
            'date': row.get('Date'),
            'start_time': row.get('Start_Time'),
            'workout_type': row.get('Workout')
        }
        
        # Extract movements (1-10)
        for i in range(1, 11):
            movement_col = f'movement_{i}'
            weight_col = f'weight_{i}'
            rep_col = f'rep_{i}'
            set_col = f'set_{i}'
            
            # Check if movement exists and is not empty
            if (movement_col in row and 
                pd.notna(row[movement_col]) and 
                str(row[movement_col]).strip() and 
                str(row[movement_col]).strip() != 'Notes'):
                
                movement_data = base_info.copy()
                movement_data.update({
                    'movement_order': i,
                    'movement': str(row[movement_col]).strip(),
                    'weight': row.get(weight_col) if pd.notna(row.get(weight_col)) else None,
                    'reps': row.get(rep_col) if pd.notna(row.get(rep_col)) else None,
                    'sets': row.get(set_col) if pd.notna(row.get(set_col)) else None
                })
                
                movements_list.append(movement_data)
    
    return pd.DataFrame(movements_list)

def get_workout_summary_stats(workout_df: pd.DataFrame) -> Dict:
    """
    Calculate comprehensive summary statistics for a specific workout type
    """
    if workout_df.empty:
        return {}
    
    # Extract movements
    movements_df = extract_movements_from_workout(workout_df)
    
    if movements_df.empty:
        return {
            'total_sessions': len(workout_df),
            'date_range': 'No data',
            'unique_movements': 0,
            'total_movements': 0
        }
    
    # Basic stats
    stats = {
        'total_sessions': len(workout_df),
        'unique_movements': movements_df['movement'].nunique(),
        'total_movements': len(movements_df),
        'avg_movements_per_session': len(movements_df) / len(workout_df) if len(workout_df) > 0 else 0
    }
    
    # Date range
    if 'date' in movements_df.columns and movements_df['date'].notna().any():
        min_date = movements_df['date'].min()
        max_date = movements_df['date'].max()
        stats['date_range'] = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        # Days between first and last workout
        date_diff = (max_date - min_date).days
        stats['days_active'] = date_diff
        
        # Average frequency (sessions per week)
        if date_diff > 0:
            stats['avg_frequency_per_week'] = (len(workout_df) / date_diff) * 7
        else:
            stats['avg_frequency_per_week'] = 0
    else:
        stats['date_range'] = 'No date information'
        stats['days_active'] = 0
        stats['avg_frequency_per_week'] = 0
    
    # Weight statistics
    weight_data = movements_df['weight'].dropna()
    if not weight_data.empty:
        stats['avg_weight'] = weight_data.mean()
        stats['max_weight'] = weight_data.max()
        stats['min_weight'] = weight_data.min()
        stats['total_volume'] = (movements_df['weight'] * movements_df['reps'] * movements_df['sets']).sum()
    else:
        stats['avg_weight'] = 0
        stats['max_weight'] = 0
        stats['min_weight'] = 0
        stats['total_volume'] = 0
    
    # Rep statistics
    rep_data = movements_df['reps'].dropna()
    if not rep_data.empty:
        stats['avg_reps'] = rep_data.mean()
        stats['max_reps'] = rep_data.max()
        stats['total_reps'] = rep_data.sum()
    else:
        stats['avg_reps'] = 0
        stats['max_reps'] = 0
        stats['total_reps'] = 0
    
    # Set statistics
    set_data = movements_df['sets'].dropna()
    if not set_data.empty:
        stats['avg_sets'] = set_data.mean()
        stats['total_sets'] = set_data.sum()
    else:
        stats['avg_sets'] = 0
        stats['total_sets'] = 0
    
    # Most common movements
    movement_counts = movements_df['movement'].value_counts()
    stats['most_common_movements'] = movement_counts.head(5).to_dict()
    
    return stats

def get_movement_progress_data(movements_df: pd.DataFrame, movement_name: str) -> pd.DataFrame:
    """
    Get progress data for a specific movement over time
    """
    if movements_df.empty:
        return pd.DataFrame()
    
    movement_data = movements_df[movements_df['movement'] == movement_name].copy()
    
    if movement_data.empty:
        return pd.DataFrame()
    
    # Sort by date
    movement_data = movement_data.sort_values('date')
    
    # Calculate total volume for each session
    movement_data['volume'] = (
        movement_data['weight'].fillna(0) * 
        movement_data['reps'].fillna(0) * 
        movement_data['sets'].fillna(0)
    )
    
    return movement_data

def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Get basic summary statistics about the workout data
    """
    if df.empty:
        return {
            'total_records': 0,
            'unique_workouts': 0,
            'unique_movements': 0,
            'date_range': 'No data',
            'columns': []
        }
    
    summary = {
        'total_records': len(df),
        'unique_workouts': df['Workout'].nunique() if 'Workout' in df.columns else 0,
        'columns': list(df.columns)
    }
    
    # Extract all movements to count unique ones
    if not df.empty:
        movements_df = extract_movements_from_workout(df)
        summary['unique_movements'] = movements_df['movement'].nunique() if not movements_df.empty else 0
        summary['total_movement_entries'] = len(movements_df)
    
    # Date range
    if 'Date' in df.columns and df['Date'].notna().any():
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        summary['date_range'] = f"{min_date} to {max_date}"
    else:
        summary['date_range'] = 'No date information'
    
    return summary