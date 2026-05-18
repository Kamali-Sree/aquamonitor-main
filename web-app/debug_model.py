#!/usr/bin/env python3
"""
Debug script to inspect YOLO model output format
"""

import numpy as np
import tensorflow as tf
from PIL import Image

# Load model
model_path = 'FINAL_3class_fish_model_float16.tflite'
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Get input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("=" * 60)
print("MODEL INPUT DETAILS")
print("=" * 60)
for i, detail in enumerate(input_details):
    print(f"Input {i}:")
    print(f"  Name: {detail['name']}")
    print(f"  Shape: {detail['shape']}")
    print(f"  Type: {detail['dtype']}")

print("\n" + "=" * 60)
print("MODEL OUTPUT DETAILS")
print("=" * 60)
for i, detail in enumerate(output_details):
    print(f"Output {i}:")
    print(f"  Name: {detail['name']}")
    print(f"  Shape: {detail['shape']}")
    print(f"  Type: {detail['dtype']}")

# Create dummy input
input_shape = input_details[0]['shape']
print(f"\n" + "=" * 60)
print("TESTING WITH DUMMY INPUT")
print("=" * 60)

# Create random test image
test_input = np.random.rand(*input_shape).astype(np.float32)
print(f"Input shape: {test_input.shape}")
print(f"Input min/max: {test_input.min():.4f} / {test_input.max():.4f}")

# Run inference
interpreter.set_tensor(input_details[0]['index'], test_input)
interpreter.invoke()

# Get outputs
print(f"\nNumber of outputs: {len(output_details)}")
for i, detail in enumerate(output_details):
    output_data = interpreter.get_tensor(detail['index'])
    print(f"\nOutput {i} ({detail['name']}):")
    print(f"  Shape: {output_data.shape}")
    print(f"  Type: {output_data.dtype}")
    print(f"  Min/Max: {output_data.min():.6f} / {output_data.max():.6f}")
    print(f"  First 20 values: {output_data.flatten()[:20]}")
    
    # If it looks like class probabilities
    if len(output_data.shape) <= 2:
        print(f"  Argmax: {np.argmax(output_data)}")
        print(f"  Softmax probs: {np.exp(output_data[0]) / np.sum(np.exp(output_data[0])) if len(output_data.shape) == 2 else 'N/A'}")
