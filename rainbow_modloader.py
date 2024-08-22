import os
import sys
import shutil
import zipfile
import json
from tkinter import Tk, filedialog, Button, Label, ttk, Canvas, PhotoImage

# Nombre del archivo de configuración
CONFIG_FILE = "rainbow_modloader_config.json"

def resource_path(relative_path):
    """Obtiene la ruta absoluta del recurso, funciona para desarrollo y compilación."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_game_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            return config.get("game_path")
    else:
        return select_new_game_path()

def select_new_game_path():
    game_path = filedialog.askdirectory(title="Select the root folder of the game")
    if game_path:
        with open(CONFIG_FILE, 'w') as file:
            json.dump({"game_path": game_path}, file)
        return game_path
    else:
        display_message("Error", "You must select a game path.")
        return None

def update_progress(progress, status_text, value):
    status_label.config(text=status_text)
    progress['value'] = value
    progress.update()

def display_message(title, message):
    status_label.config(text=f"{title}: {message}")

def create_backup(game_path, progress, status_label):
    backup_folder = os.path.join(game_path, 'backup')
    worlds_path = os.path.join(game_path, 'data/worlds/SMATRS Demo 2')

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    backup_path = os.path.join(backup_folder, 'SMATRS_Demo_2_Backup')
    if not os.path.exists(backup_path):
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

def apply_mod(game_path, progress, status_label, buttons, file_path=None):
    if not file_path:
        file_path = filedialog.askopenfilename(filetypes=[("RSM Files", "*.rsm")])
    
    if file_path:
        try:
            for button in buttons:
                button.config(state="disabled")
            
            create_backup(game_path, progress, status_label)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(game_path)
            update_progress(progress, "Installing Mod...", 100)
            
            mod_name = os.path.basename(file_path)
            display_message("Mod", f"{mod_name} applied successfully.")
        except Exception as e:
            display_message("Error", f"An error occurred while applying the mod: {e}")
        finally:
            for button in buttons:
                button.config(state="normal")

def apply_modpack(game_path, progress, status_label, buttons):
    modpack_path = filedialog.askopenfilename(filetypes=[("RSMP Files", "*.rsmp")])

    if modpack_path:
        try:
            for button in buttons:
                button.config(state="disabled")
            
            create_backup(game_path, progress, status_label)

            with zipfile.ZipFile(modpack_path, 'r') as modpack_zip:
                mod_files = [name for name in modpack_zip.namelist() if name.endswith('.rsm')]

                total_mods = len(mod_files)
                for i, mod_file in enumerate(mod_files):
                    with modpack_zip.open(mod_file) as mod_zip_file:
                        with zipfile.ZipFile(mod_zip_file) as mod_zip:
                            mod_zip.extractall(game_path)

                    progress_value = ((i + 1) / total_mods) * 100
                    update_progress(progress, f"Installing Mod {i + 1}/{total_mods}...", progress_value)
            
            display_message("Modpack", "Modpack applied successfully.")
        except Exception as e:
            display_message("Error", f"An error occurred while applying the modpack: {e}")
        finally:
            for button in buttons:
                button.config(state="normal")

def restore_backup(game_path, progress, status_label, buttons):
    backup_path = os.path.join(game_path, 'backup/SMATRS_Demo_2_Backup')
    worlds_path = os.path.join(game_path, 'data/worlds/SMATRS Demo 2')

    if os.path.exists(backup_path):
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
    for button in buttons:
        button.config(state="normal")

def create_mod(progress, status_label):
    folder_path = filedialog.askdirectory(title="Select the 'data' folder to create a mod")

    if folder_path and os.path.basename(folder_path) == 'data':
        save_path = filedialog.asksaveasfilename(defaultextension=".rsm", filetypes=[("RSM Files", "*.rsm")], title="Save the mod as")
        if save_path:
            with zipfile.ZipFile(save_path, 'w') as mod_zip:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                        mod_zip.write(file_path, arcname)
            display_message("Create Mod", "Mod created successfully.")
        else:
            display_message("Create Mod", "Mod creation canceled.")
    else:
        display_message("Error", "The selected folder must be named 'data'.")

def create_modpack(progress, status_label):
    file_paths = filedialog.askopenfilenames(filetypes=[("RSM Files", "*.rsm")], title="Select multiple mods to create a modpack")
    
    if file_paths and len(file_paths) > 1:
        save_path = filedialog.asksaveasfilename(defaultextension=".rsmp", filetypes=[("RSMP Files", "*.rsmp")], title="Save the modpack as")
        if save_path:
            with zipfile.ZipFile(save_path, 'w') as modpack_zip:
                for mod_path in file_paths:
                    modpack_zip.write(mod_path, os.path.basename(mod_path))
            display_message("Create Modpack", "Modpack created successfully.")
        else:
            display_message("Create Modpack", "Modpack creation canceled.")
    else:
        display_message("Error", "You must select at least two mods to create a modpack.")

def create_gui(file_path=None):
    global status_label

    root = Tk()
    root.title("Rainbow Modloader")
    root.geometry("800x600")
    root.resizable(False, False)

    canvas = Canvas(root, width=800, height=600)
    canvas.pack(fill="both", expand=True)
    
    background_image = PhotoImage(file=resource_path("background.png"))
    canvas.create_image(0, 0, anchor="nw", image=background_image)

    game_path = get_game_path()
    if not game_path:
        root.destroy()
        return

    progress = ttk.Progressbar(root, orient="horizontal", length=390, mode="determinate")
    progress_window = canvas.create_window(10, 580, anchor="sw", window=progress)

    status_label = Label(root, text="Welcome to Rainbow Modloader", font=("Arial", 14))
    status_window = canvas.create_window(10, 540, anchor="sw", window=status_label)

    apply_mod_button = Button(root, text="Apply Mod", font=("Arial", 10), command=lambda: apply_mod(game_path, progress, status_label, [apply_mod_button, restore_backup_button]), width=15, height=1)
    apply_mod_button_window = canvas.create_window(535, 565, anchor="se", window=apply_mod_button)

    import_modpack_button = Button(root, text="Apply Modpack", font=("Arial", 10), command=lambda: apply_modpack(game_path, progress, status_label, [apply_mod_button, restore_backup_button, import_modpack_button]), width=15, height=1)
    import_modpack_button_window = canvas.create_window(535, 595, anchor="se", window=import_modpack_button)

    create_mod_button = Button(root, text="Create Mod", font=("Arial", 10), command=lambda: create_mod(progress, status_label), width=15, height=1)
    create_mod_button_window = canvas.create_window(665, 565, anchor="se", window=create_mod_button)

    create_modpack_button = Button(root, text="Create Modpack", font=("Arial", 10), command=lambda: create_modpack(progress, status_label), width=15, height=1)
    create_modpack_button_window = canvas.create_window(665, 595, anchor="se", window=create_modpack_button)

    change_path_button = Button(root, text="Change Game Path", font=("Arial", 10), command=lambda: change_game_path(progress, status_label), width=15, height=1)
    change_path_button_window = canvas.create_window(795, 565, anchor="se", window=change_path_button)
    
    restore_backup_button = Button(root, text="Remove Mods", font=("Arial", 10), command=lambda: restore_backup(game_path, progress, status_label, [apply_mod_button, restore_backup_button]), width=15, height=1)
    restore_backup_button_window = canvas.create_window(795, 595, anchor="se", window=restore_backup_button)

    # Si se ha pasado un archivo .rsm, aplicarlo automáticamente
    if file_path and file_path.endswith(".rsm"):
        apply_mod(game_path, progress, status_label, [apply_mod_button, restore_backup_button], file_path)

    root.mainloop()

def change_game_path(progress, status_label):
    """Permite al usuario seleccionar una nueva ruta para el juego y actualiza el archivo de configuración."""
    new_game_path = select_new_game_path()
    if new_game_path:
        display_message("Game Path", "Game path changed successfully.")
    else:
        display_message("Error", "Game path change was cancelled.")

if __name__ == "__main__":
    mod_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    create_gui(mod_file_path)
