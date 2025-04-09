from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from conexion import get_db_connection

# Crear un Blueprint para las rutas de salida de producto
salida_producto = Blueprint('salida_producto', __name__)

@salida_producto.route('/salida_producto', methods=['GET', 'POST'])
def salida_producto_route():
    if request.method == 'POST':
        # Obtener datos del formulario
        id_o_nombre = request.form.get('id_producto')  # Puede ser ID o nombre
        cantidad_vendida = request.form.get('cantidad_vendida')

        # Depuración: imprime los datos del formulario
        print(f"Depuración: ID o nombre del producto: {id_o_nombre}, Cantidad Vendida: {cantidad_vendida}")

        # Validar que los datos no estén vacíos
        if not id_o_nombre or not cantidad_vendida:
            print("Depuración: Faltan datos (id_producto o cantidad_vendida)")
            return jsonify({'error': 'Faltan datos (id_producto o cantidad_vendida)'}), 400

        try:
            cantidad_vendida = int(cantidad_vendida)
        except ValueError:
            print("Depuración: Cantidad debe ser un número válido")
            return jsonify({'error': 'Cantidad debe ser un número válido'}), 400

        conexion = get_db_connection()
        cursor = conexion.cursor()

        try:
            # Buscar el producto por ID o nombre
            cursor.execute("""
                SELECT id_productos, cantidad, minimo, precio 
                FROM productos 
                WHERE id_productos = %s OR nombre_producto = %s
            """, (id_o_nombre, id_o_nombre))
            producto = cursor.fetchone()

            if not producto:
                print(f"Depuración: Producto no encontrado con ID o nombre: {id_o_nombre}")
                return jsonify({'error': 'Producto no encontrado'}), 404

            id_producto, stock_actual, stock_minimo, precio = producto

            if cantidad_vendida > stock_actual:
                print(f"Depuración: No hay suficiente stock para el producto {id_o_nombre}")
                return jsonify({'error': 'No hay suficiente stock'}), 400

            # Registrar salida en la tabla movimientos
            total_movimiento = cantidad_vendida * precio
            cursor.execute("""
                INSERT INTO movimientos (id_productos, tipo, cantidad, fecha, total_movimiento) 
                VALUES (%s, 'salida', %s, NOW(), %s)
            """, (id_producto, cantidad_vendida, total_movimiento))

            # Actualizar el stock del producto
            nuevo_stock = stock_actual - cantidad_vendida
            cursor.execute("UPDATE productos SET cantidad = %s WHERE id_productos = %s", (nuevo_stock, id_producto))

            # Verificar si el stock es menor o igual al mínimo
            if nuevo_stock <= stock_minimo:
                flash(f"Advertencia: El stock de {id_o_nombre} está bajo ({nuevo_stock} unidades)", 'warning')

            # Confirmar cambios
            conexion.commit()
            flash("Salida de producto registrada correctamente", 'success')
            print(f"Depuración: Salida registrada con éxito para el producto {id_o_nombre}")

        except Exception as e:
            conexion.rollback()
            print(f"Depuración: Error en la transacción - {str(e)}")
            return jsonify({'error': str(e)}), 500

        finally:
            cursor.close()
            conexion.close()

    # Si el método es GET, renderiza la plantilla HTML
    return render_template('salida_producto.html')

@salida_producto.route('/obtener_productos_principal')
def obtener_productos_principal():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_productos, nombre_producto, precio, foto_url, cantidad FROM productos limit 4")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    productos_list = []
    for p in productos:
        # Limpia la ruta de la imagen
        foto_url = p[3].replace('\\', '/')  # Convertir barras
        foto_url = foto_url.replace('static/', '')  # Eliminar static/ si existe
        
        if not foto_url.startswith('imagenes/'):
            foto_url = f"imagenes/{foto_url}"
            
        productos_list.append({
            'id_productos': p[0],
            'nombre_producto': p[1],
            'precio': float(p[2]),
            'foto_url': f"/static/{foto_url}",
            'cantidad': p[4]
        })
    
    return jsonify(productos_list)

@salida_producto.route('/obtener_ventas_productos')
def obtener_ventas_productos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Consulta que suma las cantidades vendidas por producto
    cur.execute("""
        SELECT p.nombre_producto, SUM(m.cantidad) as total_vendido
        FROM movimientos m
        JOIN productos p ON m.id_productos = p.id_productos
        WHERE m.tipo = 'salida'
        GROUP BY p.nombre_producto
        ORDER BY total_vendido DESC
    """)
    
    ventas = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([{
        'nombre_producto': v[0],
        'total_vendido': v[1] or 0
    } for v in ventas])

@salida_producto.route('/obtener_productos')
def obtener_productos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_productos, nombre_producto, precio FROM productos")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    productos_list = [{
        'id_productos': p[0],
        'nombre_producto': p[1],
        'precio': float(p[2])
    } for p in productos]
    
    return jsonify(productos_list)