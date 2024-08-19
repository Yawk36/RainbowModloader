import os
import sys
import shutil
import zipfile
import json
from tkinter import Tk, filedialog, Button, Label, messagebox, ttk, Canvas, PhotoImage

# Nombre del archivo de configuración
CONFIG_FILE = "rainbow_modloader_config.json"

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, funciona para desarrollo y compilación."""
    try:
        # PyInstaller crea una carpeta temporal y almacena el path en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Obtener la ruta del juego desde el archivo de configuración o solicitarla al usuario
def get_game_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            return config.get("game_path")
    else:
        game_path = filedialog.askdirectory(title="Select the root folder of the game")
        if game_path:
            with open(CONFIG_FILE, 'w') as file:
                json.dump({"game_path": game_path}, file)
            return game_path
        else:
            display_message("Error", "You must select a game path.")
            return None

# Actualizar la barra de progreso y el texto de estado
def update_progress(progress, status_text, value):
    status_label.config(text=status_text)
    progress['value'] = value
    progress.update()

# Mostrar mensajes en la interfaz
def display_message(title, message):
    status_label.config(text=f"{title}: {message}")

# Crear la carpeta de backup si no existe ya un backup previo
def create_backup(game_path, progress, status_label):
    backup_folder = os.path.join(game_path, 'backup')
    worlds_path = os.path.join(game_path, 'data/worlds/SMATRS Demo 2')

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    backup_path = os.path.join(backup_folder, 'SMATRS_Demo_2_Backup')
    if not os.path.exists(backup_path):
        # Copiar archivos uno por uno para actualizar la barra de progreso
        total_files = sum([len(files) for r, d, files in os.walk(worlds_path)])
        copied_files = 0

        os.makedirs(backup_path)
        
        for root, dirs, files in os.walk(worlds_path):
            rel_path = os.path.relpath(root, worlds_path)
            dest_dir = os.path.join(backup_path, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                progress_value = (copied_files / total_files) * 100
                update_progress(progress, "Creating Backup...", progress_value)

        display_message("Backup", "Backup created successfully.")
    else:
        display_message("Backup", "Backup already exists. No new backup was created.")

# Aplicar un mod
def apply_mod(game_path, progress, status_label, buttons):
    file_path = filedialog.askopenfilename(filetypes=[("RSM Files", "*.rsm")])
    if file_path:
        try:
            # Desactivar botones durante la tarea
            for button in buttons:
                button.config(state="disabled")
            
            # Crear el backup si aún no se ha creado
            create_backup(game_path, progress, status_label)
            
            # Extraer el archivo .rsm (que es un .zip) en la carpeta raíz del juego
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(game_path)
            update_progress(progress, "Installing Mod...", 100)
            
            # Obtener el nombre del archivo sin la ruta completa
            mod_name = os.path.basename(file_path)
            display_message("Mod", f"{mod_name} applied successfully.")
        except Exception as e:
            display_message("Error", f"An error occurred while applying the mod: {e}")
        finally:
            # Reactivar botones y actualizar el estado
            for button in buttons:
                button.config(state="normal")

# Restaurar el backup y quitar mods
def restore_backup(game_path, progress, status_label, buttons):
    backup_path = os.path.join(game_path, 'backup/SMATRS_Demo_2_Backup')
    worlds_path = os.path.join(game_path, 'data/worlds/SMATRS Demo 2')

    if os.path.exists(backup_path):
        # Eliminar la carpeta original
        if os.path.exists(worlds_path):
            shutil.rmtree(worlds_path)

        total_files = sum([len(files) for r, d, files in os.walk(backup_path)])
        copied_files = 0

        os.makedirs(worlds_path)

        for root, dirs, files in os.walk(backup_path):
            rel_path = os.path.relpath(root, backup_path)
            dest_dir = os.path.join(worlds_path, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                progress_value = (copied_files / total_files) * 100
                update_progress(progress, "Restoring Backup...", progress_value)

        display_message("Restored", "SMATRS mods have been removed.")
    else:
        display_message("Error", "Backup not found.")
    # Reactivar botones al final de la tarea
    for button in buttons:
        button.config(state="normal")

# GUI
def create_gui():
    global status_label

    root = Tk()
    root.title("Rainbow Modloader")
    root.geometry("800x600")
    root.resizable(False, False)  # Evitar maximizar la ventana

    # Crear un canvas para la imagen de fondo
    canvas = Canvas(root, width=800, height=600)
    canvas.pack(fill="both", expand=True)
    
    # Cargar la imagen de fondo
    background_image = PhotoImage(file=resource_path("background.png"))
    canvas.create_image(0, 0, anchor="nw", image=background_image)

    # Obtener la ruta del juego
    game_path = get_game_path()
    if not game_path:
        root.destroy()
        return

    # Barra de progreso
    progress = ttk.Progressbar(root, orient="horizontal", length=390, mode="determinate")
    progress_window = canvas.create_window(10, 580, anchor="sw", window=progress)

    # Etiqueta de estado
    status_label = Label(root, text="Welcome to Rainbow Modloader", font=("Arial", 14))
    status_window = canvas.create_window(10, 540, anchor="sw", window=status_label)

    # Botones
    apply_mod_button = Button(root, text="Apply Mod", font=("Arial", 14), command=lambda: apply_mod(game_path, progress, status_label, [apply_mod_button, restore_backup_button]), width=15, height=2)
    apply_mod_button_window = canvas.create_window(595, 590, anchor="se", window=apply_mod_button)
    
    restore_backup_button = Button(root, text="Remove Mods", font=("Arial", 14), command=lambda: restore_backup(game_path, progress, status_label, [apply_mod_button, restore_backup_button]), width=15, height=2)
    restore_backup_button_window = canvas.create_window(785, 590, anchor="se", window=restore_backup_button)

    # Run the interface
    root.mainloop()

if __name__ == "__main__":
    create_gui()