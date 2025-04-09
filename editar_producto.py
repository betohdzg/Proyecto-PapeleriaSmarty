from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from conexion import get_db_connection
import psycopg2.extras
import os

# Cambiamos el nombre del Blueprint para evitar conflictos
producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/producto/<string:producto_id>/editar', methods=['GET'])
def mostrar_formulario_edicion(producto_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT p.*, c.nombre_categoria 
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.id_productos = %s
        """, (producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('ver_productos.mostrar_productos'))
        
        cur.execute("SELECT id_categoria, nombre_categoria FROM categorias")
        categorias = cur.fetchall()
        
        producto = dict(producto)
        if producto['foto_url']:
            producto['foto_url'] = producto['foto_url'].replace('\\', '/')
            if not producto['foto_url'].startswith('/static/'):
                producto['foto_url'] = f"/static/{producto['foto_url'].lstrip('/')}"
        
        return render_template('editar_producto.html', 
                           producto=producto,
                           categorias=categorias)
    
    except Exception as e:
        print(f"Error al cargar formulario de edición: {str(e)}")
        flash('Error al cargar el formulario de edición', 'error')
        return redirect(url_for('ver_productos.mostrar_productos'))
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@producto_bp.route('/producto/<string:producto_id>/actualizar', methods=['POST'])
def actualizar_producto(producto_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar si el producto existe
        cur.execute("SELECT id_productos FROM productos WHERE id_productos = %s", (producto_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        # Obtener datos del formulario con valores por defecto
        nombre = request.form.get('nombre_producto', '')
        descripcion = request.form.get('descripcion', '')
        
        try:
            precio = float(request.form.get('precio', 0))
            cantidad = int(request.form.get('cantidad', 0))
            minimo = int(request.form.get('minimo', 0))
            id_categoria = int(request.form.get('id_categoria', 0))
        except ValueError as e:
            return jsonify({'success': False, 'error': 'Valores numéricos inválidos'}), 400
        
        # Validar campos requeridos
        if not nombre or not descripcion or id_categoria == 0:
            return jsonify({'success': False, 'error': 'Todos los campos son requeridos'}), 400
        
        # Manejar la imagen
        foto = request.files.get('foto')
        update_query = """
            UPDATE productos SET
            nombre_producto = %s, descripcion = %s, precio = %s,
            cantidad = %s, minimo = %s, id_categoria = %s
        """
        params = [nombre, descripcion, precio, cantidad, minimo, id_categoria]
        
        if foto and foto.filename:
            filename = f"producto_{producto_id}_{foto.filename}"
            filepath = os.path.join('static', 'uploads', filename)
            foto.save(filepath)
            update_query += ", foto_url = %s"
            params.append(filepath)
        
        update_query += " WHERE id_productos = %s RETURNING id_productos"
        params.append(producto_id)
        
        cur.execute(update_query, tuple(params))
        
        if not cur.fetchone():
            return jsonify({'success': False, 'error': 'No se pudo actualizar el producto'}), 400
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Producto actualizado correctamente',
            'redirect': url_for('ver_productos.mostrar_productos')
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar producto: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno al actualizar el producto'
        }), 500
        
    finally:
        if 'cur' in locals(): 
            cur.close()
        if 'conn' in locals(): 
            conn.close()