"""
Predictor de demanda usando Machine Learning
Implementa varios algoritmos para predecir la demanda futura
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime, timedelta
import joblib
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone


class PredictorDemanda:
    """
    Sistema de predicción de demanda usando múltiples algoritmos ML
    """
    
    def __init__(self):
        self.modelos = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression()
        }
        self.scaler = StandardScaler()
        self.mejor_modelo = None
        self.precision_modelo = 0.0
    
    def extraer_caracteristicas(self, producto_id, dias_historicos=365):
        """
        Extrae características relevantes para la predicción
        """
        from analytics.models import EventoInventario
        from ventas.models import ItemPedido
        from django.db.models import F
        
        fecha_inicio = timezone.now() - timedelta(days=dias_historicos)
        
        # Obtener eventos de ventas del producto
        eventos = EventoInventario.objects.filter(
            producto_id=producto_id,
            tipo_evento='venta',
            fecha_evento__gte=fecha_inicio
        ).order_by('fecha_evento')
        
        if not eventos.exists():
            return None, None
        
        # Convertir a DataFrame para análisis
        data = []
        for evento in eventos:
            fecha = evento.fecha_evento
            data.append({
                'fecha': fecha,
                'cantidad': evento.cantidad,
                'precio': float(evento.precio_unitario),
                'dia_semana': fecha.weekday(),
                'mes': fecha.month,
                'dia_mes': fecha.day,
                'es_fin_semana': fecha.weekday() >= 5,
                'cliente_id': evento.cliente_id if evento.cliente else None,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return None, None
        
        # Agregar por día para tener series temporales consistentes
        df['fecha_solo'] = df['fecha'].dt.date
        ventas_diarias = df.groupby('fecha_solo').agg({
            'cantidad': 'sum',
            'precio': 'mean',
            'dia_semana': 'first',
            'mes': 'first',
            'dia_mes': 'first',
            'es_fin_semana': 'first',
        }).reset_index()
        
        # Crear características adicionales
        ventas_diarias['ventas_7d_promedio'] = ventas_diarias['cantidad'].rolling(7, min_periods=1).mean()
        ventas_diarias['ventas_30d_promedio'] = ventas_diarias['cantidad'].rolling(30, min_periods=1).mean()
        ventas_diarias['tendencia_7d'] = ventas_diarias['cantidad'].pct_change(7).fillna(0)
        ventas_diarias['precio_relativo'] = ventas_diarias['precio'] / ventas_diarias['precio'].mean()
        
        # Variables estacionales
        ventas_diarias['es_inicio_mes'] = ventas_diarias['dia_mes'] <= 7
        ventas_diarias['es_fin_mes'] = ventas_diarias['dia_mes'] >= 25
        
        # Limpiar datos faltantes
        ventas_diarias = ventas_diarias.fillna(0)
        
        # Separar características y target
        caracteristicas = [
            'dia_semana', 'mes', 'dia_mes', 'es_fin_semana',
            'ventas_7d_promedio', 'ventas_30d_promedio', 'tendencia_7d',
            'precio_relativo', 'es_inicio_mes', 'es_fin_mes'
        ]
        
        X = ventas_diarias[caracteristicas].values
        y = ventas_diarias['cantidad'].values
        
        return X, y
    
    def entrenar_modelos(self, X, y):
        """
        Entrena múltiples modelos y selecciona el mejor
        """
        if len(X) < 10:  # Mínimo de datos para entrenar
            return False
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Escalar características
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        mejores_resultados = {'modelo': None, 'score': -np.inf, 'mae': np.inf}
        
        for nombre, modelo in self.modelos.items():
            try:
                # Entrenar modelo
                modelo.fit(X_train_scaled, y_train)
                
                # Predecir en test
                y_pred = modelo.predict(X_test_scaled)
                
                # Evaluar modelo
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(modelo, X_train_scaled, y_train, cv=3, scoring='r2')
                cv_mean = cv_scores.mean()
                
                print(f"Modelo {nombre}: R² = {r2:.3f}, MAE = {mae:.3f}, CV = {cv_mean:.3f}")
                
                # Seleccionar mejor modelo
                if cv_mean > mejores_resultados['score']:
                    mejores_resultados['modelo'] = nombre
                    mejores_resultados['score'] = cv_mean
                    mejores_resultados['mae'] = mae
                    self.mejor_modelo = modelo
                    self.precision_modelo = cv_mean
                    
            except Exception as e:
                print(f"Error entrenando {nombre}: {e}")
                continue
        
        return mejores_resultados['modelo'] is not None
    
    def predecir_demanda(self, producto_id, dias_futuros=[7, 15, 30, 60, 90]):
        """
        Predice la demanda para períodos específicos
        """
        X, y = self.extraer_caracteristicas(producto_id)
        
        if X is None or y is None:
            return None
        
        # Entrenar modelos si es necesario
        if self.mejor_modelo is None:
            exito = self.entrenar_modelos(X, y)
            if not exito:
                return None
        
        # Preparar características para predicción
        fecha_actual = datetime.now()
        predicciones = {}
        
        for dias in dias_futuros:
            fecha_futura = fecha_actual + timedelta(days=dias)
            
            # Crear características para la fecha futura
            caracteristicas_futuras = np.array([[
                fecha_futura.weekday(),  # dia_semana
                fecha_futura.month,      # mes
                fecha_futura.day,        # dia_mes
                1 if fecha_futura.weekday() >= 5 else 0,  # es_fin_semana
                np.mean(y[-7:]) if len(y) >= 7 else np.mean(y),  # ventas_7d_promedio
                np.mean(y[-30:]) if len(y) >= 30 else np.mean(y),  # ventas_30d_promedio
                0,  # tendencia_7d (default)
                1.0,  # precio_relativo (default)
                1 if fecha_futura.day <= 7 else 0,   # es_inicio_mes
                1 if fecha_futura.day >= 25 else 0,  # es_fin_mes
            ]])
            
            # Escalar y predecir
            caracteristicas_scaled = self.scaler.transform(caracteristicas_futuras)
            demanda_predicha = self.mejor_modelo.predict(caracteristicas_scaled)[0]
            
            # Aplicar lógica de negocio (no puede ser negativa)
            demanda_predicha = max(0, int(demanda_predicha))
            
            predicciones[f'demanda_{dias}dias'] = demanda_predicha
        
        return predicciones
    
    def calcular_metricas_estacionalidad(self, producto_id):
        """
        Calcula métricas de estacionalidad para el producto
        """
        from analytics.models import EventoInventario
        
        fecha_inicio = timezone.now() - timedelta(days=365)
        eventos = EventoInventario.objects.filter(
            producto_id=producto_id,
            tipo_evento='venta',
            fecha_evento__gte=fecha_inicio
        )
        
        if not eventos.exists():
            return {'factor_estacionalidad': 1.0, 'mes_mayor_demanda': 1}
        
        # Agrupar por mes
        ventas_por_mes = {}
        for evento in eventos:
            mes = evento.fecha_evento.month
            if mes not in ventas_por_mes:
                ventas_por_mes[mes] = 0
            ventas_por_mes[mes] += evento.cantidad
        
        if not ventas_por_mes:
            return {'factor_estacionalidad': 1.0, 'mes_mayor_demanda': 1}
        
        promedio_mensual = sum(ventas_por_mes.values()) / len(ventas_por_mes)
        mes_mayor_demanda = max(ventas_por_mes, key=ventas_por_mes.get)
        factor_estacionalidad = ventas_por_mes.get(mes_mayor_demanda, promedio_mensual) / promedio_mensual
        
        return {
            'factor_estacionalidad': factor_estacionalidad,
            'mes_mayor_demanda': mes_mayor_demanda,
            'ventas_por_mes': ventas_por_mes
        }
    
    def guardar_modelo(self, producto_id, directorio='ml_models'):
        """
        Guarda el modelo entrenado
        """
        import os
        if not os.path.exists(directorio):
            os.makedirs(directorio)
        
        if self.mejor_modelo is not None:
            archivo_modelo = f"{directorio}/modelo_demanda_producto_{producto_id}.joblib"
            joblib.dump({
                'modelo': self.mejor_modelo,
                'scaler': self.scaler,
                'precision': self.precision_modelo
            }, archivo_modelo)
            return archivo_modelo
        return None
    
    def cargar_modelo(self, producto_id, directorio='ml_models'):
        """
        Carga un modelo previamente entrenado
        """
        import os
        archivo_modelo = f"{directorio}/modelo_demanda_producto_{producto_id}.joblib"
        
        if os.path.exists(archivo_modelo):
            datos = joblib.load(archivo_modelo)
            self.mejor_modelo = datos['modelo']
            self.scaler = datos['scaler'] 
            self.precision_modelo = datos['precision']
            return True
        return False