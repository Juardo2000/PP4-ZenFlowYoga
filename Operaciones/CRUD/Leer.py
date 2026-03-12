from Operaciones.CRUD.conexionMySQL import *
from mysql.connector import Error


def loginCO(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Password FROM Yoguis WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()

def loginAD(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Password FROM Administradores WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()
            
def loginRE(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Password FROM Instructores WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()
   
            
def leerYogui(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT * FROM Yoguis WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()

def leerTodosLosYogui():
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Nombre, Apellido, Telefono, clasesRestantes FROM Yoguis")
            resultados = cursor.fetchall()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()
            
                     
def datosYogui(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Nombre, Telefono FROM Yoguis WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()


def datosAdmin(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Nombre, Telefono FROM Administradores WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()
            
def datosIns(correo):
        cursor = crearCursor()
        try:
            cursor.execute("SELECT Correo, Nombre, Telefono FROM Instructores WHERE Correo = %s", (correo,))
            resultados = cursor.fetchone()
            return resultados
        except Error as ex:
            print(f"Error al selecionar los datos: {ex}")
        finally:
            cursor.close()

def leerInstructores():
    cursor = crearCursor()
    try:
        cursor.execute("SELECT id_instructor, correo, password, nombre, especialidad, telefono, experiencia, estado, fecha_registro, bio, foto FROM Instructores")
        resultados = cursor.fetchall()
        print(resultados)
        return resultados
    except Error as ex:
        print(f"Error al mostrar instructores: {ex}")
        return []
    finally:
        cursor.close()
            
def ver_reservaciones(res):
        cursor = crearCursor()
        try:
                cursor.execute("SELECT * FROM Reservas where restaurante = %s",(res,))
                resultados = cursor.fetchall()
                return resultados
        except Error as ex:
            print(f"Error al ver reservaciones: {ex}")
        finally:
            cursor.close()


def ver_reservaciones_comensal(co):
        cursor = crearCursor()
        try:
                cursor.execute("SELECT * FROM Reservas where correo = %s",(co,))
                resultados = cursor.fetchone()
                return resultados
        except Error as ex:
            print(f"Error al ver reservaciones: {ex}")
        finally:
            cursor.close()
            
def leerPaquetes():
        cursor = crearCursor()
        try:
            cursor.execute("SELECT * FROM paquetes")
            resultados = cursor.fetchall()
            return resultados
        except Error as ex:
            print(f"Error al ver paquetes: {ex}")


def es_instructor(correo):
    """Verifica si un correo pertenece a un instructor"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            SELECT id_instructor FROM Instructores 
            WHERE correo = %s AND estado = 'activo'
        """, (correo,))
        
        return cursor.fetchone() is not None
    except Error as ex:
        print(f"Error al verificar instructor: {ex}")
        return False
    finally:
        cursor.close()
        
def obtener_instructor(correo):
    cursor = crearCursor()
    try:
        cursor.execute("""
            SELECT * FROM Instructores 
            WHERE correo = %s AND estado = 'activo'
        """, (correo,))
        
        return cursor.fetchone()
    except Error as ex:
        print(f"Error al obtener instructor: {ex}")
        return None
    finally:
        cursor.close()
        
def buscar_usuarios(termino):
    """Busca usuarios por nombre, correo o teléfono"""
    cursor = crearCursor()
    try:
        busqueda = f"%{termino}%"
        cursor.execute("""
            SELECT Correo, Nombre, Apellido, Telefono, clasesRestantes, 
                   DATE_FORMAT(FechaRegistro, '%d/%m/%Y') as FechaRegistro 
            FROM Yoguis 
            WHERE Correo LIKE %s OR Nombre LIKE %s OR Apellido LIKE %s OR Telefono LIKE %s
            ORDER BY FechaRegistro DESC
        """, (busqueda, busqueda, busqueda, busqueda))
        resultados = cursor.fetchall()
        return resultados
    except Error as ex:
        print(f"Error al buscar usuarios: {ex}")
        return []
    finally:
        cursor.close()  
        

def obtener_estadisticas_generales():
    """Obtiene estadísticas generales del sistema"""
    cursor = crearCursor()
    try:
        stats = {}
        
        # Total de usuarios
        cursor.execute("SELECT COUNT(*) FROM Yoguis")
        stats['total_usuarios'] = cursor.fetchone()[0] or 0
        
        # Total de instructores
        cursor.execute("SELECT COUNT(*) FROM Instructores WHERE COALESCE(estado, 'activo') = 'activo'")
        stats['total_instructores'] = cursor.fetchone()[0] or 0
        
        # Reservas activas (contar asistentes en eventos futuros)
        try:
            from Operaciones.Scripts.google_services import get_calendar_service
            from datetime import datetime, timedelta
            
            service = get_calendar_service()
            now = datetime.utcnow().isoformat() + 'Z'
            future = (datetime.utcnow() + timedelta(days=60)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=future,
                maxResults=250,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            
            total_reservas = 0
            for event in events:
                attendees = event.get('attendees', [])
                for a in attendees:
                    if a.get('responseStatus') != 'declined' and a.get('email') != event.get('organizer', {}).get('email'):
                        total_reservas += 1
            
            stats['total_reservas'] = total_reservas
        except Exception as e:
            print(f"Error al obtener reservas: {e}")
            stats['total_reservas'] = 0
        
        # Clases en calendario
        try:
            from Operaciones.Scripts.google_services import get_yoga_classes_from_calendar
            clases = get_yoga_classes_from_calendar(days_ahead=30)
            stats['clases_calendario'] = len(clases)
        except:
            stats['clases_calendario'] = 0
        
        # Clases totales disponibles (puntos de los usuarios)
        cursor.execute("SELECT COALESCE(SUM(clasesRestantes), 0) FROM Yoguis")
        stats['clases_totales'] = cursor.fetchone()[0] or 0
        
        return stats
    except Error as ex:
        print(f"Error al obtener estadísticas: {ex}")
        return {'total_usuarios': 0, 'total_instructores': 0, 'total_reservas': 0, 'clases_calendario': 0, 'clases_totales': 0}
    finally:
        cursor.close()
        
        
def obtener_pagos_pendientes():
    """Obtiene todos los pagos pendientes de la tabla Pagos"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            SELECT id_pago, Correo, Referencia, monto, fecha_pago, paqueteID, metodo_pago
            FROM Pagos
            WHERE EstadoDePago = 'pendiente'
            ORDER BY fecha_pago DESC
        """)
        resultados = cursor.fetchall()
        return resultados
    except Error as ex:
        print(f"Error al obtener pagos pendientes: {ex}")
        return []
    finally:
        cursor.close()

def obtener_pagos_confirmados():
    """Obtiene los últimos pagos confirmados"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            SELECT id_pago, Correo, Referencia, monto, fecha_pago, paqueteID, metodo_pago
            FROM Pagos
            WHERE EstadoDePago = 'confirmado'
            ORDER BY fecha_pago DESC
            LIMIT 20
        """)
        resultados = cursor.fetchall()
        return resultados
    except Error as ex:
        print(f"Error al obtener pagos confirmados: {ex}")
        return []
    finally:
        cursor.close()
        
def obtener_ventas_por_mes(mes=None, año=None):
    """Obtiene las ventas del mes especificado (por defecto mes actual)"""
    cursor = crearCursor()
    try:
        from datetime import datetime
        
        if mes is None or año is None:
            hoy = datetime.now()
            mes = hoy.month
            año = hoy.year
        
        # Obtener pagos confirmados del mes
        cursor.execute("""
            SELECT id_pago, Correo, Referencia, paqueteID, Monto, fecha_pago, metodo_pago
            FROM Pagos
            WHERE EstadoDePago = 'confirmado' 
            AND MONTH(fecha_pago) = %s AND YEAR(fecha_pago) = %s
            ORDER BY fecha_pago DESC
        """, (mes, año))
        
        pagos = cursor.fetchall()
        
        # Procesar pagos
        pagos_procesados = []
        total_ingresos = 0
        
        for pago in pagos:
            # Convertir monto a float (índice 4 porque la consulta ahora tiene 7 campos)
            monto = float(pago[4]) if pago[4] is not None else 0
            
            pagos_procesados.append((
                pago[0],  # id_pago
                pago[1],  # Correo
                pago[2],  # Referencia
                monto,    # Monto (convertido)
                pago[5],  # fecha_pago (datetime)
                pago[3],  # paqueteID
                pago[6]   # metodo_pago
            ))
            
            total_ingresos += monto
        
        return {
            'pagos': pagos_procesados,
            'total_ingresos': total_ingresos,
            'cantidad_pagos': len(pagos)
        }
    except Error as ex:
        print(f"Error al obtener ventas por mes: {ex}")
        return {'pagos': [], 'total_ingresos': 0, 'cantidad_pagos': 0}
    finally:
        cursor.close()

def obtener_ventas_por_dia_semana(mes=None, año=None):
    """Obtiene las ventas agrupadas por día de la semana para el mes especificado"""
    cursor = crearCursor()
    try:
        from datetime import datetime
        
        if mes is None or año is None:
            hoy = datetime.now()
            mes = hoy.month
            año = hoy.year
        
        # Días de la semana en español
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        # Inicializar contadores
        ventas_por_dia = {dia: {'cantidad': 0, 'monto': 0} for dia in dias_semana}
        
        # Obtener pagos del mes
        cursor.execute("""
            SELECT monto, fecha_pago
            FROM Pagos
            WHERE EstadoDePago = 'confirmado' 
            AND MONTH(fecha_pago) = %s AND YEAR(fecha_pago) = %s
        """, (mes, año))
        
        pagos = cursor.fetchall()
        
        for pago in pagos:
            monto = pago[0]
            fecha = pago[1]
            
            # Obtener día de la semana (0 = lunes, 6 = domingo)
            dia_semana_num = fecha.weekday()
            dia_nombre = dias_semana[dia_semana_num]
            
            ventas_por_dia[dia_nombre]['cantidad'] += 1
            ventas_por_dia[dia_nombre]['monto'] += monto
        
        # Encontrar el día con más ventas
        dia_max = max(ventas_por_dia.items(), key=lambda x: x[1]['cantidad']) if any(v['cantidad'] > 0 for v in ventas_por_dia.values()) else ('Sin datos', {'cantidad': 0, 'monto': 0})
        
        return {
            'ventas_por_dia': ventas_por_dia,
            'dia_mas_ventas': dia_max[0],
            'cantidad_max': dia_max[1]['cantidad'],
            'monto_max': dia_max[1]['monto']
        }
    except Error as ex:
        print(f"Error al obtener ventas por día: {ex}")
        return None
    finally:
        cursor.close()

def obtener_meses_disponibles():
    """Obtiene los meses y años en los que hay pagos confirmados"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            SELECT DISTINCT YEAR(fecha_pago) as año, MONTH(fecha_pago) as mes
            FROM Pagos
            WHERE EstadoDePago = 'confirmado'
            ORDER BY año DESC, mes DESC
        """)
        
        resultados = cursor.fetchall()
        meses_nombres = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        meses_disponibles = []
        for año, mes in resultados:
            meses_disponibles.append({
                'año': año,
                'mes': mes,
                'nombre': meses_nombres[mes],
                'valor': f"{año}-{mes:02d}"
            })
        
        return meses_disponibles
    except Error as ex:
        print(f"Error al obtener meses disponibles: {ex}")
        return []
    finally:
        cursor.close()