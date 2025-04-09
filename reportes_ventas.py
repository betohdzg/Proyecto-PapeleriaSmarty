from flask import render_template, request, make_response
from conexion import get_db_connection
import psycopg2.extras
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
from flask import make_response

def reportes_ventas():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    download = request.args.get('download') == 'pdf'
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if fecha_inicio and fecha_fin:
        cur.execute("""
            SELECT m.id_moviento, m.id_productos, m.tipo, 
                   m.cantidad, m.fecha, m.total_movimiento,
                   p.nombre_producto
            FROM movimientos m
            LEFT JOIN productos p ON m.id_productos = p.id_productos
            WHERE m.tipo = 'salida'
            AND m.fecha BETWEEN %s AND %s 
            ORDER BY m.fecha DESC;
        """, (fecha_inicio, fecha_fin))
        movimientos = cur.fetchall()
        
        if download:
            return generar_pdf(movimientos, fecha_inicio, fecha_fin)
    else:
        movimientos = []

    cur.close()
    conn.close()
    return render_template('reportes_ventas.html', movimientos=movimientos)

def generar_pdf(movimientos, fecha_inicio, fecha_fin):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          rightMargin=40, leftMargin=40,
                          topMargin=40, bottomMargin=40)
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'estilo_titulo',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#6A0DAD'),  # Morado de Papelería Smarty
        alignment=1  # Centrado
    )
    
    estilo_subtitulo = ParagraphStyle(
        'estilo_subtitulo',
        parent=styles['Heading2'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        alignment=1
    )
    
    # Contenido del PDF
    contenido = []
    
    # Título
    contenido.append(Paragraph("Papelería Smarty", estilo_titulo))
    contenido.append(Paragraph("Reporte de Ventas", estilo_titulo))
    contenido.append(Spacer(1, 12))
    
    # Subtítulo con fechas
    contenido.append(Paragraph(
        f"Del {fecha_inicio} al {fecha_fin}",
        estilo_subtitulo
    ))
    contenido.append(Spacer(1, 24))
    
    # Preparar datos de la tabla
    datos_tabla = [
        ['ID Movimiento', 'Producto', 'Tipo', 'Cantidad', 'Fecha', 'Total']
    ]
    
    for mov in movimientos:
        fecha_formateada = mov['fecha'].strftime('%d/%m/%Y %H:%M')
        total_formateado = f"${mov['total_movimiento']:.2f}"
        datos_tabla.append([
            str(mov['id_moviento']),
            mov['nombre_producto'],
            mov['tipo'],
            str(mov['cantidad']),
            fecha_formateada,
            total_formateado
        ])
    
    # Crear tabla con estilo
    tabla = Table(datos_tabla)
    estilo_tabla = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6A0DAD')),  # Morado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Filas
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5E6FF')),  # Morado claro
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D9B3FF')),  # Borde morado
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5E6FF')]),
    ])
    
    tabla.setStyle(estilo_tabla)
    contenido.append(tabla)
    
    # Construir PDF
    doc.build(contenido)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_ventas_{fecha_inicio}_al_{fecha_fin}.pdf'
    
    return response