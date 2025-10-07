from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, F, Value
from inventario.models import Producto, RecomendacionReposicion
from django.db.models import Sum
import logging

class Command(BaseCommand):
    help = 'Genera recomendaciones automáticas de reposición basadas en análisis de ventas y stock'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--productos',
            nargs='+',
            type=str,
            help='Códigos específicos de productos a analizar',
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar generación aunque ya existan recomendaciones activas',
        )
        parser.add_argument(
            '--solo-criticos',
            action='store_true', 
            help='Analizar solo productos con stock crítico',
        )
        parser.add_argument(
            '--dias-analisis',
            type=int,
            default=30,
            help='Días de historial de ventas a analizar (default: 30)',
        )
        
    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS('🤖 GENERADOR AUTOMÁTICO DE RECOMENDACIONES'))
        self.stdout.write("=" * 80)
        
        # Obtener productos a analizar
        if options['productos']:
            productos = Producto.objects.filter(
                codigo__in=options['productos'],
                activo=True
            ).annotate(
                stock_total_calculated=Sum('stock__cantidad')
            )
            self.stdout.write(f"📦 Analizando productos específicos: {', '.join(options['productos'])}")
        elif options['solo_criticos']:
            productos = Producto.objects.filter(
                activo=True
            ).annotate(
                stock_total_calculated=Sum('stock__cantidad')
            ).filter(
                stock_total_calculated__lt=F('stock_minimo')
            )
            self.stdout.write("⚠️ Analizando solo productos con alerta de stock")
        else:
            # Analizar todos los productos activos con stock o ventas recientes
            productos = Producto.objects.filter(activo=True).annotate(
                stock_total_calculated=Sum('stock__cantidad')
            )
            self.stdout.write("🔍 Analizando todos los productos activos")
        
        self.stdout.write(f"Total de productos a analizar: {productos.count()}")
        self.stdout.write("-" * 80)
        
        # Contadores
        recomendaciones_generadas = 0
        productos_analizados = 0
        productos_sin_necesidad = 0
        errores = 0
        
        for producto in productos:
            productos_analizados += 1
            
            try:
                self.stdout.write(f"\n📦 {producto.codigo} - {producto.nombre}")
                
                # Verificar si tiene stock
                stock_actual = getattr(producto, 'stock_total_calculated', None) or producto.stock_total
                self.stdout.write(f"   Stock actual: {stock_actual} unidades (mínimo: {producto.stock_minimo})")
                
                # Generar recomendación
                recomendacion = producto.generar_recomendacion_inteligente(
                    forzar=options['forzar']
                )
                
                if recomendacion:
                    recomendaciones_generadas += 1
                    
                    self.stdout.write(
                        f"   ✅ Recomendación generada: {recomendacion.get_prioridad_display()}"
                    )
                    self.stdout.write(f"      💰 Cantidad sugerida: {recomendacion.cantidad_sugerida} unidades")
                    self.stdout.write(f"      📊 Cobertura actual: {recomendacion.descripcion_cobertura}")
                    self.stdout.write(f"      📈 Tendencia ventas: {recomendacion.tendencia_porcentaje:+.1f}%")
                    
                    if recomendacion.proveedor_sugerido:
                        self.stdout.write(f"      🏭 Proveedor sugerido: {recomendacion.proveedor_sugerido.nombre}")
                        if recomendacion.valor_total_sugerido:
                            self.stdout.write(f"      💵 Valor estimado: ${recomendacion.valor_total_sugerido:,.0f}")
                    
                    if recomendacion.fecha_agotamiento_estimada:
                        self.stdout.write(f"      ⏰ Agotamiento estimado: {recomendacion.fecha_agotamiento_estimada}")
                    
                    self.stdout.write(f"      📝 Razón: {recomendacion.razon_principal}")
                    
                    # Color según prioridad
                    if recomendacion.prioridad == 'critica':
                        status_style = self.style.ERROR
                    elif recomendacion.prioridad == 'alta':
                        status_style = self.style.WARNING  
                    elif recomendacion.prioridad == 'media':
                        status_style = self.style.NOTICE
                    else:
                        status_style = self.style.SUCCESS
                        
                    self.stdout.write(
                        status_style(f"      🚨 PRIORIDAD: {recomendacion.get_prioridad_display()}")
                    )
                    
                else:
                    productos_sin_necesidad += 1
                    self.stdout.write("   ✓ No requiere reposición en este momento")
                    
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error al analizar: {str(e)}")
                )
                logging.error(f"Error analizando producto {producto.codigo}: {str(e)}")
        
        # Resumen final
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE ANÁLISIS'))
        self.stdout.write("=" * 80)
        
        self.stdout.write(f"📦 Productos analizados: {productos_analizados}")
        self.stdout.write(f"✅ Recomendaciones generadas: {recomendaciones_generadas}")
        self.stdout.write(f"✓ Productos sin necesidad: {productos_sin_necesidad}")
        
        if errores > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores encontrados: {errores}"))
        
        # Estadísticas por prioridad
        if recomendaciones_generadas > 0:
            self.stdout.write("\n📋 RECOMENDACIONES POR PRIORIDAD:")
            
            from django.db.models import Count
            
            stats = RecomendacionReposicion.objects.filter(
                fecha_generacion__date=timezone.now().date(),
                activa=True
            ).values('prioridad').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            for stat in stats:
                prioridad = stat['prioridad']
                cantidad = stat['cantidad']
                
                if prioridad == 'critica':
                    icon = "🚨"
                    style = self.style.ERROR
                elif prioridad == 'alta': 
                    icon = "⚠️"
                    style = self.style.WARNING
                elif prioridad == 'media':
                    icon = "📊"
                    style = self.style.NOTICE
                else:
                    icon = "ℹ️"
                    style = self.style.SUCCESS
                    
                self.stdout.write(
                    style(f"   {icon} {prioridad.title()}: {cantidad} recomendaciones")
                )
        
        # Valor total de inversión sugerida
        valor_total_inversion = RecomendacionReposicion.objects.filter(
            fecha_generacion__date=timezone.now().date(),
            activa=True,
            valor_total_sugerido__isnull=False
        ).aggregate(
            total=Sum('valor_total_sugerido')
        )['total'] or 0
        
        if valor_total_inversion > 0:
            self.stdout.write(f"\n💰 Inversión total sugerida: ${valor_total_inversion:,.0f}")
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS('🎉 ANÁLISIS COMPLETADO'))
        self.stdout.write("=" * 80)
        
        if recomendaciones_generadas > 0:
            self.stdout.write("📱 Para revisar las recomendaciones, visite:")
            self.stdout.write("   http://127.0.0.1:8000/inventario/recomendaciones/")
        else:
            self.stdout.write("✓ Todos los productos tienen stock adecuado")