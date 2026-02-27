#!/usr/bin/env python3
"""
CC Model Switcher
A minimal tool for switching Claude Code API provider configurations
"""

__version__ = "1.0.0"
__author__ = "jlmaoju"
__license__ = "MIT"

import json
import sys
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("Error: tkinter is required. Please install Python tk support.")
    sys.exit(1)


# ============================================================
# Data Model
# ============================================================

@dataclass
class ModelProfile:
    id: str
    name: str
    base_url: str
    api_key: str
    timeout: int
    model_mappings: Dict[str, str] = field(default_factory=lambda: {
        "haiku": "",
        "sonnet": "",
        "opus": ""
    })

    @staticmethod
    def create_default(name: str = "New Profile") -> 'ModelProfile':
        return ModelProfile(
            id=str(uuid.uuid4()),
            name=name,
            base_url="",
            api_key="",
            timeout=3000000,
            model_mappings={"haiku": "", "sonnet": "", "opus": ""}
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ModelProfile':
        return ModelProfile(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            base_url=data.get("base_url", data.get("baseUrl", "")),
            api_key=data.get("api_key", data.get("apiKey", data.get("key", ""))),
            timeout=int(data.get("timeout", 3000000)),
            model_mappings=data.get("model_mappings", data.get("modelMappings", data.get("models", {
                "haiku": "", "sonnet": "", "opus": ""
            })))
        )


# ============================================================
# Color Theme (matching the React design)
# ============================================================

class Theme:
    # Backgrounds
    BG_PRIMARY = "#0a0a0a"
    BG_SIDEBAR = "#111111"
    BG_INPUT = "#0a0a0a"
    BG_CARD = "#111111"
    BG_HOVER = "#1a1a1a"
    BG_SELECTED = "#27272a"  # zinc-800/60

    # Text
    TEXT_PRIMARY = "#fafafa"    # zinc-100
    TEXT_SECONDARY = "#d4d4d8"  # zinc-300
    TEXT_MUTED = "#71717a"      # zinc-500
    TEXT_DIM = "#52525b"        # zinc-600

    # Borders
    BORDER = "#27272a"          # zinc-800
    BORDER_DIM = "#1f1f23"      # zinc-800/60

    # Accent colors
    ACCENT = "#6366f1"          # indigo-500
    ACCENT_DIM = "#4f46e5"      # indigo-600
    SUCCESS = "#10b981"         # emerald-500
    DANGER = "#f87171"          # red-400

    # Button
    BTN_PRIMARY_BG = "#fafafa"
    BTN_PRIMARY_FG = "#18181b"
    BTN_SECONDARY_BG = "#27272a"
    BTN_SECONDARY_FG = "#d4d4d8"

    # Fonts
    if sys.platform == "darwin":
        FONT_FAMILY = "SF Pro Text"
        FONT_MONO = "SF Mono"
    elif sys.platform == "win32":
        FONT_FAMILY = "Segoe UI"
        FONT_MONO = "Cascadia Code"
    else:
        FONT_FAMILY = "Ubuntu"
        FONT_MONO = "Ubuntu Mono"

    FONT_BASE = (FONT_FAMILY, 10)
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_LABEL = (FONT_FAMILY, 9)
    FONT_TITLE = (FONT_FAMILY, 11, "bold")
    FONT_MONO_BASE = (FONT_MONO, 10)


# ============================================================
# Application
# ============================================================

class ModelSwitcherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CC Model Switcher")
        self.root.configure(bg=Theme.BG_PRIMARY)

        # Paths
        self.config_dir = Path.home() / ".claude"
        self.config_file = self.config_dir / "settings.json"
        self.storage_dir = Path(__file__).parent.resolve()
        self.storage_file = self.storage_dir / "saved_configs.json"

        # State
        self.profiles: list[ModelProfile] = []
        self.active_profile_id: Optional[str] = None
        self.editing_profile_id: Optional[str] = None
        self.show_api_key = False

        # UI references
        self.profile_buttons: Dict[str, tk.Frame] = {}
        self.name_var = tk.StringVar()
        self.base_url_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.timeout_var = tk.StringVar()
        self.haiku_var = tk.StringVar()
        self.sonnet_var = tk.StringVar()
        self.opus_var = tk.StringVar()

        # Load data
        self.load_profiles()

        # Build UI
        self.build_ui()

        # Window setup
        self.root.update_idletasks()
        self.root.minsize(900, 720)
        self.root.geometry("960x780")
        self.center_window()

        # Select first profile or active
        self.initial_selection()

        # Start the green dot animation
        self.animate_active_dot()

    # --------------------------------------------------------
    # Data Persistence
    # --------------------------------------------------------

    def load_profiles(self):
        """Load profiles from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both old format (dict) and new format (with profiles array)
                if isinstance(data, dict) and "profiles" in data:
                    self.profiles = [ModelProfile.from_dict(p) for p in data["profiles"]]
                    self.active_profile_id = data.get("active_profile_id")
                elif isinstance(data, dict):
                    # Old format: convert
                    self.profiles = []
                    for name, config in data.items():
                        profile = ModelProfile.from_dict(config)
                        profile.name = name
                        self.profiles.append(profile)
                    if self.profiles:
                        self.active_profile_id = self.profiles[0].id
            except Exception as e:
                print(f"Failed to load profiles: {e}")

        if not self.profiles:
            # Create default profile
            default = ModelProfile.create_default("Example")
            default.base_url = "https://api.example.com"
            self.profiles.append(default)
            self.save_profiles()

    def save_profiles(self):
        """Save profiles to storage"""
        try:
            data = {
                "profiles": [p.to_dict() for p in self.profiles],
                "active_profile_id": self.active_profile_id
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def get_profile_by_id(self, profile_id: str) -> Optional[ModelProfile]:
        for p in self.profiles:
            if p.id == profile_id:
                return p
        return None

    def get_editing_profile(self) -> Optional[ModelProfile]:
        return self.get_profile_by_id(self.editing_profile_id) if self.editing_profile_id else None

    # --------------------------------------------------------
    # UI Building
    # --------------------------------------------------------

    def build_ui(self):
        """Build the main UI"""
        # Main container
        self.main_container = tk.Frame(self.root, bg=Theme.BG_PRIMARY)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.build_sidebar()

        # Main content
        self.build_main_content()

    def build_sidebar(self):
        """Build the left sidebar"""
        sidebar = tk.Frame(self.main_container, bg=Theme.BG_SIDEBAR, width=256)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Header
        header = tk.Frame(sidebar, bg=Theme.BG_SIDEBAR, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg=Theme.BG_SIDEBAR)
        header_inner.pack(fill=tk.X, padx=16, pady=16)

        # Icon placeholder (using text)
        icon_label = tk.Label(
            header_inner,
            text="⚙",
            bg=Theme.BG_SIDEBAR,
            fg=Theme.ACCENT,
            font=(Theme.FONT_FAMILY, 12)
        )
        icon_label.pack(side=tk.LEFT)

        title = tk.Label(
            header_inner,
            text="Model Switcher",
            bg=Theme.BG_SIDEBAR,
            fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_TITLE
        )
        title.pack(side=tk.LEFT, padx=(8, 0))

        version = tk.Label(
            header_inner,
            text=f"v{__version__}",
            bg=Theme.BG_SIDEBAR,
            fg=Theme.TEXT_DIM,
            font=(Theme.FONT_MONO, 8)
        )
        version.pack(side=tk.RIGHT)

        # Separator
        tk.Frame(sidebar, bg=Theme.BORDER_DIM, height=1).pack(fill=tk.X)

        # Profiles section
        profiles_header = tk.Frame(sidebar, bg=Theme.BG_SIDEBAR)
        profiles_header.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(
            profiles_header,
            text="PROFILES",
            bg=Theme.BG_SIDEBAR,
            fg=Theme.TEXT_MUTED,
            font=(Theme.FONT_FAMILY, 9, "bold")
        ).pack(side=tk.LEFT)

        # Add button
        add_btn = tk.Label(
            profiles_header,
            text="+",
            bg=Theme.BG_SIDEBAR,
            fg=Theme.TEXT_MUTED,
            font=(Theme.FONT_FAMILY, 14),
            cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT)
        add_btn.bind("<Button-1>", lambda e: self.add_profile())
        add_btn.bind("<Enter>", lambda e: add_btn.config(fg=Theme.TEXT_PRIMARY))
        add_btn.bind("<Leave>", lambda e: add_btn.config(fg=Theme.TEXT_MUTED))

        # Profile list container
        self.profile_list = tk.Frame(sidebar, bg=Theme.BG_SIDEBAR)
        self.profile_list.pack(fill=tk.BOTH, expand=True, padx=12)

        self.refresh_profile_list()

    def refresh_profile_list(self):
        """Refresh the profile list in sidebar"""
        for widget in self.profile_list.winfo_children():
            widget.destroy()
        self.profile_buttons.clear()

        for profile in self.profiles:
            self.create_profile_item(profile)

    def create_profile_item(self, profile: ModelProfile):
        """Create a profile item in the sidebar"""
        is_editing = profile.id == self.editing_profile_id
        is_active = profile.id == self.active_profile_id

        bg = Theme.BG_SELECTED if is_editing else Theme.BG_SIDEBAR
        fg = Theme.TEXT_PRIMARY if is_editing else Theme.TEXT_MUTED

        item = tk.Frame(self.profile_list, bg=bg, cursor="hand2")
        item.pack(fill=tk.X, pady=1)

        inner = tk.Frame(item, bg=bg)
        inner.pack(fill=tk.X, padx=12, pady=10)

        label = tk.Label(
            inner,
            text=profile.name,
            bg=bg,
            fg=fg,
            font=Theme.FONT_BASE,
            anchor=tk.W
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Active indicator (green dot)
        if is_active:
            dot_frame = tk.Frame(inner, bg=bg)
            dot_frame.pack(side=tk.RIGHT)

            # Outer glow dot (for animation)
            self.glow_dot = tk.Label(
                dot_frame,
                text="●",
                bg=bg,
                fg=Theme.SUCCESS,
                font=(Theme.FONT_FAMILY, 8)
            )
            self.glow_dot.pack()

        # Store reference
        self.profile_buttons[profile.id] = item

        # Bindings
        def on_click(e, pid=profile.id):
            self.select_profile(pid)

        def on_enter(e):
            if profile.id != self.editing_profile_id:
                item.config(bg=Theme.BG_HOVER)
                inner.config(bg=Theme.BG_HOVER)
                label.config(bg=Theme.BG_HOVER)

        def on_leave(e):
            target_bg = Theme.BG_SELECTED if profile.id == self.editing_profile_id else Theme.BG_SIDEBAR
            item.config(bg=target_bg)
            inner.config(bg=target_bg)
            label.config(bg=target_bg)

        for widget in [item, inner, label]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def animate_active_dot(self):
        """Animate the green dot for active profile"""
        if hasattr(self, 'glow_dot') and self.glow_dot.winfo_exists():
            current = self.glow_dot.cget("fg")
            # Toggle between bright and dim
            new_color = "#34d399" if current == Theme.SUCCESS else Theme.SUCCESS
            self.glow_dot.config(fg=new_color)

        self.root.after(800, self.animate_active_dot)

    def build_main_content(self):
        """Build the main content area"""
        main = tk.Frame(self.main_container, bg=Theme.BG_PRIMARY)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top bar
        self.build_top_bar(main)

        # Form area (scrollable would be nice, but keeping it simple)
        self.form_frame = tk.Frame(main, bg=Theme.BG_PRIMARY)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

        self.build_form()

        # Bottom action bar
        self.build_action_bar(main)

    def build_top_bar(self, parent):
        """Build the top bar"""
        topbar = tk.Frame(parent, bg=Theme.BG_PRIMARY, height=56)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        inner = tk.Frame(topbar, bg=Theme.BG_PRIMARY)
        inner.pack(fill=tk.X, padx=32, pady=16)

        self.topbar_title = tk.Label(
            inner,
            text="Select a profile",
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_TITLE
        )
        self.topbar_title.pack(side=tk.LEFT)

        # Active indicator
        self.active_indicator = tk.Frame(inner, bg=Theme.BG_PRIMARY)
        self.active_indicator.pack(side=tk.RIGHT)

        # Separator
        tk.Frame(parent, bg=Theme.BORDER_DIM, height=1).pack(fill=tk.X)

    def update_active_indicator(self):
        """Update the active indicator in top bar"""
        for widget in self.active_indicator.winfo_children():
            widget.destroy()

        if self.editing_profile_id == self.active_profile_id and self.active_profile_id:
            dot = tk.Label(
                self.active_indicator,
                text="●",
                bg=Theme.BG_PRIMARY,
                fg=Theme.SUCCESS,
                font=(Theme.FONT_FAMILY, 6)
            )
            dot.pack(side=tk.LEFT, padx=(0, 6))

            label = tk.Label(
                self.active_indicator,
                text="Current Active",
                bg=Theme.BG_PRIMARY,
                fg=Theme.TEXT_MUTED,
                font=Theme.FONT_SMALL
            )
            label.pack(side=tk.LEFT)

    def build_form(self):
        """Build the form fields"""
        form = self.form_frame

        # Clear existing
        for widget in form.winfo_children():
            widget.destroy()

        # Max width container
        container = tk.Frame(form, bg=Theme.BG_PRIMARY)
        container.pack(fill=tk.X, expand=False)

        # Name field
        self.create_field(container, "Name", self.name_var, mono=False)

        # Base URL field
        self.create_field(container, "Base URL", self.base_url_var, mono=True)

        # API Key field
        self.create_api_key_field(container)

        # Timeout field
        self.create_field(container, "Timeout (ms)", self.timeout_var, mono=True, width=200)

        # Separator
        tk.Frame(container, bg=Theme.BORDER_DIM, height=1).pack(fill=tk.X, pady=24)

        # Model Mappings
        self.create_model_mappings(container)

    def create_field(self, parent, label_text: str, var: tk.StringVar, mono: bool = False, width: int = None):
        """Create a form field"""
        frame = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        frame.pack(fill=tk.X, pady=8)

        label = tk.Label(
            frame,
            text=label_text,
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_MUTED,
            font=Theme.FONT_LABEL
        )
        label.pack(anchor=tk.W, pady=(0, 6))

        entry = tk.Entry(
            frame,
            textvariable=var,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_SECONDARY,
            insertbackground=Theme.TEXT_SECONDARY,
            font=Theme.FONT_MONO_BASE if mono else Theme.FONT_BASE,
            bd=0,
            highlightthickness=1,
            highlightbackground=Theme.BORDER,
            highlightcolor=Theme.ACCENT
        )
        if width:
            entry.config(width=width // 8)
            entry.pack(anchor=tk.W, ipady=10, ipadx=12)
        else:
            entry.pack(fill=tk.X, ipady=10, ipadx=12)

    def create_api_key_field(self, parent):
        """Create the API key field with show/hide toggle"""
        frame = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        frame.pack(fill=tk.X, pady=8)

        label = tk.Label(
            frame,
            text="API Key",
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_MUTED,
            font=Theme.FONT_LABEL
        )
        label.pack(anchor=tk.W, pady=(0, 6))

        entry_frame = tk.Frame(frame, bg=Theme.BG_INPUT, highlightthickness=1,
                               highlightbackground=Theme.BORDER, highlightcolor=Theme.ACCENT)
        entry_frame.pack(fill=tk.X)

        self.api_key_entry = tk.Entry(
            entry_frame,
            textvariable=self.api_key_var,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_SECONDARY,
            insertbackground=Theme.TEXT_SECONDARY,
            font=Theme.FONT_MONO_BASE,
            bd=0,
            show="•"
        )
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, ipadx=12)

        self.eye_btn = tk.Label(
            entry_frame,
            text="👁",
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_MUTED,
            font=(Theme.FONT_FAMILY, 10),
            cursor="hand2"
        )
        self.eye_btn.pack(side=tk.RIGHT, padx=12)
        self.eye_btn.bind("<Button-1>", self.toggle_api_key_visibility)

    def toggle_api_key_visibility(self, event=None):
        """Toggle API key visibility"""
        self.show_api_key = not self.show_api_key
        self.api_key_entry.config(show="" if self.show_api_key else "•")
        self.eye_btn.config(text="🙈" if self.show_api_key else "👁")

    def create_model_mappings(self, parent):
        """Create model mappings section"""
        header = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            header,
            text="Model Mappings",
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_FAMILY, 10, "bold")
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="OPTIONAL",
            bg=Theme.BG_SELECTED,
            fg=Theme.TEXT_MUTED,
            font=(Theme.FONT_FAMILY, 8),
            padx=6,
            pady=2
        ).pack(side=tk.LEFT, padx=(8, 0))

        # Mappings card
        card = tk.Frame(parent, bg=Theme.BG_CARD, highlightthickness=1,
                        highlightbackground=Theme.BORDER_DIM)
        card.pack(fill=tk.X)

        mappings = [
            ("Haiku", self.haiku_var),
            ("Sonnet", self.sonnet_var),
            ("Opus", self.opus_var)
        ]

        for i, (name, var) in enumerate(mappings):
            row = tk.Frame(card, bg=Theme.BG_CARD)
            row.pack(fill=tk.X, padx=4, pady=4)

            if i > 0:
                tk.Frame(row, bg=Theme.BORDER_DIM, height=1).pack(fill=tk.X)

            inner = tk.Frame(row, bg=Theme.BG_CARD)
            inner.pack(fill=tk.X, pady=4)

            tk.Label(
                inner,
                text=name,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_MUTED,
                font=Theme.FONT_BASE,
                width=10,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=(8, 0))

            entry = tk.Entry(
                inner,
                textvariable=var,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_SECONDARY,
                insertbackground=Theme.TEXT_SECONDARY,
                font=Theme.FONT_MONO_BASE,
                bd=0,
                highlightthickness=1,
                highlightbackground=Theme.BG_CARD,
                highlightcolor=Theme.BORDER
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, ipadx=8, padx=(0, 8))

        # Help text
        tk.Label(
            parent,
            text="Map standard Anthropic model names to your custom provider's models.",
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_DIM,
            font=Theme.FONT_SMALL
        ).pack(anchor=tk.W, pady=(8, 0))

    def build_action_bar(self, parent):
        """Build the bottom action bar"""
        bar = tk.Frame(parent, bg=Theme.BG_PRIMARY, height=64)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        # Separator
        tk.Frame(bar, bg=Theme.BORDER_DIM, height=1).pack(fill=tk.X, side=tk.TOP)

        inner = tk.Frame(bar, bg=Theme.BG_PRIMARY)
        inner.pack(fill=tk.BOTH, expand=True, padx=32)

        # Delete button (left)
        delete_btn = tk.Label(
            inner,
            text="🗑  Delete Profile",
            bg=Theme.BG_PRIMARY,
            fg="#f87171",
            font=Theme.FONT_BASE,
            cursor="hand2"
        )
        delete_btn.pack(side=tk.LEFT, pady=16)
        delete_btn.bind("<Button-1>", lambda e: self.delete_profile())
        delete_btn.bind("<Enter>", lambda e: delete_btn.config(fg="#fca5a5"))
        delete_btn.bind("<Leave>", lambda e: delete_btn.config(fg="#f87171"))

        # Right buttons
        btn_group = tk.Frame(inner, bg=Theme.BG_PRIMARY)
        btn_group.pack(side=tk.RIGHT, pady=12)

        # Save Draft button
        save_btn = tk.Label(
            btn_group,
            text="Save Draft",
            bg=Theme.BTN_SECONDARY_BG,
            fg=Theme.BTN_SECONDARY_FG,
            font=Theme.FONT_BASE,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 12))
        save_btn.bind("<Button-1>", lambda e: self.save_draft())
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg=Theme.BG_HOVER))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=Theme.BTN_SECONDARY_BG))

        # Apply & Save button
        apply_btn = tk.Label(
            btn_group,
            text="✓  Apply & Save",
            bg=Theme.BTN_PRIMARY_BG,
            fg=Theme.BTN_PRIMARY_FG,
            font=(Theme.FONT_FAMILY, 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        )
        apply_btn.pack(side=tk.LEFT)
        apply_btn.bind("<Button-1>", lambda e: self.apply_and_save())
        apply_btn.bind("<Enter>", lambda e: apply_btn.config(bg="#ffffff"))
        apply_btn.bind("<Leave>", lambda e: apply_btn.config(bg=Theme.BTN_PRIMARY_BG))

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    def initial_selection(self):
        """Select initial profile"""
        if self.active_profile_id:
            self.select_profile(self.active_profile_id)
        elif self.profiles:
            self.select_profile(self.profiles[0].id)

    def select_profile(self, profile_id: str):
        """Select a profile for editing"""
        self.editing_profile_id = profile_id
        profile = self.get_profile_by_id(profile_id)

        if profile:
            self.name_var.set(profile.name)
            self.base_url_var.set(profile.base_url)
            self.api_key_var.set(profile.api_key)
            self.timeout_var.set(str(profile.timeout))
            self.haiku_var.set(profile.model_mappings.get("haiku", ""))
            self.sonnet_var.set(profile.model_mappings.get("sonnet", ""))
            self.opus_var.set(profile.model_mappings.get("opus", ""))

            self.topbar_title.config(text=profile.name)
            self.update_active_indicator()

        self.refresh_profile_list()

    def add_profile(self):
        """Add a new profile"""
        new_profile = ModelProfile.create_default()

        # Find unique name
        base_name = "New Profile"
        name = base_name
        counter = 1
        existing_names = [p.name for p in self.profiles]
        while name in existing_names:
            counter += 1
            name = f"{base_name} {counter}"
        new_profile.name = name

        self.profiles.append(new_profile)
        self.save_profiles()
        self.refresh_profile_list()
        self.select_profile(new_profile.id)

    def delete_profile(self):
        """Delete the current profile"""
        if not self.editing_profile_id:
            return

        profile = self.get_profile_by_id(self.editing_profile_id)
        if not profile:
            return

        if not messagebox.askyesno("Confirm", f"Delete '{profile.name}'?"):
            return

        self.profiles = [p for p in self.profiles if p.id != self.editing_profile_id]

        if self.active_profile_id == self.editing_profile_id:
            self.active_profile_id = None

        self.save_profiles()
        self.refresh_profile_list()

        if self.profiles:
            self.select_profile(self.profiles[0].id)
        else:
            self.editing_profile_id = None
            self.topbar_title.config(text="No profiles")

    def get_form_data(self) -> dict:
        """Get current form data"""
        return {
            "name": self.name_var.get().strip(),
            "base_url": self.base_url_var.get().strip(),
            "api_key": self.api_key_var.get().strip(),
            "timeout": int(self.timeout_var.get() or 3000000),
            "model_mappings": {
                "haiku": self.haiku_var.get().strip(),
                "sonnet": self.sonnet_var.get().strip(),
                "opus": self.opus_var.get().strip()
            }
        }

    def save_draft(self):
        """Save without applying"""
        if not self.editing_profile_id:
            return

        profile = self.get_profile_by_id(self.editing_profile_id)
        if not profile:
            return

        data = self.get_form_data()
        profile.name = data["name"]
        profile.base_url = data["base_url"]
        profile.api_key = data["api_key"]
        profile.timeout = data["timeout"]
        profile.model_mappings = data["model_mappings"]

        self.save_profiles()
        self.refresh_profile_list()
        self.topbar_title.config(text=profile.name)

        messagebox.showinfo("Saved", "Profile saved as draft.")

    def apply_and_save(self):
        """Apply and save the configuration"""
        if not self.editing_profile_id:
            return

        profile = self.get_profile_by_id(self.editing_profile_id)
        if not profile:
            return

        data = self.get_form_data()

        if not data["base_url"]:
            messagebox.showwarning("Warning", "Base URL is required.")
            return

        # Update profile
        profile.name = data["name"]
        profile.base_url = data["base_url"]
        profile.api_key = data["api_key"]
        profile.timeout = data["timeout"]
        profile.model_mappings = data["model_mappings"]

        # Set as active
        self.active_profile_id = self.editing_profile_id

        self.save_profiles()
        self.apply_to_claude_code(profile)
        self.refresh_profile_list()
        self.update_active_indicator()
        self.topbar_title.config(text=profile.name)

        messagebox.showinfo("Applied", "Configuration applied!\n\nRestart Claude Code for changes to take effect.")

    def apply_to_claude_code(self, profile: ModelProfile):
        """Write config to Claude Code settings"""
        config = {
            "env": {
                "ANTHROPIC_BASE_URL": profile.base_url,
                "ANTHROPIC_AUTH_TOKEN": profile.api_key,
                "API_TIMEOUT_MS": str(profile.timeout),
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1
            }
        }

        if profile.model_mappings.get("haiku"):
            config["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = profile.model_mappings["haiku"]
        if profile.model_mappings.get("sonnet"):
            config["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] = profile.model_mappings["sonnet"]
        if profile.model_mappings.get("opus"):
            config["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = profile.model_mappings["opus"]

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            if self.config_file.exists():
                backup = self.config_dir / "settings.json.backup"
                shutil.copy2(self.config_file, backup)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply: {e}")

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')


def main():
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    app = ModelSwitcherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
