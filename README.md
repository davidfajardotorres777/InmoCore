# BioTrace
### Sistema de Trazabilidad de Muestras Biológicas y Datos Genómicos

Proyecto Integrador — Bases de Datos II · 2026

---

## El problema

En laboratorios de investigación genética y hospitales, el rastreo del ciclo de vida de una muestra biológica (desde su extracción al paciente, almacenamiento, procesamiento y posterior secuenciación) suele estar fragmentado en múltiples planillas de cálculo. Esta dispersión genera inconsistencias, pérdida de datos críticos para la trazabilidad y dificulta las consultas transversales (ej. "¿qué análisis genómicos se realizaron sobre muestras de pacientes con diabetes tipo 2 en 2025?").

BioTrace resuelve este problema consolidando los datos operativos. Es un módulo de persistencia (DAO) que almacena de forma unificada e indexada los Pacientes, Muestras y Análisis Genómicos en MongoDB. Este enfoque orientado a documentos permite flexibilidad en la estructuración de la metadata genómica sin perder la capacidad de consulta.

---

## Arquitectura

El proyecto implementa el patrón **Data Access Object (DAO)** para encapsular la interacción con MongoDB.
```
Notebook/App → BioTraceDAO → MongoDB (Docker)
```

**Colecciones de MongoDB:**
- **pacientes**: Datos demográficos y clínicos.
- **muestras**: Información de la toma de muestras (fecha, tipo de tejido, origen).
- **analisis**: Resultados de los procesos (ej. Secuenciación, PCR) y métricas de calidad (Q-score, cobertura).

---

## Estructura del proyecto

```
BioTrace/
├── db_models/
│   ├── __init__.py
│   ├── paciente.py      # Entidad Paciente
│   ├── muestra.py       # Entidad Muestra biológica
│   └── analisis.py      # Entidad Análisis Genómico/Clínico
├── dao.py               # BioTraceDAO — interfaz principal con MongoDB
├── config_vars.py       # Lectura de variables de entorno (dotenv)
├── setup_db.py          # Configuración inicial e índices de MongoDB
├── seed.py              # Poblador de datos de prueba (faker)
├── demo.ipynb           # Notebook de demostración y análisis con Pandas
├── docker-compose.yml   # Contenedor MongoDB
├── requirements.txt     # Dependencias de Python
└── .env.example         # Ejemplo de configuración
```

---

## Instalación y Ejecución

### Requisitos previos
- Python 3.12 o superior
- Docker Desktop
- Git

### 1. Entorno y Dependencias
```bash
python -m venv venv
```
Activar en Windows: `venv\Scripts\activate`
Activar en Linux/Mac: `source venv/bin/activate`

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Variables de entorno
Crear un archivo `.env` en la raíz (basado en `.env.example`):
```
MONGO_URI=mongodb://localhost:27017
DB_NAME=biotrace_db
```

### 3. Levantar la base de datos
```bash
docker compose up -d
```
Verifica con `docker ps` que `biotrace-mongo` esté corriendo.

### 4. Inicializar y Poblar la BD
Crea las colecciones y los índices de rendimiento:
```bash
python setup_db.py
```

Inserta datos de prueba sintéticos:
```bash
python seed.py
```

### 5. Explorar los datos
Abre Jupyter Notebook para ver cómo opera el DAO y el análisis en Pandas:
```bash
jupyter notebook demo.ipynb
```
