"""
Testing script to validate your dynamic workout page system
Run this to check if your data structure works with the new system
"""

import pandas as pd
import sys
import os

def test_workout_detection(df):
    """Test that workout types are properly detected"""
    print("=== Testing Workout Detection ===")
    
    from utils.data_loader import get_unique_workouts
    
    workouts = get_unique_workouts(df)
    print(f"Found {len(workouts)} unique workout types:")
    for workout in workouts:
        print(f"  - {workout}")
    
    return len(workouts) > 0

def test_movement_extraction(df):
    """Test that movements are properly extracted"""
    print("\n=== Testing Movement Extraction ===")
    
    from utils.data_loader import extract_movements_from_workout
    
    movements_df = extract_movements_from_workout(df)
    
    if movements_df.empty:
        print("❌ No movements extracted - check your column naming")
        return False
    
    print(f"✅ Extracted {len(movements_df)} movement entries")
    print(f"✅ Found {movements_df['movement'].nunique()} unique movements")
    
    # Show sample
    print("\nSample movements:")
    print(movements_df[['date', 'workout_type', 'movement', 'weight', 'reps', 'sets']].head())
    
    return True

def test_data_validation(df):
    """Test data validation function"""
    print("\n=== Testing Data Validation ===")
    
    from utils.data_loader import validate_data_structure
    
    is_valid, issues = validate_data_structure(df)
    
    if is_valid:
        print("✅ Data structure is valid!")
    else:
        print("⚠️  Data structure issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    return is_valid

def run_full_test():
    """Run complete test suite"""
    print("🧪 Testing Dynamic Workout Page System")
    print("=" * 50)
    
    # Test with sample data first
    sample_data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Workout': ['Push Day', 'Pull Day', 'Push Day'],
        'movement_1': ['Bench Press', 'Pull-ups', 'Bench Press'],
        'weight_1': [185, 0, 190],
        'rep_1': [8, 12, 6],
        'set_1': [3, 3, 4],
        'movement_2': ['Shoulder Press', 'Rows', 'Incline Press'],
        'weight_2': [95, 70, 155],
        'rep_2': [10, 10, 8],
        'set_2': [3, 3, 3]
    }
    
    test_df = pd.DataFrame(sample_data)
    test_df['Date'] = pd.to_datetime(test_df['Date'])
    
    print("Testing with sample data...")
    
    # Run tests
    tests = [
        test_workout_detection(test_df),
        test_movement_extraction(test_df), 
        test_data_validation(test_df)
    ]
    
    print(f"\n{'=' * 50}")
    print(f"Test Results: {sum(tests)}/{len(tests)} passed")
    
    if all(tests):
        print("🎉 All tests passed! Your system should work correctly.")
    else:
        print("❌ Some tests failed. Check the issues above.")
    
    # Try to load real data if available
    print(f"\n{'=' * 50}")
    print("Attempting to load real data...")
    
    try:
        from utils.data_loader import load_workout_data
        real_df = load_workout_data()
        
        if real_df is not None and not real_df.empty:
            print("✅ Successfully loaded real data!")
            print(f"Real data shape: {real_df.shape}")
            
            # Test real data
            print("\nTesting real data...")
            real_tests = [
                test_workout_detection(real_df),
                test_movement_extraction(real_df),
                test_data_validation(real_df)
            ]
            
            print(f"Real data tests: {sum(real_tests)}/{len(real_tests)} passed")
            
        else:
            print("⚠️  Could not load real data (this is OK for initial testing)")
            
    except Exception as e:
        print(f"⚠️  Could not test real data: {e}")

if __name__ == "__main__":
    run_full_test()