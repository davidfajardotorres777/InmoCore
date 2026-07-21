# Universidad Nacional de Chilecito

## Equipo de Trabajo
Alesandro David Fajardo Torres (davidfajardotorres7@gmail.com)

---

# InmoCore V3 Enterprise
### Sistema SaaS PropTech con Arquitectura Multi-tenant, Object Storage y Búsqueda Semántica

Proyecto Integrador — Bases de Datos II · Universidad Nacional de Chilecito · 2026

---

## El problema

Una inmobiliaria que gestiona propiedades en distintos formatos (planillas, WhatsApp, carpetas sueltas) pierde trazabilidad rápido: no sabe con certeza qué propiedades tiene publicadas, no detecta a tiempo un precio cargado por error, y no tiene forma de que un cliente busque "algo luminoso con balcón" sin revisar título por título.

InmoCore resuelve ese problema como una plataforma SaaS: varias agencias inmobiliarias comparten la misma infraestructura pero cada una opera de forma completamente aislada (multi-tenancy), con reglas de negocio automáticas que las alertan sobre datos sospechosos, y con búsqueda semántica para que sus clientes encuentren propiedades por lenguaje natural en vez de filtros rígidos.

---

## Ecosistema de Bases de Datos

InmoCore no se limita a una sola tecnología. Integra un ecosistema completo:

1. **MongoDB**: datos estructurados y operacionales, con búsquedas geoespaciales `2dsphere` (Agencias, Propiedades, Clientes, Contratos, Alertas).
2. **MinIO (S3 Compatible)**: Object Storage para las fotos en alta resolución de las propiedades.
3. **ChromaDB**: base de datos vectorial de IA para buscar descripciones de propiedades por similitud semántica.

## Características Avanzadas

- **Multi-tenancy (Aislamiento por Agencia)**: `InmoCoreDAO` requiere un `agencia_id` en su inicialización, y lo aplica como filtro obligatorio en cada lectura y escritura. Una agencia no puede ver ni modificar datos de otra.
- **Alertas Basadas en Reglas**: si se publica una propiedad en Venta con un precio sospechosamente bajo (< 10.000 USD), se dispara automáticamente una alerta hacia la colección `alertas`.
- **Integración S3**: `StorageDAO` maneja la conexión con MinIO para las fotos de las propiedades.
- **Búsqueda IA Vectorial**: `VectorDAO` indexa las descripciones en ChromaDB y permite buscarlas con lenguaje natural.
- **Geo-Radar**: consultas `$nearSphere` para encontrar propiedades dentro de un radio alrededor de la agencia.
- **Reportes Agregados**: `InmoCoreDAO.reporte_propiedades_por_tipo` agrupa las propiedades por tipo con `$group`/`$avg` (Aggregation Pipeline).
- **Interfaz Gráfica de Escritorio**: aplicación construida con `customtkinter`, con pestañas para publicar propiedades, resolver alertas, buscar semánticamente y buscar por geolocalización.

---

## Estructura del proyecto

```
InmoCore/
├── db_models/
│   ├── __init__.py     # Re-exporta todos los modelos
│   ├── agencia.py       # Tenant raíz del sistema
│   ├── propiedad.py     # Inmueble publicado por una agencia
│   ├── cliente.py       # Comprador/inquilino de una agencia
│   ├── contrato.py      # Operación entre un cliente y una propiedad
│   └── alerta.py        # Evento generado por una regla de negocio
├── dao.py                # AdminDAO, InmoCoreDAO, StorageDAO, VectorDAO
├── config_vars.py        # Variables de conexión desde .env
├── setup_db.py            # Creación de colecciones e índices
├── seed.py                # Datos de prueba (Mongo + MinIO + ChromaDB)
├── demo.ipynb              # Notebook de demostración del DAO
├── main_ui.py               # Interfaz gráfica (customtkinter)
├── docker-compose.yml        # MongoDB 7.0 + MinIO
└── requirements.txt            # Dependencias del proyecto
```

---

## Instalación y Ejecución

### Requisitos previos
- Python 3.12 o superior
- Docker Desktop
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/davidfajardotorres777/InmoCore.git
cd InmoCore
```

### 2. Entorno
```bash
python -m venv venv
# Activar según tu SO (venv\Scripts\activate o source venv/bin/activate)
pip install -r requirements.txt
```

### 3. Variables
Copiá `.env.example` a `.env`.
```bash
cp .env.example .env
```

### 4. Levantar Infraestructura
Esto levanta MongoDB y MinIO.
```bash
docker compose up -d
```
Podés acceder a la consola de MinIO en http://localhost:9001 (usuario: `admin`, contraseña: `password`).

### 5. Setup y Seed
```bash
python setup_db.py
python seed.py
```
`setup_db.py` crea las colecciones e índices (incluyendo los `2dsphere` y las restricciones de unicidad). `seed.py` genera dos agencias de ejemplo, propiedades con descripciones realistas indexadas en ChromaDB, fotos simuladas en MinIO, clientes y contratos.

### 6. Notebook de demostración
```bash
jupyter notebook demo.ipynb
```
Recorre multi-tenancy, alertas, publicación e indexado semántico, búsqueda por similitud, búsqueda geoespacial y el reporte agregado por tipo de propiedad.

### 7. Lanzar Interfaz de Usuario
```bash
python main_ui.py
```
La aplicación gráfica permite elegir la agencia, publicar propiedades nuevas, resolver alertas, buscar por lenguaje natural y buscar por cercanía geográfica.

---

## Colecciones en MongoDB

- `agencias` — tenants del sistema (sin filtro de tenancy, es la colección raíz)
- `propiedades` — inmuebles publicados, filtrados siempre por `agencia_id`
- `clientes` — compradores/inquilinos, filtrados por `agencia_id`
- `contratos` — operaciones entre cliente y propiedad, filtrados por `agencia_id`
- `alertas` — eventos automáticos de negocio, filtrados por `agencia_id`
