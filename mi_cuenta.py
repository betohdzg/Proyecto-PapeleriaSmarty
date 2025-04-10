from flask import Flask, redirect, render_template, session, url_for
from conexion import get_db_connection

app = Flask(__name__)

@app.route('/mi_cuenta')
def mi_cuenta():
    if 'usuario' not in session:
        return redirect(url_for('home'))  # Redirigir si no hay sesión

    # Obtener los datos del usuario desde la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, correo, contrasena FROM usuarios WHERE correo = %s", (session['usuario']['correo'],))
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return "Usuario no encontrado", 404

    # Pasar los datos a la plantilla
    return render_template('mi_cuenta.html', nombre=usuario[0], correo=usuario[1], contrasena=usuario[2])