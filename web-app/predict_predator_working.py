#!/usr/bin/env python3
"""
Threat Detection using TensorFlow Lite Model  
Detects threats including: cormorant, egret, heron, tortoise, snake, human intruder
"""

import sys
import json
import os
import warnings
import numpy as np
from PIL import Image
import io
import contextlib

warnings.filterwarnings('ignore')

# Class names mapping - your 6 threat classes
CLASS_NAMES = {
    0: 'cormorant',
    1: 'egret',
    2: 'heron',
    3: 'snake',
    4: 'tortoise',
    5: 'human intruder',
}

def get_interpreter(model_path):
    """Load TensorFlow Lite interpreter"""
    try:
        import tensorflow as tf
        return tf.lite.Interpreter(model_path=model_path)
    except:
        try:
            from tflite_runtime.interpreter import Interpreter
            return Interpreter(model_path=model_path)
        except Exception as e:
            raise Exception(f"Failed to load TFLite model: {e}")

def load_and_prepare_image(image_path, target_size=(640, 640)):
    """Load and prepare image for inference"""
    img = Image.open(image_path).convert('RGB')
    img = img.resize(target_size, Image.BILINEAR)
    img_array = np.array(img, dtype=np.float32) / 255.0  # Normalize to 0-1
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def run_inference(model_path, image_path):
    """Run inference and return detections"""
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            interpreter = get_interpreter(model_path)
            interpreter.allocate_tensors()
            
            # Get input and output details
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Prepare image
            input_shape = input_details[0]['shape']
            target_size = (int(input_shape[2]), int(input_shape[1])) if len(input_shape) == 4 else (640, 640)
            image_data = load_and_prepare_image(image_path, target_size)
            
            # Run inference
            interpreter.set_tensor(input_details[0]['index'], image_data)
            interpreter.invoke()
            
            # Get output
            output_data = interpreter.get_tensor(output_details[0]['index'])
            
        return output_data
        
    except Exception as e:
        raise Exception(f"Inference failed: {e}")

def parse_detections(output, confidence_threshold=0.25):
    """
    Parse TFLite YOLO output to extract detections.
    Handles multiple output formats.
    """
    detections = []
    num_classes = len(CLASS_NAMES)
    
    try:
        # Handle shape (1, 9, 8400) - Standard YOLO format
        if output.ndim == 3 and output.shape[1] >= 5:
            # Remove batch dimension
            output = output[0]
            
            # Extract class scores (skip first 4 which are bbox)
            class_scores = output[4:, :]
            
            # Objectness = maximum class score for each anchor
            if class_scores.shape[0] > 0:
                objectness = np.max(class_scores, axis=0)
                
                # Find detections where objectness > threshold
                high_conf_mask = objectness > confidence_threshold
                high_conf_indices = np.where(high_conf_mask)[0]
                
                # Extract detections
                for idx in high_conf_indices:
                    class_probs = class_scores[:, idx]
                    class_id = int(np.argmax(class_probs))
                    confidence = float(objectness[idx])
                    
                    detections.append({
                        'class_id': class_id,
                        'confidence': confidence
                    })
        
        # Handle 2D format: (num_detections, features)
        elif output.ndim == 2 and output.shape[0] > 0:
            if output.shape[1] >= 5:
                for detection in output:
                    # Try format: [x, y, w, h, conf, ...class_scores]
                    conf = float(detection[4])
                    if conf >= confidence_threshold:
                        # Extract class info
                        if len(detection) > 5:
                            class_id = int(detection[5])
                        else:
                            class_id = 0
                        detections.append({'class_id': class_id, 'confidence': conf})
        
        # Handle 1D format - single detection
        elif output.ndim == 1 and len(output) >= 5:
            conf = float(output[4])
            if conf >= confidence_threshold:
                class_id = int(output[5]) if len(output) > 5 else 0
                detections.append({'class_id': class_id, 'confidence': conf})
    
    except Exception as e:
        sys.stderr.write(f"ERROR in parse_detections: {str(e)}\n")
    
    return detections

def main():
    try:
        # Validate input
        if len(sys.argv) < 2:
            result = {'predator': 'Error', 'confidence': 0.0}
            print(json.dumps(result))
            return
        
        image_path = sys.argv[1]
        
        # Check image exists
        if not os.path.exists(image_path):
            result = {'predator': 'Error', 'confidence': 0.0}
            print(json.dumps(result))
            return
        
        # Validate image
        try:
            with Image.open(image_path) as img:
                img.verify()
        except:
            result = {'predator': 'Error', 'confidence': 0.0}
            print(json.dumps(result))
            return
        
        # Find model
        model_path = os.path.join(os.path.dirname(__file__), 'third_yolo.tflite')
        
        if not os.path.exists(model_path):
            result = {'predator': 'Error', 'confidence': 0.0}
            print(json.dumps(result))
            return
        
        # Run inference
        output = run_inference(model_path, image_path)
        
        # Parse detections
        detections = parse_detections(output, confidence_threshold=0.1)  # Lower threshold to catch more
        
        # Get top detection
        if not detections:
            # No detections above threshold - output the highest scoring class regardless
            try:
                if output.ndim == 3:
                    output_2d = output[0]
                elif output.ndim == 2:
                    output_2d = output
                else:
                    output_2d = output.reshape(-1)
                
                # Get class scores
                if output_2d.ndim > 1:
                    class_scores = output_2d[4:, :]
                    if class_scores.shape[0] > 0:
                        max_scores = np.max(class_scores, axis=0)
                        best_idx = np.argmax(max_scores)
                        class_id = int(np.argmax(class_scores[:, best_idx]))
                        confidence = float(max_scores[best_idx])
                    else:
                        class_id = 0
                        confidence = 0.0
                else:
                    class_scores = output_2d[4:]
                    class_id = int(np.argmax(class_scores))
                    confidence = float(np.max(class_scores))
                
                if confidence < 0.1:  # If even the best score is very low
                    result = {'predator': 'No Threat Detected', 'confidence': 0.0}
                else:
                    class_name = CLASS_NAMES.get(class_id, f"Unknown_{class_id}")
                    result = {'predator': class_name, 'confidence': round(float(confidence), 4)}
            except Exception as e:
                result = {'predator': 'No Threat Detected', 'confidence': 0.0}
        else:
            top = max(detections, key=lambda x: x['confidence'])
            class_id = top['class_id']
            confidence = float(top['confidence'])
            
            # Get class name - your 6 classes or generic class
            if class_id in CLASS_NAMES:
                class_name = CLASS_NAMES[class_id]
            else:
                class_name = f"Unknown_{class_id}"
            
            result = {
                'predator': class_name,
                'confidence': round(confidence, 4)
            }
        
        print(json.dumps(result))
        
    except Exception as e:
        result = {'predator': 'Error', 'confidence': 0.0}
        print(json.dumps(result))

if __name__ == '__main__':
    main()