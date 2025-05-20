from flask import Flask, render_template, request, url_for, redirect
import sqlite3
import os
import logging
from datetime import datetime

app = Flask(__name__)
DATABASE = 'db'

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    logging.info(f"Abriendo conexión a la base de datos: {conn}")  # Registro
    return conn

def close_db(conn):
    if conn:
        logging.info(f"Cerrando conexión a la base de datos: {conn}")  # Registro
        conn.close()

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rifa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            numeros TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    logging.info("Tabla 'rifa' creada (si no existía)")  # Registro
    close_db(conn)

# Check if the database file exists, if not, initialize the database
if not os.path.exists(DATABASE):
    with app.app_context():
        init_db()
    logging.info('Base de datos inicializada.')  # Registro

def get_numeros_disponibles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT numeros FROM rifa')
    numeros_asignados = [fila['numeros'] for fila in cursor.fetchall()]
    close_db(conn)
    numeros_ocupados = set()
    for asignacion in numeros_asignados:
        numeros_ocupados.update(asignacion.split(','))
    numeros_disponibles = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in numeros_ocupados]
    return numeros_disponibles

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db()
    cursor = conn.cursor()
    mensaje = None
    numeros_disponibles = get_numeros_disponibles()
    anio = datetime.now().year

    if request.method == 'POST':
        nombre = request.form['nombre']
        numeros_rifa = request.form.getlist('numeros')
        if not numeros_rifa:
            mensaje = "Debes seleccionar al menos un número."
            close_db(conn)
            return render_template('index.html',  mensaje=mensaje, numeros_disponibles=numeros_disponibles, anio=anio)

        numeros_str = ','.join(numeros_rifa)

        try:
            cursor.execute('INSERT INTO rifa (nombre, numeros) VALUES (?, ?)', (nombre, numeros_str))
            conn.commit()
            logging.info(f"Números registrados para {nombre}: {numeros_str}")  # Registro
            mensaje = f'Los números {numeros_str} han sido registrados para {nombre}.'
        except sqlite3.IntegrityError:
            mensaje = f'Los números {numeros_str} ya han sido registrados.'
            return render_template('index.html', mensaje=mensaje, numeros_disponibles=numeros_disponibles, anio=anio)
        except sqlite3.OperationalError as e:
            mensaje = f'Error al registrar los números: {e}'
            logging.error(f"Error de base de datos: {e}")  # Registro
            close_db(conn)
            return render_template('index.html', mensaje=mensaje, numeros_disponibles=numeros_disponibles, anio=anio)
        except Exception as e:
            mensaje = f"Ocurrió un error inesperado: {e}"
            logging.error(f"Error inesperado: {e}")  # Registro
            close_db(conn)
            return render_template('index.html', mensaje=mensaje, numeros_disponibles=numeros_disponibles, anio=anio)

    cursor.execute('SELECT nombre, numeros FROM rifa ORDER BY nombre')
    participantes = cursor.fetchall()
    close_db(conn)
    return render_template('index.html', mensaje=mensaje, numeros_disponibles=numeros_disponibles, participantes=participantes, anio=anio)

@app.route('/lista_rifa')
def lista_rifa():
    conn = get_db()
    cursor = conn.cursor()
    anio = datetime.now().year
    try:
        cursor.execute('SELECT nombre, numeros FROM rifa ORDER BY nombre')
        participantes = cursor.fetchall()
    except sqlite3.OperationalError as e:
        logging.error(f"Error de base de datos al seleccionar participantes: {e}")  # Registro
        participantes = []
    close_db(conn)
    return render_template('lista_rifa.html', participantes=participantes, anio=anio)

if __name__ == '__main__':
    app.run(debug=True, port=3030)
