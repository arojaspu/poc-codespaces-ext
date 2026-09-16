"""App minima. Existe solo para que el Codespace tenga trabajo real de Python
que justifique las extensiones del allowlist (Python, Pylance, debugpy, Ruff)."""

from .almacen import Almacen, Articulo

__all__ = ["Almacen", "Articulo"]
