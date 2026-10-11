import os
import logging
from typing import Dict, Any, Union
import pandas as pd
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ML_Inference')

class InvestorSegmenter:
    """
    Handles the K-Means inference pipeline for investor segmentation.
    Ensures that input features match the training pipeline exactly to prevent shape/feature mismatches.
    """
    
    EXPECTED_FEATURES = ['total_invested', 'txn_count', 'annual_income']

    def __init__(self, models_dir: str = '../models'):
        """
        Initializes the segmenter by loading the pre-trained scaler and KMeans models.
        
        Args:
            models_dir (str): Relative or absolute path to the directory containing .pkl models.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_path = os.path.join(base_dir, models_dir)
        
        try:
            self.scaler = joblib.load(os.path.join(self.models_path, 'investor_scaler.pkl'))
            self.kmeans = joblib.load(os.path.join(self.models_path, 'investor_kmeans_model.pkl'))
            logger.info("Successfully loaded ML models (Scaler & KMeans).")
        except FileNotFoundError as e:
            logger.error(f"Could not find model files in {self.models_path}. Ensure the notebook has been run.", exc_info=True)
            raise e

    def predict_cluster(self, investor_data: Union[Dict[str, float], pd.DataFrame]) -> int:
        """
        Predicts the investor segment (cluster) for new, unseen data.
        
        Args:
            investor_data (Union[Dict[str, float], pd.DataFrame]): A dictionary or single-row DataFrame 
                containing 'total_invested', 'txn_count', and 'annual_income'.
                
        Returns:
            int: The predicted cluster ID (0, 1, or 2).
            
        Raises:
            ValueError: If the required features are missing from the input data.
        """
        # Convert dictionary to DataFrame to ensure feature names match training exactly
        if isinstance(investor_data, dict):
            df_input = pd.DataFrame([investor_data])
        else:
            df_input = investor_data.copy()

        # Validate feature presence
        missing_features = [f for f in self.EXPECTED_FEATURES if f not in df_input.columns]
        if missing_features:
            raise ValueError(f"Missing required features for inference: {missing_features}")

        # Ensure correct column order to prevent scaling shape mismatches
        df_input = df_input[self.EXPECTED_FEATURES]

        try:
            # Scale features using the loaded StandardScaler
            X_scaled = self.scaler.transform(df_input)
            
            # Predict the cluster
            cluster = self.kmeans.predict(X_scaled)[0]
            logger.info(f"Successfully predicted cluster {cluster} for input data.")
            return int(cluster)
        except Exception as e:
            logger.error(f"Inference failed during scaling or prediction: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    # Test the inference pipeline with mock unseen data
    logger.info("Running ML Pipeline Verification...")
    try:
        segmenter = InvestorSegmenter()
        
        mock_investor = {
            'total_invested': 500000.0,
            'txn_count': 12,
            'annual_income': 25.5
        }
        
        cluster_id = segmenter.predict_cluster(mock_investor)
        print(f"\\n[SUCCESS] Mock Investor was assigned to Cluster: {cluster_id}")
    except Exception as e:
        print(f"\\n[ERROR] Pipeline verification failed: {e}")
