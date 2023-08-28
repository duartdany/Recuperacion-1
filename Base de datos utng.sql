DROP DATABASE IF EXISTS utng;
CREATE DATABASE IF NOT EXISTS utng;
USE utng;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    correo VARCHAR(30) NOT NULL,
    password VARCHAR(200) NOT NULL,
    usuario varchar(20) NOT null,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion date
);

CREATE TABLE IF NOT EXISTS materias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
	FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    nombre_materia VARCHAR(50) NOT NULL,
    carrera VARCHAR(50) NOT NULL,
    cantidad_alumnos INT NOT NULL,
    area varchar (40) NOT NULL,
    periodo varchar (40) NOT NULL,
    maestro varchar (40) NOT NULL,
    edificio varchar (10) NOT NULL
);

CREATE TABLE IF NOT EXISTS alumnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materia_id INT,
	FOREIGN KEY (materia_id) REFERENCES materias(id),
    nombre VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    carrera VARCHAR(50) NOT NULL,
    cuatrimestre INT NOT NULL,
    edad INT NOT NULL,
    numero_control INT NOT NULL UNIQUE,
    promedio FLOAT NOT NULL
);
