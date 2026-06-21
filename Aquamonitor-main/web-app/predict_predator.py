import sys
import json
import os
import warnings
import shutil
import tempfile

warnings.filterwarnings('ignore')

try:
    from ultralytics import YOLO

    if len(sys.argv) < 2:
        raise Exception("Image path not provided")

    img_path = sys.argv[1]

    if not os.path.exists(img_path):
        raise Exception("Image file not found")

    # Try multiple model paths
    model_candidates = [
        os.path.join(os.path.dirname(__file__), 'model.pt'),
        os.path.join(os.path.dirname(__file__), 'best.pt', 'third_yolo.pt'),
    ]

    model_path = None
    for candidate in model_candidates:
        if os.path.exists(candidate):
            model_path = candidate
            break

    if not model_path:
        raise Exception(f"Model not found at any of: {model_candidates}")

    print(f"Using model path: {model_path}", file=sys.stderr)

    # If there's a permission issue, try copying to temp
    try:
        model = YOLO(model_path)
    except PermissionError:
        print(f"Permission denied on {model_path}, trying temp copy...", file=sys.stderr)
        temp_dir = tempfile.gettempdir()
        temp_model = os.path.join(temp_dir, 'yolo_model_temp.pt')
        shutil.copy2(model_path, temp_model)
        model = YOLO(temp_model)

    # Run inference
    results = model(img_path, conf=0.5)

    # Parse results
    detections = []
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = result.names[cls]
            detections.append({
                'class': class_name,
                'confidence': conf
            })

    if not detections:
        predator = 'No Predator Detected'
        confidence = 0.0
    else:
        # Sort by confidence and take the highest
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        predator = detections[0]['class']
        confidence = detections[0]['confidence']

    result = {
        'predator': predator,
        'confidence': confidence
    }

    print(json.dumps(result))

except Exception as e:
    error_msg = str(e)
    print(error_msg, file=sys.stderr)
    error_result = {
        'error': error_msg
    }
    print(json.dumps(error_result))