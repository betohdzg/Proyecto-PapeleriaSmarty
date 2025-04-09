from flask import redirect, url_for, session, request, flash
from conexion import get_db_connection

def validar_login(correo, contrasena):
    """
    Función para validar el login.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Buscar el usuario en la base de datos
        cur.execute('SELECT nombre, correo, contrasena, rol FROM usuarios WHERE correo = %s', (correo,))
        usuario = cur.fetchone()

        if not usuario:
            return False  # Usuario no encontrado

        # Verificar la contraseña (en este caso, se usa MD5 como en PHP)
        if usuario[2] == contrasena:  # Comparación directa (MD5)
            session['correo'] = usuario[1]
            session['usuario'] = {
                'nombre': usuario[0],
                'correo': usuario[1],
                'rol': usuario[3]
            }
            return True  # Login exitoso
        else:
            return False  # Contraseña incorrecta

    finally:
        cur.close()
        conn.close()

def login():
    """
    Función para manejar el login.
    """
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        if not correo or not contrasena:
            flash('Por favor, complete todos los campos', 'warning')
            return redirect(url_for('home'))

        # Validar el login
        if validar_login(correo, contrasena):
            return redirect(url_for('index'))  # Redirigir a index.html
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('home'))

    # Si es una solicitud GET, simplemente renderiza el formulario
    return None