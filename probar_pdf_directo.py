from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import os
import django
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

from ventas.models import Factura

def generar_pdf_simple(request, pk):
    """Generar PDF de factura simplificado"""
    try:
        factura = Factura.objects.get(pk=pk)
        
        # Crear buffer para PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Contenido del PDF
        title = Paragraph(f"FACTURA {factura.numero}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información básica
        info = f"""
        <b>Cliente:</b> {factura.cliente.nombre_completo}<br/>
        <b>Documento:</b> {factura.cliente.numero_documento}<br/>
        <b>Fecha:</b> {factura.fecha_creacion.strftime('%d/%m/%Y')}<br/>
        <b>Estado:</b> {factura.estado}<br/>
        <b>Total:</b> ${factura.total}
        """
        
        info_para = Paragraph(info, styles['Normal'])
        elements.append(info_para)
        
        # Construir PDF
        doc.build(elements)
        
        # Retornar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero}.pdf"'
        
        print(f"✅ PDF generado para factura {factura.numero}")
        return response
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return HttpResponse(f"Error: {e}", status=500)

if __name__ == "__main__":
    # Probar generación directa
    print("🔧 PROBANDO GENERACIÓN DIRECTA DE PDF")
    print("=" * 50)
    
    facturas = Factura.objects.all()
    print(f"📋 Facturas disponibles: {facturas.count()}")
    
    if facturas.exists():
        factura = facturas.first()
        print(f"📄 Generando PDF para factura: {factura.numero}")
        
        # Simular request básico
        class MockRequest:
            def __init__(self):
                pass
        
        mock_request = MockRequest()
        response = generar_pdf_simple(mock_request, factura.id)
        
        if response.status_code == 200:
            print(f"✅ PDF generado exitosamente ({len(response.content)} bytes)")
        else:
            print(f"❌ Error en PDF: {response.status_code}")
    else:
        print("❌ No hay facturas para probar")