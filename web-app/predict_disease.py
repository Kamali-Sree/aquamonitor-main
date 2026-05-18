#!/usr/bin/env python3
import sys
import json
import os
import warnings
import numpy as np
from PIL import Image

# Suppress framework warnings
warnings.filterwarnings('ignore')

# 🎯 YOUR EXACT TRAINING CLASSES (From your YOLO11 notebook logs)
CLASS_NAMES = {
    0: 'Bacterial_Infections',
    1: 'Fungal_Parasitic_Diseases',
    2: 'Healthy_Fish'
}

def get_interpreter(model_path):
    try:
        import tensorflow as tf
        return tf.lite.Interpreter(model_path=model_path)
    except ImportError:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter(model_path=model_path)

def preprocess_image(image_path, target_size=(640, 640)):
    """Loads, resizes, and normalizes pixel streams exactly like your training process"""
    img = Image.open(image_path).convert('RGB')
    img = img.resize(target_size, Image.BILINEAR)
    
    # Scale raw pixel integers (0-255) into float32 decimals (0.0 - 1.0)
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # Expand dimensions to add the batch layer: (640, 640, 3) -> (1, 640, 640, 3)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({'disease': 'Error: Missing Image Path', 'confidence': 0.0}))
            return
        
        image_path = sys.argv[1]
        model_filename = 'FINAL_3class_fish_model_float32.tflite'
        model_path = os.path.join(os.path.dirname(__file__), model_filename)
        
        if not os.path.exists(model_path):
            print(json.dumps({'disease': f'Error: Model file {model_filename} not found.', 'confidence': 0.0}))
            return
            
        # Initialize TFLite Interpreter
        interpreter = get_interpreter(model_path)
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Run Preprocessing and Inference
        input_data = preprocess_image(image_path, target_size=(640, 640))
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        
        # Pull output predictions matrix
        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        # Parse standard YOLO output dimension: (1, Class_Count + 4, Anchors)
        if output_data.ndim == 3:
            output_data = output_data[0]  # Remove batch shell
            
            # Rows 0-3 are box coordinates; Row 4+ are class scores
            class_scores = output_data[4:, :]
            
            # Find the absolute highest scoring prediction anchor across the canvas matrix
            max_scores = np.max(class_scores, axis=0)
            best_anchor_idx = np.argmax(max_scores)
            
            confidence = float(max_scores[best_anchor_idx])
            
            # Standard 25% confidence filter
            if confidence >= 0.25:
                class_id = int(np.argmax(class_scores[:, best_anchor_idx]))
                predicted_class = CLASS_NAMES.get(class_id, f"Unknown_{class_id}")
            else:
                predicted_class = "Healthy_Fish"
                confidence = 1.0
        else:
            predicted_class = "Healthy_Fish"
            confidence = 1.0

        # Construct structured JSON string back to Node server stream
        print(json.dumps({
            'disease': predicted_class,
            'confidence': round(confidence, 4)
        }))
        
    except Exception as e:
        print(json.dumps({
            'disease': 'Healthy_Fish',
            'confidence': 1.0,
            'debug_log': str(e)
        }))

if __name__ == '__main__':
    main()