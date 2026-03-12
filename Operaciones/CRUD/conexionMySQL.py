import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
load_dotenv()

def conexionMySQL():
    try:
     #conexion, importante estar al tanto de cada dato
        conexion = mysql.connector.connect(
        user="avnadmin", 
        password = os.getenv("MysqlPassword"),
        host = "TU HOST",
        database = "Proyecto_Equipo3", 
        port="24529")
        return conexion
    
    except Error:
        print("Error")

conexion = conexionMySQL()
 
def crearCursor():
    return conexion.cursor()

def commit():
    conexion.commit() 
