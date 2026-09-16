"""Inventario en memoria. Deliberadamente simple."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Articulo:
    sku: str
    nombre: str
    precio: float

    def __post_init__(self) -> None:
        if self.precio < 0:
            raise ValueError("el precio no puede ser negativo")


@dataclass
class Almacen:
    _items: dict[str, tuple[Articulo, int]] = field(default_factory=dict)

    def agregar(self, articulo: Articulo, cantidad: int = 1) -> None:
        if cantidad <= 0:
            raise ValueError("la cantidad debe ser positiva")
        actual = self._items.get(articulo.sku)
        nueva = cantidad + (actual[1] if actual else 0)
        self._items[articulo.sku] = (articulo, nueva)

    def retirar(self, sku: str, cantidad: int = 1) -> int:
        if sku not in self._items:
            raise KeyError(f"sku desconocido: {sku}")
        articulo, disponible = self._items[sku]
        if cantidad > disponible:
            raise ValueError(f"stock insuficiente para {sku}: {disponible} < {cantidad}")
        restante = disponible - cantidad
        self._items[sku] = (articulo, restante)
        return restante

    def stock(self, sku: str) -> int:
        return self._items.get(sku, (None, 0))[1]

    def valor_total(self) -> float:
        return round(sum(a.precio * c for a, c in self._items.values()), 2)
