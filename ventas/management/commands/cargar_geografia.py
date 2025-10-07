from django.core.management.base import BaseCommand
from ventas.models import Departamento, Ciudad
import os

class Command(BaseCommand):
    help = 'Carga la geografía completa de Colombia desde citys.txt'

    def handle(self, *args, **options):
        self.stdout.write("🌍 Cargando geografía completa de Colombia...")

        # Leer el archivo citys.txt
        archivo_citys = 'citys.txt'
        if not os.path.exists(archivo_citys):
            self.stdout.write("❌ Error: No se encontró el archivo citys.txt")
            return

        departamentos_ciudades = {}

        # Intentar diferentes codificaciones
        encodings = ['latin-1', 'cp1252', 'utf-8', 'iso-8859-1']
        archivo_contenido = None

        for encoding in encodings:
            try:
                with open(archivo_citys, 'r', encoding=encoding) as archivo:
                    archivo_contenido = archivo.readlines()
                self.stdout.write(f"✅ Archivo leído correctamente con codificación: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if archivo_contenido is None:
            self.stdout.write("❌ Error: No se pudo leer el archivo con ninguna codificación")
            return

        # Procesar las líneas
        for i, linea in enumerate(archivo_contenido):
            if i == 0:  # Saltar encabezado
                continue
                
            linea = linea.strip()
            if linea and '\t' in linea:
                # El archivo usa tabulaciones como separador
                partes = linea.split('\t')
                if len(partes) >= 2:
                    departamento = partes[0].strip().upper()
                    ciudad = partes[1].strip().title()
                    
                    # Limpiar nombres
                    departamento = departamento.replace('"', '').strip()
                    ciudad = ciudad.replace('"', '').strip()
                    
                    if departamento and ciudad:
                        if departamento not in departamentos_ciudades:
                            departamentos_ciudades[departamento] = []
                        if ciudad not in departamentos_ciudades[departamento]:
                            departamentos_ciudades[departamento].append(ciudad)

        self.stdout.write(f"📖 Procesados {len(departamentos_ciudades)} departamentos del archivo")

        total_deps_creados = 0
        total_ciudades_creadas = 0

        # Crear departamentos y ciudades
        for dept_nombre, ciudades_lista in departamentos_ciudades.items():
            # Crear código único para departamento
            codigo_dept = dept_nombre[:3].upper()
            contador = 1
            codigo_original = codigo_dept
            
            # Asegurar que el código sea único
            while Departamento.objects.filter(codigo=codigo_dept).exists():
                codigo_dept = f"{codigo_original}{contador}"
                contador += 1
            
            # Crear departamento
            dept, created = Departamento.objects.get_or_create(
                nombre=dept_nombre,
                defaults={'codigo': codigo_dept}
            )
            
            if created:
                total_deps_creados += 1
                self.stdout.write(f"✅ Departamento: {dept_nombre}")
            
            # Crear ciudades para este departamento
            ciudades_dept_creadas = 0
            for ciudad_nombre in ciudades_lista:
                ciudad, created = Ciudad.objects.get_or_create(
                    nombre=ciudad_nombre,
                    departamento=dept,
                    defaults={'codigo_postal': ''}
                )
                
                if created:
                    total_ciudades_creadas += 1
                    ciudades_dept_creadas += 1
            
            if ciudades_dept_creadas > 0:
                self.stdout.write(f"  🏙️ {ciudades_dept_creadas} ciudades en {dept_nombre}")

        self.stdout.write(f"\n📊 Resumen final:")
        self.stdout.write(f"   • Departamentos creados: {total_deps_creados}")
        self.stdout.write(f"   • Ciudades creadas: {total_ciudades_creadas}")
        self.stdout.write(f"   • Total departamentos en BD: {Departamento.objects.count()}")
        self.stdout.write(f"   • Total ciudades en BD: {Ciudad.objects.count()}")

        # Mostrar algunos ejemplos
        self.stdout.write(f"\n🎯 Ejemplos de departamentos cargados:")
        for dept in Departamento.objects.all()[:5]:
            cant_ciudades = Ciudad.objects.filter(departamento=dept).count()
            self.stdout.write(f"   • {dept.nombre}: {cant_ciudades} ciudades")

        self.stdout.write("\n🎉 ¡Geografía completa de Colombia cargada exitosamente!")

        # Verificar que Bogotá esté disponible
        bogota = Ciudad.objects.filter(nombre__icontains='Bogota').first()
        if bogota:
            self.stdout.write(f"✅ Bogotá encontrada: {bogota.nombre}, {bogota.departamento.nombre}")
        else:
            self.stdout.write("⚠️ Bogotá no encontrada, verificar datos")