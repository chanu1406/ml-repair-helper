"""
Baseline model training script for Repair Helper.

This script trains a baseline regression model to predict auto insurance claim repair costs.
It handles data loading, preprocessing, training, evaluation, and artifact saving with
robust missing data handling.

Usage:
    python -m ml.baseline
"""

import json
import os
import sys
from pathlib import Path
from typing import Tuple, Optional

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def find_dataset() -> Tuple[Path, str]:
    """
    Find the dataset to use for training.

    Priority:
    1. data/raw/insurance_claims.csv (if exists)
    2. Largest CSV file in data/raw/

    Returns:
        Tuple of (Path to CSV file, filename)

    Raises:
        FileNotFoundError: If no CSV files found in data/raw/
    """
    data_dir = Path("data/raw")

    # Check for insurance_claims.csv first
    preferred_file = data_dir / "insurance_claims.csv"
    if preferred_file.exists():
        print(f"✓ Found preferred dataset: {preferred_file.name}")
        return preferred_file, preferred_file.name

    # Otherwise, find the largest CSV
    csv_files = list(data_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}. "
            "Please ensure data/raw/ contains at least one CSV file."
        )

    # Select largest CSV by file size
    largest_csv = max(csv_files, key=lambda p: p.stat().st_size)
    print(f"✓ Using largest CSV: {largest_csv.name} ({largest_csv.stat().st_size / 1024:.1f} KB)")

    return largest_csv, largest_csv.name


def load_dataset_with_na_handling(path: Path) -> pd.DataFrame:
    """
    Load CSV with comprehensive NA token handling.

    Args:
        path: Path to CSV file

    Returns:
        DataFrame with common NA tokens properly recognized
    """
    na_values = ["", "NA", "N/A", "na", "n/a", "NaN", "nan", "?", "NULL", "None"]

    df = pd.read_csv(path, na_values=na_values, keep_default_na=True)

    return df


def print_data_quality_report(df: pd.DataFrame, title: str = "DATA QUALITY REPORT") -> None:
    """
    Print a data quality report showing missing value statistics.

    Args:
        df: DataFrame to analyze
        title: Title for the report
    """
    print("\n" + "="*50)
    print(title)
    print("="*50)

    # Calculate missing percentages
    missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)

    # Show top 5 columns with missing values
    top_missing = missing_pct[missing_pct > 0].head(5)

    if len(top_missing) > 0:
        print("\nTop 5 columns with missing values:")
        for col, pct in top_missing.items():
            print(f"  • {col}: {pct:.1f}%")
    else:
        print("\n✓ No missing values detected")

    total_missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    print(f"\nOverall missing: {total_missing_pct:.2f}% of all cells")
    print("="*50 + "\n")


def identify_target_column(df: pd.DataFrame) -> str:
    """
    Identify the target column for prediction.

    Priority order (case-insensitive):
    1. Check predefined list: ["loss", "total claim amount", "total_claim_amount",
                                "claim_amount", "amount", "charges", "cost"]
    2. If none found, use the LAST numeric column

    Args:
        df: DataFrame to search for target column

    Returns:
        Name of the target column

    Raises:
        ValueError: If no suitable target column found
    """
    # Predefined target column names (case-insensitive)
    target_candidates = [
        "loss",
        "total claim amount",
        "total_claim_amount",
        "claim_amount",
        "amount",
        "charges",
        "cost"
    ]

    # Create case-insensitive column mapping
    col_lower_map = {col.lower(): col for col in df.columns}

    # Check each candidate
    for candidate in target_candidates:
        if candidate.lower() in col_lower_map:
            target_col = col_lower_map[candidate.lower()]
            print(f"✓ Target column identified: '{target_col}'")
            return target_col

    # Fallback: use last numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        raise ValueError(
            "No numeric columns found in dataset. "
            "Cannot identify a suitable target column."
        )

    target_col = numeric_cols[-1]
    print(f"⚠ No predefined target found. Using last numeric column: '{target_col}'")

    return target_col


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce numeric-looking object columns to numeric types.

    This strips currency symbols and commas before attempting conversion.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with numeric columns coerced
    """
    df = df.copy()

    # Get object columns
    object_cols = df.select_dtypes(include=['object']).columns

    coerced_count = 0
    for col in object_cols:
        # Try to clean and convert to numeric
        cleaned = df[col].astype(str).replace({",": "", r"\$": ""}, regex=True)
        numeric_attempt = pd.to_numeric(cleaned, errors='coerce')

        # If most values successfully converted, replace the column
        non_null_original = df[col].notna().sum()
        non_null_converted = numeric_attempt.notna().sum()

        # If we didn't lose too many values (>80% retained), use numeric version
        if non_null_original > 0 and (non_null_converted / non_null_original) > 0.8:
            df[col] = pd.to_numeric(cleaned, errors='ignore')
            if pd.api.types.is_numeric_dtype(df[col]):
                coerced_count += 1

    if coerced_count > 0:
        print(f"✓ Coerced {coerced_count} object column(s) to numeric")

    return df


def clean_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Clean features by removing high-missing and constant columns.

    Steps:
    1. Remove columns with >95% missing values
    2. Remove constant/near-constant columns (<=1 unique non-null value)

    Args:
        df: Input DataFrame (without target)

    Returns:
        Tuple of (cleaned DataFrame, cleaning stats dict)
    """
    initial_cols = len(df.columns)
    cleaning_stats = {
        'high_missing_removed': 0,
        'constant_removed': 0
    }

    # Remove columns with >95% missing
    missing_pct = df.isnull().sum() / len(df)
    high_missing_cols = missing_pct[missing_pct > 0.95].index.tolist()

    if high_missing_cols:
        df = df.drop(columns=high_missing_cols)
        cleaning_stats['high_missing_removed'] = len(high_missing_cols)
        print(f"⚠ Removed {len(high_missing_cols)} column(s) with >95% missing values")

    # Remove constant/near-constant columns
    constant_cols = []
    for col in df.columns:
        n_unique = df[col].nunique(dropna=True)
        if n_unique <= 1:
            constant_cols.append(col)

    if constant_cols:
        df = df.drop(columns=constant_cols)
        cleaning_stats['constant_removed'] = len(constant_cols)
        print(f"⚠ Removed {len(constant_cols)} constant/near-constant column(s)")

    final_cols = len(df.columns)
    total_removed = initial_cols - final_cols

    if total_removed > 0:
        print(f"✓ Feature cleaning: {initial_cols} → {final_cols} columns ({total_removed} removed)")
    else:
        print(f"✓ No columns removed during cleaning ({final_cols} columns retained)")

    return df, cleaning_stats


def prepare_data(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, pd.Series, dict]:
    """
    Prepare data with robust missing value handling.

    Strategy:
    1. Drop only rows where TARGET is missing
    2. Clean and coerce numeric columns
    3. Remove high-missing (>95%) and constant columns
    4. Keep feature missingness for imputation in pipeline

    Args:
        df: Input DataFrame
        target_col: Name of target column

    Returns:
        Tuple of (features DataFrame, target Series, prep stats dict)
    """
    initial_rows = len(df)

    print_data_quality_report(df, "DATA QUALITY REPORT (Raw Data)")

    # Step 1: Drop rows where target is missing
    df_clean = df.dropna(subset=[target_col])

    rows_dropped = initial_rows - len(df_clean)
    if rows_dropped > 0:
        print(f"⚠ Dropped {rows_dropped} rows with missing target ({rows_dropped/initial_rows*100:.1f}%)")

    print(f"✓ Rows after dropping missing target: {len(df_clean)}")

    # Safety check: ensure we have enough data
    if len(df_clean) < 50:
        raise ValueError(
            f"Insufficient data after cleaning: only {len(df_clean)} rows remain.\n"
            f"Original rows: {initial_rows}, dropped: {rows_dropped}\n"
            f"Suggestions:\n"
            f"  1. Verify CSV file has enough valid data\n"
            f"  2. Check if NA tokens are correctly specified\n"
            f"  3. Verify target column '{target_col}' is correct\n"
            f"  4. Inspect data/raw/ for data quality issues"
        )

    # Step 2: Separate features and target
    y = df_clean[target_col]
    X = df_clean.drop(columns=[target_col])

    # Step 3: Coerce numeric-looking columns
    X = coerce_numeric_columns(X)

    # Step 4: Clean features (remove high-missing and constant columns)
    X, cleaning_stats = clean_features(X)

    prep_stats = {
        'initial_rows': initial_rows,
        'final_rows': len(X),
        'rows_dropped': rows_dropped,
        'initial_features': len(df.columns) - 1,
        'final_features': len(X.columns),
        **cleaning_stats
    }

    return X, y, prep_stats


def create_preprocessing_pipeline(X: pd.DataFrame) -> ColumnTransformer:
    """
    Create preprocessing pipeline with imputation for features.

    Pipeline:
    - Numeric columns: SimpleImputer(strategy='median')
    - Categorical columns: SimpleImputer(strategy='most_frequent') -> OneHotEncoder

    Args:
        X: Features DataFrame

    Returns:
        ColumnTransformer for preprocessing
    """
    # Identify categorical and numeric columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    print(f"✓ Feature types: {len(categorical_cols)} categorical, {len(numeric_cols)} numeric")

    # Create transformers list
    transformers = []

    if numeric_cols:
        transformers.append((
            'num',
            SimpleImputer(strategy='median'),
            numeric_cols
        ))

    if categorical_cols:
        transformers.append((
            'cat',
            Pipeline([
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ]),
            categorical_cols
        ))

    if not transformers:
        raise ValueError("No valid feature columns found for preprocessing")

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder='drop'
    )

    return preprocessor


def train_baseline_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> Tuple[Pipeline, dict]:
    """
    Train baseline model and evaluate on validation set.

    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target

    Returns:
        Tuple of (trained pipeline, metrics dict)
    """
    print("\n" + "="*50)
    print("TRAINING BASELINE MODEL")
    print("="*50)

    # Create preprocessing pipeline
    preprocessor = create_preprocessing_pipeline(X_train)

    # Create full pipeline with model
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', HistGradientBoostingRegressor(random_state=42))
    ])

    # Train the model
    print("\n⏳ Training HistGradientBoostingRegressor...")
    pipeline.fit(X_train, y_train)
    print("✓ Training complete")

    # Make predictions on validation set
    y_pred = pipeline.predict(X_val)

    # Calculate metrics
    mae = mean_absolute_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred)

    metrics = {
        'mae': float(mae),
        'r2': float(r2)
    }

    print("\n" + "="*50)
    print("VALIDATION METRICS")
    print("="*50)
    print(f"MAE (Mean Absolute Error): ${mae:,.2f}")
    print(f"R² (R-squared):            {r2:.4f}")
    print("="*50 + "\n")

    return pipeline, metrics


def save_artifacts(
    pipeline: Pipeline,
    metrics: dict,
    dataset_name: str,
    target_col: str
) -> None:
    """
    Save model artifacts and metadata to ml/artifacts/.

    Args:
        pipeline: Trained pipeline
        metrics: Dictionary of evaluation metrics
        dataset_name: Name of the dataset file used
        target_col: Name of target column
    """
    artifacts_dir = Path("ml/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = artifacts_dir / "model.pkl"
    joblib.dump(pipeline, model_path)
    print(f"✓ Model saved to: {model_path}")

    # Save metadata
    meta = {
        "dataset": dataset_name,
        "target": target_col,
        "mae": metrics['mae'],
        "r2": metrics['r2']
    }

    meta_path = artifacts_dir / "meta.json"
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"✓ Metadata saved to: {meta_path}")


def log_to_mlflow(
    pipeline: Pipeline,
    metrics: dict,
    target_col: str
) -> None:
    """
    Log model, parameters, and metrics to MLflow.

    Args:
        pipeline: Trained pipeline
        metrics: Dictionary of evaluation metrics
        target_col: Name of target column
    """
    # Set tracking URI and experiment
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("baseline")

    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("target", target_col)

        # Log metrics
        mlflow.log_metric("mae", metrics['mae'])
        mlflow.log_metric("r2", metrics['r2'])

        # Log model
        mlflow.sklearn.log_model(pipeline, "model")

        print("✓ Logged to MLflow (experiment: 'baseline')")


def main():
    """Main training pipeline."""
    print("\n" + "="*50)
    print("REPAIR HELPER - BASELINE MODEL TRAINING")
    print("="*50 + "\n")

    try:
        # 1. Find and load dataset
        print("Step 1: Loading dataset...")
        dataset_path, dataset_name = find_dataset()
        df = load_dataset_with_na_handling(dataset_path)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns\n")

        # 2. Identify target column
        print("Step 2: Identifying target column...")
        target_col = identify_target_column(df)
        print()

        # 3. Prepare data with robust missing value handling
        print("Step 3: Preparing data...")
        X, y, prep_stats = prepare_data(df, target_col)
        print()

        # 4. Split into train/validation
        print("Step 4: Splitting data (80/20 train/val)...")
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42
        )
        print(f"✓ Train set: {len(X_train)} samples")
        print(f"✓ Val set:   {len(X_val)} samples\n")

        # 5. Train model
        pipeline, metrics = train_baseline_model(X_train, y_train, X_val, y_val)

        # 6. Save artifacts
        print("Step 5: Saving artifacts...")
        save_artifacts(pipeline, metrics, dataset_name, target_col)
        print()

        # 7. Log to MLflow
        print("Step 6: Logging to MLflow...")
        log_to_mlflow(pipeline, metrics, target_col)
        print()

        print("="*50)
        print("✓ BASELINE MODEL TRAINING COMPLETE")
        print("="*50 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
