"""
Improved Baseline Model with Feature Engineering and Hyperparameter Tuning

This script enhances the baseline model with:
1. Feature engineering (derived features)
2. Data-driven business rules
3. Hyperparameter tuning
4. Better evaluation metrics
"""

import json
import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Import baseline functions
sys.path.append(str(Path(__file__).parent))
from baseline import (
    find_dataset,
    load_dataset_with_na_handling,
    identify_target_column,
    coerce_numeric_columns,
    create_preprocessing_pipeline,
    save_artifacts
)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features to improve model accuracy

    Features added:
    - vehicle_age: Age of vehicle at time of incident
    - days_to_claim: Days between policy bind and incident
    - claim_to_premium_ratio: Claim amount relative to annual premium
    - is_luxury_brand: Boolean for luxury vehicle brands
    - is_high_theft_model: Boolean for high-theft vehicle models
    - has_bodily_injury: Boolean for claims with injuries
    - has_property_damage: Boolean for property damage
    - total_witnesses_police: Combined witness and police report indicator
    """

    df = df.copy()

    print("\n" + "="*50)
    print("FEATURE ENGINEERING")
    print("="*50)

    features_added = []

    # 1. Vehicle age at incident
    if 'auto_year' in df.columns and 'incident_date' in df.columns:
        try:
            df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')
            df['incident_year'] = df['incident_date'].dt.year
            df['vehicle_age'] = df['incident_year'] - df['auto_year']
            # Cap at reasonable range
            df['vehicle_age'] = df['vehicle_age'].clip(0, 50)
            features_added.append("vehicle_age")
        except Exception as e:
            print(f"⚠ Could not create vehicle_age: {e}")

    # 2. Days to claim (policy tenure at incident)
    if 'policy_bind_date' in df.columns and 'incident_date' in df.columns:
        try:
            df['policy_bind_date'] = pd.to_datetime(df['policy_bind_date'], errors='coerce')
            df['days_to_claim'] = (df['incident_date'] - df['policy_bind_date']).dt.days
            # Cap at reasonable range (0 to 10 years)
            df['days_to_claim'] = df['days_to_claim'].clip(0, 3650)
            features_added.append("days_to_claim")
        except Exception as e:
            print(f"⚠ Could not create days_to_claim: {e}")

    # 3. Claim to premium ratio (fraud indicator)
    if 'total_claim_amount' in df.columns and 'policy_annual_premium' in df.columns:
        try:
            df['claim_to_premium_ratio'] = df['total_claim_amount'] / (df['policy_annual_premium'] + 1)
            # Cap at reasonable range
            df['claim_to_premium_ratio'] = df['claim_to_premium_ratio'].clip(0, 100)
            features_added.append("claim_to_premium_ratio")
        except Exception as e:
            print(f"⚠ Could not create claim_to_premium_ratio: {e}")

    # 4. Deductible to premium ratio
    if 'policy_deductable' in df.columns and 'policy_annual_premium' in df.columns:
        try:
            df['deductible_ratio'] = df['policy_deductable'] / (df['policy_annual_premium'] + 1)
            features_added.append("deductible_ratio")
        except Exception as e:
            print(f"⚠ Could not create deductible_ratio: {e}")

    # 5. Is luxury brand
    if 'auto_make' in df.columns:
        luxury_brands = ['Mercedes', 'BMW', 'Audi', 'Lexus', 'Porsche', 'Jaguar',
                        'Land Rover', 'Tesla', 'Maserati', 'Alfa Romeo', 'Infiniti', 'Acura']
        df['is_luxury_brand'] = df['auto_make'].isin(luxury_brands).astype(int)
        features_added.append("is_luxury_brand")

    # 6. Is high-theft model (based on common high-theft vehicles)
    if 'auto_make' in df.columns and 'auto_model' in df.columns:
        high_theft = [
            ('Honda', 'Civic'), ('Honda', 'Accord'), ('Toyota', 'Camry'),
            ('Nissan', 'Altima'), ('Toyota', 'Corolla'), ('Ford', 'F-150'),
            ('Chevrolet', 'Silverado'), ('GMC', 'Sierra')
        ]
        df['is_high_theft_model'] = df.apply(
            lambda row: (row.get('auto_make'), row.get('auto_model')) in high_theft,
            axis=1
        ).astype(int)
        features_added.append("is_high_theft_model")

    # 7. Has bodily injury
    if 'bodily_injuries' in df.columns:
        df['has_bodily_injury'] = (df['bodily_injuries'] > 0).astype(int)
        features_added.append("has_bodily_injury")

    # 8. Has property damage
    if 'property_damage' in df.columns:
        # Convert YES/NO to boolean
        df['has_property_damage'] = (df['property_damage'] == 'YES').astype(int)
        features_added.append("has_property_damage")

    # 9. Police report and witnesses combined indicator
    if 'police_report_available' in df.columns and 'witnesses' in df.columns:
        df['police_and_witnesses'] = (
            (df['police_report_available'] == 'YES') & (df['witnesses'] > 0)
        ).astype(int)
        features_added.append("police_and_witnesses")

    # 10. Time of day categories
    if 'incident_hour_of_the_day' in df.columns:
        def categorize_hour(hour):
            if pd.isna(hour):
                return 'Unknown'
            hour = int(hour)
            if 6 <= hour < 12:
                return 'Morning'
            elif 12 <= hour < 17:
                return 'Afternoon'
            elif 17 <= hour < 21:
                return 'Evening'
            else:
                return 'Night'

        df['time_of_day'] = df['incident_hour_of_the_day'].apply(categorize_hour)
        features_added.append("time_of_day")

    # 11. Months as customer category
    if 'months_as_customer' in df.columns:
        def categorize_tenure(months):
            if pd.isna(months):
                return 'Unknown'
            if months < 12:
                return 'New (<1yr)'
            elif months < 36:
                return 'Medium (1-3yr)'
            elif months < 60:
                return 'Long (3-5yr)'
            else:
                return 'Very Long (5+yr)'

        df['customer_tenure_category'] = df['months_as_customer'].apply(categorize_tenure)
        features_added.append("customer_tenure_category")

    print(f"✓ Added {len(features_added)} engineered features:")
    for feat in features_added:
        print(f"  • {feat}")
    print("="*50 + "\n")

    return df


def calculate_data_driven_multipliers(df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Calculate actual multipliers from data instead of using hardcoded values

    Returns dict with:
    - regional_multipliers: Cost multiplier by state
    - severity_multipliers: Damage cost as % of vehicle value by severity
    - collision_type_adjustments: Cost adjustments by collision type
    """

    print("\n" + "="*50)
    print("CALCULATING DATA-DRIVEN BUSINESS RULES")
    print("="*50)

    multipliers = {}

    # 1. Regional multipliers (state-based)
    if 'incident_state' in df.columns or 'policy_state' in df.columns:
        state_col = 'incident_state' if 'incident_state' in df.columns else 'policy_state'

        # Calculate average claim by state relative to overall average
        overall_avg = df[target_col].mean()
        state_avgs = df.groupby(state_col)[target_col].mean()
        regional_mult = (state_avgs / overall_avg).to_dict()

        multipliers['regional_multipliers'] = regional_mult

        print(f"✓ Calculated regional multipliers for {len(regional_mult)} states")
        # Show top 5 most expensive and cheapest
        sorted_regions = sorted(regional_mult.items(), key=lambda x: x[1], reverse=True)
        print("  Most expensive states:")
        for state, mult in sorted_regions[:5]:
            print(f"    {state}: {mult:.2f}x")
        print("  Least expensive states:")
        for state, mult in sorted_regions[-5:]:
            print(f"    {state}: {mult:.2f}x")

    # 2. Severity multipliers (if we have vehicle value data)
    if 'incident_severity' in df.columns and 'vehicle_claim' in df.columns and 'auto_year' in df.columns:
        try:
            # Estimate vehicle value using depreciation model
            from backend.app.accurate_depreciation import calculate_accurate_value

            # For each severity level, calculate average claim as % of vehicle value
            severity_ratios = {}

            for severity in df['incident_severity'].dropna().unique():
                severity_df = df[df['incident_severity'] == severity].copy()

                # Skip if too few samples
                if len(severity_df) < 10:
                    continue

                # Calculate value-to-claim ratios
                ratios = []
                for _, row in severity_df.iterrows():
                    try:
                        value, _ = calculate_accurate_value(
                            make=row.get('auto_make', 'Toyota'),
                            model=row.get('auto_model', 'Camry'),
                            year=row.get('auto_year', 2010),
                            mileage=row.get('auto_mileage')
                        )
                        if value > 0 and row['vehicle_claim'] > 0:
                            ratio = row['vehicle_claim'] / value
                            # Only include reasonable ratios (0-200%)
                            if 0 < ratio <= 2.0:
                                ratios.append(ratio)
                    except:
                        continue

                if ratios:
                    severity_ratios[severity] = np.median(ratios)

            if severity_ratios:
                multipliers['severity_ratios'] = severity_ratios
                print(f"\n✓ Calculated severity ratios:")
                for sev, ratio in sorted(severity_ratios.items(), key=lambda x: x[1]):
                    print(f"    {sev}: {ratio:.1%} of vehicle value")

        except Exception as e:
            print(f"⚠ Could not calculate severity ratios: {e}")

    # 3. Collision type adjustments
    if 'collision_type' in df.columns:
        overall_avg = df[target_col].mean()
        collision_avgs = df.groupby('collision_type')[target_col].mean()
        collision_mult = (collision_avgs / overall_avg).to_dict()

        multipliers['collision_type_multipliers'] = collision_mult

        print(f"\n✓ Calculated collision type multipliers:")
        for col_type, mult in sorted(collision_mult.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {col_type}: {mult:.2f}x")

    print("="*50 + "\n")

    return multipliers


def train_improved_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    tune_hyperparameters: bool = True
) -> Tuple[Pipeline, dict]:
    """
    Train improved model with optional hyperparameter tuning
    """

    print("\n" + "="*50)
    print("TRAINING IMPROVED MODEL")
    print("="*50)

    # Create preprocessing pipeline
    preprocessor = create_preprocessing_pipeline(X_train)

    if tune_hyperparameters:
        print("\n⏳ Hyperparameter tuning with cross-validation...")
        print("   Testing different configurations...")

        from sklearn.model_selection import RandomizedSearchCV

        # Define parameter distributions
        param_distributions = {
            'regressor__max_iter': [200, 300, 500],
            'regressor__max_depth': [5, 10, 15, 20, None],
            'regressor__learning_rate': [0.01, 0.05, 0.1],
            'regressor__l2_regularization': [0.0, 0.01, 0.1],
            'regressor__min_samples_leaf': [10, 20, 30],
        }

        # Base pipeline
        base_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(random_state=42))
        ])

        # Random search (faster than grid search)
        search = RandomizedSearchCV(
            base_pipeline,
            param_distributions,
            n_iter=20,  # Try 20 random combinations
            cv=3,  # 3-fold cross-validation
            scoring='neg_mean_absolute_error',
            random_state=42,
            n_jobs=-1,  # Use all CPU cores
            verbose=1
        )

        search.fit(X_train, y_train)

        print(f"\n✓ Best parameters found:")
        for param, value in search.best_params_.items():
            print(f"  • {param}: {value}")

        pipeline = search.best_estimator_

        # Show cross-validation score
        cv_mae = -search.best_score_
        print(f"\n✓ Cross-validation MAE: ${cv_mae:,.2f}")

    else:
        # Use improved default parameters
        print("\n⏳ Training with improved default parameters...")

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', HistGradientBoostingRegressor(
                max_iter=300,  # More iterations
                max_depth=15,  # Deeper trees
                learning_rate=0.05,  # Slower learning
                l2_regularization=0.01,  # Small regularization
                min_samples_leaf=20,
                random_state=42
            ))
        ])

        pipeline.fit(X_train, y_train)
        print("✓ Training complete")

    # Make predictions on validation set
    y_pred = pipeline.predict(X_val)

    # Calculate comprehensive metrics
    mae = mean_absolute_error(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    r2 = r2_score(y_val, y_pred)

    # Calculate median absolute error (more robust to outliers)
    median_ae = np.median(np.abs(y_val - y_pred))

    # Calculate percentage errors
    mape = np.mean(np.abs((y_val - y_pred) / y_val)) * 100

    metrics = {
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2),
        'median_ae': float(median_ae),
        'mape': float(mape)
    }

    print("\n" + "="*50)
    print("VALIDATION METRICS")
    print("="*50)
    print(f"MAE (Mean Absolute Error):     ${mae:,.2f}")
    print(f"RMSE (Root Mean Squared Error): ${rmse:,.2f}")
    print(f"R² (R-squared):                 {r2:.4f}")
    print(f"Median Absolute Error:          ${median_ae:,.2f}")
    print(f"MAPE (Mean Absolute % Error):   {mape:.2f}%")
    print("="*50 + "\n")

    return pipeline, metrics


def main():
    """Main training pipeline with improvements"""

    print("\n" + "="*50)
    print("REPAIR HELPER - IMPROVED MODEL TRAINING")
    print("="*50 + "\n")

    try:
        # 1. Load dataset
        print("Step 1: Loading dataset...")
        dataset_path, dataset_name = find_dataset()
        df = load_dataset_with_na_handling(dataset_path)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns\n")

        # 2. Identify target
        print("Step 2: Identifying target column...")
        target_col = identify_target_column(df)
        print()

        # 3. Feature Engineering
        print("Step 3: Engineering features...")
        df = engineer_features(df)

        # 4. Calculate data-driven business rules
        print("Step 4: Calculating data-driven multipliers...")
        multipliers = calculate_data_driven_multipliers(df, target_col)

        # Save multipliers for use in business rules
        artifacts_dir = Path("ml/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        with open(artifacts_dir / "business_rules.json", 'w') as f:
            json.dump(multipliers, f, indent=2)
        print(f"✓ Saved business rules to: {artifacts_dir / 'business_rules.json'}\n")

        # 5. Prepare data
        print("Step 5: Preparing data...")
        # Drop target column and separate
        y = df[target_col]
        X = df.drop(columns=[target_col])

        # Drop rows with missing target
        mask = y.notna()
        X = X[mask]
        y = y[mask]

        # Coerce numeric columns
        X = coerce_numeric_columns(X)

        print(f"✓ Final dataset: {len(X)} rows, {len(X.columns)} features\n")

        # 6. Train/val split
        print("Step 6: Splitting data (80/20 train/val)...")
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42
        )
        print(f"✓ Train set: {len(X_train)} samples")
        print(f"✓ Val set:   {len(X_val)} samples\n")

        # 7. Train improved model
        pipeline, metrics = train_improved_model(
            X_train, y_train, X_val, y_val,
            tune_hyperparameters=True  # Set to False for faster training
        )

        # 8. Save artifacts
        print("Step 7: Saving artifacts...")

        # Save model
        model_path = artifacts_dir / "model_improved.pkl"
        joblib.dump(pipeline, model_path)
        print(f"✓ Model saved to: {model_path}")

        # Save metadata
        meta = {
            "dataset": dataset_name,
            "target": target_col,
            "trained_at": datetime.now().isoformat(),
            "features_count": len(X.columns),
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            **metrics
        }

        meta_path = artifacts_dir / "model_improved_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        print(f"✓ Metadata saved to: {meta_path}\n")

        # 9. Compare with baseline
        baseline_meta_path = artifacts_dir / "meta.json"
        if baseline_meta_path.exists():
            with open(baseline_meta_path, 'r') as f:
                baseline_meta = json.load(f)

            print("="*50)
            print("COMPARISON: BASELINE vs IMPROVED")
            print("="*50)
            print(f"                        Baseline      Improved      Change")
            print(f"MAE:                    ${baseline_meta['mae']:>9,.2f}  ${metrics['mae']:>9,.2f}  {(metrics['mae']-baseline_meta['mae'])/baseline_meta['mae']*100:>+6.1f}%")
            print(f"R²:                     {baseline_meta['r2']:>10.4f}  {metrics['r2']:>10.4f}  {(metrics['r2']-baseline_meta['r2'])*100:>+6.2f} pts")

            if metrics['mae'] < baseline_meta['mae']:
                improvement = (baseline_meta['mae'] - metrics['mae']) / baseline_meta['mae'] * 100
                print(f"\n🎉 IMPROVEMENT: {improvement:.1f}% reduction in MAE!")
            print("="*50 + "\n")

        print("="*50)
        print("✓ IMPROVED MODEL TRAINING COMPLETE")
        print("="*50 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
