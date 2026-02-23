-- ============================================================
-- MODELO DE DATOS UNIFICADO - ALMA + PERSONAL
-- Para analisis y cruce de datos
-- ============================================================

-- ============================================================
-- TABLAS MAESTRAS (de ALMA)
-- ============================================================

CREATE TABLE IF NOT EXISTS alma_usuarios (
    id INT PRIMARY KEY,
    rut VARCHAR(15) NOT NULL,           -- Normalizado de Iniciales
    nombre VARCHAR(200),
    login_id VARCHAR(50),
    activo CHAR(1) DEFAULT 'N',
    es_doctor CHAR(1) DEFAULT 'N',
    es_enfermera CHAR(1) DEFAULT 'N',
    ultimo_login_fecha DATE,
    ultimo_login_hora TIME,
    grupo_id INT,
    perfil_id INT,
    care_prov_id INT,
    hospital_id INT,
    email VARCHAR(100),
    movil VARCHAR(20),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alma_usuarios_rut ON alma_usuarios(rut);

CREATE TABLE IF NOT EXISTS alma_grupos (
    id INT PRIMARY KEY,
    descripcion VARCHAR(200),
    nivel_seguridad INT,
    fecha_desde DATE,
    fecha_hasta DATE,
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alma_perfiles (
    id INT PRIMARY KEY,
    codigo VARCHAR(20),
    descripcion VARCHAR(200),
    fecha_desde DATE,
    fecha_hasta DATE,
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alma_profesionales (
    id INT PRIMARY KEY,
    codigo VARCHAR(100),
    rut VARCHAR(15),                    -- Normalizado de NombreCompleto
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    activo CHAR(1) DEFAULT 'N',
    es_especialista CHAR(1) DEFAULT 'N',
    es_cirujano CHAR(1) DEFAULT 'N',
    es_anestesista CHAR(1) DEFAULT 'N',
    es_radiologo CHAR(1) DEFAULT 'N',
    especialidad_id INT,
    num_registro VARCHAR(50),
    email VARCHAR(100),
    movil VARCHAR(20),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alma_profesionales_rut ON alma_profesionales(rut);

CREATE TABLE IF NOT EXISTS alma_especialidades (
    id INT PRIMARY KEY,
    codigo VARCHAR(20),
    descripcion VARCHAR(200),
    fecha_desde DATE,
    fecha_hasta DATE,
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alma_hospitales (
    id INT PRIMARY KEY,
    codigo VARCHAR(20),
    descripcion VARCHAR(200),
    fecha_desde DATE,
    fecha_hasta DATE,
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLAS DE RELACION (de ALMA)
-- ============================================================

CREATE TABLE IF NOT EXISTS alma_usuarios_grupos (
    usuario_id INT,
    usuario_rut VARCHAR(15),
    activo CHAR(1),
    grupo_id INT,
    grupo_desc VARCHAR(200),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, grupo_id)
);

CREATE INDEX idx_alma_ug_rut ON alma_usuarios_grupos(usuario_rut);

CREATE TABLE IF NOT EXISTS alma_usuarios_perfiles (
    usuario_id INT,
    usuario_rut VARCHAR(15),
    activo CHAR(1),
    perfil_id INT,
    perfil_desc VARCHAR(200),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, perfil_id)
);

CREATE INDEX idx_alma_up_rut ON alma_usuarios_perfiles(usuario_rut);

CREATE TABLE IF NOT EXISTS alma_profesionales_especialidades (
    profesional_id INT,
    codigo VARCHAR(100),
    rut VARCHAR(15),
    activo CHAR(1),
    es_especialista CHAR(1),
    especialidad_id INT,
    especialidad_desc VARCHAR(200),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (profesional_id, especialidad_id)
);

-- ============================================================
-- TABLAS DE PERSONAL (de SIRH)
-- ============================================================

CREATE TABLE IF NOT EXISTS personal_funcionarios (
    rut VARCHAR(15) PRIMARY KEY,        -- RUT-DV normalizado
    rut_numero INT,
    rut_dv CHAR(1),
    nombre VARCHAR(200),
    planta VARCHAR(50),                 -- MEDICOS, PROFESIONALES, etc.
    calidad_juridica VARCHAR(100),
    grado INT,
    genero CHAR(1),
    nacionalidad VARCHAR(50),
    ley VARCHAR(20),                    -- LEY 15.076, 18.834, 19.664
    establecimiento VARCHAR(100),
    fecha_nacimiento DATE,
    edad INT,
    unidad VARCHAR(100),
    cargo VARCHAR(100),
    transitorio CHAR(1),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS personal_medicos (
    rut VARCHAR(15) PRIMARY KEY,
    rut_numero INT,
    rut_dv CHAR(1),
    nombre VARCHAR(200),
    planta VARCHAR(50),
    calidad_juridica VARCHAR(100),
    grado INT,
    genero CHAR(1),
    nacionalidad VARCHAR(50),
    ley VARCHAR(20),
    numero_horas INT,
    fecha_nacimiento DATE,
    unidad VARCHAR(100),
    cargo VARCHAR(100),
    inscripcion_sis VARCHAR(100),       -- Inscripcion superintendencia
    correl_planta VARCHAR(20),
    transitorio CHAR(1),
    fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- VISTAS DE ANALISIS
-- ============================================================

-- Vista: Funcionarios con su estado en ALMA
CREATE VIEW IF NOT EXISTS v_funcionarios_alma AS
SELECT
    f.rut,
    f.nombre AS nombre_personal,
    f.planta,
    f.cargo,
    f.unidad,
    f.ley,
    u.id AS alma_usuario_id,
    u.nombre AS nombre_alma,
    u.activo AS alma_activo,
    u.es_doctor AS alma_es_doctor,
    u.ultimo_login_fecha,
    p.codigo AS perfil_codigo,
    p.descripcion AS perfil_desc,
    g.descripcion AS grupo_desc,
    h.descripcion AS hospital_desc,
    CASE
        WHEN u.id IS NULL THEN 'SIN_ALMA'
        WHEN u.activo = 'Y' THEN 'ACTIVO'
        ELSE 'INACTIVO'
    END AS estado_alma
FROM personal_funcionarios f
LEFT JOIN alma_usuarios u ON f.rut = u.rut
LEFT JOIN alma_perfiles p ON u.perfil_id = p.id
LEFT JOIN alma_grupos g ON u.grupo_id = g.id
LEFT JOIN alma_hospitales h ON u.hospital_id = h.id;

-- Vista: Medicos sin flag doctor en ALMA
CREATE VIEW IF NOT EXISTS v_medicos_sin_flag AS
SELECT
    f.rut,
    f.nombre,
    f.cargo,
    f.unidad,
    u.id AS alma_id,
    u.nombre AS nombre_alma,
    u.es_doctor,
    u.activo
FROM personal_funcionarios f
INNER JOIN alma_usuarios u ON f.rut = u.rut
WHERE f.planta = 'MEDICOS'
AND (u.es_doctor IS NULL OR u.es_doctor != 'Y');

-- Vista: Funcionarios sin usuario ALMA
CREATE VIEW IF NOT EXISTS v_funcionarios_sin_alma AS
SELECT
    f.rut,
    f.nombre,
    f.planta,
    f.cargo,
    f.unidad,
    f.ley
FROM personal_funcionarios f
LEFT JOIN alma_usuarios u ON f.rut = u.rut
WHERE u.id IS NULL;

-- Vista: Usuarios ALMA inactivos que son funcionarios activos
CREATE VIEW IF NOT EXISTS v_usuarios_inactivos AS
SELECT
    f.rut,
    f.nombre AS nombre_personal,
    f.cargo,
    u.nombre AS nombre_alma,
    u.activo,
    u.ultimo_login_fecha
FROM personal_funcionarios f
INNER JOIN alma_usuarios u ON f.rut = u.rut
WHERE u.activo != 'Y';

-- Vista: Todos los grupos de un usuario
CREATE VIEW IF NOT EXISTS v_usuario_todos_grupos AS
SELECT
    ug.usuario_rut AS rut,
    u.nombre,
    GROUP_CONCAT(ug.grupo_desc SEPARATOR ' | ') AS grupos
FROM alma_usuarios_grupos ug
INNER JOIN alma_usuarios u ON ug.usuario_id = u.id
GROUP BY ug.usuario_rut, u.nombre;

-- Vista: Todos los perfiles de un usuario
CREATE VIEW IF NOT EXISTS v_usuario_todos_perfiles AS
SELECT
    up.usuario_rut AS rut,
    u.nombre,
    GROUP_CONCAT(up.perfil_desc SEPARATOR ' | ') AS perfiles
FROM alma_usuarios_perfiles up
INNER JOIN alma_usuarios u ON up.usuario_id = u.id
GROUP BY up.usuario_rut, u.nombre;

-- ============================================================
-- QUERIES DE ANALISIS COMUNES
-- ============================================================

-- Q1: Resumen de funcionarios por estado ALMA
/*
SELECT estado_alma, COUNT(*) as cantidad
FROM v_funcionarios_alma
GROUP BY estado_alma;
*/

-- Q2: Medicos sin flag ordenados por unidad
/*
SELECT unidad, COUNT(*) as cantidad
FROM v_medicos_sin_flag
GROUP BY unidad
ORDER BY cantidad DESC;
*/

-- Q3: Funcionarios sin ALMA por planta
/*
SELECT planta, COUNT(*) as cantidad
FROM v_funcionarios_sin_alma
GROUP BY planta
ORDER BY cantidad DESC;
*/
