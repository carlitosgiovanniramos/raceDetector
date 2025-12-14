"""
Interfaz Gráfica para Gestión de Participantes
Sistema de Cronometraje de Carreras
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gestor_participantes import GestorParticipantes
import os


class InterfazParticipantes:
    """Interfaz gráfica para gestionar participantes de carreras"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("📋 Gestión de Participantes - Sistema de Cronometraje")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)  # Tamaño mínimo de ventana
        self.root.configure(bg="#f0f0f0")
        
        # Inicializar gestor
        self.gestor = GestorParticipantes()
        
        # Configurar estilo
        self.configurar_estilos()
        
        # Crear interfaz
        self.crear_widgets()
        
        # Cargar datos iniciales
        self.actualizar_tabla()
        self.actualizar_estadisticas()
    
    def configurar_estilos(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilo para botones
        style.configure('Action.TButton', 
                       font=('Arial', 10, 'bold'),
                       padding=8)
        
        # Estilo para labels de sección
        style.configure('Section.TLabel',
                       font=('Arial', 12, 'bold'),
                       background='#f0f0f0')
        
        # Estilo para estadísticas
        style.configure('Stats.TLabel',
                       font=('Arial', 10),
                       background='#f0f0f0')
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # ===== MARCO SUPERIOR: BÚSQUEDA Y FILTROS =====
        frame_busqueda = tk.Frame(self.root, bg="#2c3e50", padx=10, pady=10)
        frame_busqueda.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(frame_busqueda, text="🔍 Buscar por Cédula:", 
                font=('Arial', 11, 'bold'), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.entry_busqueda = tk.Entry(frame_busqueda, font=('Arial', 11), width=20)
        self.entry_busqueda.pack(side=tk.LEFT, padx=5)
        self.entry_busqueda.bind('<KeyRelease>', self.buscar_tiempo_real)
        
        tk.Button(frame_busqueda, text="🔍 Buscar", command=self.buscar_participante,
                 bg="#3498db", fg="white", font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_busqueda, text="🔄 Mostrar Todos", command=self.actualizar_tabla,
                 bg="#95a5a6", fg="white", font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_busqueda, text="📊 Estadísticas", command=self.mostrar_estadisticas_detalladas,
                 bg="#9b59b6", fg="white", font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_busqueda, text="🔄 Recargar Tabla", command=self.recargar_tabla,
                 bg="#8e44ad", fg="white", font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Botón Volver (al final de la barra)
        tk.Button(frame_busqueda, text="◀️ Volver", command=self.volver_menu_principal,
                 bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'),
                 padx=15, pady=5, cursor="hand2").pack(side=tk.RIGHT, padx=5)
        
        # ===== MARCO CENTRAL: TABLA DE PARTICIPANTES =====
        frame_tabla = tk.Frame(self.root, bg="#f0f0f0")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(frame_tabla, text="👥 Lista de Participantes", 
                font=('Arial', 12, 'bold'), bg="#f0f0f0").pack(anchor=tk.W, pady=(0, 5))
        
        # Crear Treeview con scrollbars
        frame_tree = tk.Frame(frame_tabla)
        frame_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y = tk.Scrollbar(frame_tree)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        columnas = ("Cédula", "Nombre", "Apellido", "Edad", "Distancia", "Género", "Contacto", "Categoría", "Dorsal", "Estado Pago")
        self.tree = ttk.Treeview(frame_tree, columns=columnas, show='headings',
                                yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set,
                                height=15)
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configurar columnas
        anchos = [100, 120, 120, 60, 80, 180, 100, 100, 70, 100]
        for col, ancho in zip(columnas, anchos):
            self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_por_columna(c))
            self.tree.column(col, width=ancho, anchor=tk.CENTER if col in ["Estado Pago", "Dorsal"] else tk.W)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Vincular eventos
        self.tree.bind('<<TreeviewSelect>>', self.al_seleccionar_participante)  # Selección simple
        self.tree.bind('<Double-1>', self.editar_participante_seleccionado)  # Doble clic
        
        # ===== MARCO INFERIOR: FORMULARIO Y ACCIONES =====
        frame_inferior = tk.Frame(self.root, bg="#ecf0f1")
        frame_inferior.pack(fill=tk.BOTH, padx=10, pady=(5, 10))
        
        # Canvas con scrollbar para el formulario completo
        canvas = tk.Canvas(frame_inferior, bg="#ecf0f1", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame_inferior, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ecf0f1")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack del canvas y scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Contenedor principal dentro del scrollable frame
        contenedor = tk.Frame(scrollable_frame, bg="#ecf0f1", padx=15, pady=15)
        contenedor.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(contenedor, text="➕ Agregar / Editar Participante", 
                font=('Arial', 11, 'bold'), bg="#ecf0f1").pack(anchor=tk.W, pady=(0, 10))
        
        # Frame para organizar formulario y botones en horizontal
        frame_horizontal = tk.Frame(contenedor, bg="#ecf0f1")
        frame_horizontal.pack(fill=tk.BOTH, expand=True)
        
        # Columna izquierda: Formulario
        frame_form = tk.Frame(frame_horizontal, bg="#ecf0f1")
        frame_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        # Campos del formulario en grid
        campos = [
            ("Cédula:", "entry_cedula"),
            ("Nombre:", "entry_nombre"),
            ("Apellido:", "entry_apellido"),
            ("Edad:", "entry_edad"),
            ("Distancia (ej: 5K, 10K):", "entry_distancia"),
            ("Género:", "entry_genero"),
            ("Contacto (Teléfono):", "entry_contacto"),
            ("Categoría:", "entry_categoria"),
            ("Dorsal:", "entry_dorsal")
        ]
        
        self.entries = {}
        for idx, (label, var_name) in enumerate(campos):
            tk.Label(frame_form, text=label, font=('Arial', 9), bg="#ecf0f1").grid(
                row=idx, column=0, sticky=tk.W, pady=3, padx=(0, 8))
            
            entry = tk.Entry(frame_form, font=('Arial', 9), width=30)
            entry.grid(row=idx, column=1, sticky=tk.EW, pady=3)
            self.entries[var_name] = entry
        
        # Estado de pago
        tk.Label(frame_form, text="Estado Pago:", font=('Arial', 9), bg="#ecf0f1").grid(
            row=len(campos), column=0, sticky=tk.W, pady=3, padx=(0, 8))
        
        self.combo_estado = ttk.Combobox(frame_form, values=["PAGADO", "PENDIENTE"],
                                        font=('Arial', 9), width=28, state='readonly')
        self.combo_estado.set("PENDIENTE")
        self.combo_estado.grid(row=len(campos), column=1, sticky=tk.EW, pady=3)
        
        frame_form.columnconfigure(1, weight=1)
        
        # Columna derecha: Botones de acción
        frame_botones = tk.Frame(frame_horizontal, bg="#ecf0f1")
        frame_botones.pack(side=tk.RIGHT, fill=tk.Y)
        
        botones = [
            ("➕ Agregar", self.agregar_participante, "#27ae60"),
            ("✏️ Editar Seleccionado", self.editar_participante_seleccionado, "#f39c12"),
            ("🗑️ Eliminar Seleccionado", self.eliminar_participante, "#e74c3c"),
            ("🧹 Limpiar Campos", self.limpiar_formulario, "#95a5a6"),
            ("� Importar CSV", self.importar_csv, "#3498db"),
            ("📤 Exportar CSV", self.exportar_csv, "#1abc9c")
        ]
        
        for texto, comando, color in botones:
            btn = tk.Button(frame_botones, text=texto, command=comando,
                           bg=color, fg="white", font=('Arial', 9, 'bold'),
                           width=22, pady=6, cursor="hand2",
                           activebackground=self.oscurecer_color(color),
                           relief=tk.FLAT, bd=0)
            btn.pack(pady=2, fill=tk.X)
        
        # Bind del mouse wheel para scroll SOLO en el área del formulario inferior
        def _on_mousewheel_canvas(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Vincular solo cuando el mouse está sobre el canvas o scrollable_frame
        canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel_canvas))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        scrollable_frame.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel_canvas))
        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        
        # ===== BARRA DE ESTADO =====
        self.frame_estado = tk.Frame(self.root, bg="#34495e", padx=10, pady=5)
        self.frame_estado.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.label_estado = tk.Label(self.frame_estado, text="", 
                                     font=('Arial', 9), bg="#34495e", fg="white", anchor=tk.W)
        self.label_estado.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.label_contador = tk.Label(self.frame_estado, text="", 
                                       font=('Arial', 9, 'bold'), bg="#34495e", fg="#ecf0f1")
        self.label_contador.pack(side=tk.RIGHT)
    
    def oscurecer_color(self, hex_color):
        """Oscurece un color hexadecimal para efecto hover"""
        rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        rgb_oscuro = [max(0, int(c * 0.8)) for c in rgb]
        return f"#{rgb_oscuro[0]:02x}{rgb_oscuro[1]:02x}{rgb_oscuro[2]:02x}"
    
    def actualizar_tabla(self, participantes=None):
        """Actualiza la tabla con los datos de participantes"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener participantes
        if participantes is None:
            participantes = self.gestor.obtener_todos()
        
        # Llenar tabla
        for p in participantes:
            valores = (
                p['cedula'],
                p['nombre'],
                p['apellido'],
                p.get('edad', ''),
                p.get('distancia', ''),
                p.get('genero', ''),
                p['contacto'],
                p.get('categoria', ''),
                p['numero_dorsal'] or "",
                p['estado_pago']
            )
            
            # Aplicar colores según estado de pago
            tags = ('pagado',) if p['estado_pago'] == 'PAGADO' else ('pendiente',)
            self.tree.insert('', tk.END, values=valores, tags=tags)
        
        # Configurar colores de filas
        self.tree.tag_configure('pagado', background='#d5f4e6')
        self.tree.tag_configure('pendiente', background='#fadbd8')
        
        self.actualizar_estadisticas()
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en la barra de estado"""
        stats = self.gestor.estadisticas()
        self.label_contador.config(
            text=f"📊 Total: {stats['total']} | ✅ Pagados: {stats['pagados']} | "
                 f"⏳ Pendientes: {stats['pendientes']} | 🏷️ Con Dorsal: {stats['con_dorsal']}"
        )
    
    def agregar_participante(self):
        """Agrega un nuevo participante"""
        # Validar campos obligatorios
        cedula = self.entries['entry_cedula'].get().strip()
        nombre = self.entries['entry_nombre'].get().strip()
        apellido = self.entries['entry_apellido'].get().strip()
        
        if not cedula or not nombre or not apellido:
            messagebox.showwarning("⚠️ Campos Incompletos", 
                                  "Cédula, Nombre y Apellido son obligatorios")
            return
        
        # Obtener valores
        edad = self.entries['entry_edad'].get().strip()
        distancia = self.entries['entry_distancia'].get().strip()
        genero = self.entries['entry_genero'].get().strip()
        contacto = self.entries['entry_contacto'].get().strip()
        categoria = self.entries['entry_categoria'].get().strip()
        numero_dorsal = self.entries['entry_dorsal'].get().strip()
        estado_pago = self.combo_estado.get()
        
        # Agregar al gestor
        exito, mensaje = self.gestor.agregar_participante(
            cedula, nombre, apellido, edad, distancia, genero, contacto, 
            categoria, numero_dorsal, estado_pago
        )
        
        if exito:
            messagebox.showinfo("✅ Éxito", mensaje)
            self.actualizar_tabla()
            self.limpiar_formulario()
            self.label_estado.config(text=mensaje)
        else:
            messagebox.showerror("❌ Error", mensaje)
            self.label_estado.config(text=mensaje)
    
    def al_seleccionar_participante(self, event=None):
        """Autocompleta los campos del formulario al seleccionar un participante de la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        # Obtener datos del participante seleccionado
        valores = self.tree.item(seleccion[0])['values']
        
        # Limpiar campos primero
        self.limpiar_formulario_sin_mensaje()
        
        # Autocompletar campos
        self.entries['entry_cedula'].config(state='normal')  # Habilitar temporalmente
        self.entries['entry_cedula'].delete(0, tk.END)
        self.entries['entry_cedula'].insert(0, valores[0])
        self.entries['entry_cedula'].config(state='readonly')  # No permitir cambiar cédula
        
        self.entries['entry_nombre'].delete(0, tk.END)
        self.entries['entry_nombre'].insert(0, valores[1])
        
        self.entries['entry_apellido'].delete(0, tk.END)
        self.entries['entry_apellido'].insert(0, valores[2])
        
        self.entries['entry_edad'].delete(0, tk.END)
        self.entries['entry_edad'].insert(0, valores[3])
        
        self.entries['entry_distancia'].delete(0, tk.END)
        self.entries['entry_distancia'].insert(0, valores[4])
        
        self.entries['entry_genero'].delete(0, tk.END)
        self.entries['entry_genero'].insert(0, valores[5])
        
        self.entries['entry_contacto'].delete(0, tk.END)
        self.entries['entry_contacto'].insert(0, valores[6])
        
        self.entries['entry_categoria'].delete(0, tk.END)
        self.entries['entry_categoria'].insert(0, valores[7])
        
        self.entries['entry_dorsal'].delete(0, tk.END)
        self.entries['entry_dorsal'].insert(0, valores[8])
        
        self.combo_estado.set(valores[9])
        
        # Actualizar barra de estado
        self.label_estado.config(text=f"📋 Participante seleccionado: {valores[1]} {valores[2]} - Modifica los campos y haz clic en '✏️ Editar Seleccionado'")
    
    def editar_participante_seleccionado(self, event=None):
        """Edita el participante seleccionado en la tabla"""
        # Verificar que haya campos llenos en el formulario
        cedula = self.entries['entry_cedula'].get().strip()
        nombre = self.entries['entry_nombre'].get().strip()
        apellido = self.entries['entry_apellido'].get().strip()
        
        if not cedula or not nombre or not apellido:
            messagebox.showwarning("⚠️ Sin Datos", 
                                  "Primero selecciona un participante de la tabla haciendo clic sobre él.\n"
                                  "Los campos se llenarán automáticamente y podrás modificarlos.")
            return
        
        # Confirmar la actualización
        respuesta = messagebox.askyesno("✏️ Confirmar Actualización",
                                       f"¿Desea guardar los cambios de:\n\n"
                                       f"{nombre} {apellido}\n"
                                       f"Cédula: {cedula}?")
        
        if respuesta:
            # Obtener nuevos valores del formulario
            campos_actualizar = {
                'nombre': nombre,
                'apellido': apellido,
                'edad': self.entries['entry_edad'].get().strip(),
                'distancia': self.entries['entry_distancia'].get().strip(),
                'genero': self.entries['entry_genero'].get().strip(),
                'contacto': self.entries['entry_contacto'].get().strip(),
                'categoria': self.entries['entry_categoria'].get().strip(),
                'numero_dorsal': self.entries['entry_dorsal'].get().strip(),
                'estado_pago': self.combo_estado.get()
            }
            
            # Actualizar en el gestor
            exito, mensaje = self.gestor.actualizar_participante(cedula, **campos_actualizar)
            
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.actualizar_tabla()
                self.limpiar_formulario()
                self.label_estado.config(text=mensaje)
            else:
                messagebox.showerror("❌ Error", mensaje)
                self.label_estado.config(text=mensaje)
    
    def eliminar_participante(self):
        """Elimina el participante seleccionado"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("⚠️ Sin Selección", "Seleccione un participante para eliminar")
            return
        
        valores = self.tree.item(seleccion[0])['values']
        cedula = valores[0]
        nombre_completo = f"{valores[1]} {valores[2]}"
        
        respuesta = messagebox.askyesno("⚠️ Confirmar Eliminación",
                                       f"¿Está seguro de eliminar a {nombre_completo}?\n"
                                       f"Esta acción no se puede deshacer.")
        
        if respuesta:
            exito, mensaje = self.gestor.eliminar_participante(cedula)
            if exito:
                messagebox.showinfo("✅ Éxito", mensaje)
                self.actualizar_tabla()
                self.label_estado.config(text=mensaje)
            else:
                messagebox.showerror("❌ Error", mensaje)
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        # Desbloquear todos los campos primero (especialmente la cédula)
        for entry in self.entries.values():
            if entry.cget('state') == 'readonly':
                entry.config(state='normal')
        
        # Limpiar todos los campos
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        
        self.combo_estado.set("PENDIENTE")
        self.label_estado.config(text="✨ Formulario limpiado - Listo para agregar nuevo participante")
    
    def limpiar_formulario_sin_mensaje(self):
        """Limpia todos los campos del formulario sin mostrar mensaje"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
            if entry.cget('state') == 'readonly':
                entry.config(state='normal')
        self.combo_estado.set("PENDIENTE")
    
    def recargar_tabla(self):
        """Recarga los datos de la tabla desde el archivo Excel"""
        try:
            self.actualizar_tabla()
            messagebox.showinfo("🔄 Tabla Recargada", 
                              "Los datos se han recargado correctamente desde la base de datos.")
            self.label_estado.config(text="🔄 Tabla recargada exitosamente")
        except Exception as e:
            messagebox.showerror("❌ Error al Recargar", 
                               f"No se pudieron recargar los datos:\n{str(e)}")
            self.label_estado.config(text=f"❌ Error al recargar: {str(e)}")
    
    def buscar_participante(self):
        """Busca un participante por cédula"""
        cedula = self.entry_busqueda.get().strip()
        if not cedula:
            messagebox.showwarning("⚠️ Campo Vacío", "Ingrese una cédula para buscar")
            return
        
        participante = self.gestor.buscar_por_cedula(cedula)
        if participante:
            self.actualizar_tabla([participante])
            self.label_estado.config(text=f"✅ Encontrado: {participante['nombre']} {participante['apellido']}")
        else:
            messagebox.showinfo("ℹ️ No Encontrado", f"No existe un participante con cédula {cedula}")
            self.label_estado.config(text=f"❌ No se encontró participante con cédula {cedula}")
    
    def buscar_tiempo_real(self, event):
        """Filtra la tabla en tiempo real mientras se escribe"""
        cedula_buscar = self.entry_busqueda.get().strip()
        if not cedula_buscar:
            self.actualizar_tabla()
            return
        
        todos = self.gestor.obtener_todos()
        filtrados = [p for p in todos if cedula_buscar in str(p['cedula'])]
        self.actualizar_tabla(filtrados)
    
    def importar_csv(self):
        """Importa participantes desde un archivo CSV"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            exito, mensaje, importados, errores = self.gestor.importar_csv(archivo)
            
            if exito:
                mensaje_completo = f"{mensaje}\n\n"
                if errores:
                    mensaje_completo += "Errores:\n" + "\n".join(errores[:10])
                    if len(errores) > 10:
                        mensaje_completo += f"\n... y {len(errores) - 10} errores más"
                
                messagebox.showinfo("📥 Importación Completada", mensaje_completo)
                self.actualizar_tabla()
                self.label_estado.config(text=mensaje)
            else:
                messagebox.showerror("❌ Error de Importación", mensaje)
    
    def exportar_csv(self):
        """Exporta participantes a un archivo CSV"""
        archivo = filedialog.asksaveasfilename(
            title="Guardar archivo CSV",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            exito, mensaje = self.gestor.exportar_csv(archivo)
            if exito:
                messagebox.showinfo("📤 Exportación Exitosa", mensaje)
                self.label_estado.config(text=mensaje)
            else:
                messagebox.showerror("❌ Error de Exportación", mensaje)
    
    def mostrar_estadisticas_detalladas(self):
        """Muestra una ventana con estadísticas detalladas"""
        stats = self.gestor.estadisticas()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("📊 Estadísticas Detalladas")
        ventana.geometry("400x300")
        ventana.configure(bg="#ecf0f1")
        
        tk.Label(ventana, text="📊 Estadísticas de Participantes",
                font=('Arial', 14, 'bold'), bg="#ecf0f1").pack(pady=15)
        
        frame_stats = tk.Frame(ventana, bg="#ecf0f1")
        frame_stats.pack(fill=tk.BOTH, expand=True, padx=20)
        
        estadisticas = [
            ("👥 Total de Participantes:", stats['total'], "#3498db"),
            ("✅ Pagados:", stats['pagados'], "#27ae60"),
            ("⏳ Pendientes:", stats['pendientes'], "#e74c3c"),
            ("🏷️ Con Dorsal Asignado:", stats['con_dorsal'], "#9b59b6"),
            ("❌ Sin Dorsal:", stats['sin_dorsal'], "#95a5a6")
        ]
        
        for idx, (label, valor, color) in enumerate(estadisticas):
            frame = tk.Frame(frame_stats, bg=color, padx=15, pady=10)
            frame.pack(fill=tk.X, pady=5)
            
            tk.Label(frame, text=label, font=('Arial', 11), bg=color, fg="white").pack(side=tk.LEFT)
            tk.Label(frame, text=str(valor), font=('Arial', 14, 'bold'), bg=color, fg="white").pack(side=tk.RIGHT)
        
        tk.Button(ventana, text="Cerrar", command=ventana.destroy,
                 bg="#34495e", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8).pack(pady=15)
    
    def volver_menu_principal(self):
        """Cierra la ventana de gestión de participantes y vuelve al menú principal"""
        respuesta = messagebox.askyesno("◀️ Volver al Menú Principal",
                                       "¿Desea volver al menú principal?\n\n"
                                       "Los cambios ya han sido guardados automáticamente.")
        if respuesta:
            self.root.destroy()
    
    def ordenar_por_columna(self, columna):
        """Ordena la tabla por la columna seleccionada"""
        # Esta funcionalidad se puede implementar más adelante
        pass


def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = InterfazParticipantes(root)
    
    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
