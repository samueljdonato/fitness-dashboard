"""
Data Loading Utilities
Handles connection to Google Sheets and data processing
"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
from typing import Tuple, Optional

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
        worksheet_name = os.getenv('GOOGLE_SHEET_WORKSHEET', 'Sheet1')
        
        try:
            spreadsheet = gc.open(sheet_name)
            
            # Try to access specific worksheet, fall back to first sheet
            try:
                if worksheet_name == 'Sheet1' or worksheet_name == '':
                    worksheet = spreadsheet.sheet1
                else:
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
        'unique_movements': df['Movement'].nunique() if 'Movement' in df.columns else 0,
        'columns': list(df.columns)
    }
    
    # Date range
    if 'Date' in df.columns and df['Date'].notna().any():
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        summary['date_range'] = f"{min_date} to {max_date}"
    else:
        summary['date_range'] = 'No date information'
    
    return summary