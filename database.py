import sqlite3

class DB():
    def __init__(self, nombre_db):
        self.conexion = sqlite3.connect(nombre_db)
        self.conexion.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conexion.cursor()
        self.crear_esquema()
    
    def consultar(self, sql, datos=()):
        self.cursor.execute(sql, datos)
        self.conexion.commit()
        return self.cursor.fetchall()

    def cerrar(self):
        self.conexion.close()

    def crear_esquema(self):
        # 1. Creación de tablas base
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Usuario (id_usuario INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, password TEXT NOT NULL, rol TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Grado_instruccion (id_grado_instruccion INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT NOT NULL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Estado_laboral (id_estado_laboral INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Categoria_personal (id_categoria_personal INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL)")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Comunas (
                                    id_comuna INTEGER PRIMARY KEY AUTOINCREMENT, 
                                    nombre TEXT UNIQUE NOT NULL)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS Personal (
                                    id_personal INTEGER PRIMARY KEY AUTOINCREMENT,
                                    cedula INT UNIQUE NOT NULL,
                                    nombres TEXT NOT NULL,
                                    apellidos TEXT NOT NULL,
                                    fecha_nacimiento DATE,
                                    direccion TEXT,
                                    correo TEXT,
                                    telefono TEXT,
                                    carnet_patria TEXT UNIQUE,
                                    titulo_obtenido TEXT,
                                    fecha_ingreso DATE,
                                    id_comuna INTEGER,
                                    cargo TEXT,
                                    codigo_dependencia TEXT,
                                    id_grado_instruccion INTEGER,
                                    id_categoria_personal INTEGER,
                                    id_estado_laboral INTEGER,
                                    FOREIGN KEY (id_comuna) REFERENCES Comunas(id_comuna),
                                    FOREIGN KEY (id_grado_instruccion) REFERENCES Grado_instruccion(id_grado_instruccion),
                                    FOREIGN KEY (id_categoria_personal) REFERENCES Categoria_personal(id_categoria_personal),
                                    FOREIGN KEY (id_estado_laboral) REFERENCES Estado_laboral(id_estado_laboral)
                                    )""")

        existe = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='vista_personal_detallada'").fetchone()
        if not existe:
            self.cursor.execute("""
                CREATE VIEW vista_personal_detallada AS 
                SELECT 
                    p.cedula, 
                    p.nombres, 
                    p.apellidos, 
                    p.fecha_nacimiento, 
                    -- Cálculo dinámico de edad: se actualiza solo con el tiempo
                    (strftime('%Y', 'now') - strftime('%Y', p.fecha_nacimiento)) - (strftime('%m-%d', 'now') < strftime('%m-%d', p.fecha_nacimiento)) AS edad,
                    p.direccion, 
                    p.correo, 
                    p.telefono, 
                    p.carnet_patria,
                    g.descripcion AS grado_instruccion,
                    p.titulo_obtenido, 
                    p.fecha_ingreso, 
                    -- Cálculo dinámico de años de servicio: se actualiza solo con el tiempo
                    (strftime('%Y', 'now') - strftime('%Y', p.fecha_ingreso)) - (strftime('%m-%d', 'now') < strftime('%m-%d', p.fecha_ingreso)) AS anos_servicio,
                    co.nombre AS comuna,
                    p.cargo,
                    p.codigo_dependencia,
                    c.nombre AS categoria,
                    e.nombre AS estado_laboral
                FROM Personal p
                LEFT JOIN Grado_instruccion g ON p.id_grado_instruccion = g.id_grado_instruccion
                LEFT JOIN Categoria_personal c ON p.id_categoria_personal = c.id_categoria_personal
                LEFT JOIN Estado_laboral e    ON p.id_estado_laboral = e.id_estado_laboral
                LEFT JOIN Comunas co          ON p.id_comuna = co.id_comuna;
            """)

        self.cursor.execute("INSERT OR IGNORE INTO Grado_instruccion (id_grado_instruccion, descripcion) VALUES (1, 'No Graduado'), (2, 'Bachiller'), (3, 'Tecnico Medio'), (4, 'Tecnico Superior'), (5,'Licenciado'),(6,'Ingeniero'),(7,'Magister'),(8,'Doctor')")
        self.cursor.execute("INSERT OR IGNORE INTO Estado_laboral (id_estado_laboral, nombre) VALUES (1, 'Activo'), (2, 'Reposo'), (3, 'Jubilado'), (4, 'Permiso')")
        self.cursor.execute("INSERT OR IGNORE INTO Categoria_personal (id_categoria_personal, nombre) VALUES (1, 'Docente I'), (2, 'Docente II'), (3, 'Docente III'), (4, 'Docente IV'), (5, 'Docente V'), (6, 'Docente VI'), (7, 'TSU I'),(8, 'TSU II'), (9, 'Profesional I'), (10, 'Profesional II'), (11, 'Profesional III'), (12,'Obrero I'), (13,'Obrero II'), (14, 'Aseador I'), (15, 'Aseador II'), (16, 'Mensajero'), (17, 'Portero'), (18, 'Vigilante'), (19, 'Otro')")
        self.cursor.execute("INSERT OR IGNORE INTO Usuario (nombre, password, rol) VALUES ('Director', '123456789', 'Director'), ('Administrador', '123456789', 'Administrador')")

db = DB("registros.db")