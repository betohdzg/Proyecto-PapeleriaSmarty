from flask import render_template, request, redirect, url_for, flash
import os
from conexion import get_db_connection

# Configura la ruta de la carpeta de imágenes
UPLOAD_FOLDER = os.path.join('static', 'imagenes')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def entrada_producto():
    if request.method == 'POST':
        # Obtener los datos del formulario
        id_productos = request.form['id_productos']
        nombre_producto = request.form['nombre_producto']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        cantidad = int(request.form['cantidad'])
        minimo = int(request.form['minimo'])
        id_categoria = int(request.form['id_categoria'])

        # Manejar la subida de la imagen
        if 'foto' not in request.files:
            flash('No se ha seleccionado ninguna imagen.', 'error')
            return redirect(request.url)
        
        foto = request.files['foto']
        if foto.filename == '':
            flash('No se ha seleccionado ninguna imagen.', 'error')
            return redirect(request.url)
        
        if foto and allowed_file(foto.filename):
            filename = foto.filename
            foto_path = os.path.join(UPLOAD_FOLDER, filename)
            foto.save(foto_path)
        else:
            flash('Formato de imagen no permitido.', 'error')
            return redirect(request.url)

        # Insertar el producto en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO productos (id_productos, nombre_producto, descripcion, precio, foto_url, cantidad, minimo, id_categoria) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (id_productos, nombre_producto, descripcion, precio, foto_path, cantidad, minimo, id_categoria)
            )
            conn.commit()
            flash('Producto agregado exitosamente.', 'success')  # Mensaje de éxito
        except Exception as e:
            conn.rollback()
            flash(f'Error al agregar el producto: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('entrada_producto'))

    # Si es una solicitud GET, obtener las categorías y mostrar el formulario
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_categoria, nombre_categoria FROM categorias")
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('entrada_producto.html', categorias=categorias)