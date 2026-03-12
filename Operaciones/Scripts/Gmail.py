from __future__ import print_function
import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes necesarios
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Archivos de configuración
CLIENT_SECRETS_FILE = 'credentials/credentials.json'
TOKEN_FILE = 'credentials/gmail_token.json'

def get_credentials():
    """Obtiene credenciales válidas para Gmail API"""
    creds = None
    
    # Cargar token existente si existe
    if os.path.exists(TOKEN_FILE):
        print("📁 Cargando token guardado...")
        try:
            with open(TOKEN_FILE, 'r') as token:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Verificar si el token es válido
            if creds and creds.valid:
                print("✅ Token válido cargado")
                return creds
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Token expirado, refrescando...")
                creds.refresh(Request())
                # Guardar token refrescado
                with open(TOKEN_FILE, 'w') as f:
                    f.write(creds.to_json())
                print("✅ Token refrescado exitosamente")
                return creds
                
        except Exception as e:
            print(f"⚠ Error con token guardado: {e}")
    
    # Si no hay credenciales válidas, obtener nuevas
    print("🔑 Iniciando nueva autenticación...")
    
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
    
    # Guardar las credenciales
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    print(f"✅ Nuevo token guardado en {TOKEN_FILE}")
    
    return creds

def create_message_html(sender, to, subject, html_body):
    """Crea un mensaje HTML para enviar por Gmail"""
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Versión HTML del mensaje
    part_html = MIMEText(html_body, 'html')
    message.attach(part_html)
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(to, subject, html_body):
    """Envía un email usando Gmail API"""
    try:
        sender = 'rivas.alvarez.juan@gmail.com'
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)
        
        message = create_message_html(sender, to, subject, html_body)
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        print(f"✅ Email enviado a {to} - ID: {sent_message['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        if "invalid_grant" in str(e) and os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print("🗑 Token inválido eliminado. Reintenta.")
        return False

def enviarCodigo(correo, codigo):
    """Envía un código de verificación con diseño bonito"""
    subject = "🧘 ZenFlow Yoga - Tu código de verificación"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
            
            <!-- Header con gradiente -->
            <div style="background: linear-gradient(135deg, #8aa9a4 0%, #dab6b0 100%); padding: 40px 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 300;">ZenFlow Yoga</h1>
                <p style="color: white; margin: 10px 0 0; opacity: 0.9; font-size: 1.1rem;">Tu código de verificación</p>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 40px 30px; background: #ffffff;">
                <h2 style="color: #4a5b5b; margin-top: 0; font-size: 1.5rem; text-align: center;">¡Bienvenido!</h2>
                
                <p style="color: #6b7f7f; font-size: 1rem; line-height: 1.6; text-align: center;">
                    Estás a un paso de comenzar tu viaje de bienestar con nosotros.
                </p>
                
                <!-- Código de verificación destacado -->
                <div style="background: #f8f4f0; border-radius: 15px; padding: 30px; margin: 30px 0; text-align: center; border: 2px dashed #8aa9a4;">
                    <p style="color: #4a5b5b; margin: 0 0 10px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px;">
                        Tu código de verificación
                    </p>
                    <div style="font-size: 3.5rem; font-weight: bold; color: #8aa9a4; letter-spacing: 8px; font-family: monospace;">
                        {codigo}
                    </div>
                    <p style="color: #dc3545; margin: 15px 0 0; font-size: 0.85rem;">
                        ⏳ Válido por 10 minutos
                    </p>
                </div>
                
                <!-- Instrucciones -->
                <div style="background: #f0f7f5; border-radius: 10px; padding: 20px; margin: 20px 0;">
                    <p style="color: #4a5b5b; margin: 0 0 10px; font-weight: 600;">
                        <span style="color: #8aa9a4;">📝</span> Instrucciones:
                    </p>
                    <ul style="color: #6b7f7f; margin: 0; padding-left: 20px;">
                        <li style="margin-bottom: 8px;">Ingresa este código en la página de registro</li>
                        <li style="margin-bottom: 8px;">El código expira en 10 minutos</li>
                        <li>Si no solicitaste este código, ignora este mensaje</li>
                    </ul>
                </div>
                
                <!-- Nota de seguridad -->
                <p style="color: #b8a9a0; font-size: 0.8rem; text-align: center; margin-top: 30px; border-top: 1px solid #e8e0d9; padding-top: 20px;">
                    Este es un mensaje automático, por favor no respondas a este correo.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f4f0; padding: 25px; text-align: center;">
                <p style="color: #8aa9a4; margin: 0 0 10px; font-size: 0.9rem;">
                    🌸 ZenFlow Yoga - Encuentra tu equilibrio
                </p>
                <p style="color: #b8a9a0; margin: 0; font-size: 0.8rem;">
                    © 2025 ZenFlow Yoga. Todos los derechos reservados.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(correo, subject, html_body)