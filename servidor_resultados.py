"""
Servidor Flask para visualización de resultados en tiempo real
Los corredores pueden consultar sus resultados desde cualquier dispositivo
"""
from flask import Flask, render_template, jsonify, request
import pandas as pd
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Configuración
EXCEL_PATH = Path("registros_dorsales.xlsx")

def leer_resultados():
    """Lee los resultados del archivo Excel"""
    try:
        if EXCEL_PATH.exists():
            df = pd.read_excel(EXCEL_PATH)
            # Convertir a diccionario
            resultados = df.to_dict('records')
            return resultados
        return []
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return []

@app.route('/')
def index():
    """Página principal con dashboard de resultados"""
    return render_template('resultados.html')

@app.route('/api/resultados')
def api_resultados():
    """API: Devuelve todos los resultados en JSON"""
    resultados = leer_resultados()
    return jsonify({
        'success': True,
        'total': len(resultados),
        'resultados': resultados,
        'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/buscar')
def api_buscar():
    """API: Busca por dorsal o nombre"""
    dorsal = request.args.get('dorsal', '').strip()
    nombre = request.args.get('nombre', '').strip().lower()
    categoria = request.args.get('categoria', '').strip()
    
    resultados = leer_resultados()
    resultados_filtrados = resultados
    
    # Filtrar por dorsal
    if dorsal:
        resultados_filtrados = [r for r in resultados_filtrados 
                               if str(r.get('Dorsal', '')) == dorsal]
    
    # Filtrar por nombre (búsqueda parcial)
    if nombre:
        resultados_filtrados = [r for r in resultados_filtrados 
                               if nombre in str(r.get('Nombre', '')).lower() 
                               or nombre in str(r.get('Apellido', '')).lower()]
    
    # Filtrar por categoría
    if categoria:
        resultados_filtrados = [r for r in resultados_filtrados 
                               if str(r.get('Categoría', '')) == categoria]
    
    return jsonify({
        'success': True,
        'total': len(resultados_filtrados),
        'resultados': resultados_filtrados
    })

@app.route('/api/categorias')
def api_categorias():
    """API: Devuelve todas las categorías disponibles"""
    resultados = leer_resultados()
    categorias = list(set([r.get('Categoría', '') for r in resultados if r.get('Categoría', '')]))
    categorias.sort()
    return jsonify({
        'success': True,
        'categorias': categorias
    })

@app.route('/api/estadisticas')
def api_estadisticas():
    """API: Devuelve estadísticas generales"""
    resultados = leer_resultados()
    
    # Contar por categoría
    categorias_count = {}
    for r in resultados:
        cat = r.get('Categoría', 'Sin categoría')
        categorias_count[cat] = categorias_count.get(cat, 0) + 1
    
    return jsonify({
        'success': True,
        'total_corredores': len(resultados),
        'por_categoria': categorias_count,
        'registrados': len([r for r in resultados if r.get('Estado') == 'Registrado']),
        'no_encontrados': len([r for r in resultados if r.get('Estado') == 'No encontrado'])
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏃 SERVIDOR DE RESULTADOS - RACE DETECTOR")
    print("="*60)
    print("\n📊 Dashboard de Resultados en Tiempo Real")
    print("\nAcceso Local:")
    print("  👉 http://localhost:5000")
    print("  👉 http://127.0.0.1:5000")
    print("\nAcceso desde Red Local:")
    print("  👉 http://[TU_IP_LOCAL]:5000")
    print("  (Ejemplo: http://192.168.1.100:5000)")
    print("\nPara acceso desde INTERNET:")
    print("  1. Instala ngrok: https://ngrok.com")
    print("  2. Ejecuta: ngrok http 5000")
    print("  3. Comparte la URL pública que ngrok te da")
    print("\n" + "="*60 + "\n")
    
    # Ejecutar servidor
    # host='0.0.0.0' permite acceso desde cualquier dispositivo en la red
    app.run(host='0.0.0.0', port=5000, debug=True)
