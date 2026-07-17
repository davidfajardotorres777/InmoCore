from faker import Faker
import random
from datetime import datetime, timedelta
from db_models.paciente import Paciente
from db_models.muestra import Muestra
from db_models.analisis import Analisis
from dao import BioTraceDAO

fake = Faker('es_AR')

def generar_datos_prueba(dao: BioTraceDAO, num_pacientes=10):
    print("Limpiando base de datos...")
    dao.col_pacientes.delete_many({})
    dao.col_muestras.delete_many({})
    dao.col_analisis.delete_many({})
    
    print(f"Generando {num_pacientes} pacientes...")
    
    tipos_muestra = ["Sangre", "Saliva", "Tejido Tumoral", "Hisopado Nasofaríngeo", "Biopsia Hepática"]
    tipos_analisis = ["Secuenciación WGS", "PCR Multiplex", "Panel Genético Oncológico", "Exoma Completo", "Microarray"]
    laboratorios = ["Lab Central BioTrace", "Genomics Lab AR", "Hospital Clínico", "Instituto Nacional del Cáncer"]
    
    for _ in range(num_pacientes):
        # Crear Paciente
        fecha_nac = fake.date_of_birth(minimum_age=18, maximum_age=90)
        paciente = Paciente(
            dni=str(fake.random_int(min=10000000, max=99999999)),
            nombre=fake.first_name(),
            apellido=fake.last_name(),
            fecha_nacimiento=datetime(fecha_nac.year, fecha_nac.month, fecha_nac.day),
            genero=random.choice(["M", "F", "X"]),
            historial_medico=fake.text(max_nb_chars=200) if random.random() > 0.5 else None
        )
        p_id = dao.insertar_paciente(paciente)
        
        # Crear de 1 a 3 muestras por paciente
        num_muestras = random.randint(1, 3)
        for _ in range(num_muestras):
            dias_atras = random.randint(1, 365)
            fecha_ext = datetime.utcnow() - timedelta(days=dias_atras)
            
            muestra = Muestra(
                paciente_id=p_id,
                tipo_muestra=random.choice(tipos_muestra),
                fecha_extraccion=fecha_ext,
                medico_solicitante=f"Dr. {fake.last_name()}",
                estado=random.choice(["Recolectada", "Procesada", "Analizada"]),
                temperatura_almacenamiento=random.uniform(-80.0, 4.0),
                notas="Muestra extraída sin complicaciones."
            )
            m_id = dao.insertar_muestra(muestra)
            
            # Si la muestra está analizada, crear 1 o 2 análisis
            if muestra.estado == "Analizada":
                num_analisis = random.randint(1, 2)
                for _ in range(num_analisis):
                    analisis = Analisis(
                        muestra_id=m_id,
                        tipo_analisis=random.choice(tipos_analisis),
                        fecha_analisis=fecha_ext + timedelta(days=random.randint(1, 10)),
                        laboratorio_origen=random.choice(laboratorios),
                        investigador_responsable=fake.name(),
                        metricas_calidad={
                            "q_score": round(random.uniform(20.0, 40.0), 2),
                            "cobertura": f"{random.randint(30, 100)}X"
                        },
                        hallazgos_clinicos="Variante patogénica detectada." if random.random() > 0.8 else "Sin hallazgos significativos."
                    )
                    dao.insertar_analisis(analisis)
                    
    print("Datos generados exitosamente.")

if __name__ == "__main__":
    dao = BioTraceDAO()
    generar_datos_prueba(dao, 20)
    dao.cerrar_conexion()
