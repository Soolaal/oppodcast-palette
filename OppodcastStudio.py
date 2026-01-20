import customtkinter as ctk
import pygame
import os
import json
import time
from datetime import datetime
from tkinter import filedialog, Menu

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_DIR = "presets"
NOTES_FILE = "notes.txt"

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "fr": {
        "commands": "COMMANDES",
        "library": "MÉDIATHÈQUE",
        "imported_files": "Fichiers importés",
        "import_btn": "Importer...",
        "mode_live": "MODE LIVE",
        "mode_edit": "MODE ÉDITION",
        "edit_switch": "Mode Édition",
        "always_top": "Toujours visible",
        "tab_jingles": "Jingle Palette",
        "tab_notes": "Notes / Conducteur",
        "btn_start": "START",
        "btn_pause": "PAUSE",
        "btn_stop": "STOP",
        "btn_resume": "REPRENDRE",
        "btn_reset": "RESET",
        "status_live": "Prêt (Live)",
        "status_edit": "Sélectionnez ou déplacez",
        "warn_edit": "Activez le Mode Édition !",
        "new_preset": "Nouvelle Palette",
        "name_prompt": "Nom :"
    },
    "en": {
        "commands": "CONTROLS",
        "library": "LIBRARY",
        "imported_files": "Imported Files",
        "import_btn": "Import...",
        "mode_live": "LIVE MODE",
        "mode_edit": "EDIT MODE",
        "edit_switch": "Edit Mode",
        "always_top": "Always on Top",
        "tab_jingles": "Soundboard",
        "tab_notes": "Notes / Script",
        "btn_start": "START",
        "btn_pause": "PAUSE",
        "btn_stop": "STOP",
        "btn_resume": "RESUME",
        "btn_reset": "RESET",
        "status_live": "Ready (Live)",
        "status_edit": "Select or Move items",
        "warn_edit": "Enable Edit Mode first!",
        "new_preset": "New Palette",
        "name_prompt": "Name:"
    }
}

class LibraryItem(ctk.CTkFrame):
    """
    Represents a single audio file in the library list (Sidebar).
    """
    def __init__(self, master, filepath, parent_app, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=6, **kwargs)
        self.filepath = filepath
        self.parent_app = parent_app
        self.grid_columnconfigure(0, weight=1)

        # File Name Label
        self.lbl_name = ctk.CTkLabel(self, text=os.path.basename(filepath), anchor="w", cursor="hand2")
        self.lbl_name.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.lbl_name.bind("<Button-1>", self.on_select)

        # Delete Button (x)
        self.btn_del = ctk.CTkButton(
            self, text="×", width=25, height=25, 
            fg_color="transparent", hover_color="#550000", 
            text_color="#FF4444", command=self.on_delete
        )
        self.btn_del.grid(row=0, column=1, padx=2, pady=2)
        
        # Bind click on frame background as well
        self.bind("<Button-1>", self.on_select)

    def on_select(self, event=None):
        self.parent_app.select_library_item(self.filepath, self)

    def on_delete(self):
        self.parent_app.remove_from_library(self.filepath)

    def set_selected(self, is_selected):
        if is_selected:
            self.configure(fg_color="#1f538d")
            self.lbl_name.configure(text_color="white", font=("Arial", 12, "bold"))
        else:
            self.configure(fg_color="transparent")
            self.lbl_name.configure(text_color="gray90", font=("Arial", 12))


class SoundButton(ctk.CTkFrame):
    """
    Represents a slot in the grid. Can hold a sound, play it, or be moved.
    """
    def __init__(self, master, slot_id, parent_app, **kwargs):
        super().__init__(master, corner_radius=8, border_width=2, border_color="#333", **kwargs)
        self.slot_id = slot_id
        self.parent_app = parent_app
        self.file_path = None
        self.sound = None
        self.channel = None
        self.duration = 0 
        
        # Visual States
        self.col_empty = "#1c1c1c"
        self.col_loaded = "#1f538d"
        self.col_playing = "#2CC985"
        
        self.configure(fg_color=self.col_empty)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main Label acts as the button area
        self.label = ctk.CTkLabel(self, text=slot_id, font=("Arial", 12, "bold"))
        self.label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.label.bind("<Button-1>", self.on_click)
        
        # Remove Button (only visible in edit mode)
        self.btn_remove = ctk.CTkButton(
            self, text="×", width=20, height=20, 
            fg_color="#CC3333", text_color="white", 
            command=self.clear_slot
        )

    def load_sound(self, path):
        if not os.path.exists(path): return
        try:
            self.file_path = path
            self.sound = pygame.mixer.Sound(path)
            self.duration = self.sound.get_length()
            self.sound.set_volume(self.parent_app.global_volume)
            
            # Format display name
            name = os.path.splitext(os.path.basename(path))[0]
            display = name[:12] + ".." if len(name) > 12 else name
            
            self.label.configure(text=f"{self.slot_id}\n{display}")
            self.configure(fg_color=self.col_loaded)
            
            self.parent_app.save_current_preset()
            self.update_edit_visuals()
        except Exception as e:
            print(f"Error loading sound: {e}")

    def clear_slot(self):
        if self.channel: 
            self.channel.stop()
        self.file_path = None
        self.sound = None
        self.duration = 0
        self.label.configure(text=f"{self.slot_id}")
        self.configure(fg_color=self.col_empty, border_color="#333")
        self.btn_remove.place_forget()
        self.parent_app.save_current_preset()

    def update_edit_visuals(self):
        """Show/Hide delete button based on Edit Mode."""
        if self.parent_app.is_edit_mode and self.file_path:
            self.btn_remove.place(relx=0.85, rely=0.15, anchor="center")
            self.configure(border_color="#555")
        else:
            self.btn_remove.place_forget()
            self.configure(border_color="#333")

    def on_click(self, event=None):
        # --- EDIT MODE LOGIC ---
        if self.parent_app.is_edit_mode:
            # 1. Assign from Library
            if self.parent_app.selected_library_path:
                self.load_sound(self.parent_app.selected_library_path)
                self.parent_app.deselect_library()
                return
            
            # 2. Move / Swap
            if self.parent_app.move_source_btn:
                source = self.parent_app.move_source_btn
                if source == self:
                    # Cancel move
                    source.configure(border_color="#555")
                    self.parent_app.move_source_btn = None
                else:
                    # Execute Swap
                    path_source = source.file_path
                    path_target = self.file_path
                    source.clear_slot()
                    self.clear_slot()
                    if path_target: source.load_sound(path_target)
                    if path_source: self.load_sound(path_source)
                    self.parent_app.move_source_btn = None
            else:
                # Select as Source
                if self.file_path:
                    self.parent_app.move_source_btn = self
                    self.configure(border_color="#E0A500")
            return

        # --- LIVE MODE LOGIC ---
        if not self.sound: return

        if self.channel and self.channel.get_busy():
            self.channel.stop()
            self.configure(fg_color=self.col_loaded)
            if self.parent_app.current_playing_btn == self:
                self.parent_app.current_playing_btn = None
        else:
            self.channel = pygame.mixer.find_channel()
            if self.channel:
                self.channel.play(self.sound)
                self.configure(fg_color=self.col_playing)
                
                # Update Global Player Bar
                self.parent_app.current_playing_btn = self
                self.parent_app.current_start_time = time.time()
                
                self.after(100, self.check_playback)

    def check_playback(self):
        if self.channel and self.channel.get_busy():
            self.after(100, self.check_playback)
        else:
            if self.file_path: 
                self.configure(fg_color=self.col_loaded)
            if self.parent_app.current_playing_btn == self:
                self.parent_app.current_playing_btn = None


class OppodcastDesktop(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- Audio Engine ---
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(32)
        
        # --- State Variables ---
        self.lang = "fr"  # Default Language
        self.global_volume = 0.8
        self.selected_library_path = None
        self.library_widgets = []
        self.is_edit_mode = False
        self.move_source_btn = None
        self.is_loading_preset = False
        self.current_playing_btn = None
        self.current_start_time = 0
        
        # Chrono State
        self.chrono_start_time = 0
        self.chrono_running = False
        self.chrono_elapsed = 0
        
        # --- Window Setup ---
        self.title("Oppodcast Studio V5.2")
        self.geometry("1200x850")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- UI Construction ---
        self.create_sidebar()
        self.create_main_area()
        
        # --- Initialization ---
        self.library_files = []
        self.refresh_presets_list()
        self.load_preset("Default")
        
        # Start Loops
        self.update_clock()
        self.update_player_bar()

    def t(self, key):
        """Helper for translation."""
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        # 1. Monitor (Top)
        self.frm_monitor = ctk.CTkFrame(self.sidebar, fg_color="#111")
        self.frm_monitor.grid(row=0, column=0, sticky="ew")
        
        self.lbl_clock = ctk.CTkLabel(self.frm_monitor, text="00:00:00", font=("Consolas", 24, "bold"), text_color="#2CC985")
        self.lbl_clock.pack(pady=(15, 5))
        
        self.lbl_chrono = ctk.CTkLabel(self.frm_monitor, text="00:00", font=("Consolas", 40, "bold"), text_color="white")
        self.lbl_chrono.pack(pady=5)
        
        frm_chrono_ctrl = ctk.CTkFrame(self.frm_monitor, fg_color="transparent")
        frm_chrono_ctrl.pack(pady=(0, 15))
        self.btn_chrono_start = ctk.CTkButton(frm_chrono_ctrl, text="START", width=70, height=25, fg_color="#2CC985", command=self.toggle_chrono)
        self.btn_chrono_start.pack(side="left", padx=5)
        self.btn_chrono_reset = ctk.CTkButton(frm_chrono_ctrl, text="RESET", width=70, height=25, fg_color="#444", command=self.reset_chrono)
        self.btn_chrono_reset.pack(side="left", padx=5)

        # 2. Controls
        self.lbl_commands = ctk.CTkLabel(self.sidebar, text=self.t("commands"), font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_commands.grid(row=1, column=0, pady=(15,5))
        
        frm_ctrl = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frm_ctrl.grid(row=2, column=0, sticky="ew", padx=10)
        self.btn_pause = ctk.CTkButton(frm_ctrl, text=self.t("btn_pause"), fg_color="#E0A500", width=120, command=self.pause_all)
        self.btn_pause.pack(side="left", padx=2)
        self.btn_stop = ctk.CTkButton(frm_ctrl, text=self.t("btn_stop"), fg_color="#CC3333", width=120, command=self.stop_all)
        self.btn_stop.pack(side="right", padx=2)

        # 3. Player Bar
        self.frm_player_bar = ctk.CTkFrame(self.sidebar, fg_color="#222")
        self.frm_player_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.lbl_track_name = ctk.CTkLabel(self.frm_player_bar, text="--", font=("Arial", 11, "bold"), text_color="white")
        self.lbl_track_name.pack(pady=(5,0))
        self.progress_bar = ctk.CTkProgressBar(self.frm_player_bar, width=220, height=8, progress_color="#2CC985")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.lbl_track_time = ctk.CTkLabel(self.frm_player_bar, text="00:00 / 00:00", font=("Consolas", 11), text_color="gray")
        self.lbl_track_time.pack(pady=(0,5))

        # 4. Volume & TopMost
        self.slider = ctk.CTkSlider(self.sidebar, from_=0, to=1, command=self.set_volume)
        self.slider.set(0.8)
        self.slider.grid(row=4, column=0, pady=5, sticky="ew", padx=20)
        
        self.switch_top = ctk.CTkSwitch(self.sidebar, text=self.t("always_top"), command=self.toggle_topmost)
        self.switch_top.grid(row=5, column=0, pady=5)
        
        # 5. Language Switch
        self.btn_lang = ctk.CTkButton(self.sidebar, text="Language: FR", width=100, fg_color="#333", command=self.toggle_language)
        self.btn_lang.grid(row=6, column=0, pady=5)

        # 6. Library
        self.lbl_lib = ctk.CTkLabel(self.sidebar, text=self.t("library"), font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_lib.grid(row=7, column=0, pady=(20, 5))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.sidebar, label_text=self.t("imported_files"))
        self.scroll_frame.grid(row=8, column=0, sticky="nsew", padx=10, pady=5)
        
        self.btn_import = ctk.CTkButton(self.sidebar, text=self.t("import_btn"), command=self.import_mass)
        self.btn_import.grid(row=9, column=0, pady=10, padx=20, sticky="ew")

        # 7. Status Label (Bottom)
        self.lbl_status = ctk.CTkLabel(self.sidebar, text=self.t("status_live"), text_color="gray", height=30)
        self.lbl_status.grid(row=10, column=0, sticky="ew", pady=5)


    def create_main_area(self):
        # Main Tab View
        self.main_tabview = ctk.CTkTabview(self)
        self.main_tabview.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        self.tab_jingles = self.main_tabview.add(self.t("tab_jingles"))
        self.tab_notes = self.main_tabview.add(self.t("tab_notes"))

        # --- Jingle Palette Tab ---
        # Top Controls (Preset & Mode)
        frm_top = ctk.CTkFrame(self.tab_jingles, fg_color="transparent")
        frm_top.pack(fill="x", pady=(0, 10))
        
        self.palette_selector = ctk.CTkOptionMenu(frm_top, values=["Default"], command=self.change_preset)
        self.palette_selector.pack(side="left", padx=5)
        
        ctk.CTkButton(frm_top, text="+", width=30, command=self.create_preset).pack(side="left")
        ctk.CTkButton(frm_top, text="Del", width=30, fg_color="#550000", command=self.delete_preset).pack(side="left", padx=5)
        
        self.switch_edit = ctk.CTkSwitch(frm_top, text=self.t("edit_switch"), command=self.toggle_edit_mode)
        self.switch_edit.pack(side="right", padx=10)

        # Grid Container
        self.grid_frame = ctk.CTkFrame(self.tab_jingles)
        self.grid_frame.pack(expand=True, fill="both")
        self.buttons_map = {}
        self.create_grid()

        # --- Notes Tab ---
        self.txt_notes = ctk.CTkTextbox(self.tab_notes, font=("Arial", 14))
        self.txt_notes.pack(expand=True, fill="both", padx=5, pady=5)
        
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as f: 
                self.txt_notes.insert("0.0", f.read())
                
        self.txt_notes.bind("<KeyRelease>", self.save_notes)

    def toggle_language(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        self.btn_lang.configure(text=f"Language: {self.lang.upper()}")
        self.update_ui_text()

    def update_ui_text(self):
        """Refreshes all labels and buttons with current language."""
        self.lbl_commands.configure(text=self.t("commands"))
        self.lbl_lib.configure(text=self.t("library"))
        self.scroll_frame.configure(label_text=self.t("imported_files"))
        self.btn_import.configure(text=self.t("import_btn"))
        self.btn_pause.configure(text=self.t("btn_pause"))
        self.btn_stop.configure(text=self.t("btn_stop"))
        self.btn_chrono_start.configure(text=self.t("btn_start") if not self.chrono_running else self.t("btn_pause"))
        self.btn_chrono_reset.configure(text=self.t("btn_reset"))
        self.switch_top.configure(text=self.t("always_top"))
        self.switch_edit.configure(text=self.t("edit_switch"))
        
        # Note: Updating Tab names in CTk is tricky, usually requires recreation. 
        # We will skip tab rename to avoid complexity, but new windows would use new lang.

        if self.is_edit_mode:
             self.lbl_status.configure(text=self.t("status_edit"))
        else:
             self.lbl_status.configure(text=self.t("status_live"))

    # --- CHRONO & CLOCK LOGIC ---
    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_clock.configure(text=now)
        if self.chrono_running:
            diff = time.time() - self.chrono_start_time + self.chrono_elapsed
            mins = int(diff // 60)
            secs = int(diff % 60)
            self.lbl_chrono.configure(text=f"{mins:02}:{secs:02}")
        self.after(1000, self.update_clock)

    def toggle_chrono(self):
        if self.chrono_running:
            self.chrono_elapsed += time.time() - self.chrono_start_time
            self.chrono_running = False
            self.btn_chrono_start.configure(text=self.t("btn_resume"), fg_color="#2CC985")
        else:
            self.chrono_start_time = time.time()
            self.chrono_running = True
            self.btn_chrono_start.configure(text=self.t("btn_pause"), fg_color="#E0A500")

    def reset_chrono(self):
        self.chrono_running = False
        self.chrono_elapsed = 0
        self.lbl_chrono.configure(text="00:00")
        self.btn_chrono_start.configure(text=self.t("btn_start"), fg_color="#2CC985")

    def toggle_topmost(self):
        self.attributes('-topmost', self.switch_top.get())

    # --- PLAYER BAR LOGIC ---
    def update_player_bar(self):
        if self.current_playing_btn and self.current_playing_btn.sound:
            elapsed = time.time() - self.current_start_time
            total = self.current_playing_btn.duration
            
            if total > 0:
                percent = min(elapsed / total, 1.0)
                self.progress_bar.set(percent)
                
                el_min, el_sec = divmod(int(elapsed), 60)
                to_min, to_sec = divmod(int(total), 60)
                rem_min, rem_sec = divmod(int(total - elapsed), 60)
                
                name = os.path.basename(self.current_playing_btn.file_path)
                display_name = name[:20]+".." if len(name)>20 else name
                
                self.lbl_track_name.configure(text=display_name)
                self.lbl_track_time.configure(text=f"{el_min:02}:{el_sec:02} / {to_min:02}:{to_sec:02} (-{rem_min:02}:{rem_sec:02})")
        else:
            self.progress_bar.set(0)
            self.lbl_track_name.configure(text="--")
            self.lbl_track_time.configure(text="00:00 / 00:00")
            
        self.after(100, self.update_player_bar)

    # --- MAIN FEATURES ---
    def toggle_edit_mode(self):
        self.is_edit_mode = self.switch_edit.get()
        self.move_source_btn = None
        if self.is_edit_mode:
            self.grid_frame.configure(border_width=2, border_color="#E0A500")
            self.lbl_status.configure(text=self.t("status_edit"), text_color="#E0A500")
        else:
            self.grid_frame.configure(border_width=0)
            self.deselect_library()
            self.lbl_status.configure(text=self.t("status_live"), text_color="#2CC985")
            
        for btn in self.buttons_map.values(): 
            btn.update_edit_visuals()

    def import_mass(self):
        if not self.is_edit_mode:
            # Temporary Toast Feedback
            tmp = ctk.CTkLabel(self, text=self.t("warn_edit"), text_color="#FF4444", font=("Arial", 16, "bold"))
            tmp.place(relx=0.5, rely=0.5, anchor="center")
            self.after(1500, tmp.destroy)
            return
            
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if files:
            for f in files:
                if f not in self.library_files: 
                    self.library_files.append(f)
            self.refresh_library_ui()

    def remove_from_library(self, path):
        if not self.is_edit_mode: return
        if path in self.library_files:
            self.library_files.remove(path)
            if self.selected_library_path == path: 
                self.deselect_library()
            self.refresh_library_ui()

    def refresh_library_ui(self):
        for widget in self.scroll_frame.winfo_children(): 
            widget.destroy()
        
        self.library_widgets = []
        for path in self.library_files:
            item = LibraryItem(self.scroll_frame, path, self)
            item.pack(fill="x", pady=2, padx=2)
            self.library_widgets.append(item)
            if not self.is_edit_mode: 
                item.btn_del.configure(state="disabled")

    def select_library_item(self, path, widget_ref):
        if not self.is_edit_mode: return
        self.selected_library_path = path
        for w in self.library_widgets: 
            w.set_selected(w == widget_ref)

    def deselect_library(self):
        self.selected_library_path = None
        for w in self.library_widgets: 
            w.set_selected(False)

    def create_grid(self):
        rows, cols = ["A", "B", "C", "D", "E"], 6
        for i in range(5): self.grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(cols): self.grid_frame.grid_columnconfigure(i, weight=1)
        
        for r, row_char in enumerate(rows):
            for c in range(cols):
                slot_id = f"{row_char}{c+1}"
                btn = SoundButton(self.grid_frame, slot_id, self)
                btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                self.buttons_map[slot_id] = btn

    def set_volume(self, val):
        self.global_volume = float(val)
        for btn in self.buttons_map.values():
            if btn.sound: 
                btn.sound.set_volume(self.global_volume)

    def stop_all(self):
        pygame.mixer.stop()
        self.current_playing_btn = None
        for btn in self.buttons_map.values():
            if btn.file_path: 
                btn.configure(fg_color=btn.col_loaded)

    def pause_all(self):
        if pygame.mixer.get_busy():
            pygame.mixer.pause()
            self.btn_pause.configure(text=self.t("btn_resume"))
        else:
            pygame.mixer.unpause()
            self.btn_pause.configure(text=self.t("btn_pause"))

    def save_notes(self, event=None):
        with open(NOTES_FILE, "w", encoding="utf-8") as f: 
            f.write(self.txt_notes.get("0.0", "end"))

    # --- PRESET MANAGEMENT (ROBUST) ---
    def refresh_presets_list(self):
        presets = [f.replace(".json", "") for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
        if not presets: presets = ["Default"]
        self.palette_selector.configure(values=presets)

    def load_preset(self, name):
        self.is_loading_preset = True
        self.current_preset_name = name
        path = os.path.join(CONFIG_DIR, f"{name}.json")
        
        # Clear grid first
        for btn in self.buttons_map.values(): 
            btn.clear_slot()
        
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        for slot, filepath in data.items():
                            if slot in self.buttons_map: 
                                self.buttons_map[slot].load_sound(filepath)
            except json.JSONDecodeError:
                print(f"Warning: Preset '{name}' is corrupted or empty. Loading empty grid.")
            except Exception as e:
                print(f"Read error: {e}")

        self.palette_selector.set(name)
        for btn in self.buttons_map.values(): 
            btn.update_edit_visuals()
        
        self.is_loading_preset = False

    def save_current_preset(self):
        if self.is_loading_preset: return
        if not hasattr(self, 'current_preset_name'): return
        
        data = {s: b.file_path for s, b in self.buttons_map.items() if b.file_path}
        path = os.path.join(CONFIG_DIR, f"{self.current_preset_name}.json")
        
        with open(path, "w") as f: 
            json.dump(data, f, indent=4)

    def create_preset(self):
        dialog = ctk.CTkInputDialog(text=self.t("name_prompt"), title=self.t("new_preset"))
        name = dialog.get_input()
        if name:
            safe = "".join(c for c in name if c.isalnum()).strip()
            self.current_preset_name = safe
            self.is_loading_preset = True 
            for btn in self.buttons_map.values(): 
                btn.clear_slot()
            self.is_loading_preset = False 
            self.save_current_preset()
            self.refresh_presets_list()
            self.palette_selector.set(safe)

    def delete_preset(self):
        curr = self.palette_selector.get()
        if curr != "Default":
            os.remove(os.path.join(CONFIG_DIR, f"{curr}.json"))
            self.refresh_presets_list()
            self.load_preset("Default")
    
    def change_preset(self, val):
        self.load_preset(val)


if __name__ == "__main__":
    app = OppodcastDesktop()
    app.mainloop()
