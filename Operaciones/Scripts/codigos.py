import random
import string
from datetime import datetime, timedelta

# Diccionario para almacenar códigos temporalmente
codigos_pendientes = {}

def generarCodigo(correo):
    """Genera un código de 6 dígitos y lo guarda temporalmente"""
    # Generar código de 6 dígitos
    codigo = ''.join(random.choices(string.digits, k=6))
    
    # Guardar con timestamp de expiración (10 minutos)
    tiempo_expiracion = datetime.now() + timedelta(minutes=10)
    
    codigos_pendientes[correo] = {
        'codigo': codigo,
        'expiracion': tiempo_expiracion,
        'intentos': 0
    }
    
    print(f"✅ Código {codigo} generado para {correo} (expira: {tiempo_expiracion.strftime('%H:%M:%S')})")
    return codigo