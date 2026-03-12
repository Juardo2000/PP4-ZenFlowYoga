from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime

def generar_reporte_pdf(mes, año, datos_ventas, ventas_por_dia):
    """Genera un PDF con el reporte de ventas del mes usando reportlab"""
    
    meses_nombres = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    mes_nombre = meses_nombres[mes]
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    elements = []
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4a5b5b'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#8aa9a4'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Título
    elements.append(Paragraph("ZenFlow Yoga", titulo_style))
    elements.append(Paragraph(f"Reporte de Ventas - {mes_nombre} {año}", subtitulo_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Resumen de ventas
    elements.append(Paragraph("Resumen de Ventas", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Tabla de resumen
    resumen_data = [
        ['Total Ingresos', f"${datos_ventas['total_ingresos']:,.2f}"],
        ['Cantidad de Ventas', str(datos_ventas['cantidad_pagos'])],
        ['Día con más ventas', f"{ventas_por_dia['dia_mas_ventas']} ({ventas_por_dia['cantidad_max']} ventas)"]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[200, 200])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#8aa9a4')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f0f7f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e8e0d9')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(resumen_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Ventas por día de la semana
    elements.append(Paragraph("Ventas por Día de la Semana", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Tabla de ventas por día
    data_dias = [['Día', 'Cantidad de Ventas', 'Monto Total']]
    for dia, valores in ventas_por_dia['ventas_por_dia'].items():
        if valores['cantidad'] > 0:
            data_dias.append([dia, str(valores['cantidad']), f"${valores['monto']:,.2f}"])
    
    if len(data_dias) > 1:
        tabla_dias = Table(data_dias, colWidths=[150, 150, 150])
        tabla_dias.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8aa9a4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e8e0d9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#faf7f2'), colors.white])
        ]))
        elements.append(tabla_dias)
    else:
        elements.append(Paragraph("No hay ventas en este período", styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Detalle de pagos
    if datos_ventas['pagos']:
        elements.append(Paragraph("Detalle de Pagos", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Cabecera de tabla de pagos
        data_pagos = [['ID', 'Correo', 'Referencia', 'Monto', 'Fecha', 'Método']]
        
        for pago in datos_ventas['pagos']:
            # Formatear fecha
            if hasattr(pago[4], 'strftime'):
                fecha = pago[4].strftime('%d/%m/%Y')
            else:
                fecha = str(pago[4])
            
            # Convertir monto a float si es necesario
            monto = pago[3]
            if isinstance(monto, str):
                try:
                    monto = float(monto.replace('$', '').replace(',', ''))
                except:
                    monto = 0.0
            
            metodo = pago[6].replace('_', ' ').title() if pago[6] else 'N/A'
            
            # Acortar correo si es muy largo
            correo = pago[1]
            if len(correo) > 25:
                correo = correo[:22] + '...'
            
            data_pagos.append([
                str(pago[0]),
                correo,
                pago[2] if pago[2] else 'N/A',
                f"${monto:,.2f}",
                fecha,
                metodo
            ])
        
        tabla_pagos = Table(data_pagos, colWidths=[40, 100, 80, 70, 70, 80])
        tabla_pagos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8aa9a4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e8e0d9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#faf7f2'), colors.white])
        ]))
        elements.append(tabla_pagos)
        
        if len(datos_ventas['pagos']) > 20:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(f"* Mostrando 20 de {len(datos_ventas['pagos'])} pagos", styles['Italic']))
    else:
        elements.append(Paragraph("No hay pagos en este período", styles['Normal']))
    
    # Fecha de generación
    elements.append(Spacer(1, 0.3*inch))
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Reporte generado el {fecha_generacion}", styles['Italic']))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer