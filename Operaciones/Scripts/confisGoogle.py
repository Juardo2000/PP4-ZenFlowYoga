# config/google_config.py
import os
from pathlib import Path

# Directorio base
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de Google API
GOOGLE_CREDENTIALS = {
    # Service Account (recomendado para servidor)
    'service_account': {
        'enabled': True,
        'file_path': BASE_DIR / 'credentials' / 'service-account.json',
        'scopes': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
    },
    # OAuth 2.0 (para interacción con usuarios)
    'oauth': {
        'enabled': False,  # Cambiar a True si lo necesitas
        'file_path': BASE_DIR / 'credentials' / 'credentials.json',
        'token_path': BASE_DIR / 'credentials' / 'token.pickle',
        'scopes': [
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/userinfo.email'
        ],
        'redirect_uri': 'http://localhost:5001/callback'
    }
}

# Configuración de calendarios
CALENDAR_CONFIG = {
    'primary_calendar_id': 'primary',  # Calendario principal
    'class_calendar_id': None,  # ID específico para clases (si tienes uno)
    'timezone': 'America/Mexico_City',  # Ajusta a tu zona horaria
    'default_duration': 60,  # Duración en minutos por defecto
    'capacity_per_class': 20  # Capacidad máxima por clase
}

# Verificar que existen los archivos de credenciales
def check_credentials():
    """Verifica que las credenciales existan"""
    credentials_ok = False
    
    # Verificar Service Account
    if GOOGLE_CREDENTIALS['service_account']['enabled']:
        service_file = GOOGLE_CREDENTIALS['service_account']['file_path']
        if os.path.exists(service_file):
            print(f"✓ Service Account encontrado: {service_file}")
            credentials_ok = True
        else:
            print(f"✗ Service Account NO encontrado: {service_file}")
    
    # Verificar OAuth
    if GOOGLE_CREDENTIALS['oauth']['enabled']:
        oauth_file = GOOGLE_CREDENTIALS['oauth']['file_path']
        if os.path.exists(oauth_file):
            print(f"✓ Credenciales OAuth encontradas: {oauth_file}")
        else:
            print(f"✗ Credenciales OAuth NO encontradas: {oauth_file}")
    
    return credentials_ok