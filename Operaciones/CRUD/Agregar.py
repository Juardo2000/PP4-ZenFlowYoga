from Operaciones.CRUD.conexionMySQL import *
from mysql.connector import Error

def registrar_comensal(comensal):
    cursor = crearCursor()
    try:
        # comensal = (correo, password, nombre, apellido, telefono)
        sql = "INSERT INTO Yoguis (Correo, password, Nombre, Apellido, Telefono) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(sql, comensal)
        commit()
    except Error as e:
        print(f"Error {e}")
        raise e
    finally:
        cursor.close()

def registrar_restaurante(restaurante):
        cursor = crearCursor()
        try:
            sql = "INSERT INTO Restaurantes (Nombre, Rif, Correo, Password, Telefono, horario_apertura, horario_cierre, descripcion, numeroDeMesas, fotos, redes_sociales, ubicacion)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(sql, restaurante)
            commit()
            print("Restaurante registrado\n")
        except Error as ex:
            print(f"Error al registrar restaurante: {ex}")
        finally:
            cursor.close()
            
            
def crear_reservacion(reserva):
    cursor = crearCursor()
    try:
        sql = "INSERT INTO Reservas (Nombre, correo, telefono, restaurante, fecha, hora, mesa, personas, comentarios) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(sql, reserva)
        commit()
        print("Reservación creada exitosamente\n")
    except Error as ex:
        print(f"Error al crear reservación: {ex}")
    finally:
        cursor.close()
        
def agregar_yogui(correo, password, nombre, telefono):
    cursor = crearCursor()
    Instructor = "Instructor"
    try:
        cursor.execute("INSERT INTO Yoguis (Correo, Password, Nombre, Apellido, Telefono) VALUES (%s, %s, %s, %s, %s)", 
                      (correo, password, nombre, Instructor, telefono))
        commit()
        return True, "Yogui registrado exitosamente"
    except Error as ex:
        print(f"Error al agregar yogui: {ex}")
        return False, f"Error: {ex}"
    finally:
        cursor.close()

def agregar_instructor(correo, password, nombre, especialidad, telefono, experiencia, bio=None, foto=None):
    cursor = crearCursor()
    try:
        # Las validaciones ya se hicieron en app.py, pero por seguridad se mantienen
        cursor.execute("""
            INSERT INTO Instructores (correo, password, nombre, especialidad, telefono, experiencia, bio, foto, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')
        """, (correo, password, nombre, especialidad, telefono, experiencia, bio, foto))
        commit()
        return True, "Instructor registrado exitosamente"
    except Error as ex:
        return False, f"Error: {ex}"
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

def insertar_pago(correo, referencia, paquete_id, monto, metodo_pago):
    """Inserta un nuevo pago pendiente en la tabla Pagos"""
    cursor = crearCursor()
    try:
        cursor.execute("""
            INSERT INTO Pagos (Correo, Referencia, EstadoDePago, paqueteID, monto, metodo_pago, fecha_pago)
            VALUES (%s, %s, 'pendiente', %s, %s, %s, NOW())
        """, (correo, referencia, paquete_id, monto, metodo_pago))
        commit()
        pago_id = cursor.lastrowid
        print(f"✅ Nuevo pago ID {pago_id} para {correo} - Método: {metodo_pago} - Monto: ${monto}")
        return True, pago_id
    except Error as ex:
        print(f"❌ Error al insertar pago: {ex}")
        return False, None
    finally:
        cursor.close()