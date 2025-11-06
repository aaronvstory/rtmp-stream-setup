#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines,invalid-name,line-too-long
"""RTMP Stream Setup Assistant (Enhanced V3 - Port Check)
A visually appealing utility to configure RTMP streaming from Android devices.
Reads configuration from config.ini. Checks for host port conflicts.
"""

# Standard library imports
import configparser
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# For folder selection dialog
TK = None
FILEDIALOG = None
TKINTER_AVAILABLE = False
try:
    import tkinter
    import tkinter.filedialog

    TK = tkinter
    FILEDIALOG = tkinter.filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    pass

# Third-party imports
try:
    import psutil
    import pyperclip
    from rich.box import ROUNDED
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    missing_modules = []
    try:
        import importlib.util

        if not importlib.util.find_spec("rich"):
            missing_modules.append("rich")
        if not importlib.util.find_spec("pyperclip"):
            missing_modules.append("pyperclip")
        if not importlib.util.find_spec("psutil"):
            missing_modules.append("psutil")
    except ImportError:
        missing_modules.extend(["rich", "pyperclip", "psutil"])

    if missing_modules:
        unique_missing = sorted(list(set(missing_modules)))
        print(
            f"Error: Required libraries not found. Please install {' '.join(unique_missing)} using:\n"
            f"pip install {' '.join(unique_missing)}"
        )
    else:
        print(
            "Error: One or more required third-party libraries (rich, pyperclip, psutil) are missing."
        )
    sys.exit(1)

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "config.ini"
DEFAULT_CONFIG = {
    "Paths": {"AdbPath": "", "MonaServerPath": "", "ObsPath": ""},
    "Device": {"PackageName": "com.telegram.a1064/com.nvshen.chmp4.SplashActivity"},
    "Network": {"RtmpPort": "1935"},
    "Options": {
        "AutoStartMonaServer": "true",
        "AutoSelectSingleDevice": "true",
        "FetchDeviceModels": "true",
        "ForceKillConflictingPortProcess": "true",
    },
}
DEFAULT_ADB_PATH_WIN = "C:\\platform-tools\\adb.exe"
DEFAULT_OBS_PATH_WIN = "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe"

# --- Unicode Symbols ---
SYMBOL_CHECK = "✓"      # U+2713 - Success/completion indicator
SYMBOL_CROSS = "✗"      # U+2717 - Failure/error indicator
SYMBOL_WARNING = "⚠"    # U+26A0 - Warning indicator
SYMBOL_ARROW_LR = "↔"   # U+2194 - Bidirectional arrow (port forwarding)
SYMBOL_ARROW_R = "→"    # U+2192 - Right arrow
SYMBOL_ARROW_L = "←"    # U+2190 - Left arrow

# --- UI Constants ---
DIVIDER_WIDTH = 40      # Total width for step divider titles


@dataclass
class Config:
    """Stores application configuration."""

    adb_path: Optional[Path] = None
    monaserver_path: Optional[Path] = None
    obs_path: Optional[Path] = None
    package_name: str = DEFAULT_CONFIG["Device"]["PackageName"]
    rtmp_port: str = DEFAULT_CONFIG["Network"]["RtmpPort"]
    auto_start_monaserver: bool = True
    auto_select_single_device: bool = True
    fetch_device_models: bool = True
    force_kill_port_process: bool = True
    devices: List[Dict[str, str]] = field(default_factory=list)


custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "yellow",
        "danger": "bold red",
        "success": "bold green",
        "error": "red",
        "rtmp": "bold magenta",
        "highlight": "bold blue",
        "header": "white on blue",
        "command": "green on black",
        "dimmed": "dim",
        "process": "italic magenta",
    }
)
console = Console(theme=custom_theme, highlight=True)

# --- Original ASCII Logo ---
LOGO = r"""
┌───────────────────────────────────────────────────────────┐
│                                                           │
│  ██████╗ ████████╗███╗   ███╗██████╗                      │
│  ██╔══██╗╚══██╔══╝████╗ ████║██╔══██╗                     │
│  ██████╔╝   ██║   ██╔████╔██║██████╔╝                     │
│  ██╔══██╗   ██║   ██║╚██╔╝██║██╔═══╝                      │
│  ██║  ██║   ██║   ██║ ╚═╝ ██║██║                          │
│  ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝                          │
│                                                           │
│  ███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗     │
│  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║     │
│  ███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║     │
│  ╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║     │
│  ███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║     │
│  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     │
│                                                           │
└───────────────────────────────────────────────────────────┘
"""

# --- Helper Functions ---
_tk_root = None


def _get_tk_root():
    global _tk_root
    if not TKINTER_AVAILABLE or not TK:
        return None
    if _tk_root is None or not _tk_root.winfo_exists():
        _tk_root = TK.Tk()
        _tk_root.withdraw()
    return _tk_root


def open_generic_file_dialog(
    title: str,
    dialog_type: str,
    initial_dir: Optional[str] = None,
    filetypes: Optional[list] = None,
) -> Optional[str]:
    root = _get_tk_root()
    if not root or not FILEDIALOG:
        console.print("[warning]Tkinter dialogs not available.[/warning]")
        return None
    try:
        root.attributes("-topmost", True)
        path_result = None
        if dialog_type == "folder":
            path_result = FILEDIALOG.askdirectory(
                parent=root, title=title, initialdir=initial_dir
            )
        elif dialog_type == "file":
            path_result = FILEDIALOG.askopenfilename(
                parent=root,
                title=title,
                initialdir=initial_dir,
                filetypes=filetypes or [("All files", "*.*")],
            )
        return path_result if path_result else None
    except Exception as e:
        console.print(f"[warning]Tkinter dialog error: {e}[/warning]")
        return None


def open_folder_browser(
    title="Select Folder", initial_dir: Optional[str] = None
) -> Optional[str]:
    return open_generic_file_dialog(title, "folder", initial_dir=initial_dir)


def open_file_browser(
    title="Select File", initial_dir: Optional[str] = None, filetypes=None
) -> Optional[str]:
    return open_generic_file_dialog(
        title, "file", initial_dir=initial_dir, filetypes=filetypes
    )


def validate_path(
    path_to_check: Path, type_hint: str, is_windows: bool
) -> Optional[Path]:
    """Validates a path object based on its expected type."""
    if type_hint == "adb_folder_win":
        adb_exe = path_to_check / "adb.exe"
        if adb_exe.is_file():
            return adb_exe.resolve()
        console.print(f"[danger]'adb.exe' not found in '{path_to_check}'.[/danger]")
    elif type_hint == "adb_file":  # Non-windows direct adb executable
        if path_to_check.is_file() and "adb" in path_to_check.name.lower():
            return path_to_check.resolve()
        console.print(
            f"[danger]'{path_to_check}' is not a valid ADB executable.[/danger]"
        )
    elif type_hint in ["mona", "obs", "file"]:  # General file
        if path_to_check.is_file():
            if type_hint == "mona" and "monaserver" not in path_to_check.name.lower():
                if not Confirm.ask(
                    f"'{path_to_check}' doesn't look like MonaServer. Use anyway?"
                ):
                    return None  # User rejected
            return path_to_check.resolve()
        console.print(f"[danger]Path '{path_to_check}' is not a valid file.[/danger]")
    return None


def get_path_interactively(
    prompt_message: str,
    default_suggestion: Optional[str],
    path_type_hint: str,
    dialog_title: str,
    dialog_filetypes: Optional[list] = None,
) -> Optional[Path]:
    is_windows = platform.system() == "Windows"
    while True:
        path_str_input: Optional[str] = None
        browse = " or type 'browse'" if TKINTER_AVAILABLE else ""
        default_disp = (
            f" (Enter for default: {default_suggestion})" if default_suggestion else ""
        )
        user_input_raw = Prompt.ask(f"{prompt_message}{default_disp}{browse}")

        if user_input_raw.lower() == "browse" and TKINTER_AVAILABLE:
            initial_dir_browse: Optional[str] = None
            if default_suggestion and Path(default_suggestion).exists():
                p_default = Path(default_suggestion)
                initial_dir_browse = str(
                    p_default.parent if p_default.is_file() else p_default
                )

            if path_type_hint == "adb_folder_win":
                path_str_input = open_folder_browser(
                    title=dialog_title, initial_dir=initial_dir_browse
                )
            else:
                path_str_input = open_file_browser(
                    title=dialog_title,
                    initial_dir=initial_dir_browse,
                    filetypes=dialog_filetypes,
                )

            if not path_str_input:
                console.print(
                    "[warning]No path selected. Try again or enter manually.[/warning]"
                )
                continue
        elif not user_input_raw.strip() and default_suggestion:
            path_str_input = default_suggestion
        elif user_input_raw.strip():
            path_str_input = user_input_raw.strip()
        elif not default_suggestion:
            if path_type_hint == "obs" and Confirm.ask(
                "Skip OBS config?", default=True
            ):
                return None
            console.print("[warning]Path cannot be empty.[/warning]")
            continue

        if not path_str_input:
            if path_type_hint == "obs":
                return None
            console.print("[warning]No path provided. Please try again.[/warning]")
            continue

        validated_p = validate_path(Path(path_str_input), path_type_hint, is_windows)
        if validated_p:
            return validated_p


def load_config() -> Config:
    app_config = Config()
    parser = configparser.ConfigParser()
    first_run = not CONFIG_FILE.exists()
    config_updated_in_session = False
    is_windows = platform.system() == "Windows"

    path_definitions = {
        "AdbPath": {
            "attr": "adb_path",
            "prompt": "ADB "
            + ("platform-tools folder" if is_windows else "executable"),
            "type": "adb_folder_win" if is_windows else "adb_file",
            "default_sugg_func": lambda: DEFAULT_ADB_PATH_WIN
            if is_windows
            else shutil.which("adb"),
            "dialog_ft": [
                ("ADB Executable", "adb.exe" if is_windows else "adb"),
                ("All files", "*.*"),
            ],
            "critical": True,
        },
        "MonaServerPath": {
            "attr": "monaserver_path",
            "prompt": "MonaServer executable",
            "type": "mona",
            "default_sugg_func": lambda: str(
                SCRIPT_DIR
                / f"MonaServer_{'Win64' if is_windows else 'Linux'}"
                / f"MonaServer{'.exe' if is_windows else ''}"
            ),
            "dialog_ft": [
                ("MonaServer", f"MonaServer{'.exe' if is_windows else ''}"),
                ("All files", "*.*"),
            ],
            "critical": True,
        },
        "ObsPath": {
            "attr": "obs_path",
            "prompt": "OBS executable (optional)",
            "type": "obs",
            "default_sugg_func": lambda: DEFAULT_OBS_PATH_WIN
            if is_windows and Path(DEFAULT_OBS_PATH_WIN).exists()
            else None,
            "dialog_ft": [
                ("OBS", "obs64.exe" if is_windows else "obs"),
                ("All files", "*.*"),
            ],
            "critical": False,
        },
    }

    if first_run:
        console.print(
            f"[warning]'{CONFIG_FILE.name}' not found. Starting interactive setup.[/warning]"
        )
        parser.read_dict(DEFAULT_CONFIG)
        console.print(
            Panel(
                "[bold yellow]First-Time Setup: Paths[/]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

        for key, details in path_definitions.items():
            default_val = details["default_sugg_func"]()
            resolved_path = get_path_interactively(
                details["prompt"],
                default_val,
                details["type"],
                f"Select {details['prompt']}",
                details["dialog_ft"],
            )
            if details["critical"] and not resolved_path:
                exit_with_error(f"{details['prompt']} is crucial and was not set.")
            setattr(app_config, details["attr"], resolved_path)
            parser["Paths"][key] = str(resolved_path) if resolved_path else ""
            config_updated_in_session = True
    else:
        parser.read(CONFIG_FILE, encoding="utf-8")
        console.print(f"[info]Loaded configuration from '{CONFIG_FILE.name}'[/info]")

        for key, details in path_definitions.items():
            path_str_from_config = parser.get("Paths", key, fallback="")
            path_obj: Optional[Path] = None

            if path_str_from_config:
                validation_type_hint = (
                    "adb_file" if key == "AdbPath" else details["type"]
                )
                path_obj = validate_path(
                    Path(path_str_from_config), validation_type_hint, is_windows
                )

            if path_obj:
                setattr(app_config, details["attr"], path_obj)
            else:
                setattr(app_config, details["attr"], None)
                if details["critical"]:
                    console.print(
                        f"[warning]Configured {details['prompt']} ('{path_str_from_config or 'empty'}') is invalid or missing. Please correct it.[/warning]"
                    )
                    default_val = details["default_sugg_func"]()
                    new_p = get_path_interactively(
                        details["prompt"],
                        default_val,
                        details["type"],
                        f"Select {details['prompt']}",
                        details["dialog_ft"],
                    )
                    if not new_p:
                        exit_with_error(
                            f"{details['prompt']} is crucial and was not set."
                        )
                    setattr(app_config, details["attr"], new_p)
                    parser.set("Paths", key, str(new_p))
                    config_updated_in_session = True
                elif key == "ObsPath" and path_str_from_config:
                    console.print(
                        f"[info]Optional OBS path ('{path_str_from_config}') invalid. Clearing.[/info]"
                    )
                    parser.set("Paths", key, "")
                    config_updated_in_session = True

    app_config.package_name = parser.get(
        "Device", "PackageName", fallback=DEFAULT_CONFIG["Device"]["PackageName"]
    )
    app_config.rtmp_port = parser.get(
        "Network", "RtmpPort", fallback=DEFAULT_CONFIG["Network"]["RtmpPort"]
    )
    app_config.auto_select_single_device = parser.getboolean(
        "Options", "AutoSelectSingleDevice", fallback=True
    )
    app_config.fetch_device_models = parser.getboolean(
        "Options", "FetchDeviceModels", fallback=True
    )
    app_config.force_kill_port_process = parser.getboolean(
        "Options",
        "ForceKillConflictingPortProcess",
        fallback=app_config.force_kill_port_process,
    )

    if config_updated_in_session:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                parser.write(f)
            console.print(
                f"[success]{SYMBOL_CHECK} Configuration saved/updated in {CONFIG_FILE}.[/success]"
            )
        except IOError as e:
            console.print(f"[danger]Error saving config updates: {e}[/danger]")

    return app_config


def find_adb(config_path_str: Optional[str]) -> Optional[str]:
    adb_executable_name = "adb.exe" if platform.system() == "Windows" else "adb"
    if config_path_str:
        config_path = Path(config_path_str)
        if (
            config_path.exists()
            and config_path.is_file()
            and "adb" in config_path.name.lower()
        ):
            return str(config_path.resolve())
    adb_from_path = shutil.which(adb_executable_name)
    if adb_from_path:
        return adb_from_path
    return None


def check_adb_version(current_config: Config) -> Tuple[bool, str]:
    if not current_config.adb_path:
        return False, "ADB path not set"
    try:
        result = subprocess.run(
            [str(current_config.adb_path), "version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if (
            result.returncode == 0
            and result.stdout
            and (match := re.search(r"Version\s+(\d+\.\d+\.\d+)", result.stdout))
        ):
            return True, match.group(1)
        return False, result.stderr.strip() or "No version output"
    except Exception as e:
        return False, f"Execution error: {e}"


def get_device_model(model_config: Config, device_id: str) -> str:
    if not model_config.fetch_device_models or not model_config.adb_path:
        return "Unknown"
    adb, cmds = (
        str(model_config.adb_path),
        {
            "model": ["shell", "getprop", "ro.product.model"],
            "mfg": ["shell", "getprop", "ro.product.manufacturer"],
        },
    )
    try:
        res_model = subprocess.run(
            [adb, "-s", device_id] + cmds["model"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        model = res_model.stdout.strip() if res_model.returncode == 0 else ""
        if model:
            return model
        res_mfg = subprocess.run(
            [adb, "-s", device_id] + cmds["mfg"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        mfg = res_mfg.stdout.strip() if res_mfg.returncode == 0 else ""
        return f"{mfg} (Model N/A)" if mfg else "Unknown"
    except subprocess.TimeoutExpired:
        return "Unknown (Timeout)"
    except Exception:
        return "Unknown (Error)"


def find_connected_devices(current_config: Config) -> List[Dict[str, str]]:
    if not current_config.adb_path:
        return []
    console.print("[info]Scanning for connected devices...")
    try:
        result = subprocess.run(
            [str(current_config.adb_path), "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except Exception as e:
        console.print(f"[danger]'adb devices' error: {e}[/danger]")
        return []

    devices_found: List[Dict[str, str]] = []
    pattern = re.compile(r"^([\w.\-:]+)\s+(device|offline|unauthorized)(?:\s+(.*))?$")
    lines = result.stdout.strip().splitlines()
    if len(lines) <= 1:
        return []

    active_matches = [
        m
        for line in lines[1:]
        if (m := pattern.match(line.strip())) and m.group(2) == "device"
    ]

    if current_config.fetch_device_models and active_matches:
        with Progress(
            SpinnerColumn(style="highlight"),
            TextColumn("Fetching models... {task.completed}/{task.total}"),
            transient=True,
        ) as p:
            task = p.add_task("Models", total=len(active_matches))
            for line in lines[1:]:
                if match := pattern.match(line.strip()):
                    is_active = match.group(2) == "device"
                    devices_found.append(
                        parse_device_line(
                            current_config,
                            match,
                            p if is_active else None,
                            task if is_active else None,
                        )
                    )
    else:
        for line in lines[1:]:
            if match := pattern.match(line.strip()):
                devices_found.append(parse_device_line(current_config, match))
    return devices_found


def parse_device_line(
    p_config: Config, match: re.Match, progress=None, task_id=None
) -> Dict[str, str]:
    did, stat, det = match.groups()
    info = {"id": did, "status": stat, "details": det or ""}
    if "_adb-tls-connect" in did:
        conn, icon = ("Wi-Fi", "📶")
    else:
        conn, icon = (
            ("Wi-Fi", "📶")
            if ":" in did and all(c in "0123456789." for c in did.split(":")[0])
            else (("Emulator", "💻") if "emulator" in did else ("USB", "🔌"))
        )
    info.update({"connection": conn, "icon": icon})
    if stat == "device":
        info["name"] = (
            get_device_model(p_config, did)
            if p_config.fetch_device_models
            else "Unknown"
        )
        if progress and task_id:
            progress.update(task_id, advance=1)
    else:
        info["name"] = f"({stat.capitalize()})"
    return info


def select_device_from_list(current_config: Config) -> Optional[Dict[str, str]]:
    devices, sel = (
        current_config.devices,
        [d for d in current_config.devices if d["status"] == "device"],
    )
    if not devices:
        console.print(
            Panel(
                "[warning]No devices found.[/warning]",
                title="[danger]No Devices[/danger]",
            )
        )
        return None

    tbl = Table(
        title="Detected Devices",
        box=ROUNDED,
        border_style="blue",
        header_style="header",
        padding=(0, 1),
    )
    for name, style, width in [
        ("#", "dim", 3),
        ("Device", "bold cyan", 25),
        ("Status", "magenta", 12),
        ("Conn.", "green", 7),
        ("ID/IP", "dim", 20),
    ]:
        tbl.add_column(name, style=style, min_width=width)
    for i, d in enumerate(devices):
        is_s = d["status"] == "device"
        s_style = (
            "success"
            if is_s
            else ("warning" if d["status"] == "unauthorized" else "error")
        )
        tbl.add_row(
            f"{i + 1}" if is_s else "-",
            f"{d['icon']} {d['name']}",
            f"[{s_style}]{d['status'].capitalize()}[/]",
            d["connection"],
            d["id"],
        )
    console.print(tbl)

    if not sel:
        msgs = (
            ["[danger]No operational devices.[/danger]"]
            + (
                ["[warning]Check auth prompt.[/warning]"]
                if any(d["status"] == "unauthorized" for d in devices)
                else []
            )
            + (
                ["[warning]Reconnect offline device.[/warning]"]
                if any(d["status"] == "offline" for d in devices)
                else []
            )
        )
        console.print(Panel("\n".join(msgs), title="[danger]Selection Error[/danger]"))
        return None

    if len(sel) == 1 and current_config.auto_select_single_device:
        d = sel[0]
        console.print(
            f"[success]{SYMBOL_CHECK} Auto-selecting: [bold]{d['icon']} {d['name']}[/bold]"
        )
        return d

    console.print("[info]Multiple devices. Select one:[/info]")
    choices, cmap = (
        [str(i + 1) for i in range(len(sel))],
        {str(i + 1): dev for i, dev in enumerate(sel)},
    )
    for i, d in enumerate(sel):
        console.print(
            f" [highlight][{i + 1}] [/]{d['icon']} {d['name']} ({d['connection']}) [dim]{d['id']}[/]"
        )
    try:
        s = Prompt.ask("Enter selection", choices=choices, show_choices=False)
        d = cmap[s]
        console.print(f"[success]{SYMBOL_CHECK} Selected: [bold]{d['icon']} {d['name']}[/bold]")
        return d
    except KeyboardInterrupt:
        console.print("\n[warning]Cancelled.[/warning]")
        sys.exit(0)
    return None


def find_process_using_port(port: int) -> Optional[Tuple[int, str]]:
    if not 0 < port <= 65535:
        return None
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.laddr.port == port and c.status == psutil.CONN_LISTEN:
                try:
                    p = psutil.Process(c.pid)
                    return c.pid, p.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except (psutil.Error, OSError, AttributeError):
        # Handle psutil errors, network errors, or attribute access issues
        pass
    return None


def kill_process_by_pid(pid: int, name: str = "process") -> bool:
    if (
        pid == 0 and platform.system() == "Windows"
    ):  # PID 0 is System Idle Process on Windows
        console.print("[error]Cannot kill PID 0 (System Idle Process).[/error]")
        return False
    try:
        p = psutil.Process(pid)
        console.print(f"[info]Killing {name} (PID:{pid})...[/info]")
        p.kill()
        try:
            p.wait(timeout=1)
        except psutil.TimeoutExpired:
            console.print(f"[warning]{name} (PID:{pid}) linger.[/warning]")
        console.print(f"[success]Kill signal sent to {name} (PID:{pid}).[/success]")
        return True
    except psutil.NoSuchProcess:
        console.print(f"[warning]{name} (PID:{pid}) gone.[/warning]")
        return True
    except Exception as e:
        console.print(f"[danger]Kill error {name} (PID:{pid}): {e}[/danger]")
        return False


def handle_port_conflict(port_str: str, p_config: Config) -> Tuple[bool, Optional[int]]:
    try:
        port = int(port_str)
        assert 0 < port <= 65535
    except (ValueError, AssertionError):
        console.print(f"[danger]Invalid port: {port_str}. Using 1935.[/danger]")
        port = 1935
    console.print(f"[info]Checking port TCP:{port}...[/info]")
    info = find_process_using_port(port)
    if info:
        pid, name = info
        console.print(
            f"[warning]{SYMBOL_WARNING} Port TCP:{port} in use by {name} (PID:{pid}).[/warning]"
        )
        if p_config.force_kill_port_process or Confirm.ask(
            f"Kill {name} (PID:{pid})?", choices=["y", "n"], default="y"
        ):
            killed = kill_process_by_pid(pid, name)
            if killed:
                console.print(f"[success]{SYMBOL_CHECK} Port {port} freed.[/success]")
                # Short delay to allow OS to fully release the port
                time.sleep(0.5)
            return killed, None if killed else pid
        elif Confirm.ask("Skip port conflict?", choices=["y", "n"], default="n"):
            console.print("[warning]Skipping. Streaming may fail.[/warning]")
            return False, pid
        else:
            exit_with_error(f"Port {port} conflict unresolved.")
    return True, None


def setup_port_forwarding(config: Config, device_info: Dict[str, str]) -> bool:
    """Set up ADB reverse port forwarding from device to host."""
    if not config.adb_path:
        return False
    device_id, port = device_info["id"], config.rtmp_port
    console.print(f"[info]Port forwarding (Dev:{port} {SYMBOL_ARROW_LR} Host:{port})...[/info]")
    cmd = [str(config.adb_path), "-s", device_id, "reverse", f"tcp:{port}", f"tcp:{port}"]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5, check=False
        )
    except Exception as e:
        console.print(f"[danger]ADB reverse error: {e}[/danger]")
        return False
    if res.returncode == 0:
        console.print(
            Text.assemble(
                (f"{SYMBOL_CHECK} Port Fwd: ", "success"),
                (f"Dev TCP:{port} {SYMBOL_ARROW_LR} Host TCP:{port}", "cyan"),
            )
        )
        return True
    console.print(
        f"[danger]Port fwd failed. ADB: {res.stderr.strip() or res.stdout.strip()}[/danger]"
    )
    return False


def launch_app(config: Config, device_info: Dict[str, str]) -> bool:
    """Launch the streaming app on the Android device."""
    if not config.adb_path:
        return False
    device_id, pkg = device_info["id"], config.package_name
    if not pkg or "/" not in pkg:
        console.print(f"[danger]Invalid PkgName: {pkg}[/danger]")
        return False
    app_s = pkg.split("/")[0]
    console.print(f"[info]Launching app [highlight]{app_s}[/highlight]...")
    cmd = [str(config.adb_path), "-s", device_id, "shell", "am", "start", "-n", pkg]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
    except Exception as e:
        console.print(f"[danger]App launch error: {e}[/danger]")
        return False
    out = (res.stdout + res.stderr).lower()
    if res.returncode == 0 and "error" not in out and "exception" not in out:
        console.print(f"{SYMBOL_CHECK} App Launch: Sent cmd for {app_s}.")
        time.sleep(0.5)
        return True
    if "permission denial" in out:
        console.print(f"[warning]{SYMBOL_WARNING} Permission denied launching app.[/warning]")
    elif "not found" in out or "unable to resolve" in out:
        console.print(f"[warning]{SYMBOL_WARNING} App {app_s} not found.[/warning]")
    else:
        console.print(f"[warning]{SYMBOL_WARNING} Unknown error launching app.[/warning]")
    if res.stdout.strip():
        console.print(f"[dim]Out: {res.stdout.strip()}[/dim]")
    if res.stderr.strip():
        console.print(f"[dim]Err: {res.stderr.strip()}[/dim]")
    return False


def copy_to_clipboard(c_config: Config):
    url = f"rtmp://127.0.0.1:{c_config.rtmp_port}/live"
    try:
        pyperclip.copy(url)
        console.print(
            Text.assemble(
                (f"{SYMBOL_CHECK} RTMP URL: ", "success"), (url, "rtmp"), (" (Copied)", "dimmed")
            )
        )
    except Exception as e:
        console.print(f"[danger]Clipboard Error: {e}\n[info]URL: [rtmp]{url}[/rtmp]")


def check_monaserver_process() -> bool:
    mona_exe_name_base = "MonaServer"
    mona_exe = f"{mona_exe_name_base}{'.exe' if platform.system() == 'Windows' else ''}".lower()
    try:
        for p in psutil.process_iter(["name", "exe", "cmdline"]):
            try:
                p_name = (p.info.get("name") or "").lower()
                p_exe = (
                    Path(p.info.get("exe") or "").name
                ).lower()  # Get just filename from exe path

                if mona_exe == p_name or mona_exe == p_exe:
                    return True
                # Fallback to checking command line arguments if name/exe is not specific enough
                if p.info.get("cmdline"):
                    if any(
                        mona_exe_name_base.lower() in arg.lower()
                        for arg in p.info["cmdline"]
                    ):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue  # Ignore processes that ended or we can't access
            except Exception:  # Catch other potential errors with process info
                continue
    except Exception:  # Catch errors during process iteration
        pass
    return False


def start_mona_server(config: Config) -> Optional[bool]:
    """Start the MonaServer RTMP server."""
    if check_monaserver_process():
        console.print(f"[success]{SYMBOL_CHECK} MonaServer already running.[/success]")
        return True
    if not config.monaserver_path or not config.monaserver_path.is_file():
        console.print(
            f"[danger]MonaServer path ('{config.monaserver_path}') is not set or invalid.[/danger]"
        )
        return False

    # Port conflict for MonaServer's port should ideally be checked *before* trying to start it.
    # This is done in the main block. If it was resolved by killing,
    # there's a small chance another app took it. Re-checking here is safer.
    port_clear, conflicting_pid = handle_port_conflict(config.rtmp_port, config)
    if not port_clear:
        console.print(
            f"[danger]MonaServer: Port TCP:{config.rtmp_port} conflict (PID {conflicting_pid}). Cannot start.[/danger]"
        )
        return False

    console.print(
        f"[info]Starting MonaServer: [dimmed]{config.monaserver_path}[/dimmed]"
    )
    try:
        # Remove creationflags to inherit console/run in background without new window
        # FIX: Redirect stdin to DEVNULL to prevent MonaServer from consuming
        # the "Enter" key pressed to exit the script.
        # stdout and stderr are inherited by default, so its output will still appear.
        subprocess.Popen(
            [str(config.monaserver_path)],
            cwd=str(config.monaserver_path.parent),
            stdin=subprocess.DEVNULL,  # MODIFIED LINE
        )
        console.print(
            f"[success]{SYMBOL_CHECK} MonaServer start command issued. Output should appear below (if any).[/success]"
        )
        time.sleep(
            1.5
        )  # Give MonaServer time to start and potentially print initial logs

        # Verify if the process actually started and is running
        if not check_monaserver_process():
            # Check port again, as MonaServer might have failed to bind
            _, still_conflicting_pid = handle_port_conflict(
                config.rtmp_port, config
            )  # Check if port is now taken by Mona
            if still_conflicting_pid is None and not find_process_using_port(
                int(config.rtmp_port)
            ):  # Port is free
                console.print(
                    "[warning]MonaServer launched, but status check failed and port is not taken. Verify manually.[/warning]"
                )
            elif (
                find_process_using_port(int(config.rtmp_port))
                and not check_monaserver_process()
            ):  # Port taken but not by Mona
                console.print(
                    f"[warning]MonaServer launched, but status check failed. Port TCP:{config.rtmp_port} might be taken by another process. Verify manually.[/warning]"
                )
            else:  # Port taken by Mona, but check_monaserver_process failed (should not happen if port is taken by Mona)
                console.print(
                    "[warning]MonaServer launched, but status check failed. Verify manually.[/warning]"
                )
            return None  # Unconfirmed status
        return True  # Successfully started
    except Exception as e:
        console.print(f"[danger]MonaServer start failed: {e}[/danger]")
        return False


def step_divider(emoji: str, title: str):
    """Print a visual step divider with emoji and title."""
    left_dashes = 5
    # Calculate remaining space for right dashes, accounting for emoji and spaces
    right_dashes = max(0, DIVIDER_WIDTH - len(title) - left_dashes)
    console.print(
        f"[dim]{'─' * left_dashes}[/dim] {emoji} [bold cyan]{title}[/bold cyan] [dim]{'─' * right_dashes}[/dim]"
    )


def exit_with_error(message: str):
    console.print(
        f"\n[danger]ERROR: {message}[/danger]\n[italic]Press Enter to exit...[/italic]"
    )
    input()
    sys.exit(1)


# --- Main Execution ---
if __name__ == "__main__":
    console.print(LOGO)  # Use the original multi-line logo
    console.print(
        Panel(
            "[white]RTMP Stream Setup Assistant[/]",
            box=ROUNDED,
            border_style="blue",
            padding=(0, 1),
            expand=False,
        )
    )
    results = {
        "Port Conflict Resolved": None,  # True if resolved, False if user skipped, None if no conflict
        "Port Forwarding": False,
        "App Launch": False,
        "RTMP URL Copied": False,
        "MonaServer": None,  # True if started, False if failed, None if unconfirmed/already running
    }
    conflicting_pid_at_start: Optional[int] = None

    step_divider("⚙️", "Configuration")
    config = load_config()

    # Initial port check for MonaServer's intended port before trying to start it
    # This is now also handled inside start_mona_server for robustness,
    # but doing it early helps inform the user.
    results["Port Conflict Resolved"], conflicting_pid_at_start = handle_port_conflict(
        config.rtmp_port, config
    )
    if not results["Port Conflict Resolved"] and conflicting_pid_at_start is not None:
        # This means user chose to skip resolving the conflict or kill failed
        console.print(
            f"[warning]Port TCP:{config.rtmp_port} conflict (PID {conflicting_pid_at_start}) was not resolved. MonaServer might fail to start or bind.[/warning]"
        )
        # We allow proceeding as start_mona_server will re-check.

    step_divider("🔍", "ADB Verification")
    adb_ok, adb_version = check_adb_version(config)
    if not adb_ok:
        exit_with_error(f"ADB check failed: {adb_version}")

    step_divider("📱", "Device Selection")
    config.devices = find_connected_devices(config)
    selected_device = select_device_from_list(config)
    if not selected_device:
        exit_with_error("No device selected.")

    step_divider("🚀", "Setup Execution")
    results["Port Forwarding"] = setup_port_forwarding(config, selected_device)
    if not results["Port Forwarding"]:
        if not Confirm.ask("Port forwarding failed. Continue anyway?", default=False):
            exit_with_error("Aborted: port forwarding failure.")
    results["App Launch"] = launch_app(config, selected_device)
    copy_to_clipboard(config)
    results["RTMP URL Copied"] = True

    if config.auto_start_monaserver:
        results["MonaServer"] = start_mona_server(config)
    else:
        console.print("[info]Auto-start MonaServer is disabled in config.[/info]")
        if check_monaserver_process():
            console.print(
                "[info]MonaServer is already running (checked manually).[/info]"
            )
            results["MonaServer"] = True  # Treat as OK if running
        else:
            results["MonaServer"] = (
                None  # Not started by script, status unknown unless user starts it
            )

    step_divider("📊", "Summary")
    summary = Table(
        box=ROUNDED,
        border_style="green",
        show_header=False,
        padding=(0, 1),
        expand=False,
    )
    summary.add_column("Item", style="bold")
    summary.add_column("Status")
    summary.add_column("Details")

    def add_s(item, flag, det="", ok="OK", fail="FAIL", warn="WARN", na="N/A"):
        smap = {True: ("success", ok), False: ("danger", fail), None: ("dimmed", na)}
        style, txt = smap.get(flag, ("error", "ERR"))

        # Special handling for Host Port status based on initial check
        if item == "Host Port":
            if flag is True:  # No conflict initially, or resolved
                style, txt = "success", ok
            elif (
                flag is False and conflicting_pid_at_start is not None
            ):  # User skipped or kill failed
                style, txt = "warning", warn
            # If flag is None (no conflict initially), it's handled by smap

        summary.add_row(item, f"[{style}]{txt}[/]", det)

    add_s("ADB", adb_ok, f"v{adb_version} @ [dim]{config.adb_path}[/dim]")
    add_s(
        "Device",
        True,  # Device selection must succeed to reach here
        f"{selected_device['icon']} {selected_device['name']} ({selected_device['connection']})",
        ok="Selected",
    )

    host_port_details = f"Host TCP:{config.rtmp_port}"
    if not results["Port Conflict Resolved"] and conflicting_pid_at_start is not None:
        host_port_details += (
            f" (Initial conflict PID:{conflicting_pid_at_start} unresolved)"
        )
    elif (
        results["Port Conflict Resolved"] is False and conflicting_pid_at_start is None
    ):  # Should not happen, means handle_port_conflict logic error
        host_port_details += " (Conflict status unclear)"

    add_s(
        "Host Port",
        results["Port Conflict Resolved"],  # Reflects initial check outcome
        host_port_details,
        ok="Clear/Resolved",  # OK if no conflict or resolved
        fail="CONFLICT",  # Should not be 'FAIL' if user skipped
        warn="UNRESOLVED",  # If user chose not to resolve
        na="No Conflict",  # If None (no conflict initially)
    )
    add_s(
        "Port Forward",
        results["Port Forwarding"],
        f"Device:{config.rtmp_port} {SYMBOL_ARROW_LR} Host:{config.rtmp_port}",
    )
    add_s(
        "App Launch",
        results["App Launch"],
        f"[dim]{config.package_name.split('/', 1)[0]}[/dim]",
        fail="FAIL/Skip",
    )
    rtmp_url = f"rtmp://127.0.0.1:{config.rtmp_port}/live"
    add_s(
        "RTMP URL",
        results["RTMP URL Copied"],
        f"[rtmp]{rtmp_url}[/rtmp] (Copied)",
        ok="Copied",
    )

    mona_status_text = "Not Started (auto-start off)"
    if config.auto_start_monaserver:
        if results["MonaServer"] is True:
            mona_status_text = "Running/Started"
        elif results["MonaServer"] is False:
            mona_status_text = "Failed to Start"
        elif results["MonaServer"] is None:  # Unconfirmed
            mona_status_text = "Start Attempted (Unconfirmed)"
    elif results["MonaServer"] is True:  # Auto-start off, but was already running
        mona_status_text = "Already Running"

    add_s(
        "MonaServer",
        results["MonaServer"],
        mona_status_text,
        ok="OK/Started",
        fail="FAIL",
        na="Unknown/Not Started",  # For None or if auto_start_monaserver is false and not running
    )
    console.print(summary)

    final_instr = [
        f"[success]{SYMBOL_CHECK} Setup Complete.[/success] RTMP URL: [rtmp]{rtmp_url}[/rtmp]"
    ]
    if not results["Port Conflict Resolved"] and conflicting_pid_at_start is not None:
        final_instr.append(
            f"[warning]{SYMBOL_WARNING} Port TCP:{config.rtmp_port} conflict (PID {conflicting_pid_at_start}) may affect MonaServer.[/warning]"
        )
    if not results["App Launch"]:
        final_instr.append(
            f"[warning]{SYMBOL_WARNING} App ({config.package_name.split('/', 1)[0]}) launch issue.[/warning]"
        )

    if results["MonaServer"] is True:
        final_instr.append(
            f"[success]{SYMBOL_CHECK} MonaServer should be running.[/success]\n[info]MonaServer output may appear in this console window.[/info]"
        )
    elif results["MonaServer"] is False:
        final_instr.append(f"[danger]{SYMBOL_CROSS} MonaServer failed to start.[/danger]")
    elif results["MonaServer"] is None and config.auto_start_monaserver:
        final_instr.append(
            f"[warning]{SYMBOL_WARNING} MonaServer start was attempted, status unconfirmed. Check console output and port.[/warning]"
        )
    elif results["MonaServer"] is None and not config.auto_start_monaserver:
        final_instr.append(
            "[info]MonaServer auto-start is off. Ensure it's running if needed.[/info]"
        )

    if config.obs_path and config.obs_path.exists():
        final_instr.append(
            f"[info]Launch OBS: [dimmed]{config.obs_path}[/dimmed][/info]"
        )
    final_instr.append("\n[info]Connect streaming software to the RTMP URL.[/info]")
    console.print(
        Panel(
            "\n".join(final_instr),
            title="Next Steps",
            border_style="blue",
            expand=False,
            padding=(0, 1),
        )
    )

    console.print("\n[italic]Press Enter to exit...[/italic]")
    try:
        input()
    except KeyboardInterrupt:
        console.print("\nExiting.")
    finally:
        if _tk_root and _tk_root.winfo_exists():
            _tk_root.destroy()
    sys.exit(0)
