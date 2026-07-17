from pymongo import MongoClient
from bson.objectid import ObjectId
from config_vars import MONGO_URI, DB_NAME
from db_models.paciente import Paciente
from db_models.muestra import Muestra
from db_models.analisis import Analisis

class BioTraceDAO:
    """
    Data Access Object para interactuar con la base de datos de BioTrace.
    Encapsula toda la logica de acceso a MongoDB.
    """
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        
        # Referencias a colecciones
        self.col_pacientes = self.db['pacientes']
        self.col_muestras = self.db['muestras']
        self.col_analisis = self.db['analisis']

    # --- PACIENTES ---
    
    def insertar_paciente(self, paciente: Paciente) -> str:
        data = paciente.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        result = self.col_pacientes.insert_one(data)
        return str(result.inserted_id)
        
    def obtener_paciente(self, paciente_id: str) -> Paciente:
        data = self.col_pacientes.find_one({"_id": ObjectId(paciente_id)})
        if data:
            data["_id"] = str(data["_id"])
            return Paciente(**data)
        return None

    def listar_pacientes(self, limit: int = 100):
        pacientes = []
        for p in self.col_pacientes.find().limit(limit):
            p["_id"] = str(p["_id"])
            pacientes.append(Paciente(**p))
        return pacientes

    # --- MUESTRAS ---
    
    def insertar_muestra(self, muestra: Muestra) -> str:
        data = muestra.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        # Validar ObjectId si se quiere usar como referencia fuerte
        data["paciente_id"] = ObjectId(data["paciente_id"])
        result = self.col_muestras.insert_one(data)
        return str(result.inserted_id)

    def obtener_muestras_por_paciente(self, paciente_id: str):
        muestras = []
        for m in self.col_muestras.find({"paciente_id": ObjectId(paciente_id)}):
            m["_id"] = str(m["_id"])
            m["paciente_id"] = str(m["paciente_id"])
            muestras.append(Muestra(**m))
        return muestras

    # --- ANALISIS ---

    def insertar_analisis(self, analisis: Analisis) -> str:
        data = analisis.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        data["muestra_id"] = ObjectId(data["muestra_id"])
        result = self.col_analisis.insert_one(data)
        return str(result.inserted_id)

    def obtener_analisis_por_muestra(self, muestra_id: str):
        analisis_list = []
        for a in self.col_analisis.find({"muestra_id": ObjectId(muestra_id)}):
            a["_id"] = str(a["_id"])
            a["muestra_id"] = str(a["muestra_id"])
            analisis_list.append(Analisis(**a))
        return analisis_list

    # --- REPORTES / AGREGACIONES (Analytics) ---

    def reporte_analisis_por_tipo(self):
        """
        Usa el Aggregation Pipeline para contar cuantos analisis hay por tipo.
        """
        pipeline = [
            {"$group": {"_id": "$tipo_analisis", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}}
        ]
        return list(self.col_analisis.aggregate(pipeline))
        
    def reporte_trazabilidad_paciente(self, paciente_id: str):
        """
        Busca todas las muestras y analisis de un paciente en una sola consulta.
        """
        pipeline = [
            {"$match": {"paciente_id": ObjectId(paciente_id)}},
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
