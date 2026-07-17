from pymongo import MongoClient
from bson.objectid import ObjectId
from minio import Minio
import io
from config_vars import (
    MONGO_URI, DB_NAME, 
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
)
from db_models.paciente import Paciente
from db_models.muestra import Muestra
from db_models.analisis import Analisis
from db_models.clinica import Clinica
from db_models.alerta import Alerta
import chromadb
from chromadb.config import Settings
import os

class StorageDAO:
    """
    Data Access Object para interactuar con MinIO (Object Storage)
    """
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
    
    def asegurar_bucket(self, bucket_name: str):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            
    def subir_archivo_bytes(self, bucket_name: str, object_name: str, data: bytes):
        self.asegurar_bucket(bucket_name)
        return self.client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data)
        )

class VectorDAO:
    """
    Data Access Object para interactuar con ChromaDB (Búsqueda Vectorial/Semántica)
    """
    def __init__(self, db_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="historiales_medicos")
        
    def indexar_historial(self, paciente_id: str, historial: str):
        if not historial:
            return
        self.collection.add(
            documents=[historial],
            metadatas=[{"paciente_id": str(paciente_id)}],
            ids=[str(paciente_id)]
        )
        
    def buscar_similitud(self, query: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

class AdminDAO:
    """
    DAO para colecciones globales (sin tenancy).
    Solo para manejo de Clínicas.
    """
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.col_clinicas = self.db['clinicas']
        
    def insertar_clinica(self, clinica: Clinica) -> str:
        data = clinica.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        result = self.col_clinicas.insert_one(data)
        return str(result.inserted_id)

    def cerrar_conexion(self):
        self.client.close()

class BioTraceDAO:
    """
    Data Access Object Operativo de BioTrace.
    ENFORCES MULTI-TENANCY: Todos los metodos requieren el clinica_id y lo usan como filtro obligatorio.
    """
    def __init__(self, clinica_id: str, uri=MONGO_URI, db_name=DB_NAME):
        self.clinica_id = ObjectId(clinica_id)
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        
        # Referencias a colecciones operativas
        self.col_pacientes = self.db['pacientes']
        self.col_muestras = self.db['muestras']
        self.col_analisis = self.db['analisis']
        self.col_alertas = self.db['alertas']

    def _verificar_tenancy(self, data: dict):
        if "clinica_id" not in data or data["clinica_id"] != self.clinica_id:
            data["clinica_id"] = self.clinica_id
        return data

    # --- PACIENTES ---
    
    def insertar_paciente(self, paciente: Paciente) -> str:
        data = paciente.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        result = self.col_pacientes.insert_one(data)
        return str(result.inserted_id)
        
    def obtener_paciente(self, paciente_id: str) -> Paciente:
        data = self.col_pacientes.find_one({
            "_id": ObjectId(paciente_id), 
            "clinica_id": self.clinica_id
        })
        if data:
            data["_id"] = str(data["_id"])
            data["clinica_id"] = str(data["clinica_id"])
            return Paciente(**data)
        return None

    def listar_pacientes(self, limit: int = 100):
        pacientes = []
        for p in self.col_pacientes.find({"clinica_id": self.clinica_id}).limit(limit):
            p["_id"] = str(p["_id"])
            p["clinica_id"] = str(p["clinica_id"])
            pacientes.append(Paciente(**p))
        return pacientes

    def buscar_pacientes_cerca_de(self, lat: float, lon: float, radio_km: float):
        """
        Consulta Geoespacial 2dsphere: Busca pacientes de la clinica en un radio determinado.
        """
        pipeline = {
            "clinica_id": self.clinica_id,
            "ubicacion": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat] # GeoJSON siempre es [lon, lat]
                    },
                    "$maxDistance": radio_km * 1000 # metros
                }
            }
        }
        pacientes = []
        for p in self.col_pacientes.find(pipeline):
            p["_id"] = str(p["_id"])
            p["clinica_id"] = str(p["clinica_id"])
            pacientes.append(Paciente(**p))
        return pacientes

    # --- MUESTRAS ---
    
    def insertar_muestra(self, muestra: Muestra) -> str:
        data = muestra.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        data["paciente_id"] = ObjectId(data["paciente_id"])
        result = self.col_muestras.insert_one(data)
        
        # BUSINESS RULE: Generar alerta si temperatura fuera de rango (-80 a 4 es normal)
        temp = data.get("temperatura_almacenamiento")
        if temp is not None and (temp > 4.0 or temp < -85.0):
            alerta = Alerta(
                clinica_id=str(self.clinica_id),
                tipo_alerta="Temperatura Crítica",
                mensaje=f"Muestra {result.inserted_id} registrada con temperatura anormal ({temp} °C).",
                entidad_referencia_id=str(result.inserted_id)
            )
            self.insertar_alerta(alerta)
            
        return str(result.inserted_id)

    # --- ANALISIS ---

    def insertar_analisis(self, analisis: Analisis) -> str:
        data = analisis.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        data["muestra_id"] = ObjectId(data["muestra_id"])
        result = self.col_analisis.insert_one(data)
        return str(result.inserted_id)

    # --- ALERTAS ---
    def insertar_alerta(self, alerta: Alerta):
        data = alerta.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        data["entidad_referencia_id"] = ObjectId(data["entidad_referencia_id"])
        self.col_alertas.insert_one(data)

    def listar_alertas(self):
        alertas = []
        for a in self.col_alertas.find({"clinica_id": self.clinica_id, "resuelta": False}):
            a["_id"] = str(a["_id"])
            a["clinica_id"] = str(a["clinica_id"])
            a["entidad_referencia_id"] = str(a["entidad_referencia_id"])
            alertas.append(Alerta(**a))
        return alertas

    # --- REPORTES / AGREGACIONES (Analytics) ---

    def reporte_analisis_por_tipo(self):
        pipeline = [
            {"$match": {"clinica_id": self.clinica_id}},
            {"$group": {"_id": "$tipo_analisis", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}}
        ]
        return list(self.col_analisis.aggregate(pipeline))
        
    def reporte_trazabilidad_paciente(self, paciente_id: str):
        pipeline = [
            {"$match": {"paciente_id": ObjectId(paciente_id), "clinica_id": self.clinica_id}},
            {
                "$lookup": {
                    "from": "analisis",
                    "localField": "_id",
                    "foreignField": "muestra_id",
                    "as": "analisis_realizados"
                }
            }
        ]
        return list(self.col_muestras.aggregate(pipeline))

    def cerrar_conexion(self):
        self.client.close()
