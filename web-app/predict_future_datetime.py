import sys
import json
import pandas as pd
import numpy as np
import requests
import os
import pickle
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def main():
    try:
        from tensorflow.keras.models import load_model
        
        # Validate arguments
        if len(sys.argv) < 4:
            raise Exception("Missing required parameters: latitude, longitude, target_datetime")
        
        # Parse arguments
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        target_datetime_str = sys.argv[3]
        species = sys.argv[4] if len(sys.argv) > 4 else 'general'
        
        # Species thresholds
        THRESHOLDS = {
            'general': {'tempMin': 20, 'tempMax': 28, 'doMin': 5, 'doMax': 12, 'phMin': 6.5, 'phMax': 8.5},
            'tilapia': {'tempMin': 25, 'tempMax': 32, 'doMin': 3, 'doMax': 15, 'phMin': 6, 'phMax': 9},
            'catfish': {'tempMin': 24, 'tempMax': 30, 'doMin': 4, 'doMax': 12, 'phMin': 6.5, 'phMax': 8.5},
            'salmon': {'tempMin': 10, 'tempMax': 18, 'doMin': 7, 'doMax': 14, 'phMin': 6.5, 'phMax': 8},
            'trout': {'tempMin': 10, 'tempMax': 16, 'doMin': 7, 'doMax': 14, 'phMin': 6.5, 'phMax': 8},
            'carp': {'tempMin': 20, 'tempMax': 28, 'doMin': 4, 'doMax': 12, 'phMin': 6.5, 'phMax': 9},
            'shrimp': {'tempMin': 26, 'tempMax': 32, 'doMin': 4, 'doMax': 10, 'phMin': 7, 'phMax': 8.5},
            'prawn': {'tempMin': 26, 'tempMax': 31, 'doMin': 4, 'doMax': 10, 'phMin': 7, 'phMax': 8.5}
        }
        thresholds = THRESHOLDS.get(species, THRESHOLDS['general'])
        
        # Parse target datetime
        try:
            # Handle different datetime formats
            if 'T' in target_datetime_str:
                if target_datetime_str.endswith('Z'):
                    target_dt = datetime.fromisoformat(target_datetime_str[:-1])
                else:
                    target_dt = datetime.fromisoformat(target_datetime_str)
            else:
                target_dt = datetime.strptime(target_datetime_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            raise Exception(f"Invalid datetime format: {target_datetime_str}")
        
        # Validate future date
        current_dt = datetime.now()
        if target_dt <= current_dt:
            raise Exception("Target date must be in the future")
        
        # Calculate time difference
        time_diff = target_dt - current_dt
        hours_ahead = max(1, int(time_diff.total_seconds() / 3600))
        days_ahead = round(hours_ahead / 24.0, 1)
        
        # Limit prediction range
        if hours_ahead > 8760:  # 1 year
            raise Exception("Cannot predict more than 1 year into the future")
        
        # Load LSTM model
        model_path = os.path.join(os.path.dirname(__file__), '..', 'water_qual_universal.keras')
        scaler_path = os.path.join(os.path.dirname(__file__), '..', 'water_qual_universal_scaler.pkl')
        
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise Exception("LSTM model files not found")
        
        model = load_model(model_path)
        with open(scaler_path, 'rb') as f:
            scaler_data = pickle.load(f)
        
        scaler = MinMaxScaler()
        scaler.min_ = scaler_data['min_']
        scaler.scale_ = scaler_data['scale_']
        scaler.data_min_ = scaler_data['data_min_']
        scaler.data_max_ = scaler_data['data_max_']
        features = scaler_data['features']
        
        # Get recent weather data
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=2)
        
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,relativehumidity_2m,precipitation,windspeed_10m&timezone=UTC"
        
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            raise Exception("Failed to fetch weather data")
        
        weather_data = response.json()
        df = pd.DataFrame({
            "air_temp": weather_data["hourly"]["temperature_2m"],
            "humidity": weather_data["hourly"]["relativehumidity_2m"],
            "rain": weather_data["hourly"]["precipitation"],
            "windspeed": weather_data["hourly"]["windspeed_10m"]
        })
        
        # Apply water quality formulas
        df["water_temp"] = df["air_temp"] - 2
        df["do"] = 8.0
        df["ph"] = 7.3
        
        # LSTM prediction
        if len(df) < 24:
            raise Exception("Insufficient weather data for prediction")
        
        # Use LSTM model
        scaled = scaler.transform(df[features].tail(24))
        X = scaled.reshape(1, 24, len(features))
        pred_scaled = model.predict(X, verbose=0)[0]
        
        # Inverse transform
        dummy = np.zeros((1, len(features)))
        dummy[0, 4:7] = pred_scaled  # water_temp, do, ph positions
        pred_full = scaler.inverse_transform(dummy)[0]
        
        # Base predictions
        base_temp = pred_full[4]
        base_do = pred_full[5]
        base_ph = pred_full[6]
        
        # Add variations for future prediction
        time_factor = min(days_ahead, 7) / 7
        
        # Daily cycle (using standard datetime attributes)
        hour = target_dt.hour
        daily_cycle = 1.5 * np.sin(2 * np.pi * (hour - 14) / 24)
        
        # Seasonal variation (using timetuple)
        day_of_year = target_dt.timetuple().tm_yday
        seasonal = 0.5 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Random variations
        temp_noise = np.random.normal(0, time_factor * 0.5)
        do_noise = np.random.normal(0, time_factor * 0.3)
        ph_noise = np.random.normal(0, time_factor * 0.1)
        
        # Final predictions
        water_temp = round(base_temp + daily_cycle + seasonal + temp_noise, 2)
        do_val = round(max(0.5, base_do - (daily_cycle * 0.1) + do_noise), 2)
        ph_val = round(np.clip(base_ph + ph_noise, 5.0, 10.0), 2)
        
        # Calculate quality score
        score = 0
        if thresholds['tempMin'] <= water_temp <= thresholds['tempMax']:
            score += 35
        elif thresholds['tempMin'] - 5 <= water_temp <= thresholds['tempMax'] + 5:
            score += 20
        else:
            score += 5
        
        if do_val >= thresholds['doMin'] + 3:
            score += 40
        elif do_val >= thresholds['doMin']:
            score += 25
        else:
            score += 10
        
        if thresholds['phMin'] <= ph_val <= thresholds['phMax']:
            score += 25
        elif thresholds['phMin'] - 0.5 <= ph_val <= thresholds['phMax'] + 0.5:
            score += 15
        else:
            score += 5
        
        if score >= 80:
            quality, color = "Excellent", "#4CAF50"
        elif score >= 60:
            quality, color = "Good", "#8BC34A"
        elif score >= 40:
            quality, color = "Fair", "#FFC107"
        else:
            quality, color = "Poor", "#F44336"
        
        # Generate recommendations
        recommendations = []
        
        # Temperature
        if water_temp < thresholds['tempMin']:
            deficit = thresholds['tempMin'] - water_temp
            if deficit > 5:
                recommendations.append(f"🚨 CRITICAL: Temperature ({water_temp}°C) will be {deficit:.1f}°C below minimum. Emergency heating required!")
            else:
                recommendations.append(f"🌡️ Temperature ({water_temp}°C) below optimal. Prepare heating systems.")
        elif water_temp > thresholds['tempMax']:
            excess = water_temp - thresholds['tempMax']
            if excess > 5:
                recommendations.append(f"🚨 CRITICAL: Temperature ({water_temp}°C) will be {excess:.1f}°C above maximum. Emergency cooling required!")
            else:
                recommendations.append(f"🌡️ Temperature ({water_temp}°C) above optimal. Prepare cooling systems.")
        else:
            recommendations.append(f"✅ Temperature ({water_temp}°C) will remain optimal for {species}")
        
        # Dissolved Oxygen
        if do_val < thresholds['doMin']:
            deficit = thresholds['doMin'] - do_val
            recommendations.append(f"🚨 CRITICAL: DO ({do_val} mg/L) will be {deficit:.1f} mg/L below minimum. Increase aeration!")
        elif do_val < thresholds['doMin'] + 2:
            recommendations.append(f"⚠️ DO ({do_val} mg/L) will be low. Monitor and prepare aeration.")
        else:
            recommendations.append(f"✅ DO ({do_val} mg/L) will remain adequate for {species}")
        
        # pH
        if ph_val < thresholds['phMin']:
            deficit = thresholds['phMin'] - ph_val
            recommendations.append(f"⚗️ pH ({ph_val}) will be {deficit:.1f} units below optimal. Prepare lime.")
        elif ph_val > thresholds['phMax']:
            excess = ph_val - thresholds['phMax']
            recommendations.append(f"⚗️ pH ({ph_val}) will be {excess:.1f} units above optimal. Prepare pH reduction.")
        else:
            recommendations.append(f"✅ pH ({ph_val}) will remain optimal for {species}")
        
        # Time-based advice
        if hours_ahead <= 2:
            recommendations.append(f"⏰ Short-term prediction ({hours_ahead}h): Monitor closely")
        elif hours_ahead <= 24:
            recommendations.append(f"📅 Daily prediction: Plan management activities")
        else:
            recommendations.append(f"📊 Extended prediction ({days_ahead} days): Strategic planning")
        
        # Species-specific advice
        if species in ['salmon', 'trout'] and water_temp > 16:
            recommendations.append(f"🐟 Cold-water species alert: Temperature may stress {species}")
        elif species == 'tilapia' and water_temp < 20:
            recommendations.append(f"🐟 Warm-water species alert: Temperature may slow {species} growth")
        elif species in ['shrimp', 'prawn'] and (ph_val < 7.2 or ph_val > 8.3):
            recommendations.append(f"🦐 Crustacean alert: pH may affect {species} shell development")
        
        # Build result
        result = {
            'success': True,
            'target_datetime': target_datetime_str,
            'days_ahead': days_ahead,
            'hours_ahead': hours_ahead,
            'predicted_values': {
                'water_temp': water_temp,
                'do': do_val,
                'ph': ph_val
            },
            'quality_score': round(score, 2),
            'quality_level': quality,
            'color': color,
            'recommendations': recommendations,
            'species': species,
            'location': {'latitude': lat, 'longitude': lon},
            'prediction_method': 'LSTM Future Forecast',
            'confidence': 'High' if hours_ahead <= 6 else 'Medium' if hours_ahead <= 24 else 'Low',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()