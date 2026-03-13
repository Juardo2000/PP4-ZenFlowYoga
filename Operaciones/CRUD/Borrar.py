from Operaciones.CRUD.conexionMySQL import *
from mysql.connector import Error
        
from Operaciones.CRUD.Editar import actualizar_paquete_yogui
from Operaciones.Scripts.google_services import cancel_all_attendees_from_class, delete_calendar_event
from Operaciones.CRUD.conexionMySQL import crearCursor
from Operaciones.Scripts.google_services import *
from Operaciones.CRUD.Editar import actualizar_paquete_yogui
from Operaciones.CRUD.Leer import leerYogui, datosYogui
from Operaciones.CRUD.conexionMySQL import crearCursor
import traceback

# En Operaciones/CRUD/AdminCRUD.py

def eliminarYogui(correo):
    """Elimina un usuario (yogui) por su correo"""
    cursor = crearCursor()
    try:
        # Verificar si el usuario existe
        cursor.execute("SELECT Correo, Nombre FROM Yoguis WHERE Correo = %s", (correo,))
        user_data = cursor.fetchone()
        if not user_data:
            return False, "Usuario no encontrado"
        
        nombre_usuario = user_data[1]
        
        cursor.execute("DELETE FROM Yoguis WHERE Correo = %s", (correo,))
        commit()
        
        return True, f"Usuario {nombre_usuario} eliminado correctamente"
    except Exception as ex:
        print(f"Error al eliminar usuario: {ex}")
        return False, f"Error al eliminar: {str(ex)}"
    finally:
        cursor.close()

def eliminarIntructor(correo_instructor, motivo=None):
    """
    Elimina un instructor, cancela todas sus clases y notifica a los alumnos
    """
    cursor = crearCursor()
    try:
        
        print(f"🔍 Eliminando instructor: {correo_instructor}")
        
        # Obtener datos del instructor
        cursor.execute("SELECT nombre FROM Instructores WHERE correo = %s", (correo_instructor,))
        instructor = cursor.fetchone()
        
        if not instructor:
            return False, "Instructor no encontrado"
        
        instructor_nombre = instructor[0]
        
        # Obtener todas sus clases
        clases = get_instructor_classes(correo_instructor, days_ahead=365)
        
        # Diccionario para acumular puntos por alumno
        puntos_por_alumno = {}
        
        for clase in clases:
            # Cancelar asistentes
            success, _, num, emails = cancel_all_attendees_from_class(clase['event_id'], correo_instructor)
            
            if success and num > 0:
                for email in emails:
                    if email not in puntos_por_alumno:
                        puntos_por_alumno[email] = 0
                    puntos_por_alumno[email] += 1
            
            # Eliminar evento
            delete_calendar_event(clase['event_id'], correo_instructor)
        
        # Devolver puntos y notificar
        for email, cantidad in puntos_por_alumno.items():
            cursor2 = crearCursor()
            cursor2.execute("SELECT Nombre, clasesRestantes FROM Yoguis WHERE Correo = %s", (email,))
            alumno = cursor2.fetchone()
            cursor2.close()
            
            if alumno:
                nombre_alumno = alumno[0]
                clases_actuales = alumno[1] or 0
                nuevas_clases = clases_actuales + cantidad
                
                actualizar_paquete_yogui(email, nuevas_clases)
                
                # ENVIAR NOTIFICACIÓN
                motivo_msg = motivo if motivo else f"El instructor {instructor_nombre} ha sido dado de baja"
                send_points_returned_email(email, nombre_alumno, cantidad, motivo_msg)
        
        # Eliminar instructor
        cursor.execute("DELETE FROM Instructores WHERE correo = %s", (correo_instructor,))
        commit()
        
        total_puntos = sum(puntos_por_alumno.values())
        return True, f"✅ Instructor eliminado. Se devolvieron {total_puntos} clases a los alumnos"
        
    except Exception as ex:
        print(f"❌ Error: {ex}")
        return False, f"Error: {str(ex)}"
    finally:
        cursor.close()

def eliminarYoguiCompleto(correo):
    """Elimina completamente un yogui de la base de datos"""
    cursor = crearCursor()
    try:
        # Verificar si el usuario existe
        cursor.execute("SELECT Nombre FROM Yoguis WHERE Correo = %s", (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return False, "Usuario no encontrado"
        
        nombre_usuario = usuario[0]
            
        # 2. Eliminar pagos pendientes del usuario
        clases_id = get_user_events(correo, days_ahead= 365)
        for id in clases_id:
            remove_attendee_from_event(id, correo)
        
        try:
            cursor.execute("DELETE FROM Pagos WHERE Correo = %s", (correo,))
        except:
            pass  # Si no existe la tabla, continuamos
        
        # 3. Finalmente eliminar el usuario
        cursor.execute("DELETE FROM Yoguis WHERE Correo = %s", (correo,))
        commit()
        
        print(f"✅ Usuario {correo} eliminado completamente de la BD")
        return True, nombre_usuario
        
    except Exception as ex:
        print(f"Error al eliminar usuario: {ex}")
        return False, str(ex)
    finally:
        cursor.close()
        
def cancelar_todas_reservas_usuario(correo_usuario, motivo=None):
    """
    Cancela todas las reservas de un usuario en Google Calendar y devuelve las clases
    """
    try:
        print(f"🔍 Buscando reservas para: {correo_usuario}")
        
        # Obtener datos del usuario
        user_data = datosYogui(correo_usuario)
        if not user_data:
            return False, "Usuario no encontrado"
        
        nombre_usuario = user_data[1]  # Nombre del usuario
        print(f"👤 Usuario: {nombre_usuario}")
        
        # Obtener eventos del usuario
        user_events = get_user_events(correo_usuario, days_ahead=60)
        print(f"📊 Eventos encontrados: {len(user_events)}")
        
        if not user_events:
            return True, "El usuario no tiene reservas activas"
        
        # Cancelar cada reserva
        canceladas = 0
        errores = []
        
        for evento in user_events:
            print(f"🔄 Cancelando: {evento['summary']} - {evento['start']}")
            success, message = remove_attendee_from_event(evento['event_id'], correo_usuario)
            if success:
                canceladas += 1
            else:
                errores.append(f"{evento['summary']}: {message}")
        
        print(f"✅ Reservas canceladas: {canceladas}")
        
        if canceladas > 0:
            # Obtener clases actuales
            cursor = crearCursor()
            cursor.execute("SELECT clasesRestantes FROM Yoguis WHERE Correo = %s", (correo_usuario,))
            resultado = cursor.fetchone()
            cursor.close()
            
            if resultado:
                clases_actuales = resultado[0] or 0
                nuevas_clases = clases_actuales + canceladas
                print(f"📊 Clases: {clases_actuales} → {nuevas_clases}")
                
                # Actualizar en BD
                actualizar_paquete_yogui(correo_usuario, nuevas_clases)
                
                # ENVIAR NOTIFICACIÓN
                motivo_msg = motivo if motivo else "Cancelación de todas tus reservas por administración"
                print(f"📧 Enviando notificación a {correo_usuario}...")
                send_points_returned_email(
                    correo_usuario, 
                    nombre_usuario, 
                    canceladas, 
                    motivo_msg
                )
        
        if errores:
            mensaje = f"✅ Se cancelaron {canceladas} reservas. Algunos errores: {', '.join(errores[:3])}"
        else:
            mensaje = f"✅ Se cancelaron {canceladas} reservas y se devolvieron {canceladas} clases a {nombre_usuario}"
        
        return True, mensaje
        
    except Exception as ex:
        print(f"❌ Error en cancelar_todas_reservas_usuario: {ex}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(ex)}"
    
def cancelar_todas_reservas_clase(event_id, instructor_email, eliminar_evento=True, motivo=None):
    """
    Cancela todas las reservas de una clase y devuelve las clases a los usuarios
    """
    try:
       
        print(f"🔍 [INICIO] Cancelando todas las reservas de la clase: {event_id}")
        
        # Obtener datos de la clase para el mensaje
        service = get_calendar_service()
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        titulo = event.get('summary', 'Clase')
        
        # Cancelar asistentes
        success, message, num_cancelados, emails = cancel_all_attendees_from_class(event_id, instructor_email)
        
        if not success:
            return False, f"❌ Error: {message}"
        
        if num_cancelados == 0:
            if eliminar_evento:
                delete_calendar_event(event_id, instructor_email)
            return True, "✅ Clase cancelada (no tenía alumnos inscritos)"
        
        # Devolver clases y notificar
        usuarios_actualizados = 0
        
        for email in emails:
            try:
                cursor = crearCursor()
                cursor.execute("SELECT Correo, Nombre, clasesRestantes FROM Yoguis WHERE Correo = %s", (email,))
                resultado = cursor.fetchone()
                
                if resultado:
                    nombre_usuario = resultado[1]
                    clases_actuales = resultado[2] if resultado[2] is not None else 0
                    nuevas_clases = clases_actuales + 1
                    
                    success_update = actualizar_paquete_yogui(email, nuevas_clases)
                    
                    if success_update:
                        usuarios_actualizados += 1
                        
                        # ENVIAR NOTIFICACIÓN DE DEVOLUCIÓN
                        motivo_msg = motivo if motivo else f"Cancelación de la clase: {titulo}"
                        send_points_returned_email(email, nombre_usuario, 1, motivo_msg)
                        
                cursor.close()
            except Exception as e:
                print(f"Error con {email}: {e}")
        
        if eliminar_evento:
            delete_calendar_event(event_id, instructor_email)
        
        return True, f"✅ Clase cancelada. Se devolvieron {usuarios_actualizados} clases"
        
    except Exception as ex:
        print(f"❌ Error: {ex}")
        return False, f"Error: {str(ex)}"
    
def eliminar_todas_clases_instructor(correo_instructor):
    """Elimina TODAS las clases futuras de un instructor y devuelve los puntos a los alumnos"""
    try:
        
        print(f"🔍 Eliminando TODAS las clases del instructor: {correo_instructor}")
        
        # Obtener todas las clases futuras del instructor
        clases = get_instructor_classes(correo_instructor, days_ahead=365)
        
        if not clases:
            return True, "El instructor no tiene clases programadas"
        
        print(f"📊 Se encontraron {len(clases)} clases para eliminar")
        
        # Diccionario para acumular puntos por alumno
        puntos_por_alumno = {}
        clases_eliminadas = 0
        errores = []
        
        for clase in clases:
            try:
                # Obtener nombre del instructor
                cursor = crearCursor()
                cursor.execute("SELECT nombre FROM Instructores WHERE correo = %s", (correo_instructor,))
                instructor_data = cursor.fetchone()
                instructor_nombre = instructor_data[0] if instructor_data else "El instructor"
                cursor.close()
                
                # Cancelar asistentes y obtener emails
                success, message, num_cancelados, emails = cancel_all_attendees_from_class(
                    clase['event_id'], correo_instructor
                )
                
                if success and num_cancelados > 0:
                    # Acumular puntos por alumno
                    for email in emails:
                        if email not in puntos_por_alumno:
                            puntos_por_alumno[email] = 0
                        puntos_por_alumno[email] += 1
                    
                    print(f"   ✅ Cancelados {num_cancelados} asistentes de clase {clase['title']}")
                
                # Eliminar el evento
                event_success, event_message = delete_calendar_event(clase['event_id'], correo_instructor)
                if event_success:
                    clases_eliminadas += 1
                    print(f"   ✅ Clase eliminada: {clase['title']}")
                else:
                    errores.append(f"No se pudo eliminar clase {clase['title']}: {event_message}")
                    
            except Exception as e:
                errores.append(f"Error con clase {clase.get('title')}: {str(e)}")
        
        # Devolver puntos a los alumnos
        puntos_devueltos = 0
        alumnos_notificados = 0
        
        for email, cantidad in puntos_por_alumno.items():
            try:
                cursor = crearCursor()
                cursor.execute("SELECT Nombre, clasesRestantes FROM Yoguis WHERE Correo = %s", (email,))
                alumno = cursor.fetchone()
                cursor.close()
                
                if alumno:
                    nombre_alumno = alumno[0]
                    clases_actuales = alumno[1] if alumno[1] is not None else 0
                    nuevas_clases = clases_actuales + cantidad
                    
                    # Actualizar en BD
                    success = actualizar_paquete_yogui(email, nuevas_clases)
                    
                    if success:
                        puntos_devueltos += cantidad
                        
                        # Enviar notificación
                        from Operaciones.Scripts.google_services import send_points_returned_email
                        send_points_returned_email(
                            email, 
                            nombre_alumno, 
                            cantidad, 
                            f"Clases canceladas por eliminación de todas las clases del instructor {instructor_nombre}"
                        )
                        alumnos_notificados += 1
                        
            except Exception as e:
                errores.append(f"Error al devolver puntos a {email}: {str(e)}")
        
        # Mensaje final
        if clases_eliminadas == len(clases):
            mensaje = f"✅ Se eliminaron {clases_eliminadas} clases. Se devolvieron {puntos_devueltos} puntos a {alumnos_notificados} alumnos."
            return True, mensaje
        else:
            mensaje = f"⚠️ Se eliminaron {clases_eliminadas} de {len(clases)} clases. Se devolvieron {puntos_devueltos} puntos. Errores: {', '.join(errores[:3])}"
            return True, mensaje
        
    except Exception as ex:
        print(f"❌ Error al eliminar todas las clases del instructor: {ex}")
        import traceback
        traceback.print_exc()
        return False, f"Error inesperado: {str(ex)}"
