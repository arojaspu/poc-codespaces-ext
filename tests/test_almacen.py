import pytest

from inventario import Almacen, Articulo


@pytest.fixture
def almacen() -> Almacen:
    a = Almacen()
    a.agregar(Articulo("SKU-1", "Teclado", 120.0), 3)
    a.agregar(Articulo("SKU-2", "Monitor", 950.5), 2)
    return a


def test_stock_inicial(almacen: Almacen) -> None:
    assert almacen.stock("SKU-1") == 3
    assert almacen.stock("SKU-404") == 0


def test_retiro_descuenta(almacen: Almacen) -> None:
    assert almacen.retirar("SKU-1", 2) == 1


def test_retiro_sin_stock(almacen: Almacen) -> None:
    with pytest.raises(ValueError):
        almacen.retirar("SKU-2", 99)


def test_valor_total(almacen: Almacen) -> None:
    assert almacen.valor_total() == pytest.approx(2261.0)


def test_precio_negativo() -> None:
    with pytest.raises(ValueError):
        Articulo("SKU-3", "Roto", -1.0)
