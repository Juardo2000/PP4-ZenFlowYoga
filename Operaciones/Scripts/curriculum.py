# curriculum.py
import base64
import uuid
from datetime import datetime
import os
from io import BytesIO

# Librerías de Google
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuración Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'gmail_token.json'
CLIENT_SECRETS_FILE = 'credencialesGmail.json'

def get_gmail_credentials():
    """Obtiene credenciales válidas para Gmail"""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            if creds and creds.valid:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, 'w') as f:
                    f.write(creds.to_json())
                return creds
                
        except Exception as e:
            print(f"⚠ Error con token guardado: {e}")
    
    # Nueva autenticación
    print("🔑 Iniciando nueva autenticación Gmail...")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES,
        redirect_uri='http://localhost:5001/'
    )
    
    creds = flow.run_local_server(
        port=5001,
        authorization_prompt_message='Por favor, autoriza la aplicación:',
        success_message='¡Autenticación exitosa! Ya puedes cerrar esta ventana.',
        open_browser=True
    )
    
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    print(f"✅ Nuevo token guardado")
    
    return creds

def create_message_with_attachment_in_memory(sender, to, subject, message_text, file_bytes, filename):
    """Crea mensaje con archivo adjunto desde memoria (sin guardar en disco)"""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Agregar texto del mensaje
    msg = MIMEText(message_text)
    message.attach(msg)
    
    # Agregar archivo adjunto DESDE MEMORIA
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(file_bytes)  # Bytes directamente
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename="{filename}"'
    )
    message.attach(part)
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def enviar_cv_directamente(correo_instructor, cv_file):
    """Envía el CV directamente sin guardar en disco"""
    try:
        print(f"📤 Enviando CV de {correo_instructor} directamente...")
        
        # Obtener credenciales
        creds = get_gmail_credentials()
        
        if not creds:
            print("❌ No se pudieron obtener credenciales")
            return {'success': False, 'error': 'Error de autenticación'}
        
        # Crear servicio Gmail
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Servicio Gmail creado")
        
        # Leer archivo a memoria
        file_bytes = cv_file.read()
        filename = cv_file.filename
        file_size = len(file_bytes)
        
        print(f"📄 Archivo en memoria: {filename} ({file_size / 1024:.1f} KB)")
        
        # Validaciones
        if file_size == 0:
            return {'success': False, 'error': 'El archivo está vacío'}
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return {'success': False, 'error': 'El archivo es demasiado grande (máx. 5MB)'}
        
        if not filename.lower().endswith('.pdf'):
            return {'success': False, 'error': 'Solo se permiten archivos PDF'}
        
        # Datos del email
        sender = 'rivas.alvarez.juan@gmail.com'
        to_admin = 'rivas.alvarez.juan@gmail.com'  # Cambia esto al correo del admin
        
        subject = f'📋 NUEVO CV INSTRUCTOR - {correo_instructor}'
        
        # Cuerpo del email para admin
        message_text_admin = f"""Nuevo Curriculum Recibido - ZenFlow Yoga

Correo del instructor: {correo_instructor}
Archivo: {filename}
Tamaño: {file_size / 1024:.1f} KB
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

El archivo PDF está adjunto a este correo.

---
Este es un mensaje automático."""
        
        # 1. ENVIAR AL ADMINISTRADOR
        print(f"📨 Enviando CV a administrador...")
        message_admin = create_message_with_attachment_in_memory(
            sender, to_admin, subject, message_text_admin, file_bytes, filename
        )
        
        result_admin = service.users().messages().send(
            userId='me',
            body=message_admin
        ).execute()
        
        print(f"✅ CV enviado a administrador")
        
        # 2. ENVIAR CONFIRMACIÓN AL INSTRUCTOR
        print(f"📧 Enviando confirmación al instructor...")
        
        # Volver a leer el archivo (si es necesario, pero ya lo tenemos en memoria)
        # Si necesitas re-leerlo: cv_file.seek(0) y cv_file.read() de nuevo
        
        subject_conf = '✅ ZenFlow Yoga - Confirmación de recepción de CV'
        
        message_text_instructor = f"""Hola,

Hemos recibido tu currículum para ser instructor en ZenFlow Yoga.

📋 Detalles:
- Correo: {correo_instructor}
- Archivo: {filename}
- Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Revisaremos tu información y nos pondremos en contacto contigo 
en un plazo de 5 días hábiles.

Gracias por tu interés en ZenFlow Yoga.

Este es un mensaje automático, por favor no responder."""
        
        # Crear mensaje simple (sin adjunto) para el instructor
        message_instructor = MIMEText(message_text_instructor)
        message_instructor['to'] = correo_instructor
        message_instructor['from'] = sender
        message_instructor['subject'] = subject_conf
        raw_instructor = base64.urlsafe_b64encode(message_instructor.as_bytes()).decode()
        
        # Enviar confirmación
        service.users().messages().send(
            userId='me',
            body={'raw': raw_instructor}
        ).execute()
        
        print(f"✅ Confirmación enviada a {correo_instructor}")
        
        return {
            'success': True,
            'filename': filename,
            'file_size': file_size,
            'message': 'CV enviado correctamente',
            'message_id': result_admin.get('id', 'N/A')
        }
        
    except Exception as e:
        print(f"❌ Error enviando CV: {str(e)}")
        
        # Manejo de errores de autenticación
        if "invalid_grant" in str(e):
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
                print("🗑 Token eliminado. Vuelve a autenticar.")
        
        return {'success': False, 'error': f'Error al enviar CV: {str(e)}'}

def procesar_curriculum(correo, cv_file):
    """
    Procesa y envía el currículum SIN GUARDARLO EN DISCO
    """
    try:
        # Validar que hay archivo
        if cv_file.filename == '':
            return {'success': False, 'error': 'No se seleccionó ningún archivo'}
        
        filename = cv_file.filename
        
        # Validar extensión
        if not filename.lower().endswith('.pdf'):
            return {'success': False, 'error': 'Solo se permiten archivos PDF'}
        
        print(f"🎯 Procesando CV para {correo}")
        print(f"   📄 Archivo: {filename}")
        
        # ENVIAR DIRECTAMENTE (sin guardar)
        resultado = enviar_cv_directamente(correo, cv_file)
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error en procesar_curriculum: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Error al procesar archivo: {str(e)}'}