import sys
import os
import random
import string
import platform
import re
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from fpdf import FPDF
from database import *

class Star():
    def __init__(self,es_director=False, usuario=""):
        self.usuario = usuario
        self.rootapp = tk.Toplevel()
        self.rootapp.protocol("WM_DELETE_WINDOW", self.cerrar_sesion)
        self.rootapp.geometry("1500x800")
        self.rootapp.title("Sistema Administrativo de Registros")
        
        self.superUsuario = es_director

        self.header_frame = tk.Frame(self.rootapp)
        self.header_frame.pack(side="top", fill="x")
        self.tree_frame = tk.Frame(self.rootapp)
        self.tree_frame.pack(side="top",fill="both",expand=True)
        self.crear_header_widgets()
        self.crear_tree_widgets()
        self.refrescar_tree()

        # boton de cerrar sesion
        self.boton_salir = tk.Button(
            self.rootapp,
            text="󰗼 Cerrar Sesión",
            command=self.cerrar_sesion,
            bg="#e64553", fg="black",
            font=("RobotoMono Nerd Font Mono", 11, "bold")
        )
        self.boton_salir.place(relx=1.0, rely=0.0, anchor="ne")

    def generar_codigo_dependencia(self):
        letras = ''.join(random.choices(string.ascii_uppercase, k=4))
        numeros = ''.join(random.choices(string.digits, k=4))
        return f"{letras}-{numeros}"

    def crear_mostrar_ventana(self):
        cedula_buscada = self.entry_cedula.get().strip().replace(".", "").replace("-", "")
        
        # 1. consultar la vista pidiendo las columnas en el ORDEN EXACTO de la tupla 'campos', esto garantiza que los cálculos de la DB lleguen donde deben.
        columnas_sql = """
            cedula, nombres, apellidos, fecha_nacimiento, edad, 
            direccion, correo, telefono, carnet_patria, 
            grado_instruccion, titulo_obtenido, fecha_ingreso, 
            anos_servicio, comuna, cargo, codigo_dependencia, 
            categoria, estado_laboral
        """
        registro_vista = db.consultar(f"SELECT {columnas_sql} FROM vista_personal_detallada WHERE cedula=(?)",(cedula_buscada,))
        
        if not registro_vista:
            messagebox.showwarning("No encontrado", "No existen datos para la cédula ingresada.")
            return

        self.ventana_mostrar = tk.Toplevel(self.rootapp)
        self.ventana_mostrar.geometry("900x550")
        self.ventana_mostrar.title(f"Registro de: {cedula_buscada}")

        self.ventana_mostrar.grid_columnconfigure((0, 2), weight=1)
        self.ventana_mostrar.grid_columnconfigure((1, 3), weight=1)

        campos = (
            "Cedula", "Nombres", "Apellidos", "Fecha de Nacimiento", "Edad", 
            "Direccion", "Correo", "Telefono", "Carnet de la Patria", 
            "Grado Instruccion", "Titulo obtenido", "Fecha de ingreso", 
            "Años de servicio", "Comuna", "Cargo", "Codigo de dependencia", 
            "Categoria Personal", "Estado Laboral"
        )
        
        datos_v = registro_vista[0]

        # 2. generar labels y entradas en DOS COLUMNAS
        for i, campo in enumerate(campos):
            col_label = 0 if i < 9 else 2
            col_entry = 1 if i < 9 else 3
            fila = i if i < 9 else i - 9

            tk.Label(self.ventana_mostrar, text=campo, font=("Arial", 10, "bold"), anchor="center").grid(
                row=fila, column=col_label, sticky="ew", padx=10, pady=8
            )
            
            entry = tk.Entry(self.ventana_mostrar, font=("Arial", 10))
            entry.grid(row=fila, column=col_entry, padx=10, pady=8, sticky="w")
            
            try:
                contenido = datos_v[i] if datos_v[i] is not None else ""
            except IndexError:
                contenido = "N/P"
                
            entry.insert(0, contenido)
            entry.config(state="readonly")

        # SECCION DE BOTONES
        frame_botones = tk.Frame(self.ventana_mostrar)
        frame_botones.grid(row=10, column=0, columnspan=4, pady=25) 

        tk.Button(frame_botones, text="󰕒 Exportar PDF", bg="#7287fd", fg="black", font=("Arial", 10, "bold"),
                  command=lambda: self.exportar_pdf_individual(datos_v)).pack(side="left", padx=10)

        if self.superUsuario:
            tk.Button(frame_botones, text="󰏫 Modificar", bg="#40a02b", fg="black", font=("Arial", 10, "bold"), width=12,
                      command=self.preparar_edicion).pack(side="left", padx=10)
            
            tk.Button(frame_botones, text="󰆴 Eliminar", bg="#e64553", fg="black", font=("Arial", 10, "bold"), width=12,
                      command=self.borrar_registro).pack(side="left", padx=10)

        tk.Button(frame_botones, text="Cerrar", bg="#6f7181", fg="black", font=("Arial", 10, "bold"), width=12,
                  command=self.ventana_mostrar.destroy).pack(side="left", padx=10)
    
    def crear_nuevo_ventana(self):
        self.ventana_nuevo = tk.Toplevel(self.rootapp)
        self.ventana_nuevo.geometry("750x650")
        self.ventana_nuevo.title("Nuevo Registro")

        grados_instruccion = db.consultar("SELECT id_grado_instruccion, descripcion FROM Grado_instruccion")
        self.mapa_grados = {desc: idx for idx, desc in grados_instruccion}
        estado_laboral = db.consultar("SELECT id_estado_laboral, nombre FROM Estado_laboral")
        self.mapa_estado_laboral = {desc: idx for idx, desc in estado_laboral}
        categoria_personal = db.consultar("SELECT id_categoria_personal, nombre FROM Categoria_personal")
        self.mapa_categoria = {desc: idx for idx, desc in categoria_personal}
        
        # obtencion de nombres de comunas existentes para las sugerencias del buscador
        comunas_query = db.consultar("SELECT nombre FROM Comunas")
        self.lista_comunas = [c[0] for c in comunas_query]
        
        campos = ("Cedula","Nombres","Apellidos","Fecha de Nacimiento","Direccion","Correo","Telefono","Carnet de la Patria", "Grado de instruccion","Titulo obtenido", "Fecha de ingreso","Comuna","Cargo","Categoria Personal", "Estado Laboral")
        self.ventana_nuevo.grid_columnconfigure(0, weight=1) 
        self.ventana_nuevo.grid_columnconfigure(1, weight=1)

        for i, campo in enumerate(campos):
            lbl = tk.Label(self.ventana_nuevo, text=campo, font=("Arial", 10, "bold"), anchor="center")
            lbl.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

        # definicion de todos los self.ent_ y self.cb_
        self.ent_cedula = tk.Entry(self.ventana_nuevo); self.ent_cedula.grid(row=0,column=1, sticky="w", padx=10)
        self.ent_nombres = tk.Entry(self.ventana_nuevo); self.ent_nombres.grid(row=1,column=1, sticky="w", padx=10)
        self.ent_apellidos = tk.Entry(self.ventana_nuevo); self.ent_apellidos.grid(row=2,column=1, sticky="w", padx=10)
        self.ent_fecha_nacimiento = tk.Entry(self.ventana_nuevo); self.ent_fecha_nacimiento.grid(row=3,column=1, sticky="w", padx=10)
        self.ent_direccion = tk.Entry(self.ventana_nuevo); self.ent_direccion.grid(row=4,column=1, sticky="w", padx=10)
        self.ent_correo = tk.Entry(self.ventana_nuevo); self.ent_correo.grid(row=5,column=1, sticky="w", padx=10)
        self.ent_telefono = tk.Entry(self.ventana_nuevo); self.ent_telefono.grid(row=6,column=1, sticky="w", padx=10)
        self.ent_carnet_patria = tk.Entry(self.ventana_nuevo); self.ent_carnet_patria.grid(row=7,column=1, sticky="w", padx=10)
        
        self.cb_grados = ttk.Combobox(self.ventana_nuevo,values=list(self.mapa_grados.keys()),state="readonly")
        self.cb_grados.grid(row=8,column=1, sticky="w", padx=10)

        self.ent_titulo = tk.Entry(self.ventana_nuevo); self.ent_titulo.grid(row=9,column=1, sticky="w", padx=10)
        self.ent_fecha_ingreso = tk.Entry(self.ventana_nuevo); self.ent_fecha_ingreso.grid(row=10,column=1, sticky="w", padx=10)
        
        # implementacion de combobox editable para permitir búsqueda y entrada de nuevas comunas
        self.cb_comuna = ttk.Combobox(self.ventana_nuevo, values=self.lista_comunas)
        self.cb_comuna.grid(row=11, column=1, sticky="w", padx=10)

        # vinculacion de evento para filtrar sugerencias en tiempo real segun lo escrito
        self.cb_comuna.bind("<KeyRelease>", self.filtrar_comunas)
        
        self.ent_cargo = tk.Entry(self.ventana_nuevo); self.ent_cargo.grid(row=12,column=1, sticky="w", padx=10)

        self.cb_categoria = ttk.Combobox(self.ventana_nuevo,values=list(self.mapa_categoria.keys()),state="readonly")
        self.cb_categoria.grid(row=13,column=1, sticky="w", padx=10)

        self.cb_estado = ttk.Combobox(self.ventana_nuevo,values=list(self.mapa_estado_laboral.keys()),state="readonly")
        self.cb_estado.grid(row=14,column=1, sticky="w", padx=10)

        # boton accion: inicialmente Guardar
        self.btn_accion = tk.Button(self.ventana_nuevo, text="Guardar", bg="#40a02b", fg="black", font=("Arial", 10, "bold"), command=self.guardar_registro_bd)
        self.btn_accion.grid(row=20, column=1, pady=20, sticky="w", padx=10)
    
    def preparar_edicion(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showerror("Error", "Introduzca una cédula")
            return
            
        # se consulta la VISTA para obtener el nombre de la comuna
        registro = db.consultar("""
            SELECT cedula, nombres, apellidos, fecha_nacimiento, edad,
                direccion, correo, telefono, carnet_patria,
                grado_instruccion, titulo_obtenido, fecha_ingreso,
                anos_servicio, comuna, cargo, codigo_dependencia,
                categoria, estado_laboral
            FROM vista_personal_detallada WHERE cedula = ?
        """, [cedula])
        
        if registro:
            if hasattr(self, 'ventana_mostrar') and self.ventana_mostrar.winfo_exists():
                self.ventana_mostrar.destroy()

            datos = registro[0] # datos vienen de la VISTA
            self.crear_nuevo_ventana()
            self.ventana_nuevo.title(f"Modificar Registro: {cedula}")
            
            self.btn_accion.config(text="Actualizar datos", bg="#40a02b", fg="black", font=("Arial", 10, "bold"), command=self.actualizar_registro_bd)

            # rellenar campos (Usando los indices de la VISTA)
            self.ent_cedula.insert(0, datos[0]) # cedula
            self.ent_cedula.config(state="disabled")
            self.ent_nombres.insert(0, datos[1])
            self.ent_apellidos.insert(0, datos[2])
            self.ent_fecha_nacimiento.insert(0, datos[3] if datos[3] else "")
            self.ent_direccion.insert(0, datos[5] if datos[5] else "")
            self.ent_correo.insert(0, datos[6] if datos[6] else "")
            self.ent_telefono.insert(0, datos[7] if datos[7] else "")
            self.ent_carnet_patria.insert(0, datos[8] if datos[8] else "")
            self.ent_carnet_patria.config(state="disabled")
            self.ent_titulo.insert(0, datos[10] if datos[10] else "")
            self.ent_fecha_ingreso.insert(0, datos[11] if datos[11] else "")
            
            self.cb_comuna.set(datos[13] if datos[13] else "")
            
            self.ent_cargo.insert(0, datos[14] if datos[14] else "")

            self.cb_grados.set(datos[9]) # el nombre ya viene en la vista
            self.cb_categoria.set(datos[16]) 
            self.cb_estado.set(datos[17])

    def validar_fechas(self, fecha_nac, fecha_ing):
        # el patron busca: 4 digitos - 2 dígitos - 2 dígitos
        patron = r"^\d{4}-\d{2}-\d{2}$"

        # 1. validar formato de fecha de nacimiento
        if not re.match(patron, fecha_nac):
            return False, "Formato de Fecha de Nacimiento incorrecto. Use: AAAA-MM-DD (Ej: 1970-02-03)"

        # 2. validar formato de fecha de ingreso
        if not re.match(patron, fecha_ing):
            return False, "Formato de Fecha de Ingreso incorrecto. Use: AAAA-MM-DD (Ej: 2000-05-15)"

        # 3. validacion logica
        try:
            fn = datetime.strptime(fecha_nac, "%Y-%m-%d")
            fi = datetime.strptime(fecha_ing, "%Y-%m-%d")
            hoy = datetime.now()

            if fn >= hoy:
                return False, "La fecha de nacimiento debe ser anterior a la fecha actual."
            if fi >= hoy:
                return False, "La fecha de ingreso debe ser anterior a la fecha actual."
            if fi < fn:
                return False, "La fecha de ingreso no puede ser anterior a la de nacimiento."
        except ValueError:
            return False, "La fecha ingresada no existe (ejemplo: 2023-02-30)."

        return True, ""

    def actualizar_registro_bd(self):
        # 1. obtener y limpiar valores de la interfaz
        nombres = self.ent_nombres.get().strip()
        apellidos = self.ent_apellidos.get().strip()
        fecha_nacimiento = self.ent_fecha_nacimiento.get().strip()
        direccion = self.ent_direccion.get().strip()
        correo = self.ent_correo.get().strip()
        telefono = self.ent_telefono.get().strip()
        titulo = self.ent_titulo.get().strip()
        fecha_ingreso = self.ent_fecha_ingreso.get().strip()
        cargo = self.ent_cargo.get().strip()
        comuna_nombre = self.cb_comuna.get().strip()

        # 2. validacion centralizada de fechas
        es_valido, mensaje = self.validar_fechas(fecha_nacimiento, fecha_ingreso)
        if not es_valido:
            messagebox.showerror("Error de Fecha", mensaje, parent=self.ventana_nuevo)
            return

        # 3. validacion de campos obligatorios basicos
        if not all([nombres, apellidos, direccion, comuna_nombre]):
            messagebox.showwarning("Atención", "Complete los campos obligatorios.", parent=self.ventana_nuevo)
            return

        try:
            # 4. recuperar la cedula de forma segura (esta disabled para evitar ediciones)
            self.ent_cedula.config(state="normal")
            cedula = self.ent_cedula.get().strip()
            self.ent_cedula.config(state="disabled")

            # 5. logica de comuna (mantenimiento de tablas relacionadas)
            res_comuna = db.consultar("SELECT id_comuna FROM Comunas WHERE nombre = ?", (comuna_nombre,))
            if res_comuna:
                id_comuna_final = res_comuna[0][0]
            else:
                db.consultar("INSERT INTO Comunas (nombre) VALUES (?)", (comuna_nombre,))
                id_comuna_final = db.consultar("SELECT id_comuna FROM Comunas WHERE nombre = ?", (comuna_nombre,))[0][0]

            # 6. mapeo de comboboxes a IDs
            id_grado = self.mapa_grados.get(self.cb_grados.get())
            id_cat = self.mapa_categoria.get(self.cb_categoria.get())
            id_est = self.mapa_estado_laboral.get(self.cb_estado.get())

            if not all([id_grado, id_cat, id_est]):
                messagebox.showwarning("Faltan datos", "Seleccione opciones en todos los menús desplegables.", parent=self.ventana_nuevo)
                return

            # 7. preparacion de la tupla para UPDATE, ya que el orden debe ser IDENTICO al SQL)
            datos_update = (
                nombres,           # 1
                apellidos,         # 2
                fecha_nacimiento,  # 3
                direccion,         # 4
                correo,            # 5
                telefono,          # 6
                titulo,            # 7
                fecha_ingreso,     # 8
                id_comuna_final,   # 9
                cargo,             # 10
                id_grado,          # 11
                id_cat,            # 12
                id_est,            # 13
                cedula             # 14 (WHERE)
            )

            # 8. sentencia SQL
            sql = """UPDATE Personal SET 
                        nombres=?, apellidos=?, fecha_nacimiento=?, direccion=?, 
                        correo=?, telefono=?, titulo_obtenido=?, 
                        fecha_ingreso=?, id_comuna=?, cargo=?, id_grado_instruccion=?, 
                        id_categoria_personal=?, id_estado_laboral=?
                     WHERE cedula=?"""

            db.consultar(sql, datos_update)

            # 9. finalizacion y feedback
            messagebox.showinfo("Éxito", "Los datos han sido actualizados correctamente.", parent=self.ventana_nuevo)
            self.refrescar_tree() 
            self.ventana_nuevo.destroy() 
            
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo actualizar: {str(e)}", parent=self.ventana_nuevo)
        
    def guardar_registro_bd(self):
        # 1. obtener valores y limpiar espacios
        cedula = self.ent_cedula.get().strip()
        nombres = self.ent_nombres.get().strip()
        apellidos = self.ent_apellidos.get().strip()
        direccion = self.ent_direccion.get().strip()
        comuna_nombre = self.cb_comuna.get().strip()
        fecha_nacimiento = self.ent_fecha_nacimiento.get().strip()
        fecha_ingreso = self.ent_fecha_ingreso.get().strip()
        
        correo = self.ent_correo.get().strip()
        telefono = self.ent_telefono.get().strip()
        carnet_patria = self.ent_carnet_patria.get().strip()
        titulo = self.ent_titulo.get().strip()
        cargo = self.ent_cargo.get().strip()

        # 2. validacion centralizada de fechas
        es_valido, mensaje = self.validar_fechas(fecha_nacimiento, fecha_ingreso)
        if not es_valido:
            messagebox.showerror("Error de Fecha", mensaje, parent=self.ventana_nuevo)
            return

        # 3. restricciones de campos obligatorios
        campos_obligatorios = [
            (cedula, "Cédula"), (nombres, "Nombres"), (apellidos, "Apellidos"),
            (direccion, "Dirección"), (comuna_nombre, "Comuna")
        ]

        for valor, nombre_campo in campos_obligatorios:
            if not valor:
                messagebox.showwarning("Campo Faltante", f"El campo '{nombre_campo}' es obligatorio.", parent=self.ventana_nuevo)
                return

        if not cedula.isdigit():
            messagebox.showwarning("Error", "La cédula debe contener solo números", parent=self.ventana_nuevo)
            return
        if carnet_patria and not carnet_patria.isdigit():
            messagebox.showwarning("Error", "El Carnet de la Patria debe contener solo números", parent=self.ventana_nuevo)
            return

        # 4. verificar duplicados en la DB
        existe = db.consultar("SELECT 1 FROM Personal WHERE cedula = ?", [cedula])
        if existe:
            messagebox.showerror("Cédula Duplicada", f"La cédula {cedula} ya existe.", parent=self.ventana_nuevo)
            return

        try:
            # 5. mapeo de combobox a IDs (llaves foraneas)
            id_grado = self.mapa_grados.get(self.cb_grados.get())
            id_cat = self.mapa_categoria.get(self.cb_categoria.get())
            id_est = self.mapa_estado_laboral.get(self.cb_estado.get())

            if not all([id_grado, id_cat, id_est]):
                messagebox.showwarning("Selección Incompleta", "Por favor, seleccione una opción en todos los menús desplegables.", parent=self.ventana_nuevo)
                return

            # 6. gestion de la tabla comunas (evitar redundancia)
            res_comuna = db.consultar("SELECT id_comuna FROM Comunas WHERE nombre = ?", (comuna_nombre,))
            
            if res_comuna:
                id_comuna_final = res_comuna[0][0]
            else:
                db.consultar("INSERT INTO Comunas (nombre) VALUES (?)", (comuna_nombre,))
                nuevo_id_res = db.consultar("SELECT id_comuna FROM Comunas WHERE nombre = ?", (comuna_nombre,))
                id_comuna_final = nuevo_id_res[0][0]

            # 7. generacion del codigo Único
            codigo_auto = self.generar_codigo_dependencia()

            # 8. preparacion de la tupla (16 campos EXACTOS)
            datos = (
                cedula, nombres, apellidos, fecha_nacimiento,
                direccion, correo, telefono, carnet_patria, 
                titulo, fecha_ingreso, id_comuna_final, cargo,
                codigo_auto, # Posición 13
                id_grado, id_cat, id_est
            )

            # 9. ejecucion de la insercion
            sql = """INSERT INTO Personal (
                cedula, nombres, apellidos, fecha_nacimiento, direccion, 
                correo, telefono, carnet_patria, titulo_obtenido, fecha_ingreso, 
                id_comuna, cargo, codigo_dependencia, id_grado_instruccion, 
                id_categoria_personal, id_estado_laboral
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

            db.consultar(sql, datos)
            
            # 10. actualizacion de interfaz y post-procesado
            messagebox.showinfo("Éxito", f"Personal registrado.\nCódigo de Dependencia: {codigo_auto}", parent=self.ventana_nuevo)
            
            # refrescamos la tabla principal para que aparezca el nuevo registro
            self.refrescar_tree()
            
            # se cierra la ventana: al hacer esto, el usuario vuelve a la pantalla principal automaticamente
            self.ventana_nuevo.destroy()

        except Exception as e:
            if "UNIQUE constraint failed: Personal.carnet_patria" in str(e):
                carnet_ingresado = self.ent_carnet_patria.get().strip()
                messagebox.showerror("Error de Duplicidad", f"El Carnet de la Patria {carnet_ingresado} ya se encuentra registrado.", parent=self.ventana_nuevo)
            elif "UNIQUE constraint failed: Personal.cedula" in str(e):
                messagebox.showerror("Error de Duplicidad", f"La cédula {cedula} ya se encuentra registrada.", parent=self.ventana_nuevo)
            else:
                messagebox.showerror("Error de Sistema", f"No se pudo guardar: {str(e)}", parent=self.ventana_nuevo)
                
    def borrar_registro(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showerror("Error", "No hay ninguna cédula seleccionada para eliminar.")
            return

        # 1. pedir confirmacion al usuario
        confirmar = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar permanentemente al empleado con cédula {cedula}?")
        
        if confirmar:
            try:
                # 2. ejecutar la eliminacion en la base de datos
                db.consultar("DELETE FROM Personal WHERE cedula = ?", (cedula,))
                
                # 3. exito: se cierra la ventana de detalles (si existe)
                if hasattr(self, 'ventana_mostrar') and self.ventana_mostrar.winfo_exists():
                    self.ventana_mostrar.destroy()
                messagebox.showinfo("Eliminado", f"El registro con la cédula {cedula} ha sido eliminado correctamente.")
                
                # 4. limpiar el buscador y refrescar la tabla principal
                self.entry_cedula.delete(0, tk.END)
                self.refrescar_tree()

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

    def crear_header_widgets(self):
        # boton refrescar
        self.boton_refrescar = tk.Button(self.header_frame, text="󰑐 Refrescar", command=self.refrescar_tree, font=("RobotoMono Nerd Font Mono", 11, "bold"))
        self.boton_refrescar.grid(row=0, column=0)
        
        # campo de entrada para la Cedula
        self.entry_cedula = tk.Entry(self.header_frame, font=("RobotoMono Nerd Font Mono", 11, "bold"))
        self.entry_cedula.grid(row=0, column=1)
        
        # boton buscar (este abrira la ventana con los botones de modificar/eliminar)
        self.boton_buscar = tk.Button(self.header_frame, text="󰍉 Buscar", command=self.buscar_cedula, font=("RobotoMono Nerd Font Mono", 11, "bold"))
        self.boton_buscar.grid(row=0, column=2)
        
        # boton nuevo
        self.boton_nuevo = tk.Button(self.header_frame, text="󰐕 Nuevo", command=self.crear_nuevo_ventana, font=("RobotoMono Nerd Font Mono", 11, "bold"), bg="#40a02b", fg="black")
        self.boton_nuevo.grid(row=0, column=3)

        # filtro de estado
        tk.Label(self.header_frame, text="Filtrar:", font=("RobotoMono Nerd Font Mono", 11)).grid(row=0, column=4, padx=5)
        self.cb_filtro_estado = ttk.Combobox(self.header_frame, values=["Todos", "Activo", "Reposo", "Jubilado", "Permiso"], state="readonly", width=10)
        self.cb_filtro_estado.set("Todos")
        self.cb_filtro_estado.grid(row=0, column=5, padx=5)
        
        # evento para filtrar automaticamente al cambiar la opcion
        self.cb_filtro_estado.bind("<<ComboboxSelected>>", lambda e: self.refrescar_tree())

        # boton exportar lista
        self.boton_exportar_lista = tk.Button(
            self.header_frame, 
            text="󰕒 Exportar PDF Lista", 
            command=self.exportar_pdf_filtrado, 
            font=("RobotoMono Nerd Font Mono", 11, "bold"),
            bg="#7287fd", fg="black"
        )
        self.boton_exportar_lista.grid(row=0, column=6, padx=10)

        # boton de ayuda
        self.boton_ayuda = tk.Button(
            self.header_frame,
            text="? Ayuda",
            command=self.mostrar_ayuda,
            font=("RobotoMono Nerd Font Mono", 11, "bold"),
            bg="#e7eb0b", fg="black"
        )
        self.boton_ayuda.grid(row=0, column=7, padx=10)
        
    def crear_tree_widgets(self):
        self.tree_columnas = ("cedula","nombres","apellidos","categoria","cargo","estado",)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree['show'] = 'headings'
        self.tree['columns'] = self.tree_columnas
        
        # definicion de titulos
        self.tree.heading("cedula",text="Cédula")
        self.tree.heading("nombres",text="Nombres")
        self.tree.heading("apellidos",text="Apellidos")
        self.tree.heading("categoria",text="Categoría de Empleado")
        self.tree.heading("cargo",text="Cargo")
        self.tree.heading("estado",text="Estado Laboral")

        # se recorre cada columna para centrar el contenido
        for col in self.tree_columnas:
            self.tree.column(col, anchor="center") 

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.pack(fill="both",expand=True)
    
    def refrescar_tree(self):
        # 1. limpiar todos los datos actuales de la tabla (treeview)
        for registro in self.tree.get_children():
            self.tree.delete(registro)
        
        # 2. obtener el estado seleccionado en el nuevo combobox de filtro
        estado_seleccionado = self.cb_filtro_estado.get()

        # 3. definir la consulta segun el filtro
        if estado_seleccionado == "Todos":
            sql = "SELECT cedula, nombres, apellidos, categoria, cargo, estado_laboral FROM vista_personal_detallada"
            parametros = ()
        else:
            # filtramos por la columna estado_laboral de tu Vista
            sql = "SELECT cedula, nombres, apellidos, categoria, cargo, estado_laboral FROM vista_personal_detallada WHERE estado_laboral = ?"
            parametros = (estado_seleccionado,)

        # 4. cargar los datos filtrados
        try:
            for registro in db.consultar(sql, parametros):
                self.tree.insert("", "end", values=registro)
        except Exception as e:
            print(f"Error al refrescar la tabla: {e}")

    def buscar_cedula(self):
        busqueda = self.entry_cedula.get().strip().replace(".", "").replace("-", "")
        if not busqueda:
            messagebox.showwarning("Error", "Por favor introduzca una cédula")
            return
        
        existe = db.consultar("SELECT 1 FROM personal WHERE cedula=(?)",(busqueda,))
        if existe:
            self.crear_mostrar_ventana()
        else:
            messagebox.showwarning("Error","No se encontro la cedula")

    def filtrar_comunas(self, event):
        # 1. si es una tecla de movimiento, no se hace nada
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return

        texto = self.cb_comuna.get().lower()
        
        # 2. solo se filtran los valores internos
        if texto == '':
            self.cb_comuna['values'] = self.lista_comunas
        else:
            filtradas = [c for c in self.lista_comunas if texto in c.lower()]
            self.cb_comuna['values'] = filtradas

    def exportar_pdf_individual(self, datos):

        # 1. pedir al usuario donde guardar el archivo antes de procesar
        sugerencia = f"Reporte_Individual_{datos[0]}.pdf"
        ruta_destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile=sugerencia,
            title="Guardar Reporte Individual"
        )

        if not ruta_destino: # si el usuario cancela
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            fecha_generacion = datetime.now().strftime("%d/%m/%Y")

            # membrete
            if os.path.exists("logo.png"):
                pdf.image("logo.png", x=10, y=8, w=25, h=25)

            pdf.set_xy(10, 12)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, "C.E. José Antonio Páez", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, "Sistema Administrativo de Registros", ln=True, align="C")
            pdf.set_font("Arial", "", 9)
            pdf.cell(0, 6, f"Fecha: {fecha_generacion}", ln=True, align="R")

            if pdf.get_y() < 36:
                pdf.set_y(36)

            # linea separadora
            pdf.ln(2)
            pdf.set_draw_color(0, 0, 0)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

            # titulo del reporte
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"REPORTE DEL PERSONAL - CÉDULA: {datos[0]}", ln=True, align="C")
            pdf.ln(4)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

            # datos personales
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Datos Personales", ln=True)
            pdf.ln(2)

            datos_personales = [
                (0, "Cédula"), (1, "Nombres"), (2, "Apellidos"),
                (3, "Fecha de Nacimiento"), (4, "Edad"), (5, "Dirección"),
                (6, "Correo"), (7, "Teléfono"), (8, "Carnet de la Patria")
            ]

            for idx, campo in datos_personales:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(50, 7, f"{campo}:", border=0)
                pdf.set_font("Arial", "", 10)
                try:
                    valor = str(datos[idx]).strip() if datos[idx] else "N/P"
                except IndexError:
                    valor = "N/P"
                limpio = valor.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 7, limpio, border=0, ln=True)

            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

            # datos laborales
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Datos Laborales", ln=True)
            pdf.ln(2)

            datos_laborales = [
                (14, "Cargo"), (16, "Categoría"), (11, "Fecha de Ingreso"),
                (12, "Años de Servicio"), (17, "Estado Laboral"),
                (15, "Código de Dependencia"), (13, "Comuna")
            ]

            for idx, campo in datos_laborales:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(50, 7, f"{campo}:", border=0)
                pdf.set_font("Arial", "", 10)
                try:
                    valor = str(datos[idx]).strip() if datos[idx] else "N/P"
                except IndexError:
                    valor = "N/P"
                limpio = valor.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 7, limpio, border=0, ln=True)

            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

            # datos academicos
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Datos Académicos", ln=True)
            pdf.ln(2)

            datos_academicos = [
                (9, "Grado de Instrucción"), (10, "Título Obtenido")
            ]

            for idx, campo in datos_academicos:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(50, 7, f"{campo}:", border=0)
                pdf.set_font("Arial", "", 10)
                try:
                    valor = str(datos[idx]).strip() if datos[idx] else "N/P"
                except IndexError:
                    valor = "N/P"
                limpio = valor.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 7, limpio, border=0, ln=True)

            pdf.set_font("Arial", "I", 8)
            generado_por = f"Reporte generado por: Usuario {self.usuario}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, generado_por, ln=True, align="R")

            pdf.output(ruta_destino)
            messagebox.showinfo("Éxito", f"PDF generado correctamente en:\n{ruta_destino}")
            self.abrir_archivo(ruta_destino)

        except Exception as e:
            messagebox.showerror("Error PDF", f"Error crítico al generar el archivo: {e}")

    def exportar_pdf_filtrado(self):
        filtro_actual = self.cb_filtro_estado.get()

        if not self.tree.get_children():
            messagebox.showwarning(
                "Reporte Vacío",
                f"No hay registros con el estado '{filtro_actual}' para exportar.",
                parent=self.rootapp
            )
            return

        sugerencia = f"Reporte_Personal_{filtro_actual}.pdf"
        ruta_destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile=sugerencia,
            title=f"Guardar Lista de Personal ({filtro_actual})"
        )

        if not ruta_destino:
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            fecha_generacion = datetime.now().strftime("%d/%m/%Y")

            if os.path.exists("logo.png"):
                pdf.image("logo.png", x=10, y=8, w=25, h=25)

            pdf.set_xy(10, 12)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, "C.E. José Antonio Páez", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, "Sistema Administrativo de Registros", ln=True, align="C")
            pdf.set_font("Arial", "", 9)
            pdf.cell(0, 6, f"Fecha: {fecha_generacion}", ln=True, align="R")

            if pdf.get_y() < 36:
                pdf.set_y(36)

            # linea separadora
            pdf.ln(2)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

            # titulo del reporte
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "REPORTE GENERAL DE PERSONAL", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 6, f"Filtro aplicado: {filtro_actual}", ln=True, align="C")
            total = len(self.tree.get_children())
            pdf.cell(0, 6, f"Total de registros: {total}", ln=True, align="C")
            pdf.ln(4)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

            # encabezados de columnas
            col_widths = [25, 40, 40, 40, 35, 20]
            encabezados = ["Cédula", "Nombres", "Apellidos", "Categoría", "Cargo", "Estado"]

            pdf.set_font("Arial", "B", 9)
            for i, enc in enumerate(encabezados):
                limpio = enc.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(col_widths[i], 7, limpio, border=0, align="C")
            pdf.ln()

            # linea bajo encabezados
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)

            # filas de datos
            pdf.set_font("Arial", "", 9)
            for item in self.tree.get_children():
                valores = self.tree.item(item)['values']
                for i, valor in enumerate(valores):
                    limpio = str(valor).encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(col_widths[i], 7, limpio, border=0, align="C")
                pdf.ln()

            pdf.set_font("Arial", "I", 8)
            generado_por = f"Reporte generado por: Usuario {self.usuario}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, generado_por, ln=True, align="R")

            pdf.output(ruta_destino)
            messagebox.showinfo("Éxito", f"Reporte generado en:\n{ruta_destino}")
            self.abrir_archivo(ruta_destino)

        except Exception as e:
            messagebox.showerror("Error PDF", f"No se pudo generar el reporte: {e}")
            
    def abrir_archivo(self, ruta):
        if platform.system() == 'Windows':
            os.startfile(ruta)
        elif platform.system() == 'Darwin': # macOS
            os.system(f'open "{ruta}"')
        else: # linux y otros
            os.system(f'xdg-open "{ruta}"')
    
    def mostrar_ayuda(self):
        ventana_ayuda = tk.Toplevel(self.rootapp)
        ventana_ayuda.title("Ayuda")
        ventana_ayuda.geometry("540x480")
        ventana_ayuda.resizable(False, False)

        instrucciones = (
            "1. BUSCAR un empleado: Escriba la cédula en el campo de búsqueda y presione 'Buscar'.",
            "2. VER detalles: Al buscar una cédula existente se abrirá una ventana con todos sus datos.",
            "3. NUEVO registro: Presione 'Nuevo' y complete los campos requeridos, luego presione 'Guardar'.",
            "4. MODIFICAR un registro: Busque la cédula, abra sus detalles y presione 'Modificar' (solo Director).",
            "5. ELIMINAR un registro: Busque la cédula, abra sus detalles y presione 'Eliminar' (solo Director).",
            "6. FILTRAR por estado: Use el menú 'Filtrar' para ver empleados Activos, en Reposo, Jubilados, de Permiso, o Todos.",
            "7. EXPORTAR PDF en lista: Presione 'Exportar PDF Lista' para guardar la lista visible como PDF según el filtro seleccionado.",
            "8. EXPORTAR PDF individual: Dentro de los detalles de un empleado, presione 'Exportar PDF'.",
            "9. REFRESCAR la tabla: Presione 'Refrescar' para recargar los datos manualmente.",
            "10. CERRAR SESIÓN: Presione 'Cerrar Sesión' para salir del sistema.",
        )

        tk.Label(ventana_ayuda, text="Guía de uso del sistema", font=("Arial", 14, "bold")).pack(pady=(15, 10))

        tk.Label(ventana_ayuda,
         text="¿Algún problema o duda? Contáctenos a través del siguiente e-mail: star_iutepi@protonmail.com",
         font=("Arial", 9), fg="#555555").pack(side="bottom", pady=(0, 10))

        tk.Button(ventana_ayuda, text="Cerrar", bg="#6c6f85", fg="black",
                font=("Arial", 10, "bold"), command=ventana_ayuda.destroy).pack(side="bottom", pady=5)
        
        frame_texto = tk.Frame(ventana_ayuda)
        frame_texto.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(frame_texto)
        scrollbar.pack(side="right", fill="y")

        texto = tk.Text(frame_texto, font=("Arial", 11), wrap="word",
                        yscrollcommand=scrollbar.set, state="normal",
                        relief="flat", padx=10, pady=5)
        texto.pack(fill="both", expand=True)

        for instruccion in instrucciones:
            texto.insert("end", instruccion + "\n\n")

        texto.config(state="disabled")
        scrollbar.config(command=texto.yview)

    def cerrar_sesion(self):
        confirmar = messagebox.askyesno("Salir", "¿Desea cerrar el sistema por completo?")
        if confirmar:
            self.rootapp.destroy()
            sys.exit()

def ejecutar_sistema():
    def iniciar_sesion(entry_nombre, entry_password, login):
        usuario_txt = entry_nombre.get().strip()
        pass_txt = entry_password.get().strip()

        if not usuario_txt or not pass_txt:
            messagebox.showwarning("Atención", "Llene todos los campos", parent=login)
            return

        consulta = db.consultar("SELECT rol FROM Usuario WHERE nombre = ? AND password = ?", (usuario_txt, pass_txt))
        
        if consulta:
            rol_obtenido = consulta[0][0]
            login.withdraw() 
            app = Star(es_director=(rol_obtenido == "Director"), usuario=usuario_txt)
            app.rootapp.mainloop()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos", parent=login)

    login = tk.Tk()
    login.title("Login - STAR")
    login.geometry("400x550")
    login.resizable(False, False)

    # titulo principal
    tk.Label(login, text="Sistema Administrativo de Registros", font=("Arial", 14, "bold")).pack(pady=(20, 10))

    try:
        img_logo = tk.PhotoImage(file="logo.png")
        logo_label = tk.Label(login, image=img_logo)
        logo_label.image = img_logo
        logo_label.pack(pady=10)
    except Exception:
        tk.Label(login, text="[ Logo no encontrado ]", fg="red").pack(pady=10)
    
    # contenedor de campos
    frame_inputs = tk.Frame(login)
    frame_inputs.pack(pady=20)

    tk.Label(frame_inputs, text="Usuario:", font=("Arial", 10)).grid(row=0, column=0, pady=10, padx=5, sticky="e")
    entry_nombre = tk.Entry(frame_inputs, font=("Arial", 10))
    entry_nombre.grid(row=0, column=1, pady=10, padx=5)

    tk.Label(frame_inputs, text="Contraseña:", font=("Arial", 10)).grid(row=1, column=0, pady=10, padx=5, sticky="e")
    entry_password = tk.Entry(frame_inputs, show="*", font=("Arial", 10))
    entry_password.grid(row=1, column=1, pady=10, padx=5)

    # boton de ingreso usando lambda para pasar los argumentos
    btn_ingresar = tk.Button(
        login, 
        text="Ingresar", 
        command=lambda: iniciar_sesion(entry_nombre, entry_password, login),
        bg="#40a02b", 
        fg="white", 
        font=("Arial", 10, "bold"),
        width=20,
        cursor="hand2"
    )
    btn_ingresar.pack(pady=20)

    # vincular la tecla enter para mayor comodidad
    login.bind('<Return>', lambda _: iniciar_sesion(entry_nombre, entry_password, login))

    login.mainloop()

if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    ejecutar_sistema() 