#!/usr/bin/env python
"""
Diagnóstico completo del sistema para detectar correcciones pendientes
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_reyes.settings')
django.setup()

def verificar_urls():
    """Verifica que todas las URLs estén funcionando"""
    print("🔗 VERIFICACIÓN DE URLs")
    print("-" * 30)
    
    try:
        from django.urls import reverse
        from django.test import RequestFactory, Client
        
        urls_criticas = [
            'ventas:dashboard',
            'ventas:cliente_list',
            'ventas:cotizacion_list',
            'ventas:pedido_list',
            'ventas:factura_list',
            'compras:dashboard',
            'inventario:producto_list',
            'inventario:bodega_list',
            'accounts:login'
        ]
        
        errores = []
        for url_name in urls_criticas:
            try:
                url = reverse(url_name)
                print(f"   ✅ {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ {url_name}: {e}")
                errores.append(f"{url_name}: {e}")
        
        return len(errores) == 0, errores
        
    except Exception as e:
        print(f"   ❌ Error en verificación de URLs: {e}")
        return False, [str(e)]

def verificar_modelos():
    """Verifica la integridad de los modelos"""
    print("\n📊 VERIFICACIÓN DE MODELOS")
    print("-" * 30)
    
    try:
        from django.apps import apps
        
        errores = []
        
        # Verificar que los modelos principales existan
        modelos_criticos = [
            ('ventas', 'Cliente'),
            ('ventas', 'Cotizacion'),
            ('ventas', 'Pedido'),
            ('ventas', 'Factura'),
            ('compras', 'Proveedor'),
            ('compras', 'OrdenCompra'),
            ('inventario', 'Producto'),
            ('inventario', 'Categoria'),
            ('inventario', 'Bodega'),
            ('accounts', 'User')
        ]
        
        for app_name, model_name in modelos_criticos:
            try:
                model = apps.get_model(app_name, model_name)
                count = model.objects.count()
                print(f"   ✅ {app_name}.{model_name}: {count} registros")
            except Exception as e:
                print(f"   ❌ {app_name}.{model_name}: {e}")
                errores.append(f"{app_name}.{model_name}: {e}")
        
        return len(errores) == 0, errores
        
    except Exception as e:
        print(f"   ❌ Error en verificación de modelos: {e}")
        return False, [str(e)]

def verificar_templates_criticos():
    """Verifica que los templates críticos existan"""
    print("\n🎨 VERIFICACIÓN DE TEMPLATES CRÍTICOS")
    print("-" * 30)
    
    templates_criticos = [
        ('templates', 'base.html'),
        ('templates', 'ventas/dashboard.html'),
        ('templates', 'ventas/cliente_list.html'),
        ('templates', 'ventas/pedido_list.html'),
        ('compras/templates', 'compras/dashboard.html'),
        ('templates', 'inventario/producto_list.html')
    ]
    
    base_dir = Path(__file__).parent
    
    errores = []
    for template_dir, template in templates_criticos:
        template_path = base_dir / template_dir / template
        if template_path.exists():
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template}")
            errores.append(template)
    
    return len(errores) == 0, errores

def verificar_vistas():
    """Verifica que las vistas principales estén definidas"""
    print("\n👁️  VERIFICACIÓN DE VISTAS")
    print("-" * 30)
    
    try:
        # Verificar importaciones de vistas
        vistas_criticas = [
            ('ventas.views', 'dashboard_view'),
            ('ventas.clientes_views', 'ClienteListView'),
            ('ventas.pedidos_views', 'PedidoListView'),
            ('compras.ordenes_views', 'compras_dashboard'),
            ('inventario.views', 'ProductoListView')
        ]
        
        errores = []
        for module_path, view_name in vistas_criticas:
            try:
                module = __import__(module_path, fromlist=[view_name])
                view = getattr(module, view_name)
                print(f"   ✅ {module_path}.{view_name}")
            except Exception as e:
                print(f"   ❌ {module_path}.{view_name}: {e}")
                errores.append(f"{module_path}.{view_name}: {e}")
        
        return len(errores) == 0, errores
        
    except Exception as e:
        print(f"   ❌ Error en verificación de vistas: {e}")
        return False, [str(e)]

def verificar_configuracion():
    """Verifica la configuración de Django"""
    print("\n⚙️  VERIFICACIÓN DE CONFIGURACIÓN")
    print("-" * 30)
    
    try:
        from django.conf import settings
        
        configuraciones = [
            ('DEBUG', settings.DEBUG),
            ('INSTALLED_APPS', len(settings.INSTALLED_APPS)),
            ('DATABASES', 'default' in settings.DATABASES),
            ('STATIC_URL', bool(settings.STATIC_URL)),
            ('TEMPLATES', len(settings.TEMPLATES) > 0)
        ]
        
        for config, valor in configuraciones:
            print(f"   ✅ {config}: {valor}")
        
        return True, []
        
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False, [str(e)]

def generar_resumen_final():
    """Genera un resumen final del diagnóstico"""
    print("\n" + "="*50)
    print("📋 DIAGNÓSTICO COMPLETO DEL SISTEMA")
    print("="*50)
    
    # Ejecutar todas las verificaciones
    urls_ok, urls_errores = verificar_urls()
    modelos_ok, modelos_errores = verificar_modelos()
    templates_ok, templates_errores = verificar_templates_criticos()
    vistas_ok, vistas_errores = verificar_vistas()
    config_ok, config_errores = verificar_configuracion()
    
    # Resumen
    print(f"\n🎯 RESUMEN DE VERIFICACIONES")
    print("-" * 30)
    print(f"   URLs: {'✅ OK' if urls_ok else '❌ ERRORES'}")
    print(f"   Modelos: {'✅ OK' if modelos_ok else '❌ ERRORES'}")
    print(f"   Templates: {'✅ OK' if templates_ok else '❌ ERRORES'}")
    print(f"   Vistas: {'✅ OK' if vistas_ok else '❌ ERRORES'}")
    print(f"   Configuración: {'✅ OK' if config_ok else '❌ ERRORES'}")
    
    # Errores encontrados
    todos_errores = urls_errores + modelos_errores + templates_errores + vistas_errores + config_errores
    
    if todos_errores:
        print(f"\n🚨 ERRORES ENCONTRADOS ({len(todos_errores)})")
        print("-" * 30)
        for i, error in enumerate(todos_errores, 1):
            print(f"   {i}. {error}")
        
        print(f"\n⚠️  SE REQUIEREN CORRECCIONES")
    else:
        print(f"\n🎉 ¡NO SE ENCONTRARON ERRORES!")
        print(f"   El sistema está funcionando correctamente")
    
    return len(todos_errores) == 0

if __name__ == "__main__":
    sistema_ok = generar_resumen_final()
    if sistema_ok:
        print(f"\n✅ DIAGNÓSTICO COMPLETO: SISTEMA LISTO")
    else:
        print(f"\n❌ DIAGNÓSTICO COMPLETO: SE REQUIEREN CORRECCIONES")