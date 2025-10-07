
// ⭐ OPTIMIZACIÓN VERDADERAMENTE ÓPTIMA - MÍNIMA DISTANCIA TOTAL ⭐

// Optimizador enfocado exclusivamente en minimizar kilómetros
function optimizarConMultiplesPuntosInicio(ubicaciones, puntoSalida, numIntentos = 8) {
    console.log(`🎯 OPTIMIZACIÓN PARA MÍNIMA DISTANCIA TOTAL`);
    console.log(`📍 Punto de salida: ${puntoSalida}`);
    console.log(`🎲 Probando múltiples enfoques para encontrar ruta mínima...`);
    
    const puntoSalidaCoords = obtenerCoordenadasPuntoSalida(puntoSalida);
    const bodegaCoords = [4.6533, -74.0625];
    
    console.log(`📍 Coordenadas exactas: [${puntoSalidaCoords[0].toFixed(4)}, ${puntoSalidaCoords[1].toFixed(4)}]`);
    
    let mejorRuta = null;
    let mejorDistancia = Infinity;
    let mejorAlgoritmo = '';
    let resultados = [];
    
    // MÉTODO 1: Nearest Neighbor puro desde punto de salida
    console.log(`\n🔄 Método 1: Nearest Neighbor desde punto exacto`);
    const ruta1 = nearestNeighborOptimo(ubicaciones, puntoSalidaCoords, bodegaCoords);
    const dist1 = calcularDistanciaTotal(ruta1, puntoSalidaCoords, bodegaCoords);
    resultados.push({ruta: ruta1, distancia: dist1, metodo: 'Nearest Neighbor'});
    console.log(`   📏 Distancia: ${dist1.toFixed(2)} km`);
    
    // MÉTODO 2: Nearest Neighbor + 2-opt intensivo
    console.log(`\n🔄 Método 2: Nearest Neighbor + 2-opt intensivo`);
    const ruta2 = optimizar2optIntenso([...ruta1], puntoSalidaCoords, bodegaCoords);
    const dist2 = calcularDistanciaTotal(ruta2, puntoSalidaCoords, bodegaCoords);
    resultados.push({ruta: ruta2, distancia: dist2, metodo: 'NN + 2-opt intensivo'});
    console.log(`   📏 Distancia: ${dist2.toFixed(2)} km`);
    
    // MÉTODO 3: Cheapest Insertion
    console.log(`\n🔄 Método 3: Cheapest Insertion`);
    const ruta3 = cheapestInsertion(ubicaciones, puntoSalidaCoords, bodegaCoords);
    const ruta3Opt = optimizar2optIntenso([...ruta3], puntoSalidaCoords, bodegaCoords);
    const dist3 = calcularDistanciaTotal(ruta3Opt, puntoSalidaCoords, bodegaCoords);
    resultados.push({ruta: ruta3Opt, distancia: dist3, metodo: 'Cheapest Insertion + 2-opt'});
    console.log(`   📏 Distancia: ${dist3.toFixed(2)} km`);
    
    // MÉTODO 4: Farthest Insertion
    console.log(`\n🔄 Método 4: Farthest Insertion`);
    const ruta4 = farthestInsertion(ubicaciones, puntoSalidaCoords, bodegaCoords);
    const ruta4Opt = optimizar2optIntenso([...ruta4], puntoSalidaCoords, bodegaCoords);
    const dist4 = calcularDistanciaTotal(ruta4Opt, puntoSalidaCoords, bodegaCoords);
    resultados.push({ruta: ruta4Opt, distancia: dist4, metodo: 'Farthest Insertion + 2-opt'});
    console.log(`   📏 Distancia: ${dist4.toFixed(2)} km`);
    
    // MÉTODO 5-8: Múltiples puntos de inicio con 2-opt
    for (let i = 5; i <= 8; i++) {
        console.log(`\n🔄 Método ${i}: Inicio aleatorio ${i-4}`);
        const rutaAleatoria = nearestNeighborDesdePuntoAleatorio(ubicaciones, puntoSalidaCoords, bodegaCoords);
        const rutaAleatoriaOpt = optimizar2optIntenso([...rutaAleatoria], puntoSalidaCoords, bodegaCoords);
        const distAleatoria = calcularDistanciaTotal(rutaAleatoriaOpt, puntoSalidaCoords, bodegaCoords);
        resultados.push({ruta: rutaAleatoriaOpt, distancia: distAleatoria, metodo: `Aleatorio ${i-4} + 2-opt`});
        console.log(`   📏 Distancia: ${distAleatoria.toFixed(2)} km`);
    }
    
    // Encontrar la mejor solución
    resultados.sort((a, b) => a.distancia - b.distancia);
    
    console.log(`\n📊 RANKING DE RESULTADOS (menor a mayor distancia):`);
    resultados.forEach((resultado, index) => {
        const emoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '   ';
        console.log(`${emoji} ${index + 1}. ${resultado.metodo}: ${resultado.distancia.toFixed(2)} km`);
    });
    
    mejorRuta = resultados[0].ruta;
    mejorDistancia = resultados[0].distancia;
    mejorAlgoritmo = resultados[0].metodo;
    
    const peorDistancia = resultados[resultados.length - 1].distancia;
    const mejora = ((peorDistancia - mejorDistancia) / peorDistancia * 100);
    
    console.log(`\n🏆 MEJOR RESULTADO:`);
    console.log(`   🎯 Algoritmo ganador: ${mejorAlgoritmo}`);
    console.log(`   📏 Distancia mínima: ${mejorDistancia.toFixed(2)} km`);
    console.log(`   📈 Mejora vs peor: ${mejora.toFixed(1)}%`);
    console.log(`   💡 Optimización enfocada en MÍNIMOS KILÓMETROS`);
    
    return {
        ruta: mejorRuta,
        distancia: mejorDistancia,
        algoritmo: mejorAlgoritmo
    };
}

// Nearest Neighbor optimizado para distancia mínima
function nearestNeighborOptimo(ubicaciones, puntoSalidaCoords, bodegaCoords) {
    const ubicacionesCopia = [...ubicaciones];
    const ruta = [];
    let currentLat = puntoSalidaCoords[0];
    let currentLng = puntoSalidaCoords[1];
    
    console.log(`   🎯 Construyendo ruta desde punto exacto...`);
    
    while (ubicacionesCopia.length > 0) {
        let menorDistancia = Infinity;
        let mejorIndice = 0;
        
        // Encontrar la ubicación más cercana
        ubicacionesCopia.forEach((ubicacion, index) => {
            const distancia = calcularDistancia(currentLat, currentLng, ubicacion.lat, ubicacion.lng);
            if (distancia < menorDistancia) {
                menorDistancia = distancia;
                mejorIndice = index;
            }
        });
        
        const siguienteUbicacion = ubicacionesCopia.splice(mejorIndice, 1)[0];
        ruta.push(siguienteUbicacion);
        
        currentLat = siguienteUbicacion.lat;
        currentLng = siguienteUbicacion.lng;
        
        console.log(`   ➜ ${ruta.length}. ${siguienteUbicacion.cliente} (+${menorDistancia.toFixed(2)} km)`);
    }
    
    return ruta;
}

// 2-opt intensivo para minimizar distancia
function optimizar2optIntenso(rutaInicial, puntoSalidaCoords, bodegaCoords) {
    console.log(`   ⚡ Aplicando 2-opt intensivo...`);
    
    if (rutaInicial.length < 3) return rutaInicial;
    
    let mejorRuta = [...rutaInicial];
    let mejorDistancia = calcularDistanciaTotal(mejorRuta, puntoSalidaCoords, bodegaCoords);
    let mejoraSinCambio = 0;
    let iteracion = 0;
    const maxIteraciones = 500; // Mucho más intensivo
    const maxSinCambio = 50;
    
    console.log(`   📏 Distancia inicial: ${mejorDistancia.toFixed(2)} km`);
    
    while (mejoraSinCambio < maxSinCambio && iteracion < maxIteraciones) {
        let mejoroEnEstaIteracion = false;
        iteracion++;
        
        for (let i = 0; i < mejorRuta.length - 2; i++) {
            for (let j = i + 2; j < mejorRuta.length; j++) {
                // Intercambio 2-opt
                const nuevaRuta = intercambiar2opt([...mejorRuta], i, j);
                const nuevaDistancia = calcularDistanciaTotal(nuevaRuta, puntoSalidaCoords, bodegaCoords);
                
                if (nuevaDistancia < mejorDistancia) {
                    const mejora = mejorDistancia - nuevaDistancia;
                    mejorRuta = nuevaRuta;
                    mejorDistancia = nuevaDistancia;
                    mejoroEnEstaIteracion = true;
                    mejoraSinCambio = 0;
                    
                    console.log(`   🎯 Mejora en iter ${iteracion}: -${mejora.toFixed(3)} km → ${nuevaDistancia.toFixed(2)} km`);
                    
                    // Si la mejora es significativa, reiniciar bucles
                    if (mejora > 0.1) {
                        i = mejorRuta.length; // Romper loop externo
                        break;
                    }
                }
            }
        }
        
        if (!mejoroEnEstaIteracion) {
            mejoraSinCambio++;
        }
    }
    
    const distanciaInicial = calcularDistanciaTotal(rutaInicial, puntoSalidaCoords, bodegaCoords);
    const ahorroTotal = distanciaInicial - mejorDistancia;
    const porcentajeAhorro = (ahorroTotal / distanciaInicial) * 100;
    
    console.log(`   ✅ 2-opt completado: ${iteracion} iteraciones`);
    console.log(`   📉 Ahorro: ${ahorroTotal.toFixed(2)} km (${porcentajeAhorro.toFixed(1)}%)`);
    
    return mejorRuta;
}

// Nearest Neighbor desde punto aleatorio
function nearestNeighborDesdePuntoAleatorio(ubicaciones, puntoSalidaCoords, bodegaCoords) {
    const ubicacionesCopia = [...ubicaciones];
    
    // Seleccionar punto de inicio aleatorio
    const indiceAleatorio = Math.floor(Math.random() * ubicacionesCopia.length);
    const puntoInicio = ubicacionesCopia.splice(indiceAleatorio, 1)[0];
    
    const ruta = [puntoInicio];
    let currentLat = puntoInicio.lat;
    let currentLng = puntoInicio.lng;
    
    // Continuar con nearest neighbor desde ese punto
    while (ubicacionesCopia.length > 0) {
        let menorDistancia = Infinity;
        let mejorIndice = 0;
        
        ubicacionesCopia.forEach((ubicacion, index) => {
            const distancia = calcularDistancia(currentLat, currentLng, ubicacion.lat, ubicacion.lng);
            if (distancia < menorDistancia) {
                menorDistancia = distancia;
                mejorIndice = index;
            }
        });
        
        const siguienteUbicacion = ubicacionesCopia.splice(mejorIndice, 1)[0];
        ruta.push(siguienteUbicacion);
        
        currentLat = siguienteUbicacion.lat;
        currentLng = siguienteUbicacion.lng;
    }
    
    return ruta;
}

// Cheapest Insertion - Inserta en la posición que menos aumenta la distancia
function cheapestInsertion(ubicaciones, puntoSalidaCoords, bodegaCoords) {
    console.log(`   💰 Aplicando Cheapest Insertion...`);
    
    if (ubicaciones.length === 0) return [];
    if (ubicaciones.length === 1) return ubicaciones;
    
    // Iniciar con el punto más cercano al inicio
    const ubicacionesCopia = [...ubicaciones];
    let menorDistanciaInicial = Infinity;
    let indicePrimero = 0;
    
    ubicacionesCopia.forEach((ubicacion, index) => {
        const distancia = calcularDistancia(puntoSalidaCoords[0], puntoSalidaCoords[1], ubicacion.lat, ubicacion.lng);
        if (distancia < menorDistanciaInicial) {
            menorDistanciaInicial = distancia;
            indicePrimero = index;
        }
    });
    
    const ruta = [ubicacionesCopia.splice(indicePrimero, 1)[0]];
    
    // Insertar cada ubicación restante en la posición que menos aumente la distancia
    while (ubicacionesCopia.length > 0) {
        let mejorCostoInsercion = Infinity;
        let mejorIndiceUbicacion = 0;
        let mejorPosicionInsercion = 0;
        
        ubicacionesCopia.forEach((ubicacion, indiceUbicacion) => {
            // Probar insertar en cada posición posible
            for (let posicion = 0; posicion <= ruta.length; posicion++) {
                const costoInsercion = calcularCostoInsercion(ruta, ubicacion, posicion, puntoSalidaCoords, bodegaCoords);
                
                if (costoInsercion < mejorCostoInsercion) {
                    mejorCostoInsercion = costoInsercion;
                    mejorIndiceUbicacion = indiceUbicacion;
                    mejorPosicionInsercion = posicion;
                }
            }
        });
        
        // Insertar en la mejor posición
        const ubicacionAInsertar = ubicacionesCopia.splice(mejorIndiceUbicacion, 1)[0];
        ruta.splice(mejorPosicionInsercion, 0, ubicacionAInsertar);
        
        console.log(`   ➜ Insertado ${ubicacionAInsertar.cliente} en posición ${mejorPosicionInsercion} (+${mejorCostoInsercion.toFixed(2)} km)`);
    }
    
    return ruta;
}

// Farthest Insertion - Inserta el punto más lejano en la mejor posición
function farthestInsertion(ubicaciones, puntoSalidaCoords, bodegaCoords) {
    console.log(`   🎯 Aplicando Farthest Insertion...`);
    
    if (ubicaciones.length === 0) return [];
    if (ubicaciones.length === 1) return ubicaciones;
    
    const ubicacionesCopia = [...ubicaciones];
    
    // Iniciar con el punto más cercano al inicio
    let menorDistanciaInicial = Infinity;
    let indicePrimero = 0;
    
    ubicacionesCopia.forEach((ubicacion, index) => {
        const distancia = calcularDistancia(puntoSalidaCoords[0], puntoSalidaCoords[1], ubicacion.lat, ubicacion.lng);
        if (distancia < menorDistanciaInicial) {
            menorDistanciaInicial = distancia;
            indicePrimero = index;
        }
    });
    
    const ruta = [ubicacionesCopia.splice(indicePrimero, 1)[0]];
    
    // En cada iteración, encontrar el punto más lejano a la ruta actual
    while (ubicacionesCopia.length > 0) {
        let mayorDistanciaMinima = -1;
        let indiceMasLejano = 0;
        
        // Encontrar el punto más lejano a la ruta actual
        ubicacionesCopia.forEach((ubicacion, indiceUbicacion) => {
            let menorDistanciaARuta = Infinity;
            
            // Calcular distancia mínima de este punto a cualquier punto de la ruta
            ruta.forEach(puntoRuta => {
                const distancia = calcularDistancia(ubicacion.lat, ubicacion.lng, puntoRuta.lat, puntoRuta.lng);
                if (distancia < menorDistanciaARuta) {
                    menorDistanciaARuta = distancia;
                }
            });
            
            if (menorDistanciaARuta > mayorDistanciaMinima) {
                mayorDistanciaMinima = menorDistanciaARuta;
                indiceMasLejano = indiceUbicacion;
            }
        });
        
        // Insertar el punto más lejano en la mejor posición
        const ubicacionMasLejana = ubicacionesCopia[indiceMasLejano];
        let mejorCostoInsercion = Infinity;
        let mejorPosicion = 0;
        
        for (let posicion = 0; posicion <= ruta.length; posicion++) {
            const costoInsercion = calcularCostoInsercion(ruta, ubicacionMasLejana, posicion, puntoSalidaCoords, bodegaCoords);
            if (costoInsercion < mejorCostoInsercion) {
                mejorCostoInsercion = costoInsercion;
                mejorPosicion = posicion;
            }
        }
        
        ubicacionesCopia.splice(indiceMasLejano, 1);
        ruta.splice(mejorPosicion, 0, ubicacionMasLejana);
        
        console.log(`   ➜ Insertado ${ubicacionMasLejana.cliente} (más lejano) en posición ${mejorPosicion}`);
    }
    
    return ruta;
}

// Calcular costo de insertar una ubicación en una posición específica
function calcularCostoInsercion(ruta, ubicacion, posicion, puntoSalidaCoords, bodegaCoords) {
    const rutaOriginal = calcularDistanciaTotal(ruta, puntoSalidaCoords, bodegaCoords);
    
    const rutaTemporal = [...ruta];
    rutaTemporal.splice(posicion, 0, ubicacion);
    
    const rutaConInsercion = calcularDistanciaTotal(rutaTemporal, puntoSalidaCoords, bodegaCoords);
    
    return rutaConInsercion - rutaOriginal;
}
