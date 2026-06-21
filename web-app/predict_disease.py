#!/usr/bin/env python3
import sys
import json
import os
import warnings
import numpy as np
from PIL import Image
import traceback

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
    except Exception as e:
        try:
            from tflite_runtime.interpreter import Interpreter
            return Interpreter(model_path=model_path)
        except Exception as tflite_err:
            raise Exception(f"TensorFlow: {str(e)}. TFLite Runtime: {str(tflite_err)}")

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
            output = {'disease': 'Error: Missing Image Path', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
        
        image_path = sys.argv[1]
        
        # Check if image file exists
        if not os.path.exists(image_path):
            output = {'disease': 'Error: Image file not found', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
        
        model_filename = 'FINAL_3class_fish_model_float32.tflite'
        model_path = os.path.join(os.path.dirname(__file__), model_filename)
        
        # Check if model file exists
        if not os.path.exists(model_path):
            output = {'disease': f'Error: Model file {model_filename} not found', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
            
        # Initialize TFLite Interpreter
        try:
            interpreter = get_interpreter(model_path)
            interpreter.allocate_tensors()
        except Exception as e:
            output = {'disease': f'Error: Failed to load model - {str(e)[:100]}', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
        
        try:
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
        except Exception as e:
            output = {'disease': f'Error: Failed to get model details - {str(e)[:100]}', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
        
        # Run Preprocessing and Inference
        try:
            input_data = preprocess_image(image_path, target_size=(640, 640))
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]['index'])
        except Exception as e:
            output = {'disease': f'Error: Failed during inference - {str(e)[:100]}', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)
        
        # Parse YOLO output
        predicted_class = "Unknown"
        confidence = 0.0
        
        try:
            if output_data.ndim == 3:
                output_data = output_data[0]  # Remove batch shell
                class_scores = output_data[4:, :]
                
                max_scores = np.max(class_scores, axis=0)
                best_anchor_idx = np.argmax(max_scores)
                confidence = float(max_scores[best_anchor_idx])
                class_id = int(np.argmax(class_scores[:, best_anchor_idx]))
                predicted_class = CLASS_NAMES.get(class_id, f"Unknown_{class_id}")
                
            elif output_data.ndim == 2:
                class_scores = output_data[4:, :]
                max_scores = np.max(class_scores, axis=0)
                best_anchor_idx = np.argmax(max_scores)
                confidence = float(max_scores[best_anchor_idx])
                class_id = int(np.argmax(class_scores[:, best_anchor_idx]))
                predicted_class = CLASS_NAMES.get(class_id, f"Unknown_{class_id}")
                
            else:
                # Fallback: try to flatten and process
                flat_output = output_data.flatten()
                num_classes = len(CLASS_NAMES)
                if len(flat_output) >= num_classes:
                    class_scores = flat_output[-num_classes:]
                    class_id = int(np.argmax(class_scores))
                    confidence = float(np.max(class_scores))
                    predicted_class = CLASS_NAMES.get(class_id, f"Unknown_{class_id}")
        
        except Exception as e:
            sys.stderr.write(f"ERROR parsing output: {str(e)}\n")
            output = {'disease': 'Error: Failed to parse model output', 'confidence': 0.0}
            print(json.dumps(output))
            sys.exit(0)

        # Normalize confidence to 0-1 range
        confidence = float(round(max(0, min(1, confidence)), 4))
        
        # Return result
        output = {
            'disease': predicted_class,
            'confidence': confidence
        }
        print(json.dumps(output))
        sys.exit(0)
        
    except Exception as e:
        # Final catch-all error handler
        error_msg = str(e)[:150]
        output = {
            'disease': 'Error: Unexpected failure',
            'confidence': 0.0
        }
        print(json.dumps(output))
        sys.stderr.write(f"FATAL ERROR: {error_msg}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()