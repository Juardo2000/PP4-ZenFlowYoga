const header = document.querySelector('header');
const footer = document.querySelector('footer');

// Mostrar notificación de sesión iniciada
function mostrarNotificacionSesionIniciada(nombreUsuario) {
    const notificacion = document.createElement('div');
    notificacion.className = 'notificacion-sesion notificacion-exito';
    notificacion.innerHTML = `
        <div class="notificacion-contenido">
            <div class="notificacion-icono">
                <i class="fas fa-spa"></i>
            </div>
            <div class="notificacion-texto">
                <strong>¡Bienvenido, ${nombreUsuario}!</strong>
                <span>Has iniciado sesión correctamente</span>
            </div>
            <button class="notificacion-cerrar" onclick="cerrarNotificacion(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notificacion);
    
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.classList.add('notificacion-salida');
            setTimeout(() => {
                if (notificacion.parentNode) {
                    notificacion.remove();
                }
            }, 500);
        }
    }, 5000);
}

// Mostrar notificación de sesión cerrada
function mostrarNotificacionSesionCerrada() {
    const notificacion = document.createElement('div');
    notificacion.className = 'notificacion-sesion notificacion-info';
    notificacion.innerHTML = `
        <div class="notificacion-contenido">
            <div class="notificacion-icono">
                <i class="fas fa-om"></i>
            </div>
            <div class="notificacion-texto">
                <strong>Sesión cerrada</strong>
                <span>Hasta pronto, gracias por visitarnos</span>
            </div>
            <button class="notificacion-cerrar" onclick="cerrarNotificacion(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notificacion);
    
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.classList.add('notificacion-salida');
            setTimeout(() => {
                if (notificacion.parentNode) {
                    notificacion.remove();
                }
            }, 500);
        }
    }, 5000);
}

// Función para cerrar notificación manualmente
function cerrarNotificacion(boton) {
    const notificacion = boton.closest('.notificacion-sesion');
    notificacion.classList.add('notificacion-salida');
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.remove();
        }
    }, 500);
}

// Función para cerrar sesión
function cerrarSesion() {
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (res.ok) {
            mostrarNotificacionSesionCerrada();
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            alert('Error cerrando sesión');
        }
    })
    .catch(error => console.error('Error:', error));
}

// Verificar sesión al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const sesionIniciada = sessionStorage.getItem('sesion_iniciada');
    const nombreUsuario = sessionStorage.getItem('nombre_usuario');
    
    if (sesionIniciada === 'true' && nombreUsuario) {
        mostrarNotificacionSesionIniciada(nombreUsuario);
        sessionStorage.removeItem('sesion_iniciada');
        sessionStorage.removeItem('nombre_usuario');
    }
});


admin = rutas.admin;
log = rutas.login;
comensal = rutas.loginY;
Admin = rutas.loginS;
inst = rutas.loginI;
nombre = rutas.Nombre;

let texto = `<li><a href="${log}" class="boton-log">Iniciar Sesión</a></li>`;

if (comensal === "true") {
    texto = `
        <li class="admin-menu-container">
            <a href="#" class="boton-log admin-btn">Mi Cuenta</a>
            <div class="admin-dropdown-menu">
                <a href="${rutas.yogui}">Mi Panel</a>
                <a href="#" onclick="cerrarSesion()">Cerrar Sesión</a>
            </div>
        </li>
    `;
}

if (inst === "true") {
    texto = `
        <li class="admin-menu-container">
            <a href="#" class="boton-log admin-btn">Instructor</a>
            <div class="admin-dropdown-menu">
                <a href="${rutas.instructor}">Panel de Instructor</a>
                <a href="#" onclick="cerrarSesion()">Cerrar Sesión</a>
            </div>
        </li>
    `;
}

if (Admin === "true") {
    texto = `
        <li class="admin-menu-container">
            <a href="#" class="boton-log admin-btn">Admin</a>
            <div class="admin-dropdown-menu">
                <a href="${rutas.admin}">Panel de Administración</a>
                <a href="#" onclick="cerrarSesion()">Cerrar Sesión</a>
            </div>
        </li>
    `;
}
 
// Construir el header
header.innerHTML = `
<div class="back">
    <div class="menu container">
        <a href="${rutas.index}" class="logo">ZenFlow Yoga</a>
        <input type="checkbox" id="menu"/>
        <label for="menu">
            <img src="https://cdn-icons-png.flaticon.com/512/1828/1828850.png" class="menu-icono" alt="Menú" style="width: 30px; height: 30px; filter: brightness(0) invert(0.5);">
        </label>
        <nav class="navbar">
            <ul>
                <li><a href="${rutas.index}">Inicio</a></li>
                <li><a href="${rutas.paquete}">Paquetes</a></li>
                <li><a href="${rutas.reservas}">Reservas</a></li>
                <li><a href="${rutas.contacto}">Contacto</a></li>
                ${texto}
            </ul>
        </nav>
    </div>
</div>
`;

// Construir el footer
footer.innerHTML = `
<ul class="social-icon">
    <li class="icon-elem">
        <a href="https://web.whatsapp.com" class="icon" target="_blank" rel="noopener noreferrer">
            <ion-icon name="logo-whatsapp"></ion-icon>
        </a>
    </li>
    <li class="icon-elem">
        <a href="https://www.instagram.com"" class="icon" target="_blank" rel="noopener noreferrer">
            <ion-icon name="logo-instagram"></ion-icon>
        </a>
    </li>
    <li class="icon-elem">
        <a href="https://www.facebook.com" class="icon" target="_blank" rel="noopener noreferrer">
            <ion-icon name="logo-facebook"></ion-icon>
        </a>
    </li>
    <li class="icon-elem">
        <a href="https://www.tiktok.com" class="icon" target="_blank" rel="noopener noreferrer">
            <ion-icon name="logo-tiktok"></ion-icon>
        </a>
    </li>
</ul>


<ul class="menu-footer">
    <li class="menu-elem">
        <a href="${rutas.index}" class="menu-icon">Inicio</a>
    </li>
    <li class="menu-elem">
        <a href="${rutas.reservas}" class="menu-icon">Reservas</a>
    </li>
    <li class="menu-elem">
        <a href="${rutas.contacto}" class="menu-icon">Contacto</a>
    </li>
</ul>
<p class="text-footer">©Copyright 2026 | Creado por Juan Rivas</p>
`;

// Funcionalidad del menú desplegable
document.addEventListener('DOMContentLoaded', function() {
    const adminBtns = document.querySelectorAll('.admin-btn');
    
    adminBtns.forEach(adminBtn => {
        const adminMenu = adminBtn.closest('.admin-menu-container').querySelector('.admin-dropdown-menu');
        
        if (adminBtn && adminMenu) {
            adminBtn.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.admin-dropdown-menu.show').forEach(menu => {
                    if (menu !== adminMenu) {
                        menu.classList.remove('show');
                    }
                });
                adminMenu.classList.toggle('show');
            });
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.admin-menu-container')) {
            document.querySelectorAll('.admin-dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
});

// Añadir iconos de Ionicons si no existen
if (!document.querySelector('script[src*="ionicons"]')) {
    const ioniconsScript = document.createElement('script');
    ioniconsScript.src = 'https://unpkg.com/ionicons@5.5.2/dist/ionicons/ionicons.js';
    document.head.appendChild(ioniconsScript);
}