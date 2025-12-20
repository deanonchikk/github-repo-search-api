import tomllib
from pathlib import Path


def _get_version() -> str:
    """
    Читает версию из pyproject.toml.

    :returns: Версия приложения.
    """
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            pyproject_data = tomllib.load(f)
            return pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
        return "0.1.0"


__version__ = _get_version()
