from mysql.connector import Error
from Operaciones.CRUD.conexionMySQL import *
from Operaciones.ClasePadre import personas
from Operaciones.CRUD.Leer import loginAD, datosAdmin

class Shala(personas):
    def __init__(self, _correo, _password, _nombre, _apellido, _telefono):
        super().init(_correo, _password, _nombre, _apellido, _telefono)
        
        pass
    pass


    def login(correo, password):
        data = loginAD(correo)
        if data is None:
            return False
        if correo == data[0] and password == data[1]:
            return True
        else:
            return False
        
        
    def datosAdmin(correo):
        admin = datosAdmin(correo)
        return admin