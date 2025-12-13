# 🌐 Servidor de Resultados en Tiempo Real

## 📋 Descripción
Sistema web para que los corredores consulten sus resultados desde cualquier dispositivo con internet.

## 🚀 Inicio Rápido

### 1. Instalar Flask
```powershell
pip install flask pandas openpyxl
```

### 2. Iniciar el Servidor
```powershell
python servidor_resultados.py
```

## 🔌 Acceso al Dashboard

### Opción 1: Red Local (Misma WiFi)
Cualquier dispositivo conectado a la misma red WiFi puede acceder:
- **URL**: `http://[TU_IP_LOCAL]:5000`
- **Ejemplo**: `http://192.168.1.100:5000`

#### ¿Cómo saber tu IP local?
```powershell
ipconfig
```
Busca "Dirección IPv4" en la conexión activa (WiFi o Ethernet)

### Opción 2: Acceso desde INTERNET (Cualquier lugar)

#### Usando ngrok (Recomendado - Gratis)
1. **Descargar ngrok**: https://ngrok.com/download
2. **Descomprimir** y mover a una carpeta accesible
3. **En una terminal separada**, ejecutar:
   ```powershell
   ngrok http 5000
   ```
4. **Copiar la URL pública** que ngrok genera (ejemplo: `https://abc123.ngrok.io`)
5. **Compartir esa URL** con los corredores

**Ventajas de ngrok:**
- ✅ Gratis para uso básico
- ✅ No requiere configuración de router
- ✅ HTTPS automático
- ✅ Funciona desde cualquier lugar del mundo

#### Usando LocalTunnel (Alternativa Gratis)
```powershell
npm install -g localtunnel
lt --port 5000
```

#### Usando Serveo (Sin instalación)
```powershell
ssh -R 80:localhost:5000 serveo.net
```

## 📱 Características del Dashboard

### Para Corredores:
- ✅ **Búsqueda por Dorsal**: Encuentra tu resultado rápidamente
- ✅ **Búsqueda por Nombre**: Por si olvidas tu dorsal
- ✅ **Filtro por Categoría**: Ve solo tu categoría
- ✅ **Actualización Automática**: Se actualiza cada 3 segundos
- ✅ **Responsive**: Funciona en celular, tablet y PC
- ✅ **Tiempo Real**: Ve a medida que llegan los corredores

### Información Visible:
- Posición general
- Número de dorsal
- Nombre completo
- Categoría
- Hora de llegada
- Estado (Registrado / No encontrado)

## 🔒 Seguridad

### Red Local
- Solo personas en tu WiFi pueden acceder
- Ideal para eventos en espacios cerrados

### Internet Público (ngrok)
- Cualquiera con el link puede ver resultados
- No expone tu IP real
- El link cambia cada vez que reinicias ngrok (versión gratis)

## 🎯 Casos de Uso

### Escenario 1: Evento en Gimnasio/Club
```
1. Conecta tu laptop a la WiFi del lugar
2. Inicia servidor_resultados.py
3. Comparte http://192.168.X.X:5000 con los corredores
4. Ellos acceden desde sus celulares en la misma WiFi
```

### Escenario 2: Carrera Abierta (Calle)
```
1. Inicia servidor_resultados.py
2. En otra terminal: ngrok http 5000
3. Comparte el link público: https://abc123.ngrok.io
4. Cualquiera con el link puede ver resultados
5. Puedes compartir el link en WhatsApp, redes sociales, etc.
```

### Escenario 3: Pantalla Grande + Móviles
```
1. Proyector/TV muestra el dashboard completo
2. Corredores usan búsqueda en sus celulares
3. Ambos se actualizan en tiempo real
```

## 🛠️ Solución de Problemas

### "No puedo acceder desde otro dispositivo"
- Verifica que el firewall de Windows no esté bloqueando el puerto 5000
- Ambos dispositivos deben estar en la misma red WiFi

### "ngrok no funciona"
- Crea cuenta gratuita en ngrok.com
- Ejecuta: `ngrok authtoken [tu-token]`

### "No se actualizan los resultados"
- El servidor lee el archivo Excel cada 3 segundos
- Verifica que `registros_dorsales.xlsx` exista y tenga datos

## 📊 APIs Disponibles

El servidor también expone estas APIs por si necesitas integrarlas:

- `GET /api/resultados` - Todos los resultados
- `GET /api/buscar?dorsal=100` - Buscar por dorsal
- `GET /api/buscar?nombre=carlos` - Buscar por nombre
- `GET /api/buscar?categoria=Elite` - Filtrar por categoría
- `GET /api/categorias` - Lista de todas las categorías
- `GET /api/estadisticas` - Estadísticas generales

## 💡 Consejos

1. **Mantén el servidor corriendo** mientras dure el evento
2. **Comparte el link antes** de que empiecen a llegar corredores
3. **Prueba el acceso** antes del evento desde diferentes dispositivos
4. **Imprime QR codes** con el link para facilitar el acceso
5. **Ten un celular de respaldo** con hotspot por si falla la WiFi

## 🔄 Flujo Completo

```
Detección → registros_dorsales.xlsx → Servidor Flask → Dashboard Web → Corredores
   (interfaz_deteccion.py)              (servidor_resultados.py)      (Celular/Tablet/PC)
```

---

**¿Preguntas?** El sistema está diseñado para ser simple y funcionar sin complicaciones técnicas.
