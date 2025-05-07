from flask import Blueprint, render_template, request, redirect, url_for, Flask, session
from entrada_producto import entrada_producto
from salida_producto import salida_producto
from mi_cuenta import mi_cuenta
from conexion import get_db_connection
from login import login
from reportes_ventas import reportes_ventas as generar_reportes  # Cambio de nombre aquí
from ver_productos import ver_productos_bp  # Corregí "ver_products"
from editar_producto import producto_bp
from dotenv import load_dotenv
import os  # Importación faltante

load_dotenv()
app = Flask(__name__, template_folder='templates')
app.secret_key = 'tu_clave_secreta'



@app.route('/', methods=['GET', 'POST'])
def home():
    # Probar la conexión a la base de datos
    try:
        conn = get_db_connection()
        print("¡Conexión a PostgreSQL exitosa!")
        conn.close()
    except Exception as e:
        print(f"Error al conectar a PostgreSQL: {e}")

    # Manejar el login
    resultado_login = login()
    if resultado_login:
        return resultado_login  # Redirigir o mostrar un mensaje de error

    # Si es una solicitud GET, mostrar el formulario de login
    return render_template('login.html')


@app.route('/index')
def index():
    if 'usuario' in session and session['usuario']['rol'] == 'administrador':
        return render_template('index.html')
    else:
        return redirect(url_for('home'))


# Ruta para Entrada de Producto
app.add_url_rule('/entrada_producto', 'entrada_producto', entrada_producto, methods=['GET', 'POST'])

# Ruta para Salida de Producto
app.register_blueprint(salida_producto)

# Ruta para Mi Cuenta
app.add_url_rule('/mi_cuenta', 'mi_cuenta', mi_cuenta)

# Ruta para Reportes de Ventas
@app.route('/reportes_ventas')
def mostrar_reportes_ventas():  # Cambiado el nombre de la función
    # Pasa todos los parámetros a la función importada
    return generar_reportes()

# Registrar blueprint sin prefijo para mantener URL simple
app.register_blueprint(ver_productos_bp)

# Asegúrate de registrar el blueprint con el prefijo correcto
app.register_blueprint(producto_bp)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))  # Cambiado de 'login' a 'home'

if __name__ == '__main__':
    app.run(debug=True)