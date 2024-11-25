# app.py
from flask import Flask, render_template, jsonify
import yaml
import asyncio
import platform
import subprocess
from datetime import datetime
import json
from ping3 import ping
import asyncio

app = Flask(__name__)

def load_initial_schools():
    """Lee el archivo YAML y retorna la data inicial sin verificar estado."""
    with open('escuelas.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data['escuelas']

def calculate_center(schools):
    """Calcula el centro del mapa basado en la concentración de escuelas."""
    if not schools:
        return [19.0, -70.0]  # Centro por defecto de República Dominicana
        
    lats = [s['latitud'] for s in schools if 'latitud' in s]
    longs = [s['longitud'] for s in schools if 'longitud' in s]
    
    if not lats or not longs:
        return [19.0, -70.0]
        
    return [sum(lats)/len(lats), sum(longs)/len(longs)]

async def ping_host(host):
    """Ejecuta ping de forma asíncrona usando ping3 y retorna True si responde, False si no."""
    if not host:
        return False

    try:
        # Ejecuta la función bloqueante `ping` en un hilo separado
        response_time = await asyncio.to_thread(ping, host, timeout=2)
        return response_time is not None
    except Exception as e:
        print(f"Error al hacer ping: {e}")
        return False

async def check_schools_status():
    """Verifica el estado de conectividad de cada escuela."""
    schools = load_initial_schools()
    tasks = []
    
    for school in schools:
        host = school.get('direccion') or school.get('IP')
        tasks.append(ping_host(host))
    
    results = await asyncio.gather(*tasks)
    
    status_updates = []
    for school, is_online in zip(schools, results):
        status_updates.append({
            'codigo': school.get('codigo'),
            'nombre': school.get('nombre'),
            'online': is_online
        })
    
    return status_updates

@app.route('/')
def index():
    """Ruta principal que renderiza el template."""
    return render_template('index.html')

@app.route('/api/initial-data')
def get_initial_data():
    """API endpoint que retorna los datos iniciales de las escuelas."""
    schools = load_initial_schools()
    center = calculate_center(schools)
    return jsonify({
        'schools': schools,
        'center': center
    })

@app.route('/api/status-updates')
def get_status_updates():
    """API endpoint que retorna las actualizaciones de estado."""
    status_updates = asyncio.run(check_schools_status())
    return jsonify({'updates': status_updates})

if __name__ == '__main__':
    app.run(debug=True)