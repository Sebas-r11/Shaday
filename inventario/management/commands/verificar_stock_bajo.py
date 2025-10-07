from django.core.management.base import BaseCommand
from django.db.models import Q, F, Sum
from inventario.models import Producto, AlertaStock
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica productos con stock bajo y genera alertas automáticas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-alertas',
            action='store_true',
            help='Crear alertas en la base de datos',
        )
        parser.add_argument(
            '--simular-stock',
            action='store_true',
            help='Simular datos de stock bajo para pruebas',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando productos con stock bajo...')
        
        # Obtener productos activos con stock mínimo definido
        productos = Producto.objects.filter(
            activo=True,
            stock_minimo__gt=0
        ).select_related('categoria')
        
        alertas_creadas = 0
        alertas_actualizadas = 0
        productos_ok = 0
        
        for producto in productos:
            # Simular stock actual para propósitos de demostración
            if options['simular_stock']:
                # Crear algunos productos con stock bajo intencionalmente
                import random
                if producto.id % 3 == 0:  # Cada 3er producto tendrá stock bajo
                    stock_actual = max(0, producto.stock_minimo - random.randint(1, 5))
                elif producto.id % 5 == 0:  # Cada 5to producto estará agotado
                    stock_actual = 0
                else:
                    stock_actual = producto.stock_minimo + random.randint(1, 20)
            else:
                # En un sistema real aquí se calcularía el stock real
                # Por ahora simulamos basado en el stock mínimo
                stock_actual = max(0, producto.stock_minimo - 2)
            
            # Generar alerta automática si es necesario
            if options['crear_alertas']:
                # Usar el método del modelo para generar alertas
                alerta = AlertaStock.generar_alerta_automatica(producto)
                
                if alerta:
                    if hasattr(alerta, '_state') and alerta._state.adding:
                        alertas_creadas += 1
                        self.stdout.write(
                            self.style.WARNING(f'🚨 Nueva alerta: {producto.codigo} - {producto.nombre}')
                        )
                    else:
                        alertas_actualizadas += 1
                        self.stdout.write(
                            self.style.WARNING(f'🔄 Alerta actualizada: {producto.codigo} - {producto.nombre}')
                        )
                else:
                    productos_ok += 1
            else:
                # Solo mostrar información sin crear alertas
                if stock_actual <= producto.stock_minimo:
                    nivel_icon = '🔴' if stock_actual == 0 else '🟡'
                    self.stdout.write(
                        f"{nivel_icon} {producto.codigo} - {producto.nombre}: "
                        f"Stock actual: {stock_actual}, Mínimo: {producto.stock_minimo}"
                    )
        
        # Mostrar resumen
        if options['crear_alertas']:
            total_alertas = alertas_creadas + alertas_actualizadas
            self.stdout.write(
                self.style.SUCCESS(
                    f'\\n📊 RESUMEN DE ALERTAS:'
                )
            )
            self.stdout.write(f'   🆕 Nuevas alertas: {alertas_creadas}')
            self.stdout.write(f'   � Alertas actualizadas: {alertas_actualizadas}')
            self.stdout.write(f'   ✅ Productos OK: {productos_ok}')
            
            if total_alertas > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\\n⚠️  TOTAL: {total_alertas} productos requieren atención'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\\n✅ Todos los productos tienen stock suficiente'
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\\n✅ Verificación completada (modo solo lectura)'
                )
            )
            self.stdout.write('   💡 Usa --crear-alertas para guardar alertas en la base de datos')
            self.stdout.write('   💡 Usa --simular-stock para generar datos de prueba')
    
    def crear_alertas_prueba(self):
        """Crear algunas alertas de prueba para demostración"""
        productos = Producto.objects.filter(activo=True)[:5]
        
        for i, producto in enumerate(productos):
            AlertaStock.objects.get_or_create(
                producto=producto,
                tipo_alerta='stock_bajo' if i % 2 == 0 else 'agotado',
                defaults={
                    'nivel': 'critico' if i % 3 == 0 else 'advertencia',
                    'mensaje': f'Alerta de prueba para {producto.nombre}',
                    'stock_actual': i,
                    'stock_minimo': producto.stock_minimo,
                    'activa': True
                }
            )