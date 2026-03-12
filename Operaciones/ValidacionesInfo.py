import re

class ValidacionError(Exception):
    pass

def validar_email(correo):
    if not re.match(r'^[^@]+@(gmail|hotmail)\.com$', correo):
        raise ValidacionError("Correo no válido.")
    return True

def validar_telefono(telefono_str):
    try:
        telefono_num = int(telefono_str)
    except ValueError:
         raise ValidacionError("Número de teléfono inválido.")
    # Si la conversión a entero fue exitosa, ahora validar con regex
    if not re.match(r'^(0412|0414|0424|0426)\d{7}$', telefono_str):
        raise ValidacionError("Número de teléfono inválido.")
    return True

def validar_clave(contraseña):
    if len(contraseña) < 8:
        raise ValidacionError("La contraseña debe tener al menos 8 caracteres.")
    return True

def validar_nombre(nombre):
    if len(nombre) < 1:
        raise ValidacionError("El nombre o Apellido no puede estar vacio.")
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóú\s]+$', nombre):
        raise ValidacionError("Nombre o Apellido no válido, solo se permiten letras y espacios.")
    return True
    
    print(rif, nombre, contraseña, correo, telefono, apertura, cierre, fotos, numeroDeMesas)
    

   