# 🧘 ZenFlow Yoga - Sistema de Gestión para Estudios de Yoga

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

## 📁 Estructura del Proyecto
