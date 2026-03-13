# 🧘 ZenFlow Yoga - Sistema de Gestión para Estudios de Yoga
https://zenflow-yoga.onrender.com

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Flask](https://img.shields.io/badge/Flask-2.3-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Google Calendar API](https://img.shields.io/badge/Google%20Calendar-API-yellow)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 📋 Descripción

**ZenFlow Yoga** es una plataforma web completa para la gestión integral de estudios de yoga. Automatiza reservas de clases, compra de paquetes, gestión de instructores, pagos y notificaciones, proporcionando paneles personalizados para yoguis (alumnos), instructores y administradores.

## ✨ Características Principales

### 👥 Gestión de Usuarios
- Registro de yoguis con verificación por correo (código de 6 dígitos)
- Registro de instructores con envío de CV en PDF
- Login seguro con roles diferenciados
- Perfil de usuario con edición de datos y cambio de contraseña

### 📅 Reserva de Clases
- Visualización de clases disponibles desde Google Calendar
- Filtros por fecha e instructor
- Reserva simple o múltiple (hasta 8 semanas)
- Cancelación de reservas con devolución automática de clases

### 👨‍🏫 Panel de Instructores
- Creación de clases presenciales o híbridas (con Google Meet)
- Clases recurrentes (semanal por 1-4 meses)
- Edición y cancelación de clases propias
- Visualización de asistentes

### 💳 Compra de Paquetes
- Múltiples métodos de pago (Pago Móvil, Zelle, PayPal)
- Registro de pagos pendientes con número de referencia
- Confirmación/rechazo por administrador
- Actualización automática de clases disponibles

### 👑 Panel de Administración
- CRUD completo de usuarios e instructores
- Gestión de pagos pendientes y confirmados
- Cancelación masiva de reservas
- Reportes de ventas por mes con gráficas
- Exportación a PDF

### 📧 Notificaciones Automáticas
- Códigos de verificación
- Confirmaciones de reserva
- Clases devueltas por cancelación
- Actualizaciones de clases
- Resultados de pagos
- Recordatorios de Google Meet

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.9+** - Lenguaje principal
- **Flask 2.3** - Framework web
- **MySQL 8.0** - Base de datos relacional
- **mysql-connector-python** - Conexión a BD

### APIs Externas
- **Google Calendar API** - Gestión de clases y reservas
- **Gmail API** - Envío de notificaciones por email
- **Google OAuth 2.0** - Autenticación

### Frontend
- **HTML5 / CSS3** - Estructura y estilos
- **JavaScript (Vanilla)** - Interactividad
- **Jinja2** - Motor de plantillas
- **Font Awesome / Ionicons** - Íconos
- **Flatpickr** - Selector de fechas
- **Diseño responsive** - Mobile-first

### Herramientas de Desarrollo
- **Git & GitHub** - Control de versiones
- **pytest** - Pruebas unitarias
- **ReportLab** - Generación de reportes PDF
- **Render** - Hosting de la aplicación
- **Aiven Cloud** - Hosting de base de datos MySQL

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.9 o superior
- MySQL 8.0
- Cuenta de Google Cloud con Calendar y Gmail API habilitadas
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tuusuario/zenflow-yoga.git
   cd zenflow-yoga

pip install -r requirements.txt

# Colocar credentials.json en la carpeta credentials/
# Colocar service-account.json en la carpeta credentials/

## Ejecutar
python app.py

Acceder a la aplicacion
http://localhost:5001

## Estructura de la base de datos

-- Tabla de Yoguis (alumnos)
CREATE TABLE Yoguis (
    Correo VARCHAR(50) PRIMARY KEY,
    Password VARCHAR(100) NOT NULL,
    Nombre VARCHAR(50) NOT NULL,
    Apellido VARCHAR(50) NOT NULL,
    Telefono DECIMAL(10,0) NOT NULL,
    PaqueteID INT,
    clasesRestantes INT DEFAULT 0
);

-- Tabla de Instructores
CREATE TABLE Instructores (
    id_instructor INT AUTO_INCREMENT PRIMARY KEY,
    correo VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    especialidad VARCHAR(100),
    telefono VARCHAR(20) NOT NULL,
    experiencia INT,
    estado VARCHAR(20) DEFAULT 'activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bio TEXT,
    foto VARCHAR(255)
);

-- Tabla de Administradores
CREATE TABLE Administradores (
    Correo VARCHAR(100) PRIMARY KEY,
    Password VARCHAR(100) NOT NULL,
    Nombre VARCHAR(100) NOT NULL,
    Apellido VARCHAR(100) NOT NULL,
    Telefono decimal(10,0)
);

-- Tabla de Paquetes
CREATE TABLE paquetes (
    ID VARCHAR(20) PRIMARY KEY,
    Precio DECIMAL(10,2) NOT NULL,
    dias INT NOT NULL
);

-- Tabla de Pagos
CREATE TABLE Pagos (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    Correo VARCHAR(100) NOT NULL,
    Referencia VARCHAR(100) NOT NULL,
    EstadoDePago VARCHAR(20) DEFAULT 'pendiente',
    paqueteID VARCHAR(20) NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(50),
    FOREIGN KEY (Correo) REFERENCES Yoguis(Correo),
    FOREIGN KEY (paqueteID) REFERENCES paquetes(ID)
);


📞 Contacto
Desarrollador: Juan Rivas

📧 Email: rivas.alvarez.juan@gmail.com

