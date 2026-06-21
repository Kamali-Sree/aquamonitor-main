import os
import sys

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model

    model_path = os.path.join(os.path.dirname(__file__), 'water_qual_universal.keras')
    print("Loading model without legacy keras...")
    model = load_model(model_path)
    print("Model loaded successfully!")
    sys.exit(0)
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
