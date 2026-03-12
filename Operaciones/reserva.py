from Operaciones.CRUD.Agregar import crear_reservacion
from Operaciones.CRUD.Leer import ver_reservaciones, ver_reservaciones_comensal
import datetime

class Reservas():
    def __init__(self, _Nombre, _correo, _telefono, _restaurante, _fecha, _hora, _mesa, _personas, _comentarios):
        self.Nombre = _Nombre,
        self.correo = _correo,
        self.telefono = _telefono,
        self.restaurante = _restaurante,
        self.fecha = _fecha,
        self.hora = _hora
        self.mesa = _mesa,
        self.personas = _personas,
        self.comentarios = _comentarios
        
        
    def agregarReserva(self):
        reserva = (
            self.Nombre[0],
            self.correo[0],
            self.telefono[0],
            self.restaurante[0],
            self.fecha[0],
            self.hora,
            self.mesa[0],
            self.personas[0],
            self.comentarios
        )
        print("reserva: ", reserva)
        crear_reservacion(reserva)
        
        
    def verReservas(restaurante):
        resultado = ver_reservaciones(restaurante)
        return resultado
    
    def verReservasComensal(comensal):
        resultado = ver_reservaciones_comensal(comensal)
        return resultado
        
