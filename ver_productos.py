from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from conexion import get_db_connection
import psycopg2.extras
import os
from flask import current_app, url_for

ver_productos_bp = Blueprint('ver_productos', __name__)

@ver_productos_bp.route('/ver_productos')
def mostrar_productos():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT id_productos, nombre_producto, precio, cantidad, foto_url
            FROM productos
            ORDER BY nombre_producto
        """)
        productos = cur.fetchall()
        
        productos_procesados = []
        for producto in productos:
            prod = dict(producto)
            
            # Normalización de rutas
            if prod['foto_url']:
                # Paso 1: Reemplazar barras invertidas
                foto_url = prod['foto_url'].replace('\\', '/')
                
                # Paso 2: Eliminar 'static/' si existe
                if foto_url.startswith('static/'):
                    foto_url = foto_url[7:]  # Elimina los primeros 7 caracteres
                
                # Paso 3: Asegurar que empiece con 'imagenes/'
                if not foto_url.startswith('imagenes/'):
                    foto_url = f"imagenes/{foto_url}"
                
                # Paso 4: Construir ruta final
                prod['foto_url'] = url_for('static', filename=foto_url)
                
                # Opcional: Verificar si el archivo existe físicamente
                ruta_fisica = os.path.join(current_app.static_folder, foto_url)
                if not os.path.exists(ruta_fisica):
                    print(f"Advertencia: No se encontró {ruta_fisica}")
                    prod['foto_url'] = url_for('static', filename='imagenes/imagen_no_disponible.jpg')
            
            productos_procesados.append(prod)
        
        return render_template('ver_productos.html', productos=productos_procesados)
    
    except Exception as e:
        print(f"Error al obtener productos: {str(e)}")
        flash('Error al cargar los productos', 'error')
        return render_template('ver_productos.html', productos=[])
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@ver_productos_bp.route('/editar_producto/<string:producto_id>')
def editar_producto(producto_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Obtener el producto
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
        
        # Obtener todas las categorías
        cur.execute("SELECT id_categoria, nombre_categoria FROM categorias")
        categorias = cur.fetchall()
        
        # Procesar foto_url si existe
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

@ver_productos_bp.route('/aumentar_stock/<string:producto_id>', methods=['POST'])
def aumentar_stock(producto_id):
    try:
        data = request.get_json()
        if not data or 'cantidad' not in data:
            return jsonify({'success': False, 'error': 'Datos inválidos'}), 400
        
        cantidad = int(data['cantidad'])
        if cantidad <= 0:
            return jsonify({'success': False, 'error': 'La cantidad debe ser positiva'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar si el producto existe
        cur.execute("SELECT cantidad, nombre_producto FROM productos WHERE id_productos = %s", (producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        # Actualizar el stock
        cur.execute("""
            UPDATE productos 
            SET cantidad = cantidad + %s
            WHERE id_productos = %s
            RETURNING cantidad, nombre_producto
        """, (cantidad, producto_id))
        
        # Obtener los resultados como tupla (sin DictCursor)
        resultado = cur.fetchone()
        nueva_cantidad = resultado[0]  # Primer elemento es cantidad
        nombre_producto = resultado[1]  # Segundo elemento es nombre
        conn.commit()
        
        return jsonify({
            'success': True,
            'nueva_cantidad': nueva_cantidad,
            'nombre_producto': nombre_producto,
            'message': f'Stock actualizado correctamente. Nuevo total: {nueva_cantidad}'
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'La cantidad debe ser un número válido'}), 400
    except Exception as e:
        print(f"Error al aumentar stock: {str(e)}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@ver_productos_bp.route('/eliminar_producto/<string:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Primero eliminar todos los movimientos relacionados
        cur.execute("DELETE FROM movimientos WHERE id_productos = %s", (producto_id,))
        
        # 2. Obtener nombre del producto antes de eliminarlo (accediendo por índice)
        cur.execute("SELECT nombre_producto FROM productos WHERE id_productos = %s", (producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        nombre_producto = producto[0]  # Accedemos por índice (0 para la primera columna)
        
        # 3. Eliminar el producto
        cur.execute("DELETE FROM productos WHERE id_productos = %s", (producto_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f"Producto '{nombre_producto}' eliminado correctamente"
        })
        
    except Exception as e:
        print(f"Error al eliminar producto: {str(e)}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()