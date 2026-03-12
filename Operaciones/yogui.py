from mysql.connector import Error
from Operaciones.CRUD.Leer import *
from Operaciones.CRUD.Agregar import registrar_comensal
from Operaciones.CRUD.conexionMySQL import *
from Operaciones.ClasePadre import personas


class Yogui(personas):
    def __init__(self, _correo, _password, _nombre, _apellido, _telefono):
        super().init(_correo, _password, _nombre, _apellido, _telefono)
        
        
    def leerYogui(correo):
        n = leerYogui(correo)
        return n

    def login(correo, password):
        data = loginCO(correo)
        if data is None:
            return False
        if correo == data[0] and password == data[1]:
            return True
        else:
            return False
        

    def crearComensales(self):
        comensal = (
            self.correo,
            self.password,
            self.nombre,
            self.apellido,
            self.telefono
        )
        registrar_comensal(comensal)

    def datosYogui(correo):
        Yogui = datosYogui(correo)
        return Yogui
    


