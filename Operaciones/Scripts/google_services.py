import os, pytz, pickle, re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from Operaciones.Scripts.Gmail import send_email

# Scopes necesarios (permisos)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',           # Leer, escribir, compartir calendarios
    'https://www.googleapis.com/auth/calendar.events',    # Leer y escribir eventos
    'https://www.googleapis.com/auth/calendar.settings.readonly',  # Leer configuraciones
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def get_google_credentials():
    """
    Obtiene o refresca las credenciales de Google API.
    Retorna credenciales válidas.
    """
    creds = None
    
    # El archivo token.pickle almacena los tokens de acceso/refresh del usuario
    token_file = 'credentials/token.pickle'
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay credenciales válidas disponibles, deja que el usuario inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Necesitas el archivo credentials.json descargado de Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', SCOPES)
            
            # Esto abrirá una ventana del navegador para autenticación
            creds = flow.run_local_server(port=0)
        
        # Guarda las credenciales para la próxima ejecución
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_calendar_service():
    """
    Retorna un servicio de Google Calendar autenticado.
    """
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_gmail_service():
    """
    Retorna un servicio de Gmail autenticado.
    """
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_calendars():
    """
    Lista todos los calendarios disponibles.
    """
    try:
        service = get_calendar_service()
        
        # Llama a la API de Calendar
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        if not calendars:
            print('No se encontraron calendarios.')
            return []
        
        print(f'Encontrados {len(calendars)} calendarios:')
        for calendar in calendars:
            summary = calendar['summary']
            calendar_id = calendar['id']
            print(f'  - {summary} (ID: {calendar_id})')
        
        return calendars
        
    except HttpError as error:
        print(f'Error al listar calendarios: {error}')
        return []

def get_events(calendar_id='primary', max_results=100, days_ahead=120):
    """
    Obtiene eventos de un calendario específico.
    
    Args:
        calendar_id: ID del calendario (por defecto 'primary')
        max_results: Máximo número de eventos a retornar
        days_ahead: Número de días en el futuro para buscar
    
    Returns:
        Lista de eventos
    """
    try:
        service = get_calendar_service()
        
        # Calcular rango de fechas
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indica UTC
        future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=future,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        print(f'Encontrados {len(events)} eventos en el calendario {calendar_id}')
        return events
        
    except HttpError as error:
        print(f'Error al obtener eventos: {error}')
        return []

def find_yoga_classes(calendar_id='primary', days_ahead=120):
    """
    Busca clases de yoga en los eventos del calendario.
    
    Args:
        calendar_id: ID del calendario
        days_ahead: Días en el futuro para buscar
    
    Returns:
        Lista de clases de yoga encontradas
    """
    events = get_events(calendar_id, days_ahead=days_ahead)
    yoga_classes = []
    
    keywords = ['yoga', 'clase', 'sesión', 'meditación', 'vinyasa', 'hatha', 'ashtanga']
    
    for event in events:
        summary = event.get('summary', '').lower()
        description = event.get('description', '').lower()
        
        # Verificar si es una clase de yoga
        is_yoga_class = False
        
        # Verificar por palabras clave en el título
        for keyword in keywords:
            if keyword in summary:
                is_yoga_class = True
                break
        
        # Verificar por palabras clave en la descripción
        if not is_yoga_class:
            for keyword in keywords:
                if keyword in description:
                    is_yoga_class = True
                    break
        
        if is_yoga_class:
            yoga_class = {
                'id': event.get('id'),
                'summary': event.get('summary', 'Clase de Yoga'),
                'description': event.get('description', ''),
                'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                'location': event.get('location', ''),
                'creator': event.get('creator', {}).get('email', ''),
                'attendees': event.get('attendees', []),
                'attendees_count': len(event.get('attendees', [])),
                'max_attendees': 20  # Valor por defecto, puedes ajustarlo
            }
            yoga_classes.append(yoga_class)
    
    print(f'Encontradas {len(yoga_classes)} clases de yoga')
    return yoga_classes

def extract_instructor(description):
    """Extrae el nombre del instructor de la descripción"""
    patterns = [
        r'instructor[:\s]*([^\n\.]+)',
        r'profesor[:\s]*([^\n\.]+)',
        r'con[:\s]*([^\n\.]+)',
        r'imparte[:\s]*([^\n\.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description or '', re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Instructor por confirmar"

def get_yoga_classes_from_calendar(days_ahead=120):
    """
    Obtiene las clases de yoga desde Google Calendar.
    Retorna una lista de diccionarios con la información de cada clase.
    """
    try:
        service = get_calendar_service()
        
        # Calcular rango de fechas
        now = datetime.utcnow().isoformat() + 'Z'
        future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Obtener eventos
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=future,
            maxResults=250,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        yoga_classes = []
        yoga_keywords = ['yoga', 'clase', 'sesión', 'meditación', 'vinyasa', 'hatha', 'ashtanga']
        
        for event in events:
            summary = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            
            # Verificar si es una clase de yoga
            is_yoga_class = any(keyword in summary for keyword in yoga_keywords)
            
            if not is_yoga_class:
                is_yoga_class = any(keyword in description for keyword in yoga_keywords)
            
            if is_yoga_class:
                # Parsear fechas
                start_time = event['start'].get('dateTime', event['start'].get('date'))
                end_time = event['end'].get('dateTime', event['end'].get('date'))
                
                # Convertir a objetos datetime
                if 'T' in start_time:  # Es datetime
                    try:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        date_str = start_dt.strftime('%Y-%m-%d')
                        time_str = start_dt.strftime('%H:%M')
                        duration = (end_dt - start_dt).seconds // 60  # Duración en minutos
                        
                        # Obtener día de la semana
                        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                        fecha_dia = dias_semana[start_dt.weekday()]
                        
                    except:
                        # Fallback si hay error en el formato
                        date_str = start_time[:10] if len(start_time) >= 10 else start_time
                        time_str = "Horario por confirmar"
                        duration = 60
                        fecha_dia = ""
                else:  # Es solo fecha
                    try:
                        start_dt = datetime.fromisoformat(start_time)
                        date_str = start_dt.strftime('%Y-%m-%d')
                        time_str = "Todo el día"
                        duration = 0
                        
                        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                        fecha_dia = dias_semana[start_dt.weekday()]
                    except:
                        date_str = start_time
                        time_str = "Horario por confirmar"
                        duration = 0
                        fecha_dia = ""
                
                # Contar asistentes actuales
                attendees = event.get('attendees', [])
                current_attendees = len([a for a in attendees if a.get('responseStatus') != 'declined'])
                
                # Capacidad máxima (por defecto 20, se puede extraer de description)
                capacity = 20
                if description:
                    capacity_match = re.search(r'capacidad[:\s]*(\d+)', description, re.IGNORECASE)
                    if capacity_match:
                        capacity = int(capacity_match.group(1))
                
                # Determinar si es híbrida
                is_hibrida = 'hibrida' in description or 'meet.google.com' in description
                meet_link = None
                if is_hibrida:
                    meet_match = re.search(r'https://meet\.google\.com/[a-z-]+', description)
                    if meet_match:
                        meet_link = meet_match.group(0)
                
                yoga_class = {
                    'event_id': event['id'],
                    'title': event.get('summary', 'Clase de Yoga'),
                    'description': event.get('description', ''),
                    'date': date_str,
                    'fecha_dia': fecha_dia,
                    'time': time_str,
                    'duration': duration,
                    'datetime_iso': start_time,
                    'location': event.get('location', 'Estudio de Yoga'),
                    'instructor': extract_instructor(event.get('description', '')),
                    'capacity': capacity,
                    'current_attendees': current_attendees,
                    'available_spots': max(0, capacity - current_attendees),
                    'is_hibrida': is_hibrida,
                    'meet_link': meet_link,
                    'raw_event': event  # Para referencia
                }
                
                yoga_classes.append(yoga_class)
        
        print(f"✅ Encontradas {len(yoga_classes)} clases de yoga en Google Calendar")
        return yoga_classes
        
    except Exception as e:
        print(f"❌ Error al obtener clases de Google Calendar: {e}")
        return []

def reserve_yoga_class(event_id, user_email, user_name, reservas_multiples=False, semanas=1):
    """
    Reserva una clase agregando al usuario como asistente.
    Si reservas_multiples=True, reserva también las siguientes semanas a la misma hora y día
    """
    try:
        service = get_calendar_service()
        
        # Obtener el evento actual
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Verificar si ya está lleno
        attendees = event.get('attendees', [])
        current_count = len([a for a in attendees if a.get('responseStatus') != 'declined'])
        
        # Extraer capacidad del evento
        capacity = 20
        description = event.get('description', '')
        if description:
            capacity_match = re.search(r'Capacidad:\s*(\d+)', description, re.IGNORECASE)
            if capacity_match:
                capacity = int(capacity_match.group(1))
        
        if current_count >= capacity:
            return False, "La clase está llena"
        
        # Verificar si el usuario ya está registrado
        existing_emails = [a.get('email') for a in attendees]
        if user_email in existing_emails:
            return False, "Ya estás registrado en esta clase"
        
        # Agregar al usuario como asistente en el evento actual
        attendees.append({
            'email': user_email,
            'displayName': user_name,
            'responseStatus': 'accepted'
        })
        
        event['attendees'] = attendees
        
        # Actualizar el evento actual
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        reservas_exitosas = 1
        eventos_reservados = [event_id]
        
        # Si se solicitan reservas múltiples
        if reservas_multiples and semanas > 1:
            from datetime import datetime, timedelta
            import pytz
            
            # Obtener la fecha y hora del evento actual
            start_time = event['start'].get('dateTime')
            if not start_time:
                return True, "Reserva exitosa (no se pueden reservar fechas futuras para eventos sin hora específica)"
            
            # Parsear la fecha (eliminar zona horaria para trabajar internamente)
            start_time_clean = start_time.split('+')[0].split('Z')[0]
            start_dt = datetime.fromisoformat(start_time_clean)
            
            # Obtener el título del evento para buscar coincidencias
            event_title = event.get('summary', '')
            
            # Buscar eventos futuros en el mismo día de la semana y hora
            for semana in range(1, semanas):
                fecha_siguiente = start_dt + timedelta(weeks=semana)
                
                # Formatear fechas correctamente para Google Calendar API
                # Usar fecha sin hora y dejar que Google maneje el día completo
                fecha_str = fecha_siguiente.strftime('%Y-%m-%d')
                time_min = fecha_str + 'T00:00:00Z'
                time_max = fecha_str + 'T23:59:59Z'
                
                print(f"🔍 Buscando eventos entre {time_min} y {time_max}")
                
                # Obtener eventos de ese día
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True
                ).execute()
                
                eventos_dia = events_result.get('items', [])
                print(f"📅 Encontrados {len(eventos_dia)} eventos en esa fecha")
                
                # Buscar un evento con el mismo título
                encontrado = False
                for evento in eventos_dia:
                    evento_summary = evento.get('summary', '')
                    evento_start = evento['start'].get('dateTime', '')
                    
                    # Comparar títulos (ignorando mayúsculas/minúsculas)
                    if evento_summary.lower() == event_title.lower():
                        print(f"✅ Evento encontrado: {evento_summary} - {evento_start}")
                        
                        # Verificar capacidad
                        evento_attendees = evento.get('attendees', [])
                        evento_count = len([a for a in evento_attendees if a.get('responseStatus') != 'declined'])
                        
                        # Extraer capacidad
                        evento_capacity = 20
                        evento_desc = evento.get('description', '')
                        if evento_desc:
                            cap_match = re.search(r'Capacidad:\s*(\d+)', evento_desc, re.IGNORECASE)
                            if cap_match:
                                evento_capacity = int(cap_match.group(1))
                        
                        if evento_count < evento_capacity:
                            # Verificar que el usuario no esté ya registrado
                            existing = [a.get('email') for a in evento_attendees]
                            if user_email not in existing:
                                # Agregar usuario a este evento
                                evento_attendees.append({
                                    'email': user_email,
                                    'displayName': user_name,
                                    'responseStatus': 'accepted'
                                })
                                evento['attendees'] = evento_attendees
                                
                                service.events().update(
                                    calendarId='primary',
                                    eventId=evento['id'],
                                    body=evento,
                                    sendUpdates='all'
                                ).execute()
                                
                                reservas_exitosas += 1
                                eventos_reservados.append(evento['id'])
                                print(f"✅ Reservada clase para la semana {semana}")
                                encontrado = True
                                break
                            else:
                                print(f"⚠️ Usuario ya registrado en evento de la semana {semana}")
                                encontrado = True
                                break
                        else:
                            print(f"❌ Evento de semana {semana} está lleno")
                
                if not encontrado:
                    print(f"❌ No se encontró evento para la semana {semana} con título '{event_title}'")
            
            mensaje = f"✅ Reserva exitosa. Se reservaron {reservas_exitosas} clases (incluyendo {semanas-1} futuras)."
        else:
            mensaje = "✅ Reserva exitosa. Revisa tu Google Calendar y email para confirmación."
        
        # Enviar confirmación por email
        try:
            send_reservation_confirmation(user_email, event, user_name, reservas_exitosas)
        except Exception as email_error:
            print(f"⚠️  Error al enviar email: {email_error}")
        
        return True, mensaje
        
    except HttpError as error:
        error_msg = f"Error de Google Calendar: {error}"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error al reservar clase: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg

def send_reservation_confirmation(user_email, event, user_name, num_reservas=1):
    """Envía un email de confirmación de reserva"""
    try:
        # Extraer información del evento
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_str = start_dt.strftime('%d/%m/%Y')
                time_str = start_dt.strftime('%H:%M')
                dia_semana = start_dt.strftime('%A')
                dias_map = {
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                dia_semana_es = dias_map.get(dia_semana, dia_semana)
            except:
                date_str = start_time[:10] if len(start_time) >= 10 else start_time
                time_str = "Horario por confirmar"
                dia_semana_es = ""
        else:
            date_str = start_time
            time_str = "Todo el día"
            dia_semana_es = ""
        
        # Crear mensaje según si es reserva múltiple o no
        if num_reservas > 1:
            subject = f"🧘 ZenFlow Yoga - Confirmación de {num_reservas} clases"
            mensaje_adicional = f"""
            <div style="background: #e8f5e9; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #28a745;">
                <h3 style="color: #155724; margin-top: 0;">📅 Reserva Múltiple</h3>
                <p style="margin: 10px 0;">Has reservado <strong>{num_reservas} clases</strong> los próximos {dia_semana_es} a las {time_str}.</p>
                <p style="margin: 5px 0;">Todas las clases han sido agregadas a tu calendario.</p>
            </div>
            """
        else:
            subject = f"🧘 ZenFlow Yoga - Confirmación de reserva"
            mensaje_adicional = ""
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #8aa9a4, #5d7c77); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🧘 ¡Reserva Confirmada!</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    Tu reserva ha sido confirmada exitosamente.
                </p>
                
                {mensaje_adicional}
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #8aa9a4;">
                    <p style="margin: 5px 0;"><strong>📅 Fecha:</strong> {date_str}</p>
                    <p style="margin: 5px 0;"><strong>🕐 Hora:</strong> {time_str}</p>
                    <p style="margin: 5px 0;"><strong>📍 Lugar:</strong> {event.get('location', 'Estudio de Yoga')}</p>
                    <p style="margin: 5px 0;"><strong>👨‍🏫 Instructor:</strong> {extract_instructor(event.get('description', ''))}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/yogui" style="background: #8aa9a4; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ver mis reservas
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - ¡Nos vemos en la clase!
                </p>
            </div>
        </div>
        """
        
        send_email(user_email, subject, html_body)
        print(f"✅ Email de confirmación enviado a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email de confirmación: {e}")
        return False

def create_event(calendar_id='primary', summary='Clase de Yoga', 
                 start_time=None, end_time=None, description='', 
                 location='', attendees=None, reminders=True):
    """
    Crea un nuevo evento en Google Calendar.
    
    Args:
        calendar_id: ID del calendario
        summary: Título del evento
        start_time: Hora de inicio (datetime object)
        end_time: Hora de fin (datetime object)
        description: Descripción del evento
        location: Ubicación
        attendees: Lista de emails de asistentes
        reminders: Si se deben agregar recordatorios
    
    Returns:
        El evento creado o None si hay error
    """
    try:
        service = get_calendar_service()
        
        # Configurar tiempos por defecto si no se proporcionan
        if not start_time:
            start_time = datetime.now() + timedelta(hours=1)
        if not end_time:
            end_time = start_time + timedelta(hours=1)
        
        # Formatear tiempos para Google Calendar
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        # Construir el evento
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time_str,
                'timeZone': 'America/Caracas',
            },
            'end': {
                'dateTime': end_time_str,
                'timeZone': 'America/Caracas',
            }
        }
        
        # Agregar asistentes si se proporcionan
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Agregar recordatorios
        if reminders:
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                    {'method': 'popup', 'minutes': 60},       # 1 hora antes
                ],
            }
        
        # Insertar el evento
        event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'  # Envía invitaciones a los asistentes
        ).execute()
        
        print(f'✅ Evento creado: {event.get("htmlLink")}')
        return event
        
    except HttpError as error:
        print(f'❌ Error al crear evento: {error}')
        return None

def add_attendee_to_event(calendar_id='primary', event_id=None, attendee_email=None):
    """
    Agrega un asistente a un evento existente.
    
    Args:
        calendar_id: ID del calendario
        event_id: ID del evento
        attendee_email: Email del asistente a agregar
    
    Returns:
        El evento actualizado o None si hay error
    """
    try:
        if not event_id or not attendee_email:
            print("❌ Se requiere event_id y attendee_email")
            return None
        
        service = get_calendar_service()
        
        # Obtener el evento actual
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Agregar el nuevo asistente
        if 'attendees' not in event:
            event['attendees'] = []
        
        # Verificar si el asistente ya existe
        existing_emails = [a.get('email') for a in event['attendees']]
        if attendee_email not in existing_emails:
            event['attendees'].append({'email': attendee_email})
        
        # Actualizar el evento
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates='all'  # Envía actualización al nuevo asistente
        ).execute()
        
        print(f'✅ Asistente {attendee_email} agregado al evento')
        return updated_event
        
    except HttpError as error:
        print(f'❌ Error al agregar asistente: {error}')
        return None

def test_connection():
    """
    Prueba la conexión a Google Calendar API.
    """
    try:
        # Listar calendarios
        calendars = list_calendars()
        
        if calendars:
            print("✅ Conexión a Google Calendar API exitosa")
            
            # Probar obtención de eventos del calendario principal
            events = get_events(max_results=5)
            
            if events:
                print("✅ Eventos obtenidos exitosamente")
                for i, event in enumerate(events[:3], 1):
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(f"  {i}. {event.get('summary', 'Sin título')} - {start}")
            
            # Probar obtener clases de yoga
            yoga_classes = get_yoga_classes_from_calendar(days_ahead=120)
            print(f"✅ Clases de yoga encontradas: {len(yoga_classes)}")
            
            return True
        else:
            print("❌ No se pudieron obtener calendarios")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


    
def get_or_create_instructor_calendar(instructor_email, instructor_name):
    """Obtiene o crea el calendario específico del instructor"""
    try:
        service = get_calendar_service()
        
        # Buscar calendario existente
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        calendar_name = f"Clases - {instructor_name}"
        
        for calendar in calendars:
            if calendar.get('summary') == calendar_name:
                print(f"✅ Calendario encontrado para {instructor_name}")
                return calendar['id']
        
        # Si no existe, crearlo
        print(f"🆕 Creando calendario para {instructor_name}...")
        calendar_body = {
            'summary': calendar_name,
            'description': f'Clases de yoga impartidas por {instructor_name} ({instructor_email})',
            'timeZone': 'America/Caracas'
        }
        
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        calendar_id = created_calendar['id']
        
        print(f"✅ Calendario creado: {calendar_id}")
        return calendar_id
        
    except Exception as e:
        print(f"❌ Error al obtener/crear calendario: {e}")
        return 'primary'  # Fallback al calendario principal

def instructor_add_class(instructor_email, instructor_name, class_data):
    """Permite a un instructor agregar una clase"""
    try:
        # Obtener calendario del instructor
        calendar_id = get_or_create_instructor_calendar(instructor_email, instructor_name)
        
        # Verificar que no choque con otras clases
        if not check_schedule_conflict(calendar_id, class_data):
            return False, "Conflicto de horario con otra clase existente"
        
        # Verificar límites del estudio (9:00 AM - 9:00 PM)
        if not within_studio_hours(class_data):
            return False, "Fuera del horario del estudio (9:00 AM - 9:00 PM)"
        
        # Crear el evento
        service = get_calendar_service()
        
        event = {
            'summary': class_data['title'],
            'location': class_data.get('location', 'Estudio de Yoga Principal'),
            'description': f"""Instructor: {instructor_name}
Tipo: {class_data.get('tipo', 'Vinyasa Yoga')}
Nivel: {class_data.get('nivel', 'Todos los niveles')}
Duración: {class_data['duration']} minutos
Capacidad máxima: {class_data['capacity']} personas

{class_data.get('description', '')}

--- Información del instructor ---
Email: {instructor_email}
""",
            'start': {
                'dateTime': class_data['start_datetime'],
                'timeZone': 'America/Caracas',
            },
            'end': {
                'dateTime': class_data['end_datetime'],
                'timeZone': 'America/Caracas',
            },
            'colorId': class_data.get('color_id', '5'),  # Verde para yoga
            'guestsCanInviteOthers': False,
            'guestsCanModify': False,
            'guestsCanSeeOtherGuests': True,
            'attendees': [],  # Inicialmente vacío
            'reminders': {
                'useDefault': True,
            },
            'extendedProperties': {
                'private': {
                    'type': 'yoga_class',
                    'capacity': str(class_data['capacity']),
                    'instructor_email': instructor_email,
                    'instructor_name': instructor_name,
                    'studio': 'YogaStudio'
                }
            }
        }
        
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        # Sincronizar con calendario principal para que aparezca en reservas
        sync_to_main_calendar(created_event, instructor_name)
        
        print(f"✅ Clase creada por {instructor_name}: {class_data['title']}")
        print(f"   Enlace: {created_event.get('htmlLink')}")
        
        return True, "Clase agregada exitosamente"
        
    except Exception as e:
        print(f"❌ Error al agregar clase: {e}")
        return False, f"Error: {str(e)}"

def check_schedule_conflict(calendar_id, new_class):
    """Verifica si hay conflicto de horario"""
    try:
        service = get_calendar_service()
        
        # Buscar eventos en el mismo día
        start_date = new_class['start_datetime'][:10]  # YYYY-MM-DD
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=f"{start_date}T00:00:00-06:00",
            timeMax=f"{start_date}T23:59:59-06:00",
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        new_start = datetime.fromisoformat(new_class['start_datetime'].replace('Z', '+00:00'))
        new_end = datetime.fromisoformat(new_class['end_datetime'].replace('Z', '+00:00'))
        
        for event in events:
            event_start = event['start'].get('dateTime')
            event_end = event['end'].get('dateTime')
            
            if event_start and event_end:
                e_start = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                e_end = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                
                # Verificar solapamiento
                if (new_start < e_end and new_end > e_start):
                    print(f"⚠️  Conflicto con: {event.get('summary')}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar conflictos: {e}")
        return True  # Permitir si hay error en la verificación

def within_studio_hours(class_data):
    """Verifica que la clase esté dentro del horario del estudio (9:00 AM - 9:00 PM)"""
    try:
        start_time = datetime.fromisoformat(class_data['start_datetime'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(class_data['end_datetime'].replace('Z', '+00:00'))
        
        # Convertir a hora local (ajusta según tu zona)
        hour = start_time.hour
        
        # Horario: 9:00 AM (9) a 9:00 PM (21)
        if 9 <= hour <= 21:
            return True
        
        print(f"⚠️  Hora fuera de rango: {hour}:00")
        return False
        
    except Exception as e:
        print(f"❌ Error al verificar horario: {e}")
        return False

def sync_to_main_calendar(event, instructor_name):
    """Sincroniza la clase con el calendario principal para reservas"""
    try:
        service = get_calendar_service()
        
        # Modificar el evento para el calendario principal
        main_event = event.copy()
        main_event['summary'] = f"{event.get('summary', 'Clase de Yoga')} - con {instructor_name}"
        
        # Agregar al calendario principal
        service.events().insert(
            calendarId='primary',
            body=main_event
        ).execute()
        
        print(f"✅ Clase sincronizada con calendario principal")
        return True
        
    except Exception as e:
        print(f"⚠️  Error al sincronizar con calendario principal: {e}")
        return False

def get_instructor_classes(instructor_email, days_ahead=60):
    """Obtiene las clases de un instructor específico filtrando por su email"""
    try:
        service = get_calendar_service()
        
        now = datetime.utcnow().isoformat() + 'Z'
        future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=future,
            maxResults=250,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        all_classes = []
        yoga_keywords = ['yoga', 'clase', 'sesión', 'meditación', 'vinyasa', 'hatha', 'ashtanga', 'yin', 'restaurativo']
        
        for event in events:
            summary = event.get('summary', '').lower()
            description = event.get('description', '')
            
            # Verificar si tiene el email del instructor
            if instructor_email in description:
                
                # Verificar si es clase de yoga
                is_yoga = any(keyword in summary for keyword in yoga_keywords)
                if not is_yoga and description:
                    is_yoga = any(keyword in description.lower() for keyword in yoga_keywords)
                
                if is_yoga:
                    class_info = parse_class_event(event)
                    all_classes.append(class_info)
        
        return all_classes
        
    except Exception as e:
        print(f"Error en get_instructor_classes: {e}")
        return []
    
def parse_class_event(event):
    """Convierte un evento de Google Calendar a formato de clase"""
    try:
        # Obtener start time
        start = event['start']
        end = event['end']
        
        # Determinar tipo de evento
        description = event.get('description', '')
        is_hibrida = 'Modalidad: Híbrida' in description if description else False
        
        # Determinar si es fecha con hora o solo fecha
        if 'dateTime' in start:
            start_time_str = start.get('dateTime')
            end_time_str = end.get('dateTime')
            
            # Parsear la fecha
            try:
                start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                
                date_str = start_dt.strftime('%Y-%m-%d')
                time_str = start_dt.strftime('%H:%M')
                duration = int((end_dt - start_dt).total_seconds() / 60)
                
            except ValueError:
                start_clean = start_time_str.split('+')[0].split('Z')[0]
                end_clean = end_time_str.split('+')[0].split('Z')[0]
                
                start_dt = datetime.fromisoformat(start_clean)
                end_dt = datetime.fromisoformat(end_clean)
                
                date_str = start_dt.strftime('%Y-%m-%d')
                time_str = start_dt.strftime('%H:%M')
                duration = int((end_dt - start_dt).total_seconds() / 60)
        
        elif 'date' in start:
            date_str = start.get('date')
            time_str = "Todo el día"
            duration = 0
            start_time_str = date_str
            end_time_str = date_str
        else:
            date_str = "Fecha no disponible"
            time_str = "Hora no disponible"
            duration = 60
            start_time_str = ""
            end_time_str = ""
        
        # Contar asistentes
        attendees = event.get('attendees', [])
        current_attendees = 0
        for a in attendees:
            if a.get('responseStatus') != 'declined':
                current_attendees += 1
        
        # Extraer capacidad de la descripción
        capacity = 20
        if description:
            capacity_match = re.search(r'Capacidad:\s*(\d+)', description)
            if capacity_match:
                capacity = int(capacity_match.group(1))
        
        # Extraer ubicación
        location_raw = event.get('location', '')
        if location_raw and location_raw.strip():
            location = location_raw.strip()
        else:
            location = 'Estudio Principal'
        
        # Extraer información del instructor
        instructor_name = "Desconocido"
        instructor_email = ""
        if description:
            instr_match = re.search(r'Instructor:\s*([^\n]+)', description)
            if instr_match:
                instructor_name = instr_match.group(1).strip()
            
            email_match = re.search(r'Email:\s*([^\n]+)', description)
            if email_match:
                instructor_email = email_match.group(1).strip()
        
        # Determinar si es híbrida
        is_hibrida = 'Modalidad: Híbrida' in description if description else False
        has_meet = 'meet.google.com' in description if description else False
        
        # Construir resultado
        result = {
            'event_id': event['id'],
            'title': event.get('summary', 'Clase de Yoga'),
            'description': description,
            'date': date_str,
            'time': time_str,
            'duration': duration,
            'start_datetime': start_time_str,
            'end_datetime': end_time_str,
            'location': location,
            'instructor_name': instructor_name,
            'instructor_email': instructor_email,
            'capacity': capacity,
            'current_attendees': current_attendees,
            'available_spots': max(0, capacity - current_attendees),
            'is_hibrida': is_hibrida,
            'has_meet': has_meet,
            'edit_link': event.get('htmlLink', ''),
            'status': 'active'
        }
        
        return result
        
    except Exception as e:
        print(f"Error al parsear evento {event.get('id', 'desconocido')}: {e}")
        
        # Retornar datos mínimos en caso de error
        return {
            'event_id': event.get('id', ''),
            'title': event.get('summary', 'Clase de Yoga'),
            'description': event.get('description', ''),
            'date': 'Fecha no disponible',
            'time': 'Hora no disponible',
            'duration': 60,
            'start_datetime': '',
            'end_datetime': '',
            'location': event.get('location', 'Estudio Principal'),
            'instructor_name': 'Desconocido',
            'instructor_email': '',
            'capacity': 20,
            'current_attendees': 0,
            'available_spots': 20,
            'is_hibrida': False,
            'has_meet': False,
            'edit_link': '',
            'status': 'error'
        }
    
def create_event_with_meet(calendar_id='primary', summary='Clase de Yoga', 
                          start_time=None, end_time=None, description='', 
                          location='', attendees=None, is_hibrida=False):
    """
    Crea un evento con Google Meet automáticamente (solo para clases híbridas).
    """
    try:
        service = get_calendar_service()
        
        # Configurar tiempos
        if not start_time:
            start_time = datetime.now() + timedelta(hours=1)
        if not end_time:
            end_time = start_time + timedelta(hours=1)
        
        # Formatear tiempos
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        # Construir el evento
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time_str,
                'timeZone': 'America/Caracas',
            },
            'end': {
                'dateTime': end_time_str,
                'timeZone': 'America/Caracas',
            }
        }
        
        # Agregar Google Meet SOLO si es híbrida
        if is_hibrida:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"yogaclass-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        
        # Agregar asistentes si se proporcionan
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Insertar el evento CON soporte para conferencia SOLO si es híbrida
        event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            conferenceDataVersion=1 if is_hibrida else 0
        ).execute()
        
        # Extraer el link de Google Meet si se creó (solo para híbridas)
        meet_link = None
        if is_hibrida and 'conferenceData' in event:
            meet_link = event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
            if not meet_link and 'hangoutLink' in event:
                meet_link = event.get('hangoutLink')
        
        print(f'✅ Evento creado: {event.get("htmlLink")}')
        if meet_link:
            print(f'🔗 Google Meet (Híbrida): {meet_link}')
        
        return event, meet_link
        
    except Exception as e:
        print(f'❌ Error al crear evento con Meet: {e}')
        return None, None

def start_meet_for_class(event_id, instructor_email):
    """
    Verifica si el instructor puede iniciar la reunión y obtiene el link.
    """
    try:
        service = get_calendar_service()
        
        # Obtener el evento
        event = service.events().get(
            calendarId='primary',
            eventId=event_id,
            conferenceDataVersion=1
        ).execute()
        
        # Verificar que el evento tenga Google Meet
        meet_link = None
        if 'conferenceData' in event:
            meet_link = event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
        elif 'hangoutLink' in event:
            meet_link = event.get('hangoutLink')
        
        if not meet_link:
            return False, "Esta clase no tiene enlace de Google Meet configurado"
        
        # Verificar que sea el horario correcto
        event_start = event['start'].get('dateTime')
        if event_start:
            start_time = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
            now = datetime.now(start_time.tzinfo)
            
            # Permitir iniciar 15 minutos antes y 2 horas después de empezar
            time_diff = (start_time - now).total_seconds() / 60  # en minutos
            
            if time_diff > 15:  # Más de 15 minutos antes
                return False, f"La clase comienza en {int(time_diff)} minutos. Puedes iniciar 15 minutos antes."
            elif time_diff < -120:  # Más de 2 horas después de empezar
                return False, "La clase ya terminó hace más de 2 horas"
        
        # Verificar que el instructor sea el organizador o esté en la descripción
        organizer_email = event.get('organizer', {}).get('email', '')
        description = event.get('description', '')
        
        if organizer_email != instructor_email and instructor_email not in description:
            return False, "No eres el instructor de esta clase"
        
        return True, meet_link
        
    except Exception as e:
        print(f"❌ Error al obtener link de Meet: {e}")
        return False, f"Error: {str(e)}"

def send_meet_reminder(user_email, class_title, meet_link, start_time):
    """
    Envía un recordatorio con el link de Google Meet.
    """
    try:
        from Operaciones.Scripts.Gmail import enviar_email
        
        # Formatear hora
        if isinstance(start_time, str):
            if 'T' in start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
                date_str = dt.strftime('%d/%m/%Y')
            else:
                time_str = "Por confirmar"
                date_str = start_time
        else:
            time_str = start_time.strftime('%H:%M')
            date_str = start_time.strftime('%d/%m/%Y')
        
        subject = f"🔔 Recordatorio: Clase {class_title} - Google Meet listo"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🧘 Clase de Yoga Online</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">{class_title}</h2>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <p><strong>📅 Fecha:</strong> {date_str}</p>
                    <p><strong>🕐 Hora:</strong> {time_str}</p>
                    <p><strong>🎥 Modalidad:</strong> Online vía Google Meet</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{meet_link}" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                            <i class="fas fa-video"></i> Unirse a Google Meet
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        <strong>💡 Consejos para la clase online:</strong><br>
                        1. Conéctate 5 minutos antes<br>
                        2. Usa auriculares para mejor audio<br>
                        3. Asegura tu conexión a internet<br>
                        4. Ten tu mat de yoga listo<br>
                        5. Enciende tu cámara si te sientes cómodo/a
                    </p>
                </div>
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                    <p style="margin: 0; color: #2e7d32;">
                        <strong>⚠️ Importante:</strong> Este enlace es personal. No lo compartas con otras personas.
                    </p>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px;">
                <p style="margin: 0; font-size: 14px;">
                    Yoga Studio - Tu bienestar es nuestra prioridad<br>
                    <small>© {datetime.now().year} Yoga Studio</small>
                </p>
            </div>
        </div>
        """
        
        enviar_email(user_email, subject, body)
        print(f"✅ Recordatorio de Meet enviado a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar recordatorio: {e}")
        return False

def get_event_meet_link(event_id):
    """
    Obtiene el link de Google Meet de un evento.
    """
    try:
        service = get_calendar_service()
        
        event = service.events().get(
            calendarId='primary',
            eventId=event_id,
            conferenceDataVersion=1
        ).execute()
        
        if 'conferenceData' in event:
            return event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
        elif 'hangoutLink' in event:
            return event.get('hangoutLink')
        
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener link de Meet: {e}")
        return None

def cancel_class(event_id, instructor_email):
    """Cancela una clase y notifica a los asistentes"""
    try:
        service = get_calendar_service()
        
        # Obtener el evento
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Verificar que sea el instructor
        description = event.get('description', '')
        if instructor_email not in description:
            return False, "No eres el instructor de esta clase"
        
        # Eliminar el evento
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'  # Notifica a todos los asistentes
        ).execute()
        
        print(f"✅ Clase cancelada: {event.get('summary')}")
        return True, "Clase cancelada exitosamente"
        
    except Exception as e:
        print(f"❌ Error al cancelar clase: {e}")
        return False, f"Error: {str(e)}"

def instructor_add_class_with_meet(instructor_email, instructor_name, class_data):
    """
    Crea una clase para un instructor con o sin Google Meet.
    El instructor siempre aparece como asistente para que le llegue la invitación
    """
    try:
        print(f"\n🎯 Creando clase para: {instructor_name} ({instructor_email})")
        
        # Determinar modalidad
        is_hibrida = class_data.get('modalidad') == 'hibrida'
        modalidad_str = "Híbrida" if is_hibrida else "Presencial"
        
        # Crear descripción
        descripcion = f"""Instructor: {instructor_name}
Email: {instructor_email}
Tipo: {class_data.get('tipo', 'Vinyasa')}
Nivel: {class_data.get('nivel', 'Todos')}
Capacidad: {class_data['capacity']}
Duración: {class_data['duration']} minutos
Modalidad: {modalidad_str}

{class_data.get('description', '')}"""
        
        service = get_calendar_service()
        
        # Parsear fechas
        start_datetime = datetime.fromisoformat(class_data['start_datetime'].replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(class_data['end_datetime'].replace('Z', '+00:00'))
        
        # Lista de asistentes (solo el instructor por ahora)
        attendees_list = [{
            'email': instructor_email,
            'displayName': instructor_name,
            'responseStatus': 'accepted'
        }]
        
        # Construir evento CON el instructor como asistente desde el principio
        event = {
            'summary': class_data['title'],
            'location': class_data.get('location', 'Estudio Principal'),
            'description': descripcion,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Caracas',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Caracas',
            },
            'attendees': attendees_list,  # Instructor como asistente
            'guestsCanInviteOthers': False,
            'guestsCanModify': False,
            'reminders': {
                'useDefault': True,
            }
        }
        
        # Agregar Google Meet si es híbrida
        conference_data_version = 0
        meet_link = None
        
        if is_hibrida:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"yogaclass-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
            conference_data_version = 1
        
        # Crear el evento CON el instructor como asistente
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=conference_data_version,
            sendUpdates='all'  # Enviar notificaciones a todos los asistentes (incluido el instructor)
        ).execute()
        
        # Extraer link de Meet si existe
        if is_hibrida:
            if 'conferenceData' in created_event:
                meet_link = created_event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
            elif 'hangoutLink' in created_event:
                meet_link = created_event.get('hangoutLink')
            
            # Actualizar descripción con el link
            if meet_link:
                updated_desc = descripcion + f"\n\nGoogle Meet: {meet_link}"
                created_event['description'] = updated_desc
                service.events().update(
                    calendarId='primary',
                    eventId=created_event['id'],
                    body=created_event
                ).execute()
        
        print(f"✅ Clase creada: {created_event.get('htmlLink')}")
        print(f"✅ Instructor {instructor_email} agregado como asistente - DEBERÍA recibir invitación")
        
        return True, f"Clase {modalidad_str} creada exitosamente", meet_link
        
    except Exception as e:
        print(f"❌ Error al crear clase: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}", None

def parse_class_event_fast(event):
    """Versión ultra rápida de parseo de eventos"""
    try:
        # Extraer datos básicos (sin procesamiento complejo)
        event_id = event.get('id', '')
        title = event.get('summary', 'Clase de Yoga')
        description = event.get('description', '')
        
        # Parsear fechas de manera simple (sin datetime complejos)
        start_time = event['start'].get('dateTime', event['start'].get('date', ''))
        
        # Extraer fecha directamente del string (más rápido)
        date_str = start_time[:10] if len(start_time) >= 10 else ''
        
        # Extraer hora si existe
        time_str = "Todo el día"
        duration = 60
        if 'T' in start_time and len(start_time) >= 16:
            time_str = start_time[11:16]  # HH:MM
        
        # Contar asistentes rápidamente
        attendees = event.get('attendees', [])
        current_attendees = 0
        for a in attendees:
            if a.get('responseStatus') != 'declined':
                current_attendees += 1
        
        # Extraer capacidad (solo si existe)
        capacity = 20
        if 'Capacidad:' in description:
            import re
            cap_match = re.search(r'Capacidad:\s*(\d+)', description)
            if cap_match:
                capacity = int(cap_match.group(1))
        
        # Extraer nombre del instructor
        instructor_name = "Desconocido"
        if 'Instructor:' in description:
            name_match = re.search(r'Instructor:\s*([^\n]+)', description)
            if name_match:
                instructor_name = name_match.group(1).strip()
        
        # Determinar si es híbrida
        is_hibrida = 'Modalidad: Híbrida' in description
        has_meet = 'meet.google.com' in description
        
        # Extraer link de Meet
        meet_link = None
        if has_meet:
            meet_match = re.search(r'https://meet\.google\.com/[a-z-]+', description)
            if meet_match:
                meet_link = meet_match.group(0)
        
        return {
            'event_id': event_id,
            'title': title,
            'description': description[:100] + '...' if len(description) > 100 else description,
            'date': date_str,
            'time': time_str,
            'duration': duration,
            'start_datetime': start_time,
            'location': event.get('location', 'Estudio de Yoga'),
            'instructor_name': instructor_name,
            'capacity': capacity,
            'current_attendees': current_attendees,
            'available_spots': max(0, capacity - current_attendees),
            'is_hibrida': is_hibrida,
            'has_meet': has_meet,
            'meet_link': meet_link
        }
    except Exception as e:
        print(f"⚠️ Error en parseo rápido: {e}")
        return None

def get_instructor_classes_fast(instructor_email, days_ahead=120, use_cache=True):
    """
    VERSIÓN OPTIMIZADA: Obtiene clases del instructor con caché y procesamiento rápido
    """
    from .cache_manager import get_cache_key, get_from_cache, save_to_cache
    
    try:
        # 1. Intentar obtener del caché
        if use_cache:
            cache_key = get_cache_key(f"classes_{instructor_email}", days_ahead)
            cached_data = get_from_cache(cache_key, max_age_minutes=5)
            if cached_data is not None:
                print(f"📦 Caché: {len(cached_data)} clases para {instructor_email}")
                return cached_data
        
        print(f"🔍 Buscando clases para: {instructor_email}")
        
        # 2. Obtener servicio
        service = get_calendar_service()
        
        # 3. Calcular fechas
        from datetime import timezone
        now = datetime.now(timezone.utc).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()
        
        # 4. Obtener eventos (solo una llamada a la API)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=future,
            maxResults=100,  # Límite razonable
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # 5. Filtrar y parsear rápidamente
        all_classes = []
        yoga_keywords = ['yoga', 'clase', 'vinyasa', 'hatha', 'ashtanga']
        
        for event in events:
            summary = event.get('summary', '').lower()
            description = event.get('description', '')
            
            # Verificar si es clase de yoga (rápido)
            is_yoga = any(k in summary for k in yoga_keywords)
            if not is_yoga and description:
                is_yoga = any(k in description.lower() for k in yoga_keywords)
            
            if is_yoga and instructor_email in description:
                class_info = parse_class_event_fast(event)
                if class_info:
                    all_classes.append(class_info)
        
        # 6. Guardar en caché
        if use_cache:
            save_to_cache(cache_key, all_classes)
        
        print(f"✅ Encontradas {len(all_classes)} clases")
        return all_classes
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    
    
def remove_attendee_from_event(event_id, user_email):
    """
    Elimina a un usuario de la lista de asistentes de un evento
    Retorna: (success, message)
    """
    try:
        service = get_calendar_service()
        
        # Obtener el evento
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Obtener lista de asistentes
        attendees = event.get('attendees', [])
        
        # Filtrar para eliminar al usuario
        new_attendees = [a for a in attendees if a.get('email') != user_email]
        
        # Si no hay cambios, el usuario no estaba
        if len(attendees) == len(new_attendees):
            return False, "Usuario no encontrado en este evento"
        
        # Actualizar el evento
        event['attendees'] = new_attendees
        
        service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'  # Notificar al usuario
        ).execute()
        
        print(f"✅ Usuario {user_email} eliminado del evento {event_id}")
        return True, "Asistencia cancelada"
        
    except Exception as e:
        print(f"❌ Error al eliminar asistente: {e}")
        return False, str(e)
    
    
def get_user_events(user_email, days_ahead=60):
    """
    Obtiene todos los eventos (clases) donde un usuario está como asistente
    Retorna: lista de eventos
    """
    try:
        service = get_calendar_service()
        
        # Calcular rango de fechas (desde ahora hasta 60 días)
        now = datetime.utcnow().isoformat() + 'Z'
        future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Obtener eventos
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=future,
            maxResults=250,  # Límite alto
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Filtrar eventos donde el usuario está como asistente
        user_events = []
        
        for event in events:
            attendees = event.get('attendees', [])
            for attendee in attendees:
                if attendee.get('email') == user_email and attendee.get('responseStatus') != 'declined':
                    user_events.append({
                        'event_id': event['id'],
                        'summary': event.get('summary', 'Clase'),
                        'start': event['start'].get('dateTime', event['start'].get('date')),
                        'attendees_count': len(attendees)
                    })
                    break
        
        print(f"✅ Encontrados {len(user_events)} eventos para {user_email}")
        return user_events
        
    except Exception as e:
        print(f"❌ Error al obtener eventos del usuario: {e}")
        return []
    
    
    
def cancel_all_attendees_from_class(event_id, instructor_email):
    """
    Elimina TODOS los asistentes de una clase específica y devuelve la lista de emails
    Retorna: (success, message, num_cancelados, lista_emails)
    """
    try:
        print(f"🔍 [Google] Cancelando asistentes de clase: {event_id}")
        
        service = get_calendar_service()
        
        # Obtener el evento
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        print(f"📋 Evento encontrado: {event.get('summary')}")
        
        # Verificar que sea clase del instructor
        description = event.get('description', '')
        if instructor_email not in description:
            print(f"❌ Instructor {instructor_email} no autorizado para esta clase")
            return False, "No tienes permisos para cancelar esta clase", 0, []
        
        print(f"✅ Instructor verificado")
        
        # Obtener lista de asistentes actuales
        attendees = event.get('attendees', [])
        print(f"📋 Total asistentes en evento: {len(attendees)}")
        
        # Obtener emails de asistentes reales (excluyendo al instructor)
        emails_asistentes = []
        for a in attendees:
            email = a.get('email')
            status = a.get('responseStatus')
            print(f"   Asistente: {email}, status: {status}")
            
            if email != instructor_email and status != 'declined':
                emails_asistentes.append(email)
        
        num_asistentes = len(emails_asistentes)
        print(f"📧 Asistentes a cancelar: {num_asistentes} - {emails_asistentes}")
        
        if num_asistentes == 0:
            print("✅ No hay asistentes para cancelar")
            return True, "La clase no tiene asistentes para cancelar", 0, []
        
        # Crear nueva lista de asistentes (solo el instructor si está)
        nuevos_attendees = []
        for a in attendees:
            if a.get('email') == instructor_email:
                nuevos_attendees.append(a)
                print(f"✅ Manteniendo al instructor en la lista")
        
        # Actualizar el evento
        event['attendees'] = nuevos_attendees
        
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'  # Notificar a todos los eliminados
        ).execute()
        
        print(f"✅ Evento actualizado. Nuevos asistentes: {len(nuevos_attendees)}")
        
        return True, f"Se cancelaron {num_asistentes} reservas", num_asistentes, emails_asistentes
        
    except Exception as e:
        print(f"❌ Error en cancel_all_attendees_from_class: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e), 0, []
    
def delete_calendar_event(event_id, instructor_email):
    """
    Elimina un evento completo de Google Calendar
    Retorna: (success, message)
    """
    try:
        service = get_calendar_service()
        
        # Obtener el evento para verificar permisos
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Verificar que sea del instructor
        description = event.get('description', '')
        if instructor_email not in description:
            return False, "No tienes permiso para eliminar esta clase"
        
        # Eliminar el evento
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
            sendUpdates='all'  # Notificar a todos
        ).execute()
        
        print(f"✅ Evento {event_id} eliminado de Google Calendar")
        return True, "Evento eliminado"
        
    except Exception as e:
        print(f"❌ Error al eliminar evento: {e}")
        return False, str(e)
    
def create_recurring_class(instructor_email, instructor_name, class_data, recurrence_rule):
    """
    Crea una clase recurrente en Google Calendar con el instructor como asistente
    """
    try:
        print(f"\n🎯 Creando clase RECURRENTE para: {instructor_name} ({instructor_email})")
        print(f"📅 Regla: {recurrence_rule}")
        
        # Determinar modalidad
        is_hibrida = class_data.get('modalidad') == 'hibrida'
        modalidad_str = "Híbrida" if is_hibrida else "Presencial"
        
        # Crear descripción
        descripcion = f"""Instructor: {instructor_name}
Email: {instructor_email}
Tipo: {class_data.get('tipo', 'Vinyasa')}
Nivel: {class_data.get('nivel', 'Todos')}
Capacidad: {class_data['capacity']}
Duración: {class_data['duration']} minutos
Modalidad: {modalidad_str}

{class_data.get('description', '')}"""
        
        service = get_calendar_service()
        
        # Parsear fechas
        start_datetime = datetime.fromisoformat(class_data['start_datetime'].replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(class_data['end_datetime'].replace('Z', '+00:00'))
        
        # Lista de asistentes (solo el instructor)
        attendees_list = [{
            'email': instructor_email,
            'displayName': instructor_name,
            'responseStatus': 'accepted'
        }]
        
        # Construir evento CON el instructor como asistente
        event = {
            'summary': class_data['title'],
            'location': class_data.get('location', 'Estudio Principal'),
            'description': descripcion,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Caracas',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Caracas',
            },
            'recurrence': [recurrence_rule],
            'attendees': attendees_list,  # Instructor como asistente
            'guestsCanInviteOthers': False,
            'guestsCanModify': False,
            'reminders': {
                'useDefault': True,
            }
        }
        
        # Agregar Google Meet si es híbrida
        conference_data_version = 0
        meet_link = None
        
        if is_hibrida:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"yogaclass-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
            conference_data_version = 1
        
        # Crear el evento
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=conference_data_version,
            sendUpdates='all'  # Enviar notificaciones al instructor
        ).execute()
        
        # Extraer link de Meet si existe
        if is_hibrida:
            if 'conferenceData' in created_event:
                meet_link = created_event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
            elif 'hangoutLink' in created_event:
                meet_link = created_event.get('hangoutLink')
            
            # Actualizar descripción con el link
            if meet_link:
                updated_desc = descripcion + f"\n\nGoogle Meet: {meet_link}"
                created_event['description'] = updated_desc
                service.events().update(
                    calendarId='primary',
                    eventId=created_event['id'],
                    body=created_event
                ).execute()
        
        # Extraer el COUNT
        import re
        count_match = re.search(r'COUNT=(\d+)', recurrence_rule)
        total_instancias = int(count_match.group(1)) if count_match else "varias"
        
        print(f"✅ Clase recurrente creada. Total instancias: {total_instancias}")
        print(f"✅ Instructor {instructor_email} agregado como asistente - DEBERÍA recibir invitación")
        
        return True, f"Clase {modalidad_str} recurrente creada ({total_instancias} sesiones)", meet_link
        
    except Exception as e:
        print(f"❌ Error al crear clase recurrente: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}", None

def get_recurrence_rule(class_date, recurrence_type):
    """
    Genera la regla RRULE para Google Calendar basada en la fecha y tipo de recurrencia
    
    La regla debe ser: FREQ=WEEKLY;BYDAY=MO, TU, etc;COUNT=N
    donde COUNT es el número TOTAL de instancias (incluyendo la primera)
    """
    try:
        from datetime import datetime
        
        # Mapeo de días de la semana a códigos de Google Calendar
        day_map = {
            0: 'MO',  # Monday
            1: 'TU',  # Tuesday
            2: 'WE',  # Wednesday
            3: 'TH',  # Thursday
            4: 'FR',  # Friday
            5: 'SA',  # Saturday
            6: 'SU'   # Sunday
        }
        
        # Obtener día de la semana de la fecha
        date_obj = datetime.strptime(class_date, '%Y-%m-%d')
        day_code = day_map[date_obj.weekday()]
        
        print(f"📅 Fecha base: {class_date} -> Día: {day_code}")
        
        # Mapeo de tipos de recurrencia a cantidad TOTAL de clases
        recurrence_counts = {
            'weekly_4': 4,   # Total 4 clases (incluye la primera)
            'weekly_8': 8,   # Total 8 clases
            'weekly_12': 12, # Total 12 clases
            'weekly_16': 16, # Total 16 clases
        }
        
        total_clases = recurrence_counts.get(recurrence_type)
        
        if not total_clases:
            return None
            
        # La regla debe especificar el día correcto (BYDAY)
        rule = f'RRULE:FREQ=WEEKLY;BYDAY={day_code};COUNT={total_clases}'
        print(f"📋 Regla generada: {rule}")
        
        return rule
        
    except Exception as e:
        print(f"Error generando regla de recurrencia: {e}")
        return None
    
def send_class_points_returned_email(user_email, user_name, cantidad_clases, razon):
    """
    Envía notificación cuando se devuelven puntos de clase
    """
    try:
        
        subject = "🧘 ZenFlow Yoga - Clases devueltas a tu cuenta"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🧘 Clases Devueltas</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    Se han devuelto <strong style="color: #28a745; font-size: 20px;">{cantidad_clases} clase(s)</strong> a tu cuenta.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <p style="margin: 0; color: #333;">
                        <strong>Motivo:</strong> {razon}
                    </p>
                </div>
                
                <p style="color: #555;">
                    Ya puedes usar estas clases para reservar nuevas sesiones.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/reservas" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ver Clases Disponibles
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Tu bienestar es nuestra prioridad
                </p>
            </div>
        </div>
        """
        
        send_email(user_email, subject, body)
        print(f"✅ Notificación de clases devueltas enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False


def send_class_updated_email(user_email, user_name, class_title, class_date, class_time, cambios):
    """
    Envía notificación cuando una clase es modificada por el instructor
    """
    try:
        from Operaciones.Scripts.Gmail import enviar_email
        
        subject = f"📝 ZenFlow Yoga - Actualización de clase: {class_title}"
        
        # Formatear fecha
        from datetime import datetime
        fecha_obj = datetime.strptime(class_date, '%Y-%m-%d')
        fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #ff9800, #f57c00); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📝 Clase Actualizada</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; color: #555;">
                    La clase <strong>"{class_title}"</strong> ha sido modificada por el instructor.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">📋 Nuevos detalles:</h3>
                    <p><strong>📅 Fecha:</strong> {fecha_formateada}</p>
                    <p><strong>🕐 Hora:</strong> {class_time}</p>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px;">
                        <p style="margin: 0; color: #856404;">
                            <strong>✏️ Cambios realizados:</strong><br>
                            {cambios}
                        </p>
                    </div>
                </div>
                
                <p style="color: #555;">
                    Por favor, revisa tu calendario para ver los detalles actualizados.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/reservas" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ver mi calendario
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Tu bienestar es nuestra prioridad
                </p>
            </div>
        </div>
        """
        
        enviar_email(user_email, subject, body)
        print(f"✅ Notificación de actualización enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False
    
def update_class(event_id, instructor_email, updated_data):
    """
    Actualiza los datos de una clase existente
    Retorna: (success, message, cambios_realizados)
    """
    try:
        service = get_calendar_service()
        
        # Obtener el evento actual
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Verificar que sea el instructor
        description = event.get('description', '')
        if instructor_email not in description:
            return False, "No tienes permiso para editar esta clase", ""
        
        # Guardar datos antiguos para comparar
        old_summary = event.get('summary', '')
        old_start = event['start'].get('dateTime', '')
        old_location = event.get('location', '')
        
        # Actualizar campos
        cambios = []
        
        if updated_data.get('title') and updated_data['title'] != old_summary:
            event['summary'] = updated_data['title']
            cambios.append(f"Título: '{old_summary}' → '{updated_data['title']}'")
        
        # Manejar fecha y hora correctamente
        if updated_data.get('start_datetime'):
            from datetime import datetime, timedelta
            import re
            
            # Limpiar el formato de fecha
            start_str = updated_data['start_datetime']
            
            # Asegurar formato ISO 8601 completo
            if 'T' in start_str:
                # Ya tiene formato datetime-local, agregar zona horaria
                if not start_str.endswith('Z') and not '+' in start_str:
                    start_str = start_str + ':00-04:00'  # Ajusta según tu zona horaria
            else:
                # Es solo fecha, agregar hora y zona
                start_str = f"{start_str}T{old_start[11:16]}:00-04:00"
            
            try:
                new_start = datetime.fromisoformat(start_str)
                new_start_str = new_start.isoformat()
            except:
                # Si falla, usar el formato original
                new_start_str = start_str
            
            if new_start_str != old_start:
                event['start']['dateTime'] = new_start_str
                
                # Recalcular end_time
                duration = updated_data.get('duration', 60)
                new_end = new_start + timedelta(minutes=duration)
                event['end']['dateTime'] = new_end.isoformat()
                
                cambios.append(f"Hora: {old_start[11:16]} → {new_start_str[11:16]}")
        
        if updated_data.get('location') and updated_data['location'] != old_location:
            event['location'] = updated_data['location']
            cambios.append(f"Ubicación: '{old_location}' → '{updated_data['location']}'")
        
        if updated_data.get('description') is not None:
            old_desc = event.get('description', '')
            
            # Preservar el link de Meet si existe
            meet_link = None
            if 'Google Meet:' in old_desc:
                meet_parts = old_desc.split('Google Meet:')
                if len(meet_parts) > 1:
                    meet_link = 'Google Meet:' + meet_parts[1]
            
            if meet_link:
                new_desc = updated_data['description'] + f"\n\n{meet_link}"
            else:
                new_desc = updated_data['description']
            
            event['description'] = new_desc
            cambios.append("Descripción actualizada")
        
        if not cambios:
            return True, "No se realizaron cambios", ""
        
        # Actualizar el evento
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        print(f"✅ Clase {event_id} actualizada")
        print(f"📝 Cambios: {cambios}")
        
        return True, "Clase actualizada exitosamente", ", ".join(cambios)
        
    except Exception as e:
        print(f"❌ Error al actualizar clase: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}", ""
    
def get_event_attendees(event_id):
    """Obtiene lista de emails de asistentes a un evento"""
    try:
        service = get_calendar_service()
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        attendees = event.get('attendees', [])
        emails = []
        
        for a in attendees:
            email = a.get('email')
            status = a.get('responseStatus')
            if email and status != 'declined':
                emails.append(email)
        
        return emails
        
    except Exception as e:
        print(f"Error obteniendo asistentes: {e}")
        return []
    
def send_instructor_removed_email(user_email, user_name, instructor_name, clases_afectadas):
    """
    Notifica a un alumno que su instructor ha sido eliminado y sus clases canceladas
    """
    try:
        
        subject = "⚠️ ZenFlow Yoga - Actualización importante sobre tus clases"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #dc3545, #c82333); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">⚠️ Actualización de Clases</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    Lamentamos informarte que el instructor <strong>"{instructor_name}"</strong> ya no forma parte de nuestro equipo.
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <p style="margin: 0; color: #333;">
                        <strong>Clases afectadas:</strong> {clases_afectadas}
                    </p>
                    <p style="margin: 10px 0 0 0; color: #28a745;">
                        <strong>✓ Se han devuelto {clases_afectadas} clases a tu cuenta</strong>
                    </p>
                </div>
                
                <p style="color: #555;">
                    Puedes usar estas clases para reservar con otros instructores o en nuevos horarios.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/reservas" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ver clases disponibles
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Siempre trabajando para tu bienestar
                </p>
            </div>
        </div>
        """
        
        send_email(user_email, subject, body)
        print(f"✅ Notificación enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False
    
def send_points_returned_email(user_email, user_name, cantidad_clases, motivo):
    """
    Envía notificación cuando se devuelven puntos de clase
    """
    try:
        
        print(f"\n📧 INTENTANDO ENVIAR EMAIL A: {user_email}")
        print(f"   Nombre: {user_name}")
        print(f"   Cantidad: {cantidad_clases}")
        print(f"   Motivo: {motivo}")
        
        subject = f"✅ {cantidad_clases} clase(s) devuelta(s) a tu cuenta"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #28a745, #20c997); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">✅ Clases Devueltas</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; color: #555;">
                    Se han devuelto <strong>{cantidad_clases} clase(s)</strong> a tu cuenta por el siguiente motivo:
                </p>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;"><strong>Motivo:</strong> {motivo}</p>
                </div>
                
                <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                    <p style="margin: 0; color: #155724; font-size: 32px; font-weight: bold;">
                        +{cantidad_clases}
                    </p>
                </div>
                
                <p style="color: #555;">
                    Puedes usar estas clases para reservar en cualquier horario disponible.
                </p>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://zenflow-yoga.onrender.com/reservas" 
                       style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ver clases disponibles
                    </a>
                </div>
            </div>
            
            <div style="background: #343a40; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">ZenFlow Yoga - Tu bienestar es nuestra prioridad</p>
            </div>
        </div>
        """
        
        resultado = send_email(user_email, subject, html_body)
        print(f"   Resultado send_email: {resultado}")
        print(f"✅ Email enviado a {user_email}")
        return resultado
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def send_admin_notification(user_email, user_name, accion, detalles=None):
    """
    Envía notificaciones generales del admin a los usuarios afectados
    accion: 'usuario_eliminado', 'instructor_agregado', 'instructor_eliminado', 'clases_agregadas'
    """
    try:
        
        # Configurar según la acción
        if accion == 'usuario_eliminado':
            subject = "ℹ️ Notificación de ZenFlow Yoga"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: #6c757d; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">ℹ️ Notificación del Sistema</h1>
                </div>
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Hola {user_name},</h2>
                    <p>Te informamos que tu cuenta en ZenFlow Yoga ha sido eliminada por un administrador.</p>
                    <p>Si tienes alguna pregunta, por favor contáctanos.</p>
                </div>
                <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0;">ZenFlow Yoga</p>
                </div>
            </div>
            """
            
        elif accion == 'instructor_agregado':
            subject = "🎉 Bienvenido como Instructor a ZenFlow Yoga"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #28a745, #20c997); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🎉 Bienvenido a ZenFlow Yoga</h1>
                </div>
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Hola {user_name},</h2>
                    <p>¡Felicidades! Has sido registrado como instructor en ZenFlow Yoga.</p>
                    <p>Ya puedes acceder al panel de instructor y comenzar a crear tus clases.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://zenflow-yoga.onrender.com/instructor" 
                           style="background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Ir al Panel de Instructor
                        </a>
                    </div>
                </div>
                <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0;">ZenFlow Yoga - Bienvenido al equipo</p>
                </div>
            </div>
            """
            
        elif accion == 'instructor_eliminado':
            subject = "ℹ️ Actualización de tu cuenta de Instructor"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: #dc3545; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">ℹ️ Actualización de Cuenta</h1>
                </div>
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Hola {user_name},</h2>
                    <p>Te informamos que tu cuenta de instructor en ZenFlow Yoga ha sido desactivada.</p>
                    <p>Si tienes alguna pregunta, por favor contáctanos.</p>
                </div>
                <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0;">ZenFlow Yoga</p>
                </div>
            </div>
            """
            
        elif accion == 'clases_agregadas':
            cantidad = detalles.get('cantidad', 0)
            total = detalles.get('total', 0)
            subject = f"✅ {cantidad} clase(s) agregada(s) a tu cuenta"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="background: linear-gradient(135deg, #28a745, #20c997); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">✅ Clases Agregadas</h1>
                </div>
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Hola {user_name},</h2>
                    <p>Un administrador ha agregado <strong>{cantidad} clase(s)</strong> a tu cuenta.</p>
                    <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;">
                        <p style="margin: 0; color: #155724; font-size: 24px; font-weight: bold;">
                            Total: {total} clases disponibles
                        </p>
                    </div>
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://zenflow-yoga.onrender.com/reservas" 
                           style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reservar ahora
                        </a>
                    </div>
                </div>
                <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0;">ZenFlow Yoga</p>
                </div>
            </div>
            """
        
        send_email(user_email, subject, html_body)
        print(f"✅ Notificación {accion} enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False
    
def send_account_deleted_email(user_email, user_name):
    """
    Envía notificación al usuario cuando su cuenta ha sido eliminada
    """
    try:
        subject = "👋 ZenFlow Yoga - Cuenta eliminada"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #6c757d, #495057); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">👋 Cuenta Eliminada</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    Te confirmamos que tu cuenta en ZenFlow Yoga ha sido eliminada exitosamente.
                </p>
                
                <div style="background: #e9ecef; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 0; color: #495057;">
                        <strong>📧 Correo:</strong> {user_email}<br>
                        <strong>📅 Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
                
                <p style="color: #555;">
                    Lamentamos verte partir. Si en algún momento deseas regresar, estaremos encantados de recibirte nuevamente.
                </p>
                
                <p style="color: #555; margin-top: 20px;">
                    Namaste,<br>
                    <strong>Equipo ZenFlow Yoga</strong>
                </p>
            </div>
            
            <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Siempre agradecidos por tu visita
                </p>
            </div>
        </div>
        """
        
        send_email(user_email, subject, html_body)
        print(f"✅ Notificación de cuenta eliminada enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación: {e}")
        return False
    
def send_pago_notification(user_email, user_name, estado, monto, referencia, paquete):
    """
    Envía notificación al usuario cuando su pago es confirmado o rechazado
    estado: 'confirmado' o 'rechazado'
    """
    try:
        if estado == 'confirmado':
            subject = "✅ ZenFlow Yoga - Pago Confirmado"
            color = "#28a745"
            icono = "✅"
            titulo = "¡Pago Confirmado!"
            mensaje = f"Tu pago por ${monto:,.2f} ha sido CONFIRMADO exitosamente."
            detalle = "Las clases han sido agregadas a tu cuenta. Ya puedes reservar tus clases."
        else:
            subject = "❌ ZenFlow Yoga - Pago Rechazado"
            color = "#dc3545"
            icono = "❌"
            titulo = "Pago Rechazado"
            mensaje = f"Tu pago por ${monto:,.2f} ha sido RECHAZADO."
            detalle = "Por favor, verifica los datos del pago o contacta a soporte."
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: {color}; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">{icono} {titulo}</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Hola {user_name},</h2>
                
                <p style="font-size: 16px; line-height: 1.6; color: #555;">
                    {mensaje}
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid {color};">
                    <p style="margin: 5px 0;"><strong>Monto:</strong> ${monto:,.2f}</p>
                    <p style="margin: 5px 0;"><strong>Referencia:</strong> {referencia}</p>
                    <p style="margin: 5px 0;"><strong>Paquete:</strong> {paquete}</p>
                </div>
                
                <p style="color: #555;">
                    {detalle}
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/yogui" style="background: {color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ir a mi panel
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Tu bienestar es nuestra prioridad
                </p>
            </div>
        </div>
        """
        
        send_email(user_email, subject, html_body)
        print(f"✅ Notificación de pago {estado} enviada a {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación de pago: {e}")
        return False
    
def send_admin_compra_notification(usuario_email, usuario_nombre, paquete_id, monto, metodo_pago, referencia):
    """
    Envía notificación al admin cuando un usuario compra un paquete
    """
    try:
        admin_email = "rivas.alvarez.juan@gmail.com"  # Tu correo
        subject = "🛒 Nueva Compra de Paquete - ZenFlow Yoga"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #8aa9a4, #5d7c77); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🛒 Nueva Compra</h1>
                <p style="color: white; margin: 10px 0 0; opacity: 0.9;">Un usuario ha realizado una compra</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333;">Detalles de la Compra:</h2>
                
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #8aa9a4;">
                    <p style="margin: 8px 0;"><strong>👤 Usuario:</strong> {usuario_nombre} ({usuario_email})</p>
                    <p style="margin: 8px 0;"><strong>📦 Paquete ID:</strong> {paquete_id}</p>
                    <p style="margin: 8px 0;"><strong>💰 Monto:</strong> ${monto:,.2f}</p>
                    <p style="margin: 8px 0;"><strong>💳 Método de pago:</strong> {metodo_pago}</p>
                    <p style="margin: 8px 0;"><strong>🔢 Referencia:</strong> {referencia}</p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;">
                        <strong>⚠️ Acción requerida:</strong> Este pago está pendiente de confirmación.
                        Ingresa al panel de administración para verificarlo.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://zenflow-yoga.onrender.com/admin?tab=pagos" style="background: #8aa9a4; color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">
                        Ver Pagos Pendientes
                    </a>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 14px;">
                    ZenFlow Yoga - Panel de Administración
                </p>
            </div>
        </div>
        """
        
        send_email(admin_email, subject, html_body)
        print(f"✅ Notificación de compra enviada al admin")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando notificación al admin: {e}")
        return False