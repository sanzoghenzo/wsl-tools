"""wsl-tools - hany classes for Windows Subsystem for Linux management."""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import time
from collections import UserDict
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence

from cached_property import cached_property
from xdg.DesktopEntry import DesktopEntry

WSL_EXE = "wsl.exe"


@dataclass
class WSLApp:
    """WSL Application."""

    name: str
    generic_name: str
    cmd: str
    gui: bool
    ico: Optional[str] = None

    # distro: WSLDistro

    @classmethod
    def from_dotdesktop(cls, app_def: Path) -> Optional["WSLApp"]:
        """Return a WSLApp from a .desktop file."""
        # TODO: handle symlinks... need to run commands inside WSL
        de = DesktopEntry(app_def)
        name = de.getName()
        generic_name = de.getGenericName()
        cmd = de.getExec()
        gui = not de.getTerminal()
        icon = de.getIcon()
        if name:
            return cls(name, generic_name, cmd, gui, icon)
        return None


@dataclass
class WSLDistro:
    """WSL distribution handler."""

    name: str
    version: int

    # manager: WSLManager = None

    def __str__(self) -> str:
        """Friendlier WSL name."""
        return self.name.replace("-", " ").capitalize()

    @cached_property
    def shell(self) -> str:
        """Default user shell path."""
        home = str(self.home_path)
        with open(self.root_unc_path / "etc" / "passwd") as passwd:
            line = next(itm for itm in passwd.readlines() if home in itm)
            return line.split(":")[-1].strip()

    @cached_property
    def _cmd_base(self) -> str:
        """Base command for launching programs in the WSL distro."""
        return f"{WSL_EXE} ~ -d {self.name}"

    def run_command(
        self,
        command: str,
        load_profile: bool = False,
        background: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Run a bash command in the distro.

        Args:
            command: command to run in the WSL distro.
            load_profile: load .profile before running the command.
            background: run the process in the background using Popen.
            kwargs: arguments to pass to the subprocess function.

        Returns:
            The result of the subprocess call.
        """
        login = "l" if load_profile else ""
        command = f"sh -c{login} '{command}'"
        run = subprocess.Popen if background else subprocess.run
        return run(f"{self._cmd_base} {command}", **kwargs)

    def get_cmd_output(self, cmd: str, **kwargs: Any) -> str:
        """
        Return the text output of a command run in the distro.

        Args:
            cmd: commmand to run in the WSL distro.
            kwargs: arguments to pass to subprocess.run

        Returns:
            command output.
        """
        run = self.run_command(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            background=False,
            **kwargs,
        )
        return run.stdout

    def _unc_path_from_cmd(self, unix_path: str) -> Path:
        return Path(
            self.get_cmd_output(f"wslpath -w `realpath {unix_path}`").strip()
        )

    def read_file(self, path: str) -> str:
        """Read the content of the file."""
        return self._unc_path_from_cmd(path).read_text()

    @cached_property
    def ip(self) -> str:
        """Return the IP assigned to this distro."""
        for line in self.read_file("/etc/resolv.conf").splitlines():
            if "nameserver" in line:
                return line.split()[1]
        raise ValueError("Cannot find ip in /etc/resolv.conf")

    @cached_property
    def root_unc_path(self) -> Path:
        """UNC path of the root."""
        return self._unc_path_from_cmd("/")

    @cached_property
    def home_unc_path(self) -> Path:
        """UNC path of the user home."""
        return self._unc_path_from_cmd("~")

    @cached_property
    def home_path(self) -> PurePosixPath:
        """POSIX path of the user home."""
        return PurePosixPath(self.get_cmd_output("echo ~").strip())

    @cached_property
    def profile_unc_path(self) -> Path:
        """UNC path of user .profile."""
        try:
            return self._unc_path_from_cmd("~/.profile")
        except subprocess.CalledProcessError:
            return self.home_unc_path / ".profile"

    @property
    def profile(self) -> str:
        """Bash .profile contents."""
        try:
            return self.profile_unc_path.read_text()
        except FileNotFoundError:
            return ""

    @profile.setter
    def profile(self, value: str) -> None:
        """Writes the value into the user profile."""
        self.profile_unc_path.write_text(value)

    def reboot(self) -> None:
        """Reboot the distro."""
        # TODO: daemon thread
        subprocess.run(f"{WSL_EXE} -t {self.name}")
        time.sleep(1)
        subprocess.run(f"{WSL_EXE} -d {self.name}")

    def remove(self) -> None:
        """Unregister the distro."""
        # WARNING: handle with care!
        subprocess.run(f"{WSL_EXE} --unregister {self.name}")

    def run_sudo(self, command: str, sudo_password: str) -> None:
        """Run the commmand with sudo."""
        self.run_command(f"echo '{sudo_password}' | sudo -H -S {command}")

    def open_in_shell(self, windows_terminal: bool) -> None:
        """
        Open the distro in a shell.

        Args:
            windows_terminal: if true, open the distro in windows terminal.
        """
        if windows_terminal:
            subprocess.Popen(f"wt -p {self.name}")
        else:
            subprocess.Popen(f"{WSL_EXE} ~ -d {self.name}")

    @property
    def theme(self) -> str:
        """GTK theme."""
        try:
            theme_line = next(
                line
                for line in self.profile.splitlines()
                if "GTK_THEME=" in line
            )
            return theme_line.split("GTK_THEME=")[-1]
        except StopIteration:
            return "Default"

    @theme.setter
    def theme(self, value: str) -> None:
        """Set the GTK theme variable in the user profile."""
        profile = self.profile
        new_line = f'export GTK_THEME="{value}"' if value != "Default" else ""
        if "export GTK_THEME=" not in profile:
            self.profile = f"{profile}{new_line}\n"
        else:
            regex = re.compile(r"^\s*export GTK_THEME=.*", re.MULTILINE)
            self.profile = regex.sub(profile, new_line)

    @cached_property
    def theme_env(self) -> str:
        """
        Return the GTK theme envvar if set.

        Defaults to Adawaita.
        """
        return "$GTK_THEME" if "GTK_THEME" in self.profile else "Adwaita"

    @cached_property
    def themes(self) -> List[str]:
        """List of GTK themes."""
        usr = self.root_unc_path / "usr"
        home = self.home_unc_path
        folders_to_check = (
            usr / "share" / "themes",
            usr / "local" / "share" / "themes",
            home / ".local" / "share" / "themes",
            home / ".themes",
        )
        return list(get_themes(folders_to_check))

    @cached_property
    def apps(self) -> Dict[str, WSLApp]:
        """List of apps with a desktop entry."""
        app_dir = self.root_unc_path / "usr" / "share" / "applications"
        apps = {}
        for app in app_dir.glob("**/*.desktop"):
            wsl_app = WSLApp.from_dotdesktop(app)
            if wsl_app:
                apps[wsl_app.name] = wsl_app
        return apps

    @cached_property
    def gui_apps(self) -> Dict[str, WSLApp]:
        """List of GUI apps with a desktop entry."""
        return {k: v for k, v in self.apps.items() if v.gui}

    def set_display(self) -> None:
        """Set the DISPLAY envvar in the user profile."""
        ip = self.ip if self.version == 2 else ""
        self._edit_profile_export("DISPLAY", f"{ip}:0")

    def _edit_profile_export(self, variable: str, value: Any) -> None:
        profile = self.profile
        new_line = f"export {variable}={value}"
        if f"export {variable}" not in profile:
            profile = profile if profile.endswith("\n") else f"{profile}\n"
            self.profile = f"{profile}{new_line}\n"
        else:
            regex = re.compile(
                f"^\\s*export\\s+{variable}\\s*=.*", re.MULTILINE
            )
            self.profile = regex.sub(profile, new_line)

    @property
    def gtk_scale(self) -> int:
        """GTK applications scale factor."""
        return 2 if "GDK_SCALE=2" in self.profile else 1

    @gtk_scale.setter
    def gtk_scale(self, scale: int) -> None:
        """Set the GDK scale in the user profile."""
        if scale not in [1, 2]:
            raise ValueError(f"GTK scale {scale} not allowed. Choose 1 or 2.")
        self._edit_profile_export("GDK_SCALE", scale)

    @property
    def qt_scale(self) -> int:
        """QT applications scale factor."""
        return 2 if "QT_SCALE_FACTOR=2" in self.profile else 1

    @qt_scale.setter
    def qt_scale(self, scale: int) -> None:
        """Set the QT scale in the default shell profile."""
        if scale not in [1, 2]:
            raise ValueError(f"QT scale {scale} not allowed. Choose 1 or 2.")
        self._edit_profile_export("QT_SCALE_FACTOR", scale)

    # TODO: dbus is only on debian based distro, handle init.d alternatives
    def start_dbus(self, sudo_password: str) -> None:
        """Ensure DBUS is running."""
        v = self.run_command("/etc/init.d/dbus start", background=True)
        if "system message bus already started" in str(v.stdout):
            return
        self.run_sudo("/etc/init.d/dbus start", sudo_password)

    def install_dbus(self, sudo_password: str) -> None:
        """Install and start DBUS."""
        self.run_sudo("apt -y install dbus dbus-x11", sudo_password)
        self.run_sudo("systemd-machine-id-setup", sudo_password)
        self.run_sudo("/etc/init.d/dbus start", sudo_password)

    def set_dbus(self) -> None:
        """Add DBUS initialization to user profile."""
        profile = self.profile
        if "/etc/init.d/dbus" not in profile:
            self.profile = f"{profile}\nsudo /etc/init.d/dbus start\n"


def get_themes(themes_dirs: Sequence[Path]) -> Iterator[str]:
    """
    Return the names of the themes installed in the given directories.

    To determine if a subdirectory is a theme one, check the existence
    of a folder with the "*gtk-*" pattern inside it.
    """
    for themes_dir in themes_dirs:
        if not themes_dir.exists():
            continue
        for path in subdirs(themes_dir):
            for subpath in subdirs(path):
                if "gtk-" in subpath.name:
                    yield path.name
                    break


def subdirs(base_dir: Path) -> Iterator[Path]:
    """Return the subdirectories inside the given directory."""
    return (p for p in base_dir.iterdir() if p.is_dir())


class WSLManager(UserDict[str, WSLDistro]):
    """Manager for the installed distributions."""

    def __init__(self, blacklist: Optional[List[str]] = None) -> None:
        super().__init__()
        if not self.installed:
            # TODO: try to install it automatically
            raise FileNotFoundError("Cannot find wsl, install it first.")
        self._blacklist = blacklist or ["docker"]
        self._get_machines()

    def refresh(self) -> None:
        """Refresh the dictionary of distributions."""
        self.data.clear()
        self._get_machines()

    def _get_machines(self) -> None:
        result = subprocess.run(
            [WSL_EXE, "-l", "-v"],
            capture_output=True,
            text=True,
            encoding="utf-16-le",
        ).stdout.splitlines()
        lines = [line[2:] for line in result if line]
        reader = csv.DictReader(lines, delimiter=" ", skipinitialspace=True)
        for machine in reader:
            name = machine.get("NAME")
            if name and all(b not in name for b in self._blacklist):
                self.data[name] = WSLDistro(
                    name, int(machine.get("VERSION", 1))
                )

    @property
    def names(self) -> List[str]:
        """List of available WSL machine names."""
        return list(self.data.keys())

    @property
    def installed(self) -> bool:
        """True if wsl is installed."""
        return shutil.which(WSL_EXE) is not None

    # def install_distro(self, distro, name, version=2):
    #     """Install a new distro."""
    #     self.data[name] = WSLDistro(name, version)
    #     raise NotImplementedError

    def import_distro(
        self, name: str, tarball: str, workdir: str, version: int = 2
    ) -> WSLDistro:
        """
        Import a distribution from a tarball file.

        Args:
            name: distribution name
            tarball: tarball file of the distribution
            workdir: directory in which to place the distribution
            version: WSL version of the distribution

        Returns:
            WSLDistro of the created distro.
        """
        subprocess.run(
            f"{WSL_EXE} --import {name} {workdir} {tarball} --version {version}"
        )
        self.data[name] = WSLDistro(name, version)
        return self.data[name]
