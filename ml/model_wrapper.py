"""
Model Wrapper for Improved Model with Feature Engineering

This wrapper handles all feature engineering automatically so users can
pass in raw claim data and get predictions.
"""

import joblib
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class ImprovedModelWrapper:
    """
    Wrapper for the improved model that handles feature engineering
    """

    def __init__(self, model_path: str = "ml/artifacts/model_improved.pkl"):
        """Load model and business rules"""

        self.model_path = Path(model_path)
        self.artifacts_dir = self.model_path.parent

        # Load model
        self.pipeline = joblib.load(self.model_path)

        # Load metadata
        meta_path = self.artifacts_dir / "model_improved_metadata.json"
        with open(meta_path, 'r') as f:
            self.metadata = json.load(f)

        # Load business rules
        rules_path = self.artifacts_dir / "business_rules.json"
        with open(rules_path, 'r') as f:
            self.business_rules = json.load(f)

        print(f"✓ Loaded improved model (MAE: ${self.metadata['mae']:,.2f})")

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply same feature engineering as training

        This must match exactly what was done in baseline_improved.py
        """

        df = df.copy()

        # 1. Vehicle age
        if 'auto_year' in df.columns and 'incident_date' in df.columns:
            try:
                df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')
                df['incident_year'] = df['incident_date'].dt.year
                df['vehicle_age'] = df['incident_year'] - df['auto_year']
                df['vehicle_age'] = df['vehicle_age'].clip(0, 50)
            except:
                df['vehicle_age'] = np.nan
                df['incident_year'] = np.nan

        # 2. Days to claim
        if 'policy_bind_date' in df.columns and 'incident_date' in df.columns:
            try:
                df['policy_bind_date'] = pd.to_datetime(df['policy_bind_date'], errors='coerce')
                df['days_to_claim'] = (df['incident_date'] - df['policy_bind_date']).dt.days
                df['days_to_claim'] = df['days_to_claim'].clip(0, 3650)
            except:
                df['days_to_claim'] = np.nan

        # 3-4. Financial ratios (will be NaN during prediction, but need columns)
        df['claim_to_premium_ratio'] = np.nan
        df['deductible_ratio'] = df.get('policy_deductable', 0) / (df.get('policy_annual_premium', 1) + 1)

        # 5. Is luxury brand
        luxury_brands = ['Mercedes', 'BMW', 'Audi', 'Lexus', 'Porsche', 'Jaguar',
                        'Land Rover', 'Tesla', 'Maserati', 'Alfa Romeo', 'Infiniti', 'Acura']
        if 'auto_make' in df.columns:
            df['is_luxury_brand'] = df['auto_make'].isin(luxury_brands).astype(int)
        else:
            df['is_luxury_brand'] = 0

        # 6. Is high-theft model
        high_theft = [
            ('Honda', 'Civic'), ('Honda', 'Accord'), ('Toyota', 'Camry'),
            ('Nissan', 'Altima'), ('Toyota', 'Corolla'), ('Ford', 'F-150'),
            ('Chevrolet', 'Silverado'), ('GMC', 'Sierra')
        ]
        if 'auto_make' in df.columns and 'auto_model' in df.columns:
            df['is_high_theft_model'] = df.apply(
                lambda row: (row.get('auto_make'), row.get('auto_model')) in high_theft,
                axis=1
            ).astype(int)
        else:
            df['is_high_theft_model'] = 0

        # 7. Has bodily injury
        if 'bodily_injuries' in df.columns:
            df['has_bodily_injury'] = (df['bodily_injuries'] > 0).astype(int)
        else:
            df['has_bodily_injury'] = 0

        # 8. Has property damage
        if 'property_damage' in df.columns:
            df['has_property_damage'] = (df['property_damage'] == 'YES').astype(int)
        else:
            df['has_property_damage'] = 0

        # 9. Police and witnesses
        if 'police_report_available' in df.columns and 'witnesses' in df.columns:
            df['police_and_witnesses'] = (
                (df['police_report_available'] == 'YES') &
                (df['witnesses'] > 0)
            ).astype(int)
        else:
            df['police_and_witnesses'] = 0

        # 10. Time of day
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

        if 'incident_hour_of_the_day' in df.columns:
            df['time_of_day'] = df['incident_hour_of_the_day'].apply(categorize_hour)
        else:
            df['time_of_day'] = 'Unknown'

        # 11. Customer tenure category
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

        if 'months_as_customer' in df.columns:
            df['customer_tenure_category'] = df['months_as_customer'].apply(categorize_tenure)
        else:
            df['customer_tenure_category'] = 'Unknown'

        return df

    def add_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add any columns the model expects that are missing

        For prediction, some columns (like injury_claim, vehicle_claim) won't be known.
        We add them as NaN so the model can still work.
        """

        # Get all expected columns from metadata
        expected_cols = [
            'months_as_customer', 'age', 'policy_number', 'policy_bind_date',
            'policy_state', 'policy_csl', 'policy_deductable', 'policy_annual_premium',
            'umbrella_limit', 'insured_zip', 'insured_sex', 'insured_education_level',
            'insured_occupation', 'insured_hobbies', 'insured_relationship',
            'capital-gains', 'capital-loss', 'incident_date', 'incident_type',
            'collision_type', 'incident_severity', 'authorities_contacted',
            'incident_state', 'incident_city', 'incident_location',
            'incident_hour_of_the_day', 'number_of_vehicles_involved',
            'property_damage', 'bodily_injuries', 'witnesses',
            'police_report_available', 'injury_claim', 'property_claim',
            'vehicle_claim', 'auto_make', 'auto_model', 'auto_year',
            'fraud_reported', '_c39',
            # Engineered features
            'vehicle_age', 'incident_year', 'days_to_claim',
            'claim_to_premium_ratio', 'deductible_ratio',
            'is_luxury_brand', 'is_high_theft_model',
            'has_bodily_injury', 'has_property_damage',
            'police_and_witnesses', 'time_of_day',
            'customer_tenure_category'
        ]

        for col in expected_cols:
            if col not in df.columns:
                df[col] = np.nan

        return df

    def predict(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction from raw claim data

        Args:
            claim_data: Dictionary with claim features

        Returns:
            Dictionary with prediction and metadata
        """

        # Convert to DataFrame
        df = pd.DataFrame([claim_data])

        # Engineer features
        df = self.engineer_features(df)

        # Add missing columns
        df = self.add_missing_columns(df)

        # Make prediction
        prediction = float(self.pipeline.predict(df)[0])

        # Build result
        result = {
            "predicted_cost": prediction,
            "model_version": "improved",
            "mae": self.metadata['mae'],
            "r2": self.metadata['r2'],
            "mape": self.metadata['mape']
        }

        # Add business rule context
        severity = claim_data.get('incident_severity')
        if severity and severity in self.business_rules['severity_ratios']:
            result['severity_ratio'] = self.business_rules['severity_ratios'][severity]

        state = claim_data.get('incident_state') or claim_data.get('policy_state')
        if state and state in self.business_rules['regional_multipliers']:
            result['regional_multiplier'] = self.business_rules['regional_multipliers'][state]

        return result

    def batch_predict(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Make predictions for multiple claims"""
        return [self.predict(claim) for claim in claims]


# Convenience function
def predict_claim_cost(claim_data: Dict[str, Any], model_path: str = "ml/artifacts/model_improved.pkl") -> Dict[str, Any]:
    """
    Convenience function to make a single prediction

    Args:
        claim_data: Dictionary with claim features
        model_path: Path to model file

    Returns:
        Prediction dictionary
    """
    wrapper = ImprovedModelWrapper(model_path)
    return wrapper.predict(claim_data)
