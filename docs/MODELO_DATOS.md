# Modelo de Datos - Analizador ALMA

## Fuentes de Datos

### 1. ALMA (Sistema Clinico)

```
┌─────────────────────────────────────────────────────────────────┐
│                         ALMA                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  Usuarios    │────▶│Usuario_Grupo │◀────│   Grupos     │    │
│  │  (01)        │     │    (07)      │     │   (02)       │    │
│  └──────┬───────┘     └──────────────┘     └──────────────┘    │
│         │                                                        │
│         │             ┌──────────────┐     ┌──────────────┐    │
│         └────────────▶│Usuario_Perfil│◀────│  Perfiles    │    │
│         │             │    (08)      │     │   (03)       │    │
│         │             └──────────────┘     └──────────────┘    │
│         │                                                        │
│         │             ┌──────────────┐     ┌──────────────┐    │
│         └────────────▶│Prof_Usuario  │◀────│Profesionales │    │
│                       │    (10)      │     │   (04)       │    │
│                       └──────────────┘     └──────┬───────┘    │
│                                                    │             │
│  ┌──────────────┐     ┌──────────────┐            │             │
│  │ Hospitales   │     │Prof_Especial │◀───────────┘             │
│  │   (06)       │     │    (09)      │                          │
│  └──────────────┘     └──────┬───────┘                          │
│                              │                                   │
│                       ┌──────▼───────┐                          │
│                       │Especialidades│                          │
│                       │    (05)      │                          │
│                       └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Personal (SIRH)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PERSONAL                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Funcionarios                           │   │
│  │  - Rut, Dv                                                │   │
│  │  - Nombre Funcionario                                     │   │
│  │  - Descripcion Planta (MEDICOS, PROFESIONALES, etc.)     │   │
│  │  - Descripcion Calidad Juridica                          │   │
│  │  - Descripcion Unidad                                     │   │
│  │  - Descripcion Cargo                                      │   │
│  │  - Ley (15.076, 18.834, 19.664)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Medicos HOV                            │   │
│  │  - Campos de Funcionarios +                               │   │
│  │  - Numero horas                                           │   │
│  │  - Inscripcion superintendencia                           │   │
│  │  - Correl. Planta                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Tablas ALMA Detalladas

### 01_Usuarios.csv
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| ID | INT | ID interno ALMA |
| Iniciales | VARCHAR | **RUT del usuario** (ej: 18179461-5) |
| Nombre | VARCHAR | Nombre completo |
| LoginID | VARCHAR | Login (puede estar vacio) |
| Activo | CHAR(1) | Y=Activo, N=Inactivo |
| EsDoctor | CHAR(1) | Y=Es medico |
| EsEnfermera | CHAR(1) | Y=Es enfermera |
| UltimoLogin_Fecha | DATE | Fecha ultimo acceso |
| UltimoLogin_Hora | TIME | Hora ultimo acceso |
| GrupoID | INT | FK a Grupos (principal) |
| PerfilID | INT | FK a Perfiles (principal) |
| CareProvID | INT | FK a Profesionales |
| HospitalID | INT | FK a Hospitales |
| Email | VARCHAR | Correo electronico |
| Movil | VARCHAR | Telefono movil |

### 02_Grupos.csv
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| ID | INT | ID del grupo |
| Descripcion | VARCHAR | Nombre del grupo de seguridad |
| NivelSeguridad | INT | Nivel de acceso |
| FechaDesde | DATE | Vigencia desde |
| FechaHasta | DATE | Vigencia hasta |

### 03_Perfiles.csv
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| ID | INT | ID del perfil |
| Codigo | VARCHAR | Codigo corto (ej: AArc, Med) |
| Descripcion | VARCHAR | Descripcion del perfil |
| FechaDesde | DATE | Vigencia desde |
| FechaHasta | DATE | Vigencia hasta |

### 04_Profesionales.csv
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| ID | INT | ID profesional |
| Codigo | VARCHAR | Codigo/Nombre |
| NombreCompleto | VARCHAR | **RUT** |
| Nombre | VARCHAR | Nombres |
| Apellido | VARCHAR | Apellidos |
| Activo | CHAR(1) | Y/N |
| EsEspecialista | CHAR(1) | Y/N |
| EsCirujano | CHAR(1) | Y/N |
| EsAnestesista | CHAR(1) | Y/N |
| EsRadiologo | CHAR(1) | Y/N |
| EspecialidadID | INT | FK a Especialidades |
| NumRegistro | VARCHAR | Numero registro SIS |

### 07_Usuarios_Grupos.csv (Relacion N:M)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| UsuarioID | INT | FK a Usuarios |
| UsuarioNombre | VARCHAR | **RUT** |
| Activo | CHAR(1) | Y/N |
| GrupoID | INT | FK a Grupos |
| GrupoDesc | VARCHAR | Descripcion grupo |

### 08_Usuarios_Perfiles.csv (Relacion N:M)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| UsuarioID | INT | FK a Usuarios |
| UsuarioNombre | VARCHAR | **RUT** |
| Activo | CHAR(1) | Y/N |
| PerfilID | INT | FK a Perfiles |
| PerfilDesc | VARCHAR | Descripcion perfil |

## Reglas de Cruce

### Llave de Cruce Principal
- **RUT** es la llave para cruzar entre sistemas
- En ALMA: Campo `Iniciales` en Usuarios, `NombreCompleto` en Profesionales
- En Personal: Campos `Rut` + `Dv`

### Formato RUT
```
ALMA:     18179461-5  (con guion)
Personal: 18179461 | 5 (separados)
Normalizado: 18179461-5
```

## Validaciones Requeridas

### 1. Existencia en ALMA
```
Funcionario.RUT EXISTS IN Usuarios.Iniciales
```

### 2. Flag Doctor para Medicos
```
IF Funcionario.Planta = 'MEDICOS'
THEN Usuario.EsDoctor = 'Y'
```

### 3. Perfil segun Cargo
| Cargo | Perfiles Esperados |
|-------|-------------------|
| MEDICO CIRUJANO | Med*, Doc*, Cir* |
| ENFERMERO(A) | Enf*, Nur* |
| TECNICO EN ENFERMERIA | Ten*, Tec* |
| KINESIOLOGO(A) | Kin* |
| MATRONA | Mat*, Mid* |

### 4. Usuario Activo
```
Funcionario activo en Personal DEBE tener Usuario.Activo = 'Y'
```

### 5. Caracteres Validos
- Sin caracteres de control (0x00-0x1F excepto tab, newline)
- Acentos validos: aeiouAEIOU con tildes, ñÑ, üÜ

## Modelo SQL Propuesto

Ver archivo: `sql/create_tables.sql`
