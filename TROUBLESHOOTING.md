# Quick Troubleshooting Checklist

## ✅ Verification Steps

### 1. Check Model Files
```powershell
# From web-app directory
ls FINAL_3class_fish_model_float32.tflite
ls third_yolo.tflite
```
Expected: Both files should exist and be > 10 MB

### 2. Check Python Dependencies
```powershell
pip list | findstr tensorflow
pip list | findstr pillow
pip list | findstr numpy
```
Expected: All three should be installed

### 3. Start Server in Debug Mode
```powershell
cd web-app
$env:DEBUG = "aquamonitor:*"
npm start
```

### 4. Test API Endpoints
```powershell
# Test if models are found
curl http://localhost:3000/api/test-disease
curl http://localhost:3000/api/test-predator

# Should return:
# {
#   "success": true,
#   "model_exists": true,
#   "model_size_mb": "XX.XX"
# }
```

---

## 🔧 Common Issues & Solutions

### Issue: "Model file not found"
**Solution:**
1. Verify files exist: `ls -la *.tflite`
2. Check paths in Python scripts match actual filenames
3. Ensure file permissions allow read access
4. Restart server after adding models

### Issue: "Failed to parse prediction result"
**Solution:**
1. Run Python script directly:
   ```powershell
   python predict_disease.py test_image.jpg
   ```
2. Look for error messages in output
3. Check if output is valid JSON

### Issue: "Python process failed with code: 1"
**Solution:**
1. Check server console for stderr output
2. Verify all imports work:
   ```powershell
   python -c "import tensorflow; import numpy; import PIL"
   ```
3. Check if TensorFlow/TFLite Interpreter is properly installed:
   ```powershell
   python -c "from tflite_runtime.interpreter import Interpreter"
   # Or
   python -c "import tensorflow as tf; tf.lite.Interpreter"
   ```

### Issue: Returns "Healthy" for obvious disease
**Solution:**
- This should be fixed with the new code
- If still happening, check if model was properly retrained
- Verify input image preprocessing (640x640 resize)

### Issue: Predator detection says "No Threat Detected" for clear predator
**Solution:**
1. Verify model training was correct
2. Check if model output shape is different from expected (see debug logs)
3. Confidence threshold might be too high - check new threshold = 0.1

---

## 📊 How to Debug Model Output

Create a debug script `test_model.py`:
```python
#!/usr/bin/env python3
import os
import sys
import numpy as np
from PIL import Image

# Load TFLite model
try:
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path='FINAL_3class_fish_model_float32.tflite')
except:
    from tflite_runtime.interpreter import Interpreter
    interpreter = Interpreter(model_path='FINAL_3class_fish_model_float32.tflite')

interpreter.allocate_tensors()

# Get input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Input Details:")
print(f"  Shape: {input_details[0]['shape']}")
print(f"  Type: {input_details[0]['dtype']}")

print("\nOutput Details:")
print(f"  Shape: {output_details[0]['shape']}")
print(f"  Type: {output_details[0]['dtype']}")

# Test with sample image
if len(sys.argv) > 1:
    img = Image.open(sys.argv[1]).convert('RGB')
    img = img.resize((640, 640))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    
    output = interpreter.get_tensor(output_details[0]['index'])
    print(f"\nOutput Array Shape: {output.shape}")
    print(f"Output Array dtype: {output.dtype}")
    print(f"Min value: {np.min(output)}")
    print(f"Max value: {np.max(output)}")
    print(f"First few values: {output.flatten()[:20]}")
```

Run it:
```powershell
python test_model.py test_image.jpg
```

---

## 📝 Expected Server Output

### Successful Disease Detection
```
🐟 Fish disease detection request received
 Processing file for disease check: upload_abc123
 Python Disease process completed with code: 0
 Final response: { disease: 'Fungal_Parasitic_Diseases', confidence: 0.8765 }
```

### Successful Predator Detection
```
 Predator detection request received
 Processing uploaded file: predator.jpg
 File path: uploads/abc123def
 Python process completed with code: 0
 Parsed prediction: { predator: 'cormorant', confidence: 0.9234 }
 Final response: { predator: 'cormorant', confidence: '92.34%' }
```

---

## 🚀 After Verifying Everything Works

1. Run both detection APIs through web UI
2. Try different image types and sizes
3. Check browser console for any JavaScript errors
4. Monitor server logs for any warnings
5. Test with edge cases (very dark/bright images, unusual formats)

---

## 📞 If All Else Fails

1. **Completely restart server:**
   ```powershell
   # Kill any running Node/Python processes
   Get-Process node, python | Stop-Process -Force
   
   # Clear uploads folder
   Remove-Item uploads/* -Force
   
   # Restart
   npm start
   ```

2. **Clear Node cache:**
   ```powershell
   Remove-Item node_modules -Recurse -Force
   npm install
   npm start
   ```

3. **Reinstall Python dependencies:**
   ```powershell
   pip uninstall tensorflow -y
   pip install tensorflow
   ```

4. **Test Python scripts independently:**
   ```powershell
   python predict_disease.py sample.jpg
   python predict_predator_working.py sample.jpg
   ```
   - Both should output valid JSON
   - Check server console for Python stderr output
