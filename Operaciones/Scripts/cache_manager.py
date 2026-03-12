# Operaciones/Scripts/cache_manager.py
import os
import pickle
import hashlib
import json
from datetime import datetime, timedelta

CACHE_DIR = 'credentials/cache'

# Asegurar que existe el directorio de caché
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(prefix, *args, **kwargs):
    """Genera una clave única para caché"""
    params = f"{prefix}_{str(args)}_{str(kwargs)}"
    return hashlib.md5(params.encode()).hexdigest()

def get_from_cache(cache_key, max_age_minutes=5):
    """Obtiene datos del caché si no han expirado"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pickle")
    
    if os.path.exists(cache_file):
        file_modified = datetime.fromtimestamp(os.path.getmtime(cache_file))
        age = (datetime.now() - file_modified).total_seconds() / 60
        
        if age < max_age_minutes:
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
    return None

def save_to_cache(cache_key, data):
    """Guarda datos en caché"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pickle")
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"⚠️ Error guardando en caché: {e}")

def clear_instructor_cache(instructor_email=None):
    """Limpia el caché de un instructor específico"""
    try:
        if instructor_email:
            count = 0
            for file in os.listdir(CACHE_DIR):
                if instructor_email in file:
                    os.remove(os.path.join(CACHE_DIR, file))
                    count += 1
            print(f"✅ Caché limpiado: {count} archivos para {instructor_email}")
        else:
            # Limpiar todo
            for file in os.listdir(CACHE_DIR):
                os.remove(os.path.join(CACHE_DIR, file))
            print("✅ Todo el caché limpiado")
    except Exception as e:
        print(f"⚠️ Error limpiando caché: {e}")