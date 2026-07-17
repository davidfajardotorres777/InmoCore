import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from dao import AdminDAO, BioTraceDAO, VectorDAO

# Premium styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BioTraceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BioTrace V3 Enterprise - Plataforma Genómica")
        self.geometry("1000x700")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Estado de sesión
        self.admin_dao = AdminDAO()
        self.clinicas = list(self.admin_dao.col_clinicas.find())
        self.clinica_actual = None
        self.dao = None
        self.vector_dao = VectorDAO()
        
        if not self.clinicas:
            messagebox.showerror("Error", "No hay clínicas en la base de datos. Ejecuta setup_db.py y seed.py primero.")
            self.destroy()
            return

        self.mostrar_login()

    def mostrar_login(self):
        # Limpiar ventana
        for widget in self.winfo_children():
            widget.destroy()
            
        self.login_frame = ctk.CTkFrame(self, corner_radius=15, width=400, height=400)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ctk.CTkLabel(self.login_frame, text="BIOTRACE", font=ctk.CTkFont(size=36, weight="bold"), text_color="#3498db").pack(pady=(40, 5))
        ctk.CTkLabel(self.login_frame, text="Sistema de Trazabilidad Genómica Multi-tenant", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 30))
        
        ctk.CTkLabel(self.login_frame, text="Seleccione su Clínica / Laboratorio (Tenant):", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        self.combo_clinica = ctk.CTkComboBox(
            self.login_frame, 
            values=[c["nombre"] for c in self.clinicas],
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.combo_clinica.pack(pady=10)
        
        btn_login = ctk.CTkButton(
            self.login_frame, 
            text="Acceder al Sistema", 
            width=300,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.iniciar_sesion
        )
        btn_login.pack(pady=30)

    def iniciar_sesion(self):
        nombre_seleccionado = self.combo_clinica.get()
        clinica = next((c for c in self.clinicas if c["nombre"] == nombre_seleccionado), None)
        if clinica:
            self.clinica_actual = clinica
            self.dao = BioTraceDAO(clinica_id=str(clinica["_id"]))
            self.mostrar_dashboard()

    def mostrar_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()
            
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="BIOTRACE", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498db").grid(row=0, column=0, padx=20, pady=(20, 5))
        ctk.CTkLabel(self.sidebar_frame, text=f"Tenant:\n{self.clinica_actual['nombre']}", font=ctk.CTkFont(size=14), text_color="#2ecc71").grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Main content
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.grid_columnconfigure(1, weight=1)
        
        self.tabview = ctk.CTkTabview(self.main_frame, width=800, height=600)
        self.tabview.pack(fill="both", expand=True)
        
        self.tabview.add("Alertas Clínicas")
        self.tabview.add("Buscador Semántico (IA)")
        self.tabview.add("Búsqueda Geoespacial")
        
        self.construir_tab_alertas(self.tabview.tab("Alertas Clínicas"))
        self.construir_tab_semantico(self.tabview.tab("Buscador Semántico (IA)"))
        self.construir_tab_geo(self.tabview.tab("Búsqueda Geoespacial"))
        
        ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", fg_color="#e74c3c", hover_color="#c0392b", command=self.mostrar_login).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

    def construir_tab_alertas(self, tab):
        ctk.CTkLabel(tab, text="Panel de Alertas Activas", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(tab, width=700, height=400)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        alertas = self.dao.listar_alertas()
        if not alertas:
            ctk.CTkLabel(scroll, text="No hay alertas activas en esta clínica.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=20)
        else:
            for a in alertas:
                frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#2c3e50")
                frame.pack(fill="x", pady=5, padx=5)
                ctk.CTkLabel(frame, text=f"⚠ {a.tipo_alerta}", font=ctk.CTkFont(weight="bold", size=16), text_color="#e74c3c").pack(anchor="w", padx=10, pady=(10, 0))
                ctk.CTkLabel(frame, text=a.mensaje, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 10))
                
    def construir_tab_semantico(self, tab):
        ctk.CTkLabel(tab, text="Buscador de Historiales Clínicos (ChromaDB Vector Search)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", padx=10, pady=10)
        
        self.entry_busqueda = ctk.CTkEntry(frame_top, placeholder_text="Ej: Paciente con fatiga crónica y dolor articular...", width=500, height=40)
        self.entry_busqueda.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(frame_top, text="Buscar con IA", command=self.ejecutar_busqueda_semantica, height=40, font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.scroll_semantico = ctk.CTkScrollableFrame(tab, width=700, height=400)
        self.scroll_semantico.pack(fill="both", expand=True, padx=10, pady=10)
        
    def ejecutar_busqueda_semantica(self):
        for widget in self.scroll_semantico.winfo_children():
            widget.destroy()
            
        query = self.entry_busqueda.get().strip()
        if not query:
            return
            
        resultados = self.vector_dao.buscar_similitud(query)
        if not resultados or not resultados['ids'][0]:
            ctk.CTkLabel(self.scroll_semantico, text="No se encontraron coincidencias.", text_color="gray").pack(pady=20)
            return
            
        for i, paciente_id in enumerate(resultados['ids'][0]):
            paciente = self.dao.obtener_paciente(paciente_id)
            if not paciente: continue
            
            distancia = resultados['distances'][0][i]
            similitud = max(0, int((1 - distancia)*100))
            historial = resultados['documents'][0][i]
            
            frame = ctk.CTkFrame(self.scroll_semantico, corner_radius=10)
            frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(frame, text=f"Paciente: {paciente.nombre} {paciente.apellido} (DNI: {paciente.dni})", font=ctk.CTkFont(weight="bold", size=16)).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(frame, text=f"Similitud Semántica: {similitud}%", font=ctk.CTkFont(size=12), text_color="#3498db").pack(anchor="w", padx=10, pady=0)
            ctk.CTkLabel(frame, text=f"Historial:\n{historial}", justify="left", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 10))

    def construir_tab_geo(self, tab):
        ctk.CTkLabel(tab, text="Búsqueda Geoespacial de Pacientes ($nearSphere)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        frame_top = ctk.CTkFrame(tab, fg_color="transparent")
        frame_top.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_top, text="Radio (KM):", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        self.entry_radio = ctk.CTkEntry(frame_top, placeholder_text="Ej: 5", width=100, height=40)
        self.entry_radio.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(frame_top, text="Encontrar Pacientes Cercanos", command=self.ejecutar_busqueda_geo, height=40, font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.scroll_geo = ctk.CTkScrollableFrame(tab, width=700, height=400)
        self.scroll_geo.pack(fill="both", expand=True, padx=10, pady=10)
        
    def ejecutar_busqueda_geo(self):
        for widget in self.scroll_geo.winfo_children():
            widget.destroy()
            
        try:
            radio = float(self.entry_radio.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido para el radio.")
            return
            
        ubicacion = self.clinica_actual.get("ubicacion")
        if not ubicacion or "coordinates" not in ubicacion:
            ctk.CTkLabel(self.scroll_geo, text="La clínica actual no tiene coordenadas registradas.", text_color="red").pack(pady=20)
            return
            
        lon, lat = ubicacion["coordinates"]
        
        pacientes = self.dao.buscar_pacientes_cerca_de(lat, lon, radio)
        
        if not pacientes:
            ctk.CTkLabel(self.scroll_geo, text="No hay pacientes en ese radio.", text_color="gray").pack(pady=20)
            return
            
        for p in pacientes:
            frame = ctk.CTkFrame(self.scroll_geo, corner_radius=10)
            frame.pack(fill="x", pady=5, padx=5)
            
            p_lon, p_lat = p.ubicacion["coordinates"]
            ctk.CTkLabel(frame, text=f"{p.nombre} {p.apellido}", font=ctk.CTkFont(weight="bold", size=16)).pack(anchor="w", padx=10, pady=(10, 0))
            ctk.CTkLabel(frame, text=f"DNI: {p.dni} | Genero: {p.genero} | Coordenadas: [{p_lon:.4f}, {p_lat:.4f}]", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(5, 10))


if __name__ == "__main__":
    app = BioTraceApp()
    app.mainloop()
