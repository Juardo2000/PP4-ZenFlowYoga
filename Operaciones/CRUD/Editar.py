from Operaciones.CRUD.conexionMySQL import *
from mysql.connector import Error


def actualizar_paquete_yogui(correo, clases):
    cursor = crearCursor()
    try:

        cursor.execute("UPDATE Yoguis SET clasesRestantes = %s WHERE Correo = %s", (clases, correo)) 
        commit()
        print(f"{clases} clases")
        return True
        
    except Error as ex:
        print(f"Error al actualizar los datos: {ex}")
        return False
    finally:
        cursor.close()
        
        
def editar_instructor(correo, nombre, especialidad, telefono, experiencia, bio, foto=None):
    """Edita los datos de un instructor existente"""
    cursor = crearCursor()
    try:
        # Verificar si el instructor existe
        cursor.execute("SELECT correo FROM Instructores WHERE correo = %s", (correo,))
        if not cursor.fetchone():
            return False, "Instructor no encontrado"
        
        # Actualizar datos

        cursor.execute("""
            UPDATE Instructores 
                SET nombre = %s, especialidad = %s, telefono = %s, 
                experiencia = %s, bio = %s, foto = %s
            WHERE correo = %s
        """, (nombre, especialidad, telefono, experiencia, bio, foto, correo))
        
        commit()
        
        if cursor.rowcount > 0:
            return True, "Instructor actualizado correctamente"
        else:
            return False, "No se realizaron cambios"
            
    except Exception as ex:
        print(f"Error al editar instructor: {ex}")
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()
        
def confirmar_pago(id_pago):
    """Confirma un pago y agrega las clases al usuario"""
    cursor = crearCursor()
    try:
        # Obtener datos del pago
        cursor.execute("""
            SELECT p.Correo, p.Monto, p.Referencia, p.paqueteID, y.Nombre, paq.dias
            FROM Pagos p
            JOIN Yoguis y ON p.Correo = y.Correo
            JOIN paquetes paq ON p.paqueteID = paq.ID
            WHERE p.id_pago = %s AND p.EstadoDePago = 'pendiente'
        """, (id_pago,))
        
        pago = cursor.fetchone()
        
        if not pago:
            return False, "Pago no encontrado o ya fue procesado"
        
        correo, monto, referencia, paquete_id, nombre_usuario, clases_a_agregar = pago
        
        # Obtener clases actuales del usuario
        cursor.execute("SELECT clasesRestantes FROM Yoguis WHERE Correo = %s", (correo,))
        resultado = cursor.fetchone()
        clases_actuales = resultado[0] if resultado[0] is not None else 0
        nuevas_clases = clases_actuales + clases_a_agregar
        
        # Actualizar clases del usuario
        cursor.execute("UPDATE Yoguis SET clasesRestantes = %s WHERE Correo = %s", (nuevas_clases, correo))
        
        # Actualizar estado del pago
        cursor.execute("UPDATE Pagos SET EstadoDePago = 'confirmado' WHERE id_pago = %s", (id_pago,))
        
        commit()
        
        # Enviar notificación al usuario
        from Operaciones.Scripts.google_services import send_pago_notification
        send_pago_notification(
            correo, 
            nombre_usuario, 
            'confirmado', 
            monto, 
            referencia, 
            f"Paquete {paquete_id} - {clases_a_agregar} clases"
        )
        
        print(f"✅ Pago {id_pago} confirmado. {clases_a_agregar} clases agregadas a {correo}")
        return True, f"Pago confirmado. {clases_a_agregar} clases agregadas a {nombre_usuario}"
        
    except Exception as ex:
        print(f"Error al confirmar pago: {ex}")
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()

def rechazar_pago(id_pago):
    """Rechaza un pago (lo marca como rechazado)"""
    cursor = crearCursor()
    try:
        # Obtener datos del pago antes de rechazarlo
        cursor.execute("""
            SELECT p.Correo, p.Monto, p.Referencia, p.paqueteID, y.Nombre
            FROM Pagos p
            JOIN Yoguis y ON p.Correo = y.Correo
            WHERE p.id_pago = %s AND p.EstadoDePago = 'pendiente'
        """, (id_pago,))
        
        pago = cursor.fetchone()
        
        if not pago:
            return False, "Pago no encontrado o ya fue procesado"
        
        correo, monto, referencia, paquete_id, nombre_usuario = pago
        
        # Actualizar estado del pago
        cursor.execute("UPDATE Pagos SET EstadoDePago = 'rechazado' WHERE id_pago = %s", (id_pago,))
        commit()
        
        # Enviar notificación al usuario
        from Operaciones.Scripts.google_services import send_pago_notification
        send_pago_notification(
            correo, 
            nombre_usuario, 
            'rechazado', 
            monto, 
            referencia, 
            f"Paquete {paquete_id}"
        )
        
        print(f"✅ Pago {id_pago} rechazado")
        return True, "Pago rechazado"
        
    except Exception as ex:
        print(f"Error al rechazar pago: {ex}")
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()
        
def actualizar_datos_yogui(correo, nombre, apellido, telefono):
    """Actualiza los datos básicos del yogui"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            UPDATE Yoguis 
            SET Nombre = %s, Apellido = %s, Telefono = %s 
            WHERE Correo = %s
        """, (nombre, apellido, telefono, correo))
        commit()
        print(f"✅ Datos actualizados para {correo}")
        return True, "Datos actualizados correctamente"
    except Error as ex:
        print(f"Error al actualizar datos: {ex}")
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()

def actualizar_password_yogui(correo, password_actual, password_nueva):
    """Actualiza la contraseña del yogui verificando la actual"""
    cursor = crearCursor()
    try:
        # Verificar contraseña actual
        cursor.execute("SELECT Password FROM Yoguis WHERE Correo = %s", (correo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            return False, "Usuario no encontrado"
        
        if resultado[0] != password_actual:
            return False, "La contraseña actual no es correcta"

        if len(password_nueva) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        cursor.execute("UPDATE Yoguis SET Password = %s WHERE Correo = %s", (password_nueva, correo))
        commit()
        return True, "Contraseña actualizada correctamente"
    except Error as ex:
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()