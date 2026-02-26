#!/usr/bin/env python3
"""
CC Model Switcher
A minimal tool for switching Claude Code API provider configurations
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("Error: tkinter is required. Please install Python tk support.")
    sys.exit(1)


class ModernStyle:
    """Modern dark theme colors"""
    BG_DARK = "#1a1a1a"
    BG_MEDIUM = "#2d2d2d"
    BG_LIGHT = "#3d3d3d"
    BG_HOVER = "#4d4d4d"

    FG_PRIMARY = "#ffffff"
    FG_SECONDARY = "#b0b0b0"
    FG_MUTED = "#707070"

    ACCENT = "#505050"
    ACCENT_HOVER = "#606060"
    ACCENT_ACTIVE = "#707070"

    BORDER = "#404040"

    # Cross-platform fonts
    if sys.platform == "darwin":
        FONT_FAMILY = "SF Pro Text"
    elif sys.platform == "win32":
        FONT_FAMILY = "Segoe UI"
    else:
        FONT_FAMILY = "Ubuntu"

    FONT_TITLE = (FONT_FAMILY, 14, "bold")
    FONT_NORMAL = (FONT_FAMILY, 10)
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_BUTTON = (FONT_FAMILY, 10)


class APISwitcherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CC Model Switcher")
        self.root.configure(bg=ModernStyle.BG_DARK)

        # Config paths
        self.config_dir = Path.home() / ".claude"
        self.config_file = self.config_dir / "settings.json"
        self.storage_dir = Path(__file__).parent.resolve()
        self.storage_file = self.storage_dir / "saved_configs.json"

        # Load saved configs
        self.saved_configs = self.load_saved_configs()
        self.current_config_name: Optional[str] = None

        # Create UI
        self.setup_styles()
        self.create_ui()

        # Set window size and center
        self.root.update_idletasks()
        self.root.minsize(820, 660)
        self.root.geometry("880x700")
        self.center_window()

        # Load first config or current
        self.load_current_config()

    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Dark.TFrame", background=ModernStyle.BG_DARK)
        style.configure("Card.TFrame", background=ModernStyle.BG_MEDIUM)

        style.configure("Dark.TLabel",
                       background=ModernStyle.BG_DARK,
                       foreground=ModernStyle.FG_PRIMARY,
                       font=ModernStyle.FONT_NORMAL)
        style.configure("Title.TLabel",
                       background=ModernStyle.BG_DARK,
                       foreground=ModernStyle.FG_PRIMARY,
                       font=ModernStyle.FONT_TITLE)

        style.configure("Dark.Vertical.TScrollbar",
                       background=ModernStyle.BG_LIGHT,
                       troughcolor=ModernStyle.BG_DARK,
                       arrowcolor=ModernStyle.FG_MUTED)

    def create_button(self, parent, text: str, command, style: str = "normal", width: int = None) -> tk.Button:
        """Create a styled button"""
        colors = {
            "normal": (ModernStyle.BG_LIGHT, ModernStyle.BG_HOVER),
            "primary": (ModernStyle.ACCENT, ModernStyle.ACCENT_HOVER),
            "muted": (ModernStyle.BG_MEDIUM, ModernStyle.BG_LIGHT),
            "danger": (ModernStyle.BG_LIGHT, "#5a3a3a"),
        }
        bg, hover = colors.get(style, colors["normal"])

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=ModernStyle.FG_PRIMARY,
            activebackground=hover,
            activeforeground=ModernStyle.FG_PRIMARY,
            font=ModernStyle.FONT_BUTTON,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            relief="flat",
            highlightthickness=0
        )
        if width:
            btn.configure(width=width)

        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))

        return btn

    def create_ui(self):
        """Create the user interface"""
        main_frame = ttk.Frame(self.root, style="Dark.TFrame", padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(main_frame, style="Dark.TFrame")
        header.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(header, text="CC Model Switcher", style="Title.TLabel").pack(side=tk.LEFT)

        # Version label
        version_label = tk.Label(
            header,
            text=f"v{__version__}",
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.FG_MUTED,
            font=ModernStyle.FONT_SMALL
        )
        version_label.pack(side=tk.RIGHT)

        # Two-column layout
        content = ttk.Frame(main_frame, style="Dark.TFrame")
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(1, weight=3)  # Right panel gets more space
        content.columnconfigure(0, weight=0, minsize=180)
        content.rowconfigure(0, weight=1)

        # Left panel - Config list
        self.create_config_list(content)

        # Right panel - Config editor
        self.create_config_editor(content)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(
            main_frame,
            textvariable=self.status_var,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.FG_MUTED,
            font=ModernStyle.FONT_SMALL,
            anchor=tk.W
        )
        status.pack(fill=tk.X, pady=(15, 0))

    def create_config_list(self, parent):
        """Create the configuration list panel"""
        left_panel = ttk.Frame(parent, style="Dark.TFrame")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Section header
        header = ttk.Frame(left_panel, style="Dark.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header, text="Profiles", style="Dark.TLabel").pack(side=tk.LEFT)

        add_btn = self.create_button(header, "+", self.add_config, "muted")
        add_btn.pack(side=tk.RIGHT)

        # Config list
        list_container = tk.Frame(
            left_panel,
            bg=ModernStyle.BG_MEDIUM,
            bd=0,
            highlightthickness=1,
            highlightbackground=ModernStyle.BORDER
        )
        list_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(list_container, bg=ModernStyle.BG_MEDIUM, bd=0, highlightthickness=0, width=160)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")

        self.config_list_frame = tk.Frame(canvas, bg=ModernStyle.BG_MEDIUM)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_window = canvas.create_window((0, 0), window=self.config_list_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        self.config_list_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.canvas = canvas
        self.refresh_config_list()

    def create_config_editor(self, parent):
        """Create the configuration editor panel"""
        right_panel = ttk.Frame(parent, style="Dark.TFrame")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)

        # Card container
        card = tk.Frame(
            right_panel,
            bg=ModernStyle.BG_MEDIUM,
            bd=0,
            highlightthickness=1,
            highlightbackground=ModernStyle.BORDER
        )
        card.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(card, bg=ModernStyle.BG_MEDIUM, padx=25, pady=20)
        inner.pack(fill=tk.BOTH, expand=True)
        inner.columnconfigure(0, weight=1)

        row = 0

        # Config name
        self._add_label(inner, "Name", row)
        row += 1

        self.name_var = tk.StringVar()
        self.name_entry = self._create_entry(inner, self.name_var)
        self.name_entry.grid(row=row, column=0, sticky="ew", pady=(0, 12), ipady=8, ipadx=10)
        row += 1

        # Base URL
        self._add_label(inner, "Base URL", row)
        row += 1

        self.base_url_var = tk.StringVar()
        self.base_url_entry = self._create_entry(inner, self.base_url_var)
        self.base_url_entry.grid(row=row, column=0, sticky="ew", pady=(0, 12), ipady=8, ipadx=10)
        row += 1

        # API Key
        self._add_label(inner, "API Key", row)
        row += 1

        key_frame = tk.Frame(inner, bg=ModernStyle.BG_MEDIUM)
        key_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        key_frame.columnconfigure(0, weight=1)

        self.key_var = tk.StringVar()
        self.key_entry = self._create_entry(key_frame, self.key_var, show="*")
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10)

        self.show_key_btn = self.create_button(key_frame, "Show", self.toggle_key_visibility, "muted")
        self.show_key_btn.pack(side=tk.RIGHT, padx=(10, 0))
        row += 1

        # Timeout
        self._add_label(inner, "Timeout (ms)", row)
        row += 1

        self.timeout_var = tk.StringVar(value="3000000")
        self.timeout_entry = self._create_entry(inner, self.timeout_var)
        self.timeout_entry.grid(row=row, column=0, sticky="ew", pady=(0, 16), ipady=8, ipadx=10)
        row += 1

        # Model mappings section
        model_label = tk.Label(
            inner,
            text="Model Mappings (Optional)",
            bg=ModernStyle.BG_MEDIUM,
            fg=ModernStyle.FG_SECONDARY,
            font=ModernStyle.FONT_SMALL
        )
        model_label.grid(row=row, column=0, sticky=tk.W, pady=(5, 8))
        row += 1

        model_frame = tk.Frame(inner, bg=ModernStyle.BG_LIGHT, bd=0)
        model_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        model_frame.columnconfigure(1, weight=1)

        model_inner = tk.Frame(model_frame, bg=ModernStyle.BG_LIGHT, padx=12, pady=12)
        model_inner.pack(fill=tk.X)
        model_inner.columnconfigure(1, weight=1)

        # Haiku
        self._add_model_row(model_inner, "Haiku", 0)
        self.haiku_var = tk.StringVar()
        self._create_model_entry(model_inner, self.haiku_var, 0)

        # Sonnet
        self._add_model_row(model_inner, "Sonnet", 1)
        self.sonnet_var = tk.StringVar()
        self._create_model_entry(model_inner, self.sonnet_var, 1)

        # Opus
        self._add_model_row(model_inner, "Opus", 2)
        self.opus_var = tk.StringVar()
        self._create_model_entry(model_inner, self.opus_var, 2)
        row += 1

        # Action buttons
        btn_frame = tk.Frame(inner, bg=ModernStyle.BG_MEDIUM)
        btn_frame.grid(row=row, column=0, sticky="ew", pady=(5, 0))

        self.apply_btn = self.create_button(btn_frame, "Apply", self.save_and_apply, "primary")
        self.apply_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.save_btn = self.create_button(btn_frame, "Save", self.save_only, "normal")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.delete_btn = self.create_button(btn_frame, "Delete", self.delete_config, "danger")
        self.delete_btn.pack(side=tk.RIGHT)

    def _add_label(self, parent, text: str, row: int):
        """Add a form label"""
        label = tk.Label(
            parent,
            text=text,
            bg=ModernStyle.BG_MEDIUM,
            fg=ModernStyle.FG_SECONDARY,
            font=ModernStyle.FONT_SMALL,
            anchor=tk.W
        )
        label.grid(row=row, column=0, sticky=tk.W, pady=(0, 4))

    def _create_entry(self, parent, var: tk.StringVar, show: str = None) -> tk.Entry:
        """Create a styled entry"""
        entry = tk.Entry(
            parent,
            textvariable=var,
            bg=ModernStyle.BG_LIGHT,
            fg=ModernStyle.FG_PRIMARY,
            insertbackground=ModernStyle.FG_PRIMARY,
            font=ModernStyle.FONT_NORMAL,
            bd=0,
            relief="flat",
            show=show or ""
        )
        return entry

    def _add_model_row(self, parent, label: str, row: int):
        """Add a model mapping row label"""
        tk.Label(
            parent,
            text=label,
            bg=ModernStyle.BG_LIGHT,
            fg=ModernStyle.FG_MUTED,
            font=ModernStyle.FONT_SMALL,
            width=7,
            anchor=tk.W
        ).grid(row=row, column=0, sticky=tk.W, pady=4)

    def _create_model_entry(self, parent, var: tk.StringVar, row: int):
        """Create a model mapping entry"""
        entry = tk.Entry(
            parent,
            textvariable=var,
            bg=ModernStyle.BG_MEDIUM,
            fg=ModernStyle.FG_PRIMARY,
            insertbackground=ModernStyle.FG_PRIMARY,
            font=ModernStyle.FONT_SMALL,
            bd=0
        )
        entry.grid(row=row, column=1, sticky="ew", pady=4, ipady=6, ipadx=8)
        if row == 0:
            setattr(self, 'haiku_var', var)
        elif row == 1:
            setattr(self, 'sonnet_var', var)
        else:
            setattr(self, 'opus_var', var)

    def refresh_config_list(self):
        """Refresh the configuration list"""
        for widget in self.config_list_frame.winfo_children():
            widget.destroy()

        for name in self.saved_configs.keys():
            self.create_config_item(name)

        if not self.saved_configs:
            placeholder = tk.Label(
                self.config_list_frame,
                text="No profiles yet.\nClick + to add.",
                bg=ModernStyle.BG_MEDIUM,
                fg=ModernStyle.FG_MUTED,
                font=ModernStyle.FONT_SMALL,
                justify=tk.CENTER,
                pady=20
            )
            placeholder.pack(fill=tk.X)

    def create_config_item(self, name: str):
        """Create a config list item"""
        is_selected = name == self.current_config_name
        bg = ModernStyle.BG_LIGHT if is_selected else ModernStyle.BG_MEDIUM

        item = tk.Frame(self.config_list_frame, bg=bg, cursor="hand2")
        item.pack(fill=tk.X, pady=1)

        label = tk.Label(
            item,
            text=name,
            bg=bg,
            fg=ModernStyle.FG_PRIMARY if is_selected else ModernStyle.FG_SECONDARY,
            font=ModernStyle.FONT_NORMAL,
            anchor=tk.W,
            padx=12,
            pady=10
        )
        label.pack(fill=tk.X)

        def on_click(event, n=name):
            self.select_config(n)

        item.bind("<Button-1>", on_click)
        label.bind("<Button-1>", on_click)

        def on_enter(event):
            if name != self.current_config_name:
                item.configure(bg=ModernStyle.BG_HOVER)
                label.configure(bg=ModernStyle.BG_HOVER)

        def on_leave(event):
            bg = ModernStyle.BG_LIGHT if name == self.current_config_name else ModernStyle.BG_MEDIUM
            item.configure(bg=bg)
            label.configure(bg=bg)

        item.bind("<Enter>", on_enter)
        item.bind("<Leave>", on_leave)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)

    def select_config(self, name: str):
        """Select a configuration"""
        if name not in self.saved_configs:
            return

        self.current_config_name = name
        config = self.saved_configs[name]

        self.name_var.set(name)
        self.base_url_var.set(config.get("base_url", ""))
        self.key_var.set(config.get("key", ""))
        self.timeout_var.set(config.get("timeout", "3000000"))
        self.haiku_var.set(config.get("models", {}).get("haiku", ""))
        self.sonnet_var.set(config.get("models", {}).get("sonnet", ""))
        self.opus_var.set(config.get("models", {}).get("opus", ""))

        self.refresh_config_list()
        self.status_var.set(f"Selected: {name}")

    def add_config(self):
        """Add a new configuration"""
        base_name = "New Profile"
        name = base_name
        counter = 1
        while name in self.saved_configs:
            counter += 1
            name = f"{base_name} {counter}"

        self.saved_configs[name] = {
            "base_url": "",
            "key": "",
            "timeout": "3000000",
            "models": {"haiku": "", "sonnet": "", "opus": ""}
        }

        self.save_configs_to_storage()
        self.refresh_config_list()
        self.select_config(name)
        self.status_var.set(f"Created: {name}")

        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)

    def delete_config(self):
        """Delete the current configuration"""
        if not self.current_config_name:
            return

        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{self.current_config_name}'?"
        )

        if result:
            del self.saved_configs[self.current_config_name]
            self.save_configs_to_storage()

            if self.saved_configs:
                first_name = list(self.saved_configs.keys())[0]
                self.select_config(first_name)
            else:
                self.current_config_name = None
                self.clear_form()

            self.refresh_config_list()
            self.status_var.set("Profile deleted")

    def clear_form(self):
        """Clear the form"""
        self.name_var.set("")
        self.base_url_var.set("")
        self.key_var.set("")
        self.timeout_var.set("3000000")
        self.haiku_var.set("")
        self.sonnet_var.set("")
        self.opus_var.set("")

    def toggle_key_visibility(self):
        """Toggle API key visibility"""
        if self.key_entry.cget("show") == "*":
            self.key_entry.config(show="")
            self.show_key_btn.config(text="Hide")
        else:
            self.key_entry.config(show="*")
            self.show_key_btn.config(text="Show")

    def load_saved_configs(self) -> Dict[str, Any]:
        """Load saved configurations from storage, create default if not exists"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load configs: {e}")

        # Create default config for first-time users
        default_configs = {
            "Example": {
                "base_url": "https://api.example.com",
                "key": "",
                "timeout": "3000000",
                "models": {"haiku": "", "sonnet": "", "opus": ""}
            }
        }
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(default_configs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default_configs

    def save_configs_to_storage(self) -> bool:
        """Save configurations to storage file"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_configs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
            return False

    def get_current_form_data(self) -> Dict[str, Any]:
        """Get current form data as config dict"""
        return {
            "base_url": self.base_url_var.get().strip(),
            "key": self.key_var.get().strip(),
            "timeout": self.timeout_var.get().strip() or "3000000",
            "models": {
                "haiku": self.haiku_var.get().strip(),
                "sonnet": self.sonnet_var.get().strip(),
                "opus": self.opus_var.get().strip()
            }
        }

    def save_only(self):
        """Save configuration to storage only"""
        new_name = self.name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Warning", "Name cannot be empty")
            return

        if self.current_config_name and new_name != self.current_config_name:
            if new_name in self.saved_configs:
                messagebox.showwarning("Warning", f"'{new_name}' already exists")
                return
            del self.saved_configs[self.current_config_name]

        self.saved_configs[new_name] = self.get_current_form_data()
        self.current_config_name = new_name

        if self.save_configs_to_storage():
            self.refresh_config_list()
            self.status_var.set(f"Saved: {new_name}")

    def save_and_apply(self):
        """Save and apply configuration to Claude Code"""
        new_name = self.name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Warning", "Name cannot be empty")
            return

        base_url = self.base_url_var.get().strip()
        key = self.key_var.get().strip()

        if not base_url:
            messagebox.showwarning("Warning", "Base URL cannot be empty")
            return

        if not key:
            result = messagebox.askyesno(
                "Confirm",
                "API Key is empty. Continue?\n(May use environment variable)"
            )
            if not result:
                return

        if self.current_config_name and new_name != self.current_config_name:
            if new_name in self.saved_configs:
                messagebox.showwarning("Warning", f"'{new_name}' already exists")
                return
            del self.saved_configs[self.current_config_name]

        self.saved_configs[new_name] = self.get_current_form_data()
        self.current_config_name = new_name

        if not self.save_configs_to_storage():
            return

        # Build Claude Code config
        config = {
            "env": {
                "ANTHROPIC_BASE_URL": base_url,
                "ANTHROPIC_AUTH_TOKEN": key,
                "API_TIMEOUT_MS": self.timeout_var.get().strip() or "3000000",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1
            }
        }

        if self.haiku_var.get().strip():
            config["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = self.haiku_var.get().strip()
        if self.sonnet_var.get().strip():
            config["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] = self.sonnet_var.get().strip()
        if self.opus_var.get().strip():
            config["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = self.opus_var.get().strip()

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            if self.config_file.exists():
                backup_file = self.config_dir / "settings.json.backup"
                shutil.copy2(self.config_file, backup_file)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.refresh_config_list()
            self.status_var.set(f"Applied: {new_name}")
            messagebox.showinfo(
                "Success",
                "Configuration applied!\n\nRestart Claude Code for changes to take effect."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply: {e}")
            self.status_var.set(f"Error: {e}")

    def load_current_config(self):
        """Load current Claude Code configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                env = config.get("env", {})
                current_base_url = env.get("ANTHROPIC_BASE_URL", "")

                for name, saved_config in self.saved_configs.items():
                    if saved_config.get("base_url") == current_base_url:
                        self.select_config(name)
                        self.status_var.set(f"Current: {name}")
                        return
            except Exception:
                pass

        if self.saved_configs:
            first_name = list(self.saved_configs.keys())[0]
            self.select_config(first_name)
        else:
            self.status_var.set("Click + to create a profile")

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


def main():
    """Main entry point"""
    # Set DPI awareness on Windows (must be before Tk init)
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    app = APISwitcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
