from mysql.connector import Error
from Operaciones.CRUD.conexionMySQL import *
from Operaciones.CRUD.Agregar import registrar_restaurante
from Operaciones.CRUD.Leer import *

class Instructor():
    
    def __init__(self, _nombreRestaurante, _rif, _correo, _password, _telefono, _apertura, _cierre, _descripcion, _NumeroDeMesas, _fotos, _redesSociales, _Ubicacion):
        self.nombreRestaurante = _nombreRestaurante
        self.rif = _rif
        self.correo = _correo
        self.password = _password
        self.telefono = _telefono
        self.apertura = _apertura
        self.cierre = _cierre
        self.descripcion = _descripcion
        self.NumeroDeMesas = _NumeroDeMesas
        self.fotos = _fotos
        self.redesSociales = _redesSociales
        self.Ubicacion = _Ubicacion
        
    
    def agregarRestaurante(self):
        restaurante = (
        self.nombreRestaurante,
        self.rif,
        self.correo,
        self.password,
        self.telefono,
        self.apertura,
        self.cierre,
        self.descripcion,
        self.NumeroDeMesas,
        self.fotos,
        self.redesSociales,
        self.Ubicacion
    )
        registrar_restaurante(restaurante)
        
    def leerdatosRestaurante():
        datos = []
        restaurantes = leerInstructores()
        for restaurante in restaurantes:
            datos.append(restaurante)
        return datos
    
    def login(correo, password):
        data = loginRE(correo)
        if data is None:
            return False
        if correo == data[0] and password == data[1]:
            return True
        else:
            return False
        
    def datosIns(correo):
        res = datosIns(correo)
        return res