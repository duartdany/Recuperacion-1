# Importando las bibliotecas necesarias
from flask import Flask, jsonify, request
import re, bcrypt, mysql.connector
from datetime import datetime

# Inicializando la aplicación Flask
app = Flask(__name__)

# Configuración para conectar a la base de datos MySQL
conexion_config = {
    'host': '192.168.0.103',
    'user': 'root',
    'password': 'linux',
    'database': 'utng'
}

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(**conexion_config)

# Función para comprobar si una contraseña coincide con una contraseña cifrada
def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Función para validar si una fecha de expiración es válida
def is_expiration_valid(fecha_expiracion_str):
    try:
        fecha_expiracion = datetime.strptime(fecha_expiracion_str, '%Y-%m-%d').date()
        if fecha_expiracion < datetime.now().date():
            return False
        return True
    except ValueError:
        return False

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validación: ambos campos 'usuario' y 'password' deben estar presentes
    if not all(key in data for key in ['usuario', 'password']):
        return {'error': 'Faltan campos requeridos'}, 400

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    # Obtener el hash de la contraseña del usuario proporcionado
    cursor.execute("SELECT password FROM usuarios WHERE usuario = %s", (data['usuario'],))
    user = cursor.fetchone()

    if not user:
        return {'error': 'Usuario no encontrado'}, 404

    # Verificar que la contraseña proporcionada coincida con la almacenada en la base de datos
    if not check_password(user['password'], data['password']):
        return {'error': 'Contraseña incorrecta'}, 401

    cursor.close()
    cnx.close()

    return {'success': 'Inicio de sesión exitoso'}, 200


@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    
    cursor.execute("SELECT id, correo, usuario, fecha_registro, fecha_expiracion FROM usuarios")
    result = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(result), 200

@app.route('/usuarios', methods=['POST'])
def add_usuarios():
    data = request.get_json()
    required_fields = ['correo', 'password', 'usuario']

    if not all(key in data for key in required_fields):
        return {'error': 'Faltan campos requeridos'}, 400

    if not es_password_valida(data['password']):
        return {'error':'La contraseña es inválida'}, 400

    # Validación de la fecha de expiración
    if 'fecha_expiracion' in data and not is_expiration_valid(data['fecha_expiracion']):
        return {'error': 'La fecha de expiración no es válida'}, 400

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    cursor.execute("SELECT correo FROM usuarios WHERE correo = %s", (data['correo'],))
    existing_mail = cursor.fetchone()

    if existing_mail:
        cursor.close()
        cnx.close()
        return {'error':'Este correo ó usuario ya está registrado'}, 409

    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    data['password'] = hashed_pw.decode('utf-8')

    insert_query = """
        INSERT INTO usuarios (correo, password, usuario, fecha_expiracion) 
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (data['correo'], data['password'], data['usuario'], data.get('fecha_expiracion')))
    cnx.commit()

    cursor.close()
    cnx.close()

    return {'success':'Registro agregado con éxito'}, 201

@app.route('/usuarios/actualizar', methods=['PUT'])
def update_usuario():
    data = request.get_json()

    # Asegúrate de que el ID del usuario se proporcione en el cuerpo de la solicitud
    if 'id' not in data:
        return {'error': 'Falta el ID del usuario en el cuerpo de la solicitud'}, 400

    usuario_id = data['id']

    updates = []
    values = []

    if 'correo' in data:
        updates.append("correo = %s")
        values.append(data['correo'])

    if 'usuario' in data:
        updates.append("usuario = %s")
        values.append(data['usuario'])

    if 'fecha_expiracion' in data:
        updates.append("fecha_expiracion = %s")
        values.append(data['fecha_expiracion'])

    if 'password' in data:
        hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        updates.append("password = %s")
        values.append(hashed_pw.decode('utf-8'))

    if not updates:
        return {'error':'No hay cambios para actualizar'}, 400

    sql_update_query = "UPDATE usuarios SET " + ", ".join(updates) + " WHERE id = %s"
    values.append(usuario_id)

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    cursor.execute(sql_update_query, values)
    cnx.commit()

    if cursor.rowcount == 0:
        cursor.close()
        cnx.close()
        return {'error':'Usuario no encontrado'}, 404

    cursor.close()
    cnx.close()

    return {'success':'Usuario actualizado con éxito'}, 200

@app.route('/usuarios/eliminar', methods=['DELETE'])
def delete_usuario():
    data = request.get_json()

    if 'correo' not in data:
        return {'error': 'Falta el campo correo'}, 400

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (data['correo'],))
    user = cursor.fetchone()

    if not user:
        return {'error': 'Usuario con el correo proporcionado no encontrado'}, 404

    cursor.execute("DELETE FROM usuarios WHERE correo = %s", (data['correo'],))
    cnx.commit()

    cursor.close()
    cnx.close()

    return {'success':'Usuario eliminado con éxito'}, 200

@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre, email, carrera, cuatrimestre, edad, numero_control, promedio FROM alumnos")
    result = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(result), 200

@app.route('/alumnos', methods=['POST'])
def add_alumno():
    data = request.get_json()

    required_fields = ['materia_id', 'nombre', 'email', 'carrera', 'cuatrimestre', 'edad', 'numero_control', 'promedio']

    if not all(key in data for key in required_fields):
        return {'error':'Faltan campos requeridos'}, 400

    # Validación de campos vacíos
    for field in required_fields:
        if not data[field]:
            return {'error': f'El campo {field} no puede estar vacío'}, 400

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    # Verificamos si el numero_control ya existe
    cursor.execute("SELECT numero_control FROM alumnos WHERE numero_control = %s", (data['numero_control'],))
    existing_alumno = cursor.fetchone()

    if existing_alumno:
        cursor.close()
        cnx.close()
        return {'error':'El numero de control ya está registrado'}, 409

    # Verificamos si el materia_id existe en la tabla materias
    cursor.execute("SELECT id FROM materias WHERE id = %s", (data['materia_id'],))
    existing_materia = cursor.fetchone()

    if not existing_materia:
        cursor.close()
        cnx.close()
        return {'error':'El materia_id no existe'}, 404

    # Si ambas validaciones pasan, procedemos a insertar el alumno
    cursor.execute("INSERT INTO alumnos (materia_id, nombre, email, carrera, cuatrimestre, edad, numero_control, promedio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                   (data['materia_id'], data['nombre'], data['email'], data['carrera'], data['cuatrimestre'], data['edad'], data['numero_control'], data['promedio']))
    cnx.commit()

    cursor.close()
    cnx.close()

    return {'success':'Alumno agregado con éxito'}, 201


@app.route('/materias', methods=['GET'])
def get_materias():
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    
    cursor.execute("SELECT nombre_materia, carrera, cantidad_alumnos, area, periodo, maestro, edificio FROM materias")
    result = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(result), 200

@app.route('/materias', methods=['POST'])
def add_materia():
    data = request.get_json()

    required_fields = ['usuario_id', 'nombre_materia', 'carrera', 'cantidad_alumnos', 'area', 'periodo', 'maestro', 'edificio']

    if not all(key in data for key in required_fields):
        return {'error':'Faltan campos requeridos'}, 400

    # Validación de campos vacíos
    for field in required_fields:
        if not data[field]:
            return {'error': f'El campo {field} no puede estar vacío'}, 400

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    # Verificamos si el usuario_id existe en la tabla usuarios
    cursor.execute("SELECT id FROM usuarios WHERE id = %s", (data['usuario_id'],))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.close()
        cnx.close()
        return {'error':'El usuario_id no existe'}, 404

    # Si la validación pasa, procedemos a insertar la materia
    cursor.execute("INSERT INTO materias (usuario_id, nombre_materia, carrera, cantidad_alumnos, area, periodo, maestro, edificio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                   (data['usuario_id'], data['nombre_materia'], data['carrera'], data['cantidad_alumnos'], data['area'], data['periodo'], data['maestro'], data['edificio']))
    cnx.commit()

    cursor.close()
    cnx.close()

    return {'success':'Materia agregada con éxito'}, 201

def es_password_valida(password):
    if len(password) < 8:
        return False
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
        return False
    return True

# Iniciar la aplicación Flask
if __name__ == "__main__":
    app.run(debug=True)
