"""wsl-tools tests."""
import ipaddress
from pathlib import Path

import pytest
from wsl_tools import wsl_posix_path
from wsl_tools import WSLApp
from wsl_tools import WSLDistro
from wsl_tools import WSLManager
from xdg.Exceptions import ParsingError

BASE_DISTRO = "alpine-base"


@pytest.fixture(scope="session")
def manager() -> WSLManager:
    """Initialize the manager."""
    yield WSLManager()


@pytest.fixture(scope="session")
def test_distro(tmp_path_factory, manager: WSLManager) -> WSLDistro:
    """Import a temporary base alpine distribution."""
    tarfile = Path(f"distros\\{BASE_DISTRO}.tar").resolve()
    distro_dir = tmp_path_factory.mktemp("distro")
    distro = manager.import_distro(BASE_DISTRO, tarfile, distro_dir)
    yield distro
    distro.remove()


@pytest.fixture
def dotdesktop_path(tmp_path_factory) -> Path:
    """Temporary file."""
    dd_folder = tmp_path_factory.mktemp("dotdesktop_files")
    dd_path = dd_folder / "text.desktop"
    yield dd_path
    dd_path.unlink()


def test_app_from_dotdesktop(dotdesktop_path: Path) -> None:
    """Dotdesktop file is translated into a WSLApp."""
    dotdesktop_path.write_text(
        """[Desktop Entry]
Name=Test app
GenericName=Generic test
Exec=/bin/test
Icon=awesome
Terminal=True
Type=Application
Categories=GTK;GNOME;Utility;
    """
    )
    app = WSLApp.from_dotdesktop(dotdesktop_path)
    assert app == WSLApp(
        "Test app", "Generic test", "/bin/test", False, ico="awesome"
    )


def test_app_from_dotdesktop_inalid(dotdesktop_path: Path) -> None:
    """Raise on empty or invalid file."""
    dotdesktop_path.write_text("")
    with pytest.raises(ParsingError):
        WSLApp.from_dotdesktop(dotdesktop_path)


def test_manager_wsl_installed(manager: WSLManager) -> None:
    """Check if it's installed."""
    assert manager.installed  # this will change based on your setup


def test_manager_names(manager: WSLManager) -> None:
    """Docker distros are blacklisted."""
    names = manager.names
    assert all("docker" not in name.lower() for name in names)
    assert all(BASE_DISTRO not in name.lower() for name in names)


def test_manager_dict(manager: WSLManager) -> None:
    """Docker distros are blacklisted."""
    assert all("docker" not in name for name in manager)
    assert BASE_DISTRO not in manager


def test_manager_names_distro_imported(
    manager: WSLManager, test_distro: WSLDistro
) -> None:
    """Imported distro appears in the manager."""
    assert BASE_DISTRO in manager.names


def test_manager_dict_distro_imported(
    manager: WSLManager, test_distro: WSLDistro
) -> None:
    """Imported distro appears in the manager."""
    assert BASE_DISTRO in manager
    assert manager[BASE_DISTRO].version == 2
    assert len(manager) >= 1


def test_manager_refresh(manager: WSLManager, test_distro: WSLDistro) -> None:
    """Imported distro appears in the manager."""
    names = set(manager.names)
    manager.refresh()
    assert names == set(manager.names)


def test_distro_name_and_repr(test_distro: WSLDistro) -> None:
    """String representation is more user-friendly."""
    assert str(test_distro) == "Alpine base"
    assert test_distro.name == BASE_DISTRO


def test_distro_root(test_distro: WSLDistro) -> None:
    """UNC paths for access from windows."""
    assert test_distro.root_unc_path == Path(r"\\wsl$\alpine-base")


def test_distro_home(test_distro: WSLDistro) -> None:
    """Default user is wsluser."""
    assert test_distro.home_unc_path == Path(r"\\wsl$\alpine-base\home\wsluser")


def test_distro_home_posix(test_distro: WSLDistro) -> None:
    """Default user is wsluser."""
    assert str(test_distro.home_path) == "/home/wsluser"


def test_distro_profile(test_distro: WSLDistro) -> None:
    """UNC profile returned even if it doesn't exist."""
    assert test_distro.profile_unc_path == Path(
        r"\\wsl$\alpine-base\home\wsluser\.profile"
    )


def test_shell(test_distro: WSLDistro) -> None:
    """Alpine default shell is ash."""
    assert test_distro.shell == "/bin/ash"


def test_apps(test_distro: WSLDistro) -> None:
    """No desktop entries in the base distro."""
    apps = test_distro.apps
    assert not apps


def test_gui_apps(test_distro: WSLDistro) -> None:
    """No desktop entries in the base distro."""
    gui_apps = test_distro.gui_apps
    assert not gui_apps


def test_ip(test_distro: WSLDistro) -> None:
    """Ip property return a valid IP."""
    ip = test_distro.ip
    assert ipaddress.ip_address(ip)


def test_dbus(test_distro: WSLDistro) -> None:
    """DBUS should start."""
    test_distro.start_dbus("wsl")


def test_profile(test_distro: WSLDistro) -> None:
    """Profile property reads and writes to user profile."""
    profile = test_distro.profile
    new_profile = f"{profile}# Just a Test"
    test_distro.profile = new_profile
    assert test_distro.profile.endswith("# Just a Test")
    test_distro.profile = profile
    assert test_distro.profile == profile


def test_gtk_scale(test_distro: WSLDistro) -> None:
    """GTK scale factor read and written correctly."""
    assert test_distro.gtk_scale == 1
    test_distro.gtk_scale = 2
    assert test_distro.gtk_scale == 2
    assert "export GDK_SCALE=2" in test_distro.profile
    with pytest.raises(ValueError):
        test_distro.gtk_scale = 3


def test_qt_scale(test_distro: WSLDistro) -> None:
    """QT scale factor read and written correctly."""
    assert test_distro.qt_scale == 1
    test_distro.qt_scale = 2
    assert test_distro.qt_scale == 2
    assert "export QT_SCALE_FACTOR=2" in test_distro.profile
    with pytest.raises(ValueError):
        test_distro.qt_scale = 3


wsl_posix_path_args = [
    (r"\\wsl$\Ubuntu-20.04\home\test\whatever", "/home/test/whatever")
]


@pytest.mark.parametrize(("unc", "expected"), wsl_posix_path_args)
def test_wsl_posix_path(unc: str, expected: str) -> None:
    """UNC path converted to linux path."""
    assert wsl_posix_path(Path(unc)) == expected
