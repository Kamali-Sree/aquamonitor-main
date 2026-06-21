import os
import sys
import zipfile
import json
import shutil

model_path = os.path.join(os.path.dirname(__file__), 'water_qual_universal.keras')
backup_path = model_path + '.bak'

if not os.path.exists(backup_path):
    shutil.copy2(model_path, backup_path)

temp_dir = os.path.join(os.path.dirname(__file__), 'temp_keras')
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

print("Extracting model...")
with zipfile.ZipFile(model_path, 'r') as zip_ref:
    zip_ref.extractall(temp_dir)

config_path = os.path.join(temp_dir, 'config.json')
with open(config_path, 'r') as f:
    config_data = json.load(f)

print("Patching config...")
# The config is typically a dictionary with 'config' containing 'layers'
if 'config' in config_data and 'layers' in config_data['config']:
    layers = config_data['config']['layers']
    for layer in layers:
        if layer.get('class_name') == 'LSTM':
            layer_config = layer.get('config', {})
            if 'time_major' in layer_config:
                print(f"Removing time_major from {layer.get('name')}")
                del layer_config['time_major']
            if 'batch_input_shape' in layer_config:
                print(f"Removing batch_input_shape from {layer.get('name')}")
                del layer_config['batch_input_shape']

with open(config_path, 'w') as f:
    json.dump(config_data, f)

print("Repacking model...")
with zipfile.ZipFile(model_path, 'w') as zip_ref:
    for folder_name, subfolders, filenames in os.walk(temp_dir):
        for filename in filenames:
            file_path = os.path.join(folder_name, filename)
            arcname = os.path.relpath(file_path, temp_dir)
            zip_ref.write(file_path, arcname)

shutil.rmtree(temp_dir)
print("Done! Model patched.")
