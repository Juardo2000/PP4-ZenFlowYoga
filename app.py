from flask import (Flask, render_template, request, flash, redirect, url_for, 
                   session, jsonify, make_response,send_file, get_flashed_messages)
from Operaciones.yogui import Yogui
from Operaciones.instructor import *
from Operaciones.shala import Shala
from Operaciones.reserva import Reservas
from Operaciones.ValidacionesInfo import *
from Operaciones.CRUD.Leer import *
from Operaciones.CRUD.Agregar import *
from Operaciones.CRUD.Borrar import *
from Operaciones.CRUD.Editar import *
from mysql.connector import Error 
from werkzeug.utils import secure_filename
import os, shutil, io, sys
from datetime import time, datetime, timedelta

#API de Google
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth
from Operaciones.Scripts.Gmail import * 
from Operaciones.Scripts.codigos import * 
from Operaciones.Scripts.Reportes import * 
from Operaciones.Scripts.curriculum import procesar_curriculum
from Operaciones.Scripts.google_services import *

print("="*60) 
print("🚀 INICIANDO APLICACIÓN EN RENDER")
print("="*60)

# Mostrar información de rutas
basedir = os.path.abspath(os.path.dirname(__file__))
print(f"📂 Directorio base: {basedir}")
print(f"📂 Archivos en base: {os.listdir(basedir)}")

# Verificar carpeta templates
template_path = os.path.join(basedir, 'templates')
if os.path.exists(template_path):
    print(f"✅ Carpeta templates encontrada: {template_path}")
    print(f"   Archivos: {os.listdir(template_path)}")
else:
    print(f"❌ Carpeta templates NO encontrada en: {template_path}")

# Verificar carpeta static
static_path = os.path.join(basedir, 'static')
if os.path.exists(static_path):
    print(f"✅ Carpeta static encontrada: {static_path}")
    print(f"   Archivos: {os.listdir(static_path)}")
else:
    print(f"❌ Carpeta static NO encontrada en: {static_path}")

print("="*60)

def crear_app():

        app = Flask(__name__)
        app.secret_key = '123456789'  # Cambia esto por una clave segura

        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Sesión de 1 hora
        
        @app.route('/')
        def index():
            logYogui = session.get('loginY', False)
            LogShala = session.get('loginS', False)
            LogInst = session.get('loginI', False)
            correo = session.get('Correo', '')
            
            # Verificar si hay flash de inicio de sesión
            mostrar_bienvenida = False
            nombre_usuario = session.get('Nombre', '')
            
            # Obtener flashes
            flashes = get_flashed_messages(with_categories=True)
            for category, message in flashes:
                if message == 'inicio_sesion_exitoso':
                    mostrar_bienvenida = True
            
            # Obtener las 3 próximas clases
            clases_proximas = []
            pagos_pendientes = 0
            
            try:
                from Operaciones.Scripts.google_services import get_yoga_classes_from_calendar
                from datetime import datetime
                from Operaciones.CRUD.conexionMySQL import crearCursor
                
                todas_clases = get_yoga_classes_from_calendar(days_ahead=30)
                clases_con_cupos = [c for c in todas_clases if c['available_spots'] > 0]
                clases_ordenadas = sorted(clases_con_cupos, key=lambda x: (x['date'], x['time']))
                
                for clase in clases_ordenadas[:3]:
                    fecha_obj = datetime.strptime(clase['date'], '%Y-%m-%d')
                    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                    
                    clase_formateada = {
                        'title': clase['title'],
                        'fecha_dia': dias_semana[fecha_obj.weekday()],
                        'fecha_formateada': f"{fecha_obj.day} de {meses[fecha_obj.month-1]}",
                        'hora': clase['time'],
                        'duracion': clase['duration'],
                        'ubicacion': clase['location'],
                        'instructor': clase['instructor'],
                        'cupos_disponibles': clase['available_spots'],
                        'is_hibrida': clase.get('is_hibrida', False),
                        'meet_link': clase.get('meet_link', None)
                    }
                    clases_proximas.append(clase_formateada)
                
                if logYogui and correo:
                    cursor = crearCursor()
                    try:
                        cursor.execute("SELECT COUNT(*) FROM Pagos WHERE Correo = %s AND EstadoDePago = 'pendiente'", (correo,))
                        resultado = cursor.fetchone()
                        if resultado:
                            pagos_pendientes = resultado[0]
                    except Exception as e:
                        print(f"Error al obtener pagos pendientes: {e}")
                    finally:
                        cursor.close()
                    
            except Exception as e:
                print(f"Error al obtener clases para el index: {e}")
            
            return render_template('index.html', 
                                logYogui=logYogui,  
                                LogShala=LogShala, 
                                LogInst=LogInst,
                                clases_proximas=clases_proximas,
                                pagos_pendientes=pagos_pendientes,
                                mostrar_bienvenida=mostrar_bienvenida,
                                nombre_usuario=nombre_usuario)
        
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            y = Yogui
            s = Shala
            i = Instructor
            if request.method == 'POST':
                correo = request.form.get('correo')
                password = request.form.get('password')
                
                try:
                    validar_email(correo)
                except ValidacionError:
                    flash("Formato de correo no válido", "danger")
                    return render_template('login.html', correo=correo)
                
                verificarS = s.login(correo, password)
                verificarY = y.login(correo, password)
                verificarI = i.login(correo, password)
                
                if verificarS:
                    session['loginS'] = True
                    datos = s.datosAdmin(correo)
                    session['Correo'] = datos[0]
                    session['Nombre'] = datos[1]
                    session['Telefono'] = datos[2]
                    flash('inicio_sesion_exitoso', 'success')
                    return redirect(url_for('index'))
                
                elif verificarI:
                    session['loginI'] = True
                    datos = i.datosIns(correo)
                    session['Correo'] = datos[0]
                    session['Nombre'] = datos[1]
                    session['Telefono'] = datos[2]
                    flash('inicio_sesion_exitoso', 'success')
                    return redirect(url_for('index')) 
                    
                elif verificarY:
                    session['loginY'] = True
                    datos = y.datosYogui(correo)
                    session['Correo'] = datos[0]
                    session['Nombre'] = datos[1]
                    session['Telefono'] = datos[2]
                    flash('inicio_sesion_exitoso', 'success')
                    return redirect(url_for('index'))
                    
                
                    
                else:
                    flash("Error en la verificación", "danger")
                    return render_template('login.html', correo=correo, password=password)
            
            return render_template('login.html')

        @app.route('/logout', methods=['POST'])
        def logout():
            session.clear()  # elimina la sesión
            return jsonify({'message': 'Sesión cerrada'}), 200

        @app.route('/admin', methods=['GET', 'POST'])
        def admin():
            """Panel del admin"""
            LogShala = session.get('loginS', False)
            
            if not LogShala:
                flash('Acceso restringido. Debes ser administrador.', 'error')
                return redirect(url_for('login'))
            
            correo = session.get('Correo', '')
            nombre = session.get('Nombre', '')
            
            # Procesar acciones POST
            if request.method == 'POST':
                accion = request.form.get('accion')
                
                if accion == 'eliminar_usuario':
                    correo_usuario = request.form.get('correo_usuario')
                    if correo_usuario:
                        cursor = crearCursor()
                        cursor.execute("SELECT Nombre FROM Yoguis WHERE Correo = %s", (correo_usuario,))
                        user_data = cursor.fetchone()
                        cursor.close()
                        
                        if user_data:
                            nombre_usuario = user_data[0]
                            success, message = eliminarYogui(correo_usuario)
                            if success:
                                send_admin_notification(correo_usuario, nombre_usuario, 'usuario_eliminado')
                            flash(message, 'success' if success else 'error')
                        else:
                            flash('❌ Usuario no encontrado', 'error')
                    else:
                        flash('❌ No se proporcionó correo de usuario', 'error')

                elif accion == 'agregar_instructor':
                    correo_instructor = request.form.get('correo', '').strip()
                    password = request.form.get('password', '').strip()
                    nombre_instructor = request.form.get('nombre', '').strip()
                    especialidad = request.form.get('especialidad', '').strip()
                    telefono = request.form.get('telefono', '').strip()
                    experiencia = request.form.get('experiencia', 0)
                    bio = request.form.get('bio', '').strip()
                    foto = None
                    
                    try:
                        validar_email(correo_instructor)
                        validar_clave(password)
                        validar_nombre(nombre_instructor)
                        validar_telefono(telefono)
                        
                        if correo_instructor and password and nombre_instructor and telefono:
                            success, message = agregar_instructor(
                                correo_instructor, password, nombre_instructor, especialidad,
                                telefono, experiencia, bio, foto
                            )
                            if success:
                                registrar_comensal((correo_instructor, password, nombre_instructor, '', telefono))
                                send_admin_notification(correo_instructor, nombre_instructor, 'instructor_agregado')
                            flash(message, 'success' if success else 'error')
                        else:
                            flash('❌ Campos obligatorios faltantes', 'error')
                            
                    except ValidacionError as e:
                        flash(str(e), 'error')
                        
                elif accion == 'editar_instructor':
                    correo_instructor = request.form.get('correo_original')
                    nombre_instructor = request.form.get('nombre', '').strip()
                    especialidad = request.form.get('especialidad', '').strip()
                    telefono = request.form.get('telefono', '').strip()
                    experiencia = request.form.get('experiencia', 0)
                    bio = request.form.get('bio', '').strip()
                    foto = None
                    
                    try:
                        validar_nombre(nombre_instructor)
                        validar_telefono(telefono)
                        
                        if correo_instructor and nombre_instructor and telefono:
                            success, message = editar_instructor(
                                correo_instructor, nombre_instructor, especialidad,
                                telefono, experiencia, bio, foto
                            )
                            flash(message, 'success' if success else 'error')
                        else:
                            flash('❌ Campos obligatorios faltantes', 'error')
                            
                    except ValidacionError as e:
                        flash(str(e), 'error')
                        
                elif accion == 'eliminar_instructor':
                    correo_instructor = request.form.get('correo_instructor')
                    
                    if correo_instructor:
                        try:
                            cursor = crearCursor()
                            cursor.execute("SELECT nombre FROM Instructores WHERE correo = %s", (correo_instructor,))
                            instructor_data = cursor.fetchone()
                            cursor.close()
                            
                            if instructor_data:
                                nombre_instructor = instructor_data[0]
                                success, message = eliminarIntructor(correo_instructor)
                                if success:
                                    send_admin_notification(correo_instructor, nombre_instructor, 'instructor_eliminado')
                                flash(message, 'success' if success else 'error')
                            else:
                                flash('❌ Instructor no encontrado', 'error')
                        except Exception as e:
                            flash(f'Error: {str(e)}', 'error')
                    else:
                        flash('❌ No se proporcionó correo del instructor', 'error')
                        
                elif accion == 'agregar_clases':
                    correo_usuario = request.form.get('correo_usuario')
                    clases_a_agregar = int(request.form.get('clases', 0))
                    
                    if clases_a_agregar > 0:
                        cursor = crearCursor()
                        try:
                            cursor.execute("SELECT Nombre, COALESCE(clasesRestantes, 0) FROM Yoguis WHERE Correo = %s", (correo_usuario,))
                            resultado = cursor.fetchone()
                            
                            if resultado:
                                nombre_usuario = resultado[0]
                                clases_actuales = resultado[1]
                                total_clases = clases_actuales + clases_a_agregar

                                success = actualizar_paquete_yogui(correo_usuario, total_clases)
                                
                                if success:
                                    detalles = {'cantidad': clases_a_agregar, 'total': total_clases}
                                    send_admin_notification(correo_usuario, nombre_usuario, 'clases_agregadas', detalles)
                                    flash(f'✅ Se agregaron {clases_a_agregar} clases. Total: {total_clases} clases', 'success')
                                else:
                                    flash(f'❌ Error al actualizar las clases', 'error')
                            else:
                                flash('❌ Usuario no encontrado', 'error')
                                
                        except Exception as e:
                            flash(f'❌ Error: {str(e)}', 'error')
                        finally:
                            cursor.close()
                    else:
                        flash('❌ Debes especificar un número válido de clases (mayor a 0)', 'error')
                        
                elif accion == 'cancelar_reservas':
                    correo_usuario = request.form.get('correo_usuario')
                    if correo_usuario:
                        success, message = cancelar_todas_reservas_usuario(correo_usuario)
                        flash(message, 'success' if success else 'error')
                    else:
                        flash('❌ No se proporcionó correo de usuario', 'error')
                        
                elif accion == 'buscar':
                    termino = request.form.get('termino_busqueda', '').strip()
                    if termino:
                        return redirect(url_for('admin', busqueda=termino, tab=request.args.get('tab', 'usuarios')))
                    else:
                        return redirect(url_for('admin', tab=request.args.get('tab', 'usuarios')))
            
                elif accion == 'confirmar_pago':
                    id_pago = request.form.get('id_pago')
                    if id_pago:
                        success, message = confirmar_pago(id_pago)
                        flash(message, 'success' if success else 'error')
                    else:
                        flash('❌ No se proporcionó ID de pago', 'error')
                    
                elif accion == 'rechazar_pago':
                    id_pago = request.form.get('id_pago')
                    if id_pago:
                        success, message = rechazar_pago(id_pago)
                        flash(message, 'success' if success else 'error')
                    else:
                        flash('❌ No se proporcionó ID de pago', 'error')
                
                return redirect(url_for('admin', tab=request.form.get('tab_actual', 'usuarios')))
            
            # GET request
            termino_busqueda = request.args.get('busqueda', '')
            tab_activa = request.args.get('tab', 'usuarios')
            
            if termino_busqueda:
                usuarios = buscar_usuarios(termino_busqueda)
            else:
                usuarios = leerTodosLosYogui()
            
            instructores = leerInstructores()
            estadisticas = obtener_estadisticas_generales()
            
            # Obtener pagos pendientes y confirmados
            pagos_pendientes = obtener_pagos_pendientes()
            pagos_confirmados = obtener_pagos_confirmados()
            
            # Obtener datos para reportes
            from datetime import datetime
            from Operaciones.CRUD.Leer import obtener_ventas_por_mes, obtener_ventas_por_dia_semana, obtener_meses_disponibles
            
            meses_disponibles = obtener_meses_disponibles()
            
            # Si no hay meses disponibles, usar mes actual
            if not meses_disponibles:
                hoy = datetime.now()
                meses_disponibles = [{'año': hoy.year, 'mes': hoy.month, 'nombre': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][hoy.month-1], 'valor': f"{hoy.year}-{hoy.month:02d}"}]
            
            # Obtener mes seleccionado (por defecto el primero de la lista)
            mes_seleccionado = request.args.get('mes', meses_disponibles[0]['valor'])
            año_seleccionado, mes_seleccionado_num = map(int, mes_seleccionado.split('-'))
            
            datos_ventas = obtener_ventas_por_mes(mes_seleccionado_num, año_seleccionado)
            ventas_por_dia = obtener_ventas_por_dia_semana(mes_seleccionado_num, año_seleccionado)
            
            return render_template('admin.html',
                                LogShala=LogShala,
                                correo=correo,
                                nombre=nombre,
                                usuarios=usuarios,
                                instructores=instructores,
                                estadisticas=estadisticas,
                                pagos_pendientes=pagos_pendientes,
                                pagos_confirmados=pagos_confirmados,
                                termino_busqueda=termino_busqueda,
                                tab_activa=tab_activa,
                                meses_disponibles=meses_disponibles,
                                mes_seleccionado=mes_seleccionado,
                                datos_ventas=datos_ventas,
                                ventas_por_dia=ventas_por_dia)
            
        @app.route('/admin/clases-instructor', methods=['POST'])
        def admin_clases_instructor():
            """Obtiene las clases de un instructor"""
            LogShala = session.get('loginS', False)
            
            if not LogShala:
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            instructor_email = request.form.get('instructor_email')
            
            if not instructor_email:
                return jsonify({'success': False, 'message': 'Falta email del instructor'}), 400
            
            from Operaciones.Scripts.google_services import get_instructor_classes
            
            clases = get_instructor_classes(instructor_email, days_ahead=120)
            
            return jsonify({'success': True, 'clases': clases})

        @app.route('/admin/cancelar-clase', methods=['POST'])
        def admin_cancelar_clase():
            """Cancela todas las reservas de una clase"""
            LogShala = session.get('loginS', False)
            
            if not LogShala:
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            event_id = request.form.get('event_id')
            instructor_email = request.form.get('instructor_email')
            
            if not event_id or not instructor_email:
                return jsonify({'success': False, 'message': 'Faltan datos'}), 400
            
            success, message = cancelar_todas_reservas_clase(event_id, instructor_email)
            
            return jsonify({'success': success, 'message': message})
        
        @app.route('/admin/eliminar-todas-clases-instructor', methods=['POST'])
        def admin_eliminar_todas_clases_instructor():
            """Elimina TODAS las clases de un instructor"""
            LogShala = session.get('loginS', False)
            
            if not LogShala:
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            correo_instructor = request.form.get('correo_instructor')
            
            if not correo_instructor:
                return jsonify({'success': False, 'message': 'Falta correo del instructor'}), 400
            
            from Operaciones.CRUD.Borrar import eliminar_todas_clases_instructor
            
            success, message = eliminar_todas_clases_instructor(correo_instructor)
            
            return jsonify({'success': success, 'message': message})
        
        @app.route('/admin/exportar-reporte', methods=['POST'])
        def exportar_reporte():
            """Exporta el reporte de ventas a PDF"""
            LogShala = session.get('loginS', False)
            
            if not LogShala:
                flash('Acceso restringido. Debes ser administrador.', 'error')
                return redirect(url_for('login'))
            
            mes = int(request.form.get('mes'))
            año = int(request.form.get('año'))
                        
            datos_ventas = obtener_ventas_por_mes(mes, año)
            ventas_por_dia = obtener_ventas_por_dia_semana(mes, año)
            
            if ventas_por_dia is None:
                flash('Error al generar el reporte', 'error')
                return redirect(url_for('admin', tab='reportes'))
            
            pdf_buffer = generar_reporte_pdf(mes, año, datos_ventas, ventas_por_dia)
            
            meses_nombres = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            mes_nombre = meses_nombres[mes]
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=f'reporte_ventas_{mes_nombre}_{año}.pdf',
                mimetype='application/pdf'
            )
        
        @app.route('/registro', methods=['GET', 'POST'])
        def registro():
            if request.method == 'POST':
                accion = request.form.get('accion')
                
                correo = request.form.get('correo', '').strip()
                password = request.form.get('password', '').strip()
                nombre = request.form.get('nombre', '').strip()
                apellido = request.form.get('apellido', '').strip()
                telefono_str = request.form.get('telefono', '').strip()
                codigo_ingresado = request.form.get('codigo', '').strip()
                
                # PASO 1: Enviar código de verificación
                if accion == 'enviar_codigo':
                    try:
                        # Validar email
                        validar_email(correo)
                        
                        # Verificar si el correo ya está registrado
                        cursor = crearCursor()
                        cursor.execute("SELECT Correo FROM Yoguis WHERE Correo = %s", (correo,))
                        if cursor.fetchone():
                            cursor.close()
                            flash("❌ Este correo ya está registrado", "danger")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=False)
                        cursor.close()
                        
                        # Generar código
                        codigo = generarCodigo(correo)
                        
                        # Enviar el código
                        if enviarCodigo(correo, codigo):
                            # Guardar en session
                            session['codigo_verificacion'] = codigo
                            session['correo_verificacion'] = correo
                            session['tiempo_envio'] = datetime.now().isoformat()
                            
                            flash(f"✅ Código enviado a {correo}. Revisa tu bandeja de entrada o spam.", "success")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=True)
                        else:
                            flash("❌ Error al enviar el código. Intenta de nuevo.", "danger")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=False)
                            
                    except ValidacionError as er:
                        flash(str(er), "danger")
                        return render_template('registro.html',
                            correo=correo,
                            password=password,
                            nombre=nombre,
                            apellido=apellido,
                            telefono=telefono_str,
                            mostrar_codigo=False)
                            
                    except Exception as e:
                        flash(f"Error: {str(e)}", "danger")
                        return render_template('registro.html',
                            correo=correo,
                            password=password,
                            nombre=nombre,
                            apellido=apellido,
                            telefono=telefono_str,
                            mostrar_codigo=False)
                
                # PASO 2: Completar registro
                elif accion == 'registrar':
                    try:
                        # Verificar que se haya enviado un código
                        if 'codigo_verificacion' not in session:
                            flash("Debes solicitar un código de verificación primero", "danger")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=False)
                        
                        # Verificar que el correo coincida
                        if session['correo_verificacion'] != correo:
                            flash("El correo ha cambiado. Solicita un nuevo código", "danger")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=True)
                        
                        # Verificar expiración (10 minutos)
                        if 'tiempo_envio' in session:
                            tiempo_envio = datetime.fromisoformat(session['tiempo_envio'])
                            if datetime.now() - tiempo_envio > timedelta(minutes=10):
                                flash("❌ El código ha expirado. Solicita uno nuevo.", "danger")
                                session.pop('codigo_verificacion', None)
                                session.pop('correo_verificacion', None)
                                return render_template('registro.html',
                                    correo=correo,
                                    password=password,
                                    nombre=nombre,
                                    apellido=apellido,
                                    telefono=telefono_str,
                                    mostrar_codigo=False)
                        
                        # Verificar el código
                        if codigo_ingresado != session['codigo_verificacion']:
                            flash("❌ Código de verificación incorrecto", "danger")
                            return render_template('registro.html',
                                correo=correo,
                                password=password,
                                nombre=nombre,
                                apellido=apellido,
                                telefono=telefono_str,
                                mostrar_codigo=True)
                        
                        # Validar todos los campos
                        validar_telefono(telefono_str)
                        validar_clave(password)
                        validar_nombre(nombre)
                        validar_nombre(apellido)
                        
                        # Registrar usuario
                        telefono = int(telefono_str)
                        c = Yogui(correo, password, nombre, apellido, telefono)
                        c.crearComensales()
                        
                        # Limpiar session
                        session.pop('codigo_verificacion', None)
                        session.pop('correo_verificacion', None)
                        session.pop('tiempo_envio', None)
                        
                        # Iniciar sesión automáticamente
                        session['loginY'] = True
                        session['Correo'] = correo
                        session['Nombre'] = nombre
                        session['Telefono'] = telefono
                        
                        flash("✅ ¡Registro exitoso! Bienvenido a ZenFlow Yoga", "success")
                        return redirect(url_for('index'))
                        
                    except ValidacionError as er:
                        flash(str(er), "danger")
                        return render_template('registro.html', 
                            correo=correo, 
                            password=password, 
                            nombre=nombre, 
                            apellido=apellido, 
                            telefono=telefono_str,
                            mostrar_codigo=True if 'codigo_verificacion' in session else False)
                            
                    except Exception as e:
                        error_msg = str(e)
                        if 'Duplicate' in error_msg or 'duplicate' in error_msg:
                            flash("❌ El correo ya está registrado.", "danger")
                        else:
                            flash(f"❌ Error en el registro: {error_msg}", "danger")
                        return render_template('registro.html', 
                            correo=correo, 
                            password=password, 
                            nombre=nombre, 
                            apellido=apellido, 
                            telefono=telefono_str,
                            mostrar_codigo=True if 'codigo_verificacion' in session else False)
            
            # GET request
            session.pop('codigo_verificacion', None)
            session.pop('correo_verificacion', None)
            session.pop('tiempo_envio', None)
            return render_template('registro.html')

        @app.route('/contacto')
        def contacto():
            logYogui = session.get('loginY', False)
            LogShala = session.get('loginS', False)
            LogInst = session.get('loginI', False)

            return render_template('contacto.html', logYogui = logYogui  , LogShala = LogShala, LogInst = LogInst)
              
        @app.route('/registroInstructor', methods=['GET', 'POST'])
        def registroInstructor():
            if request.method == 'POST':
                accion = request.form.get('accion')
                correo = request.form.get('correo', '').strip()
                codigo_ingresado = request.form.get('codigo', '').strip()
                
                if accion == 'enviar_codigo':
                    try:
                        validar_email(correo)
                        
                        codigo = generarCodigo(correo)
                        enviarCodigo(correo, codigo)
                        
                        session['codigo_verificacion_instructor'] = codigo
                        session['correo_verificacion_instructor'] = correo
                        session['timestamp_envio_instructor'] = datetime.now().isoformat()
                        
                        flash("✅ Código de verificación enviado", "success")
                        return render_template('registroInstructor.html',
                            correo=correo,
                            mostrar_codigo=True)
                            
                    except ValidacionError as e:
                        flash(str(e), "danger")
                        return render_template('registroInstructor.html',
                            correo=correo,
                            mostrar_codigo=False)
                
                elif accion == 'verificar_codigo':
                    try:
                        if 'codigo_verificacion_instructor' not in session:
                            flash("Debes solicitar un código primero", "danger")
                            return render_template('registroInstructor.html',
                                correo=correo,
                                mostrar_codigo=False)
                        
                        if session['correo_verificacion_instructor'] != correo:
                            flash("El correo ha cambiado. Solicita un nuevo código", "danger")
                            return render_template('registroInstructor.html',
                                correo=correo,
                                mostrar_codigo=True)
                        
                        codigo_correcto = session['codigo_verificacion_instructor']
                        if codigo_ingresado != codigo_correcto:
                            flash("❌ Código incorrecto", "danger")
                            return render_template('registroInstructor.html',
                                correo=correo,
                                mostrar_codigo=True,
                                codigo_ingresado=codigo_ingresado)
                        
                        session['correo_verificado_instructor'] = correo
                        flash("✅ Correo verificado exitosamente", "success")
                        return render_template('registroInstructor.html',
                            correo_verificado=True,
                            correo=correo)
                        
                    except Exception as e:
                        flash(f"Error en verificación: {str(e)}", "danger")
                        return render_template('registroInstructor.html',
                            correo=correo,
                            mostrar_codigo=True)
                
                elif accion == 'completar_registro':
                    try:
                        if 'correo_verificado_instructor' not in session:
                            flash("Debes verificar tu correo primero", "danger")
                            return redirect(url_for('registroInstructor'))
                        
                        if session['correo_verificado_instructor'] != correo:
                            flash("Correo no coincide con la verificación", "danger")
                            return redirect(url_for('registroInstructor'))
                        
                        if 'cv_pdf' not in request.files:
                            flash("Debes subir tu currículum", "danger")
                            return render_template('registroInstructor.html',
                                correo_verificado=True,
                                correo=correo)
                        
                        cv_file = request.files['cv_pdf']
                        
                        if cv_file.filename == '':
                            flash("No se seleccionó ningún archivo", "danger")
                            return render_template('registroInstructor.html',
                                correo_verificado=True,
                                correo=correo)
                        
                        resultado = procesar_curriculum(correo, cv_file)
                        
                        if resultado['success']:
                            session.pop('codigo_verificacion_instructor', None)
                            session.pop('correo_verificacion_instructor', None)
                            session.pop('correo_verificado_instructor', None)
                            
                            flash("✅ Registro completado. Nos pondremos en contacto contigo pronto.", "success")
                            return redirect(url_for('index'))
                        else:
                            flash(f"Error al procesar CV: {resultado['error']}", "danger")
                            return render_template('registroInstructor.html',
                                correo_verificado=True,
                                correo=correo)
                            
                    except Exception as e:
                        flash(f"Error en el registro: {str(e)}", "danger")
                        return render_template('registroInstructor.html',
                            correo_verificado=True,
                            correo=correo)
            
            if request.args.get('reset'):
                session.pop('codigo_verificacion_instructor', None)
                session.pop('correo_verificacion_instructor', None)
                session.pop('correo_verificado_instructor', None)
            
            if 'correo_verificado_instructor' in session:
                return render_template('registroInstructor.html',
                    correo_verificado=True,
                    correo=session['correo_verificado_instructor'])
            
            if 'correo_verificacion_instructor' in session:
                return render_template('registroInstructor.html',
                    correo=session['correo_verificacion_instructor'],
                    mostrar_codigo=True)
            
            return render_template('registroInstructor.html')
        
        @app.route('/reservas', methods=['GET', 'POST'])
        def reservas():
            """Página principal de reservas con Google Calendar"""
            
            logYogui = session.get('loginY', False)
            LogShala = session.get('loginS', False)
            LogInst = session.get('loginI', False)
            
            correo = session.get('Correo', '')
            nombre = session.get('Nombre', '')
            estaLog = bool(correo)
            
            # Obtener clases disponibles
            if request.method == 'POST':
                # Procesar reserva
                if not estaLog:
                    flash('Debes iniciar sesión para hacer una reserva', 'error')
                    return redirect(url_for('login'))
                
                event_id = request.form.get('event_id')
                reservas_multiples = request.form.get('reservas_multiples') == 'true'
                semanas = int(request.form.get('semanas', 1))
                
                if not event_id:
                    flash('No se seleccionó ninguna clase', 'error')
                    return redirect(url_for('reservas'))
                
                # Verificar que el usuario tenga clases disponibles
                cursor = crearCursor()
                try:
                    cursor.execute("SELECT clasesRestantes FROM Yoguis WHERE Correo = %s", (correo,))
                    resultado = cursor.fetchone()
                    
                    if not resultado or resultado[0] <= 0:
                        flash('No tienes clases disponibles. Compra un paquete primero.', 'error')
                        return redirect(url_for('paquetes'))
                    
                    # Verificar que tenga suficientes clases para reserva múltiple
                    if reservas_multiples and resultado[0] < semanas:
                        flash(f'No tienes suficientes clases. Necesitas {semanas} clases y tienes {resultado[0]}.', 'error')
                        return redirect(url_for('reservas'))
                    
                    # Hacer reserva en Google Calendar
                    success, message = reserve_yoga_class(event_id, correo, nombre, reservas_multiples, semanas)
                    
                    if success:
                        # Restar las clases al usuario
                        clases_a_restar = semanas if reservas_multiples else 1
                        nuevas_clases = resultado[0] - clases_a_restar
                        actualizar_paquete_yogui(correo, nuevas_clases)
                        
                        if reservas_multiples:
                            flash(f'✅ Reserva múltiple exitosa. Se reservaron {semanas} clases.', 'success')
                        else:
                            flash('✅ Reserva exitosa. Revisa tu correo para la confirmación.', 'success')
                    else:
                        flash(f'❌ Error al reservar: {message}', 'error')
                        
                except Exception as e:
                    flash(f'Error al procesar la reserva: {str(e)}', 'error')
                finally:
                    cursor.close()
                
                return redirect(url_for('reservas'))
            
            # GET request - mostrar clases disponibles
            clases = []
            clases_filtradas = []
            fecha_filtro = request.args.get('fecha', '')
            instructor_filtro = request.args.get('instructor', '')
            
            try:
                from datetime import datetime
                clases = get_yoga_classes_from_calendar(days_ahead=120)
                
                # Procesar cada clase para añadir formato de fecha y modalidad
                for clase in clases:
                    clase['is_hibrida'] = clase.get('is_hibrida', False)
                    clase['meet_link'] = clase.get('meet_link', None)
                    
                    # Formatear fecha para mostrar
                    try:
                        fecha_obj = datetime.strptime(clase['date'], '%Y-%m-%d')
                        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                        clase['fecha_formateada'] = f"{fecha_obj.day} de {meses[fecha_obj.month-1]}"
                    except:
                        clase['fecha_formateada'] = clase['date']
                
                # Aplicar filtros
                for clase in clases:
                    if fecha_filtro and clase['date'] != fecha_filtro:
                        continue
                    if instructor_filtro and instructor_filtro.lower() not in clase['instructor'].lower():
                        continue
                    
                    if clase['available_spots'] > 0:
                        clases_filtradas.append(clase)
                
                print(f"✅ {len(clases_filtradas)} clases disponibles después de filtrar")
                
            except Exception as e:
                print(f"❌ Error al cargar clases: {e}")
                flash(f'Error al cargar clases: {str(e)}', 'error')
            
            # Obtener clases restantes del usuario
            clases_restantes = 0
            if estaLog:
                cursor = crearCursor()
                try:
                    cursor.execute("SELECT clasesRestantes FROM Yoguis WHERE Correo = %s", (correo,))
                    resultado = cursor.fetchone()
                    if resultado and resultado[0] is not None:
                        clases_restantes = resultado[0]
                    else:
                        clases_restantes = 0
                except Exception as e:
                    print(f"Error al obtener clases restantes: {e}")
                finally:
                    cursor.close()
            
            # Obtener instructores únicos para el filtro
            instructores = sorted(list(set([clase['instructor'] for clase in clases if clase['instructor']])))
            
            # Obtener fecha de hoy para el filtro
            from datetime import date
            hoy = date.today().isoformat()
            
            return render_template('reservas.html',
                                logYogui=logYogui,
                                LogShala=LogShala,
                                LogInst=LogInst,
                                correo=correo,
                                nombre=nombre,
                                estaLog=estaLog,
                                clases=clases_filtradas,
                                clases_restantes=clases_restantes,
                                fecha_filtro=fecha_filtro,
                                instructor_filtro=instructor_filtro,
                                instructores=instructores,
                                hoy=hoy)

        @app.route('/paquetes', methods=['GET', 'POST'])
        def paquetes():
            if request.method == 'POST':
                accion = request.form.get('accion')
                
                if accion == 'pago_pendiente':
                    id_paquete = request.form.get('id_paquete')
                    precio = request.form.get('precio')
                    clases = request.form.get('clases')  
                    correo = request.form.get('correo')
                    metodo_pago = request.form.get('metodo_pago')
                    referencia = request.form.get('referencia')
                    
                    print(f"📝 Nuevo pago pendiente: id_paquete={id_paquete}, metodo={metodo_pago}, ref={referencia}, monto=${precio}")
                    
                    # Validar que el usuario esté logueado
                    if not (session.get('loginY') or session.get('loginS') or session.get('loginI')):
                        flash('Debes iniciar sesión para comprar un paquete', 'error')
                        return redirect(url_for('login'))
                    
                    # Validar datos recibidos
                    if not all([id_paquete, precio, clases, correo, metodo_pago, referencia]):
                        flash('❌ Datos incompletos para el pago', 'error')
                        return redirect(url_for('paquetes'))
                    
                    try:
                        # Validar que el correo de la sesión coincida
                        correo_sesion = session.get('Correo')
                        if correo_sesion != correo:
                            flash('❌ Error de seguridad: el correo no coincide con la sesión', 'error')
                            return redirect(url_for('paquetes'))
                        
                        # Obtener nombre del usuario
                        cursor = crearCursor()
                        cursor.execute("SELECT Nombre FROM Yoguis WHERE Correo = %s", (correo,))
                        user_data = cursor.fetchone()
                        cursor.close()
                        
                        nombre_usuario = user_data[0] if user_data else correo
                        
                        from Operaciones.CRUD.Agregar import insertar_pago
                        
                        # Insertar nuevo pago en Pagos (incluye metodo_pago)
                        success, id_pago = insertar_pago(correo, referencia, id_paquete, float(precio), metodo_pago)
                        
                        if success:
                            # ENVIAR NOTIFICACIÓN AL ADMIN
                            from Operaciones.Scripts.google_services import send_admin_compra_notification
                            send_admin_compra_notification(
                                usuario_email=correo,
                                usuario_nombre=nombre_usuario,
                                paquete_id=id_paquete,
                                monto=float(precio),
                                metodo_pago=metodo_pago,
                                referencia=referencia
                            )
                            
                            flash(f'✅ Pago registrado exitosamente. ID de pago: {id_pago} - Método: {metodo_pago} - Referencia: {referencia} - Monto: ${precio}', 'success')
                            return redirect(url_for('index'))
                        else:
                            flash('❌ Error al registrar el pago', 'error')
                            return redirect(url_for('paquetes'))
                        
                    except Exception as e:
                        print(f"❌ Error al procesar pago: {e}")
                        flash(f'❌ Error al procesar el pago: {str(e)}', 'error')
                        return redirect(url_for('paquetes'))
                
                else:
                    # COMPRA DIRECTA (código existente)
                    id_paquete = request.form.get('id_paquete')
                    precio = request.form.get('precio')
                    clases = request.form.get('clases')  
                    correo = request.form.get('correo')
                    
                    print(f"Datos recibidos: id_paquete={id_paquete}, precio={precio}, clases={clases}, correo={correo}")
                    
                    # Validar que el usuario esté logueado
                    if not (session.get('loginY') or session.get('loginS') or session.get('loginI')):
                        flash('Debes iniciar sesión para comprar un paquete', 'error')
                        return redirect(url_for('login'))
                    
                    # Validar datos recibidos
                    if not id_paquete or not precio or not clases or not correo:
                        flash('Datos incompletos para la compra', 'error')
                        return redirect(url_for('paquetes'))
                    
                    try:
                        correo_sesion = session.get('Correo')
                        if correo_sesion != correo:
                            flash('Error de seguridad: el correo no coincide con la sesión', 'error')
                            return redirect(url_for('paquetes'))
                        
                        from Operaciones.CRUD.Editar import actualizar_paquete_yogui
                        
                        cursor = crearCursor()
                        cursor.execute("SELECT clasesRestantes FROM Yoguis WHERE Correo = %s", (correo,))
                        resultado = cursor.fetchone()
                        clases_restantes = resultado[0] if resultado[0] is not None else 0
                        cursor.close()
                        
                        clases_totales = int(clases) + clases_restantes
                        
                        if actualizar_paquete_yogui(correo, int(clases_totales)):
                            flash(f'¡Compra exitosa! Paquete {id_paquete} asignado ({clases_totales} clases).', 'success')
                        else:
                            flash('Error al procesar la compra', 'error')
                        
                    except Exception as e:
                        flash(f'Error inesperado: {str(e)}', 'error')
                        print(f"Error en compra: {e}")
                    
                    return redirect(url_for('paquetes'))
            
            else:
                # GET normal para mostrar los paquetes
                logYogui = session.get('loginY', False)
                LogShala = session.get('loginS', False)
                LogInst = session.get('loginI', False)
                from Operaciones.CRUD.Leer import leerPaquetes
                paquetes = leerPaquetes()
                
                correo = ""
                estaLog = False
                if logYogui or LogInst or LogShala: 
                    correo = session.get('Correo', '')
                    estaLog = True
                
                # Verificar pagos pendientes para este usuario
                pagos_pendientes = []
                if estaLog:
                    try:
                        cursor = crearCursor()
                        cursor.execute("""
                            SELECT id_pago, Referencia, paqueteID, monto, fecha_pago, metodo_pago 
                            FROM Pagos 
                            WHERE Correo = %s AND EstadoDePago = 'pendiente'
                            ORDER BY fecha_pago DESC
                        """, (correo,))
                        pagos_pendientes = cursor.fetchall()
                        cursor.close()
                    except Exception as e:
                        print(f"Error al consultar pagos pendientes: {e}")
                        pass
                
                return render_template('paquetes.html', 
                                    logYogui=logYogui, 
                                    LogShala=LogShala, 
                                    LogInst=LogInst, 
                                    correo=correo, 
                                    estaLog=estaLog, 
                                    paquetes=paquetes,
                                    pagos_pendientes=pagos_pendientes)
                        
        @app.route('/instructor', methods=['GET', 'POST'])
        def instructor():
            """Panel de instructor"""
            
            LogInst = session.get('loginI', False)
            
            if not LogInst:
                flash('Acceso restringido', 'error')
                return redirect(url_for('login'))
            
            correo = session.get('Correo', '')
            nombre = session.get('Nombre', '')
            
            # Verificar instructor
            if not es_instructor(correo):
                flash('No tienes permisos', 'error')
                return redirect(url_for('index'))
            
            # Obtener info del instructor
            instructor_info = obtener_instructor(correo)
            
            # PROCESAR POST (crear clase)
            if request.method == 'POST':
                action = request.form.get('action')
                
                if action == 'add_class':
                    try:
                        # Obtener datos del formulario
                        title = request.form.get('title', '').strip()
                        class_date = request.form.get('date', '').strip()
                        start_time = request.form.get('start_time', '').strip()
                        duration = int(request.form.get('duration', 60))
                        capacity = int(request.form.get('capacity', 20))
                        is_hibrida = request.form.get('is_hibrida') == 'true'
                        recurrence = request.form.get('recurrence', 'none')
                        
                        # Validar
                        if not title or not class_date or not start_time:
                            flash('❌ Faltan campos obligatorios', 'error')
                            return redirect(url_for('instructor'))
                        
                        # Validar teléfono si se proporciona (para el instructor)
                        telefono = request.form.get('telefono', '').strip()
                        if telefono:
                            try:
                                validar_telefono(telefono)
                            except ValidacionError as e:
                                flash(str(e), 'error')
                                return redirect(url_for('instructor'))
                        
                        # Crear fechas base
                        start_datetime = f"{class_date}T{start_time}:00"
                        end_datetime = (datetime.fromisoformat(start_datetime) + timedelta(minutes=duration)).isoformat()
                        
                        # Datos de la clase
                        class_data = {
                            'title': title,
                            'start_datetime': start_datetime,
                            'end_datetime': end_datetime,
                            'capacity': capacity,
                            'duration': duration,
                            'tipo': request.form.get('type', 'Vinyasa'),
                            'nivel': request.form.get('level', 'Todos'),
                            'location': request.form.get('location', 'Estudio Principal'),
                            'description': request.form.get('description', ''),
                            'modalidad': 'hibrida' if is_hibrida else 'presencial'
                        }
                        
                        # Si es recurrente, usar función especial
                        if recurrence != 'none':
                            from Operaciones.Scripts.google_services import get_recurrence_rule, create_recurring_class
                            
                            recurrence_rule = get_recurrence_rule(class_date, recurrence)
                            
                            if recurrence_rule:
                                success, message, meet_link = create_recurring_class(
                                    correo, nombre, class_data, recurrence_rule
                                )
                                
                                if success:
                                    flash(f'✅ {message}', 'success')
                                else:
                                    flash(f'❌ {message}', 'error')
                            else:
                                flash('❌ Tipo de recurrencia no válido', 'error')
                        else:
                            # Clase normal (una sola vez)
                            from Operaciones.Scripts.google_services import instructor_add_class_with_meet
                            success, message, _ = instructor_add_class_with_meet(correo, nombre, class_data)
                            
                            if success:
                                flash('✅ Clase creada exitosamente', 'success')
                            else:
                                flash(f'❌ {message}', 'error')
                        
                    except Exception as e:
                        flash(f'❌ Error: {str(e)}', 'error')
                    
                    return redirect(url_for('instructor'))
                
                elif action == 'cancel_class':
                    event_id = request.form.get('event_id')
                    if event_id:
                        from Operaciones.CRUD.Borrar import cancelar_todas_reservas_clase
                        
                        success, message = cancelar_todas_reservas_clase(
                            event_id, correo, 
                            eliminar_evento=True, 
                            motivo="Cancelación por el instructor"
                        )
                        
                        if success:
                            flash(message, 'success')
                        else:
                            flash(f'❌ {message}', 'error')
                            
                    return redirect(url_for('instructor'))
            
            # Obtener todas las clases
            todas_clases = get_instructor_classes(correo, days_ahead=120)
            
            # Debug: imprimir información de las clases
            print(f"📊 Total clases encontradas: {len(todas_clases)}")
            for i, clase in enumerate(todas_clases):
                print(f"  Clase {i+1}: {clase.get('title')} - Asistentes: {clase.get('current_attendees', 0)} - Capacidad: {clase.get('capacity', 20)}")
            
            ahora = datetime.now()
            
            clases_futuras = []
            clases_pasadas = []
            total_alumnos = 0
            capacidad_total = 0
            
            for clase in todas_clases:
                try:
                    # Determinar si es futura o pasada
                    es_futura = False
                    
                    if clase.get('start_datetime'):
                        try:
                            fecha_clase = datetime.fromisoformat(clase['start_datetime'].replace('Z', '+00:00'))
                            es_futura = fecha_clase > ahora
                        except:
                            # Si hay error con el formato, intentar con date
                            if clase.get('date'):
                                fecha_clase = datetime.strptime(clase['date'], '%Y-%m-%d')
                                es_futura = fecha_clase.date() >= ahora.date()
                            else:
                                es_futura = True  # Por defecto, mostrar como futura
                    elif clase.get('date'):
                        fecha_clase = datetime.strptime(clase['date'], '%Y-%m-%d')
                        es_futura = fecha_clase.date() >= ahora.date()
                    else:
                        es_futura = True
                    
                    # Obtener asistentes y capacidad (con valores por defecto)
                    asistentes = clase.get('current_attendees', 0)
                    if asistentes is None:
                        asistentes = 0
                        
                    capacidad = clase.get('capacity', 20)
                    if capacidad is None:
                        capacidad = 20
                    
                    if es_futura:
                        clases_futuras.append(clase)
                        total_alumnos += asistentes
                        capacidad_total += capacidad
                    else:
                        clases_pasadas.append(clase)
                        
                except Exception as e:
                    print(f"Error procesando clase: {e}")
                    # En caso de error, mostrar como futura
                    clases_futuras.append(clase)
                    total_alumnos += clase.get('current_attendees', 0)
                    capacidad_total += clase.get('capacity', 20)
            
            # Ordenar
            clases_futuras.sort(key=lambda x: x.get('start_datetime', x.get('date', '')))
            clases_pasadas.sort(key=lambda x: x.get('start_datetime', x.get('date', '')), reverse=True)
            
            # Calcular ocupación promedio (evitar división por cero)
            if capacidad_total > 0:
                ocupacion = (total_alumnos / capacidad_total) * 100
            else:
                ocupacion = 0
            
            print(f"📊 Resumen: {len(clases_futuras)} futuras, {len(clases_pasadas)} pasadas")
            print(f"📊 Total alumnos: {total_alumnos}, Capacidad total: {capacidad_total}, Ocupación: {ocupacion:.1f}%")
            
            # Obtener fecha de hoy para el formulario
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            return render_template('instructor.html',
                                LogInst=LogInst,
                                correo=correo,
                                nombre=nombre,
                                instructor_info=instructor_info,
                                clases_futuras=clases_futuras,
                                clases_pasadas=clases_pasadas,
                                hoy=hoy,
                                total_alumnos=total_alumnos,
                                ocupacion_promedio=round(ocupacion, 1))
        
        @app.route('/instructor/editar-clase', methods=['POST'])
        def instructor_editar_clase():
            """Edita una clase existente"""
            LogInst = session.get('loginI', False)
            
            if not LogInst:
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            correo = session.get('Correo', '')
            event_id = request.form.get('event_id')
            
            if not event_id:
                return jsonify({'success': False, 'message': 'Falta ID del evento'}), 400
            
            try:

                
                # Recoger datos del formulario
                updated_data = {
                    'title': request.form.get('title'),
                    'start_datetime': request.form.get('start_datetime'),
                    'duration': int(request.form.get('duration', 60)),
                    'location': request.form.get('location'),
                    'description': request.form.get('description')
                }
                
                # Actualizar la clase
                success, message, cambios = update_class(event_id, correo, updated_data)
                
                if success and cambios:
                    # Obtener asistentes para notificar
                    from Operaciones.Scripts.google_services import get_event_attendees
                    attendees = get_event_attendees(event_id)
                    
                    # Obtener detalles de la clase para el email
                    class_title = updated_data.get('title', 'Clase')
                    class_date = updated_data.get('start_datetime', '')[:10]
                    class_time = updated_data.get('start_datetime', '')[11:16]
                    
                    # Notificar a cada asistente
                    for attendee_email in attendees:
                        if attendee_email != correo:  # No notificar al instructor
                            user_data = datosYogui(attendee_email)
                            if user_data:
                                user_name = user_data[1]  # Nombre del usuario
                                send_class_updated_email(
                                    attendee_email, user_name, 
                                    class_title, class_date, class_time, 
                                    cambios
                                )
                    
                    return jsonify({
                        'success': True, 
                        'message': f'✅ Clase actualizada. Se notificó a los alumnos.',
                        'cambios': cambios
                    })
                elif success:
                    return jsonify({'success': True, 'message': '✅ No se realizaron cambios'})
                else:
                    return jsonify({'success': False, 'message': f'❌ {message}'})
                    
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})
           
        @app.route('/instructor/get-class-data/<event_id>')
        def get_class_data(event_id):
            """Obtiene datos de una clase para edición"""
            LogInst = session.get('loginI', False)
            
            if not LogInst:
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            try:
                from Operaciones.Scripts.google_services import get_calendar_service
                from datetime import datetime
                
                service = get_calendar_service()
                event = service.events().get(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                
                # Extraer datos relevantes
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Calcular duración
                end = event['end'].get('dateTime', event['end'].get('date'))
                duration = 60  # valor por defecto
                
                if start and end and 'T' in start and 'T' in end:
                    try:
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        duration = int((end_dt - start_dt).total_seconds() / 60)
                    except:
                        pass
                
                # Limpiar descripción para edición
                description = event.get('description', '')
                if 'Google Meet:' in description:
                    description = description.split('Google Meet:')[0].strip()
                
                # Formatear fecha para input datetime-local (YYYY-MM-DDTHH:MM)
                formatted_start = start
                if 'T' in start:
                    # Eliminar zona horaria para el input
                    formatted_start = start.split('+')[0].split('Z')[0][:16]
                
                return jsonify({
                    'success': True,
                    'title': event.get('summary', ''),
                    'start_datetime': formatted_start,
                    'duration': duration,
                    'location': event.get('location', 'Estudio Principal'),
                    'description': description
                })
                
            except Exception as e:
                print(f"Error obteniendo datos de clase: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'message': str(e)}), 500
                
        @app.route('/instructor/start-meet', methods=['POST'])
        def start_meet():
            """Iniciar Google Meet para una clase híbrida"""
            if not session.get('loginI'):
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            event_id = request.form.get('event_id')
            correo = session.get('Correo', '')
            
            success, result = start_meet_for_class(event_id, correo)
            
            if success:
                return jsonify({'success': True, 'meet_link': result})
            else:
                return jsonify({'success': False, 'message': result})

        @app.route('/instructor/send-meet-reminders', methods=['POST'])
        def send_meet_reminders():
            """Enviar recordatorios de Google Meet para clase híbrida"""
            if not session.get('loginI'):
                return jsonify({'success': False, 'message': 'No autorizado'}), 401
            
            event_id = request.form.get('event_id')
            correo = session.get('Correo', '')
            
            try:
                # Obtener el evento para extraer información
                service = get_calendar_service()
                event = service.events().get(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                
                # Verificar que sea clase híbrida y del instructor
                if 'Modalidad: Híbrida' not in event.get('description', ''):
                    return jsonify({'success': False, 'message': 'Esta no es una clase híbrida'})
                
                if correo not in event.get('description', ''):
                    return jsonify({'success': False, 'message': 'No eres el instructor de esta clase'})
                
                # Obtener link de Meet
                meet_link = get_event_meet_link(event_id)
                if not meet_link:
                    return jsonify({'success': False, 'message': 'No hay enlace de Google Meet configurado'})
                
                # Obtener asistentes
                attendees = event.get('attendees', [])
                
                # Enviar recordatorios (esto es un ejemplo - ajusta según tu implementación)
                for attendee in attendees:
                    user_email = attendee.get('email')
                    user_name = attendee.get('displayName', 'Alumno')
                    
                    if user_email and attendee.get('responseStatus') != 'declined':
                        # Aquí llamarías a tu función para enviar emails
                        # send_meet_reminder(user_email, event.get('summary', 'Clase de Yoga'), meet_link, event['start'].get('dateTime'))
                        print(f"Enviar recordatorio a: {user_email}")
                
                return jsonify({'success': True, 'message': f'Recordatorios enviados a {len(attendees)} alumnos'})
                
            except Exception as e:
                print(f"Error al enviar recordatorios: {e}")
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})
  
        @app.route('/yogui', methods=['GET', 'POST'])
        def yogui():
            """Panel del yogui - Ver reservas y editar perfil"""
            
            logYogui = session.get('loginY', False)
            
            if not logYogui:
                flash('Acceso restringido. Debes iniciar sesión como yogui.', 'error')
                return redirect(url_for('login'))
            
            correo = session.get('Correo', '')
            nombre = session.get('Nombre', '')
            
            # Procesar acciones POST
            if request.method == 'POST':
                action = request.form.get('action')  # <--- action se define AQUÍ
                
                # Cancelar reserva
                if action == 'cancel_reservation':
                    event_id = request.form.get('event_id')
                    
                    if event_id:
                        success, message = remove_attendee_from_event(event_id, correo)
                        
                        if success:
                            user_data = leerYogui(correo)
                            if user_data:
                                clases_actuales = user_data[6] if user_data[6] is not None else 0
                                nuevas_clases = clases_actuales + 1
                                
                                actualizar_paquete_yogui(correo, nuevas_clases)
                                
                                send_points_returned_email(
                                    correo, 
                                    nombre, 
                                    1, 
                                    "Cancelación de reserva por el usuario"
                                )
                                
                                flash('✅ Reserva cancelada. Se ha devuelto 1 clase a tu cuenta.', 'success')
                            else:
                                flash('❌ Error al obtener datos del usuario', 'error')
                        else:
                            flash(f'❌ Error al cancelar: {message}', 'error')
                    
                    return redirect(url_for('yogui'))
                
                # Actualizar datos personales
                elif action == 'update_profile':
                    nuevo_nombre = request.form.get('nombre', '').strip()
                    nuevo_apellido = request.form.get('apellido', '').strip()
                    nuevo_telefono = request.form.get('telefono', '').strip()
                    
                    try:
                        validar_nombre(nuevo_nombre)
                        validar_nombre(nuevo_apellido)
                        validar_telefono(nuevo_telefono)
                        
                        if nuevo_nombre and nuevo_apellido and nuevo_telefono:
                            success, message = actualizar_datos_yogui(correo, nuevo_nombre, nuevo_apellido, nuevo_telefono)
                            if success:
                                session['Nombre'] = nuevo_nombre
                                flash(message, 'success')
                            else:
                                flash(message, 'error')
                        else:
                            flash('❌ Todos los campos son obligatorios', 'error')
                            
                    except ValidacionError as e:
                        flash(str(e), 'error')
                    
                    return redirect(url_for('yogui'))
                
                # Cambiar contraseña
                elif action == 'change_password':
                    password_actual = request.form.get('password_actual')
                    password_nueva = request.form.get('password_nueva')
                    password_confirm = request.form.get('password_confirm')
                    
                    try:
                        validar_clave(password_nueva)
                        
                        if not password_actual or not password_nueva or not password_confirm:
                            flash('❌ Todos los campos son obligatorios', 'error')
                        elif password_nueva != password_confirm:
                            flash('❌ Las contraseñas nuevas no coinciden', 'error')
                        else:
                            success, message = actualizar_password_yogui(correo, password_actual, password_nueva)
                            flash(message, 'success' if success else 'error')
                            
                    except ValidacionError as e:
                        flash(str(e), 'error')
                    
                    return redirect(url_for('yogui'))
                
                # Eliminar cuenta
                elif action == 'delete_account':
                    confirmacion = request.form.get('confirmacion')
                    
                    if confirmacion != "ELIMINAR":
                        flash('❌ Debes escribir "ELIMINAR" para confirmar', 'error')
                        return redirect(url_for('yogui'))
                    
                    # Obtener datos del usuario antes de eliminar
                    user_data = leerYogui(correo)
                    if not user_data:
                        flash('❌ Error al obtener datos del usuario', 'error')
                        return redirect(url_for('yogui'))
                    
                    nombre_usuario = user_data[2]  # nombre
                    
                    # Eliminar de la base de datos
                    success, result = eliminarYoguiCompleto(correo)
                    
                    if success:
                        # Enviar notificación de despedida
                        try:
                            send_account_deleted_email(correo, nombre_usuario)
                        except:
                            pass  # Si falla el email, continuamos con el cierre de sesión
                        
                        # Cerrar sesión
                        session.clear()
                        
                        flash('✅ Tu cuenta ha sido eliminada exitosamente. Te enviaremos un correo de confirmación.', 'success')
                        return redirect(url_for('index'))
                    else:
                        flash(f'❌ Error al eliminar la cuenta: {result}', 'error')
                        return redirect(url_for('yogui'))
            
            # CÓDIGO GET (fuera del POST)
            # Obtener reservas del usuario
            reservas = []
            try:
                user_events = get_user_events(correo, days_ahead=60)
                
                for event_data in user_events:
                    event_id = event_data['event_id']
                    try:
                        event = get_calendar_service().events().get(
                            calendarId='primary',
                            eventId=event_id
                        ).execute()
                        
                        class_info = parse_class_event(event)
                        reservas.append(class_info)
                    except Exception as e:
                        print(f"Error al obtener detalle de evento {event_id}: {e}")
                        continue
                    
            except Exception as e:
                print(f"Error al obtener reservas: {e}")
                flash('Error al cargar tus reservas', 'error')
            
            # Obtener datos del usuario
            user_data = leerYogui(correo)
            if user_data:
                # user_data[0] = correo
                # user_data[1] = password
                # user_data[2] = nombre
                # user_data[3] = apellido
                # user_data[4] = telefono
                # user_data[5] = paquete
                # user_data[6] = clasesRestantes
                
                clases_restantes = user_data[6] if user_data[6] is not None else 0
                datos_usuario = {
                    'nombre': user_data[2],
                    'apellido': user_data[3],
                    'telefono': user_data[4]
                }
            else:
                clases_restantes = 0
                datos_usuario = {'nombre': '', 'apellido': '', 'telefono': ''}
                flash('Error al cargar tus datos de usuario', 'error')
            
            return render_template('yogui.html',
                                logYogui=logYogui,
                                correo=correo,
                                nombre=nombre,
                                datos_usuario=datos_usuario,
                                reservas=reservas,
                                clases_restantes=clases_restantes)
  
        return app

if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, port=5001)
