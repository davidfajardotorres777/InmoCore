from pymongo import MongoClient
from bson.objectid import ObjectId
from minio import Minio
import io
import chromadb
from config_vars import (
    MONGO_URI, DB_NAME, 
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
)
from db_models.propiedad import Propiedad
from db_models.cliente import Cliente
from db_models.contrato import Contrato
from db_models.agencia import Agencia
from db_models.alerta import Alerta

class StorageDAO:
    """
    Data Access Object para interactuar con MinIO (Fotos de Propiedades)
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
        self.collection = self.client.get_or_create_collection(name="descripciones_propiedades")
        
    def indexar_descripcion(self, propiedad_id: str, descripcion: str):
        if not descripcion:
            return
        self.collection.add(
            documents=[descripcion],
            metadatas=[{"propiedad_id": str(propiedad_id)}],
            ids=[str(propiedad_id)]
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
    Solo para manejo de Agencias Inmobiliarias.
    """
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.col_agencias = self.db['agencias']
        
    def insertar_agencia(self, agencia: Agencia) -> str:
        data = agencia.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        result = self.col_agencias.insert_one(data)
        return str(result.inserted_id)

    def cerrar_conexion(self):
        self.client.close()

class InmoCoreDAO:
    """
    Data Access Object Operativo de InmoCore.
    ENFORCES MULTI-TENANCY: Todos los metodos requieren el agencia_id y lo usan como filtro obligatorio.
    """
    def __init__(self, agencia_id: str, uri=MONGO_URI, db_name=DB_NAME):
        self.agencia_id = ObjectId(agencia_id)
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        
        # Referencias a colecciones operativas
        self.col_propiedades = self.db['propiedades']
        self.col_clientes = self.db['clientes']
        self.col_contratos = self.db['contratos']
        self.col_alertas = self.db['alertas']

    def _verificar_tenancy(self, data: dict):
        if "agencia_id" not in data or data["agencia_id"] != self.agencia_id:
            data["agencia_id"] = self.agencia_id
        return data

    # --- PROPIEDADES ---
    
    def insertar_propiedad(self, propiedad: Propiedad) -> str:
        data = propiedad.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        
        # BUSINESS RULE: Generar alerta si el precio es sospechosamente bajo (< 10000 USD para venta)
        if data.get("operacion") == "Venta" and data.get("precio_usd", 999999) < 10000:
            alerta = Alerta(
                agencia_id=str(self.agencia_id),
                tipo_alerta="Precio Anómalo",
                mensaje=f"Propiedad registrada con precio de Venta sospechoso ({data['precio_usd']} USD).",
                entidad_referencia_id="PENDING" # Updated below
            )
            data_alerta = alerta.model_dump(by_alias=True, exclude_none=True)
            if "_id" in data_alerta and data_alerta["_id"] is None: del data_alerta["_id"]
            data_alerta = self._verificar_tenancy(data_alerta)
            alert_result = self.col_alertas.insert_one(data_alerta)
            alert_id = alert_result.inserted_id
        else:
            alert_id = None

        result = self.col_propiedades.insert_one(data)
        
        if alert_id:
            self.col_alertas.update_one({"_id": alert_id}, {"$set": {"entidad_referencia_id": str(result.inserted_id)}})
            
        return str(result.inserted_id)
        
    def obtener_propiedad(self, propiedad_id: str) -> Propiedad:
        data = self.col_propiedades.find_one({
            "_id": ObjectId(propiedad_id), 
            "agencia_id": self.agencia_id
        })
        if data:
            data["_id"] = str(data["_id"])
            data["agencia_id"] = str(data["agencia_id"])
            return Propiedad(**data)
        return None

    def listar_propiedades(self, limit: int = 100):
        props = []
        for p in self.col_propiedades.find({"agencia_id": self.agencia_id}).limit(limit):
            p["_id"] = str(p["_id"])
            p["agencia_id"] = str(p["agencia_id"])
            props.append(Propiedad(**p))
        return props

    def buscar_propiedades_cerca_de(self, lat: float, lon: float, radio_km: float):
        """
        Consulta Geoespacial 2dsphere: Busca propiedades de la agencia en un radio determinado.
        """
        pipeline = {
            "agencia_id": self.agencia_id,
            "ubicacion": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "$maxDistance": radio_km * 1000 # metros
                }
            }
        }
        props = []
        for p in self.col_propiedades.find(pipeline):
            p["_id"] = str(p["_id"])
            p["agencia_id"] = str(p["agencia_id"])
            props.append(Propiedad(**p))
        return props

    # --- CLIENTES ---
    
    def insertar_cliente(self, cliente: Cliente) -> str:
        data = cliente.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        result = self.col_clientes.insert_one(data)
        return str(result.inserted_id)

    # --- CONTRATOS ---

    def insertar_contrato(self, contrato: Contrato) -> str:
        data = contrato.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None: del data["_id"]
        data = self._verificar_tenancy(data)
        data["propiedad_id"] = ObjectId(data["propiedad_id"])
        data["cliente_id"] = ObjectId(data["cliente_id"])
        result = self.col_contratos.insert_one(data)
        return str(result.inserted_id)

    # --- ALERTAS ---

    def listar_alertas(self):
        alertas = []
        for a in self.col_alertas.find({"agencia_id": self.agencia_id, "resuelta": False}):
            a["_id"] = str(a["_id"])
            a["agencia_id"] = str(a["agencia_id"])
            a["entidad_referencia_id"] = str(a["entidad_referencia_id"])
            alertas.append(Alerta(**a))
        return alertas

    def cerrar_conexion(self):
        self.client.close()
