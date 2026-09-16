import json
from pathlib import Path

import pytest

from ext_guard import evidence
from ext_guard.policy import Policy

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy() -> Policy:
    return Policy.load(RAIZ / "policy" / "allowlist.yaml")


def test_permite_por_id(policy: Policy) -> None:
    assert policy.permite("ms-python.python")
    assert policy.permite("MS-Python.Python")  # insensible a mayusculas


def test_permite_por_publisher(policy: Policy) -> None:
    assert policy.permite("github.copilot")


def test_bloquea_no_listadas(policy: Policy) -> None:
    for objetivo in policy.test_targets:
        assert not policy.permite(objetivo), f"{objetivo} no deberia estar permitida"


def test_render_cierra_con_comodin(policy: Policy) -> None:
    bloque = policy.as_vscode_allowed()
    assert bloque["*"] is False
    assert bloque["ms-python.python"] is True


def test_devcontainer_sin_drift() -> None:
    """El devcontainer debe reflejar exactamente el allowlist."""
    from ext_guard.__main__ import _sin_comentarios

    texto = (RAIZ / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8")
    datos = json.loads(_sin_comentarios(texto))
    actual = datos["customizations"]["vscode"]["settings"]["extensions.allowed"]
    assert actual == Policy.load(RAIZ / "policy" / "allowlist.yaml").as_vscode_allowed()


def test_cadena_de_evidencia(tmp_path: Path) -> None:
    archivo = tmp_path / "eventos.jsonl"
    evidence.registrar(archivo, {"evento": "check", "violaciones": []})
    evidence.registrar(archivo, {"evento": "check", "violaciones": ["x.y"]})
    assert evidence.verificar(archivo)[0]


def test_evidencia_alterada_se_detecta(tmp_path: Path) -> None:
    archivo = tmp_path / "eventos.jsonl"
    evidence.registrar(archivo, {"evento": "check", "violaciones": []})
    evidence.registrar(archivo, {"evento": "check", "violaciones": ["x.y"]})
    lineas = archivo.read_text(encoding="utf-8").splitlines()
    manipulada = json.loads(lineas[1])
    manipulada["violaciones"] = []
    lineas[1] = json.dumps(manipulada, ensure_ascii=False)
    archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    ok, detalle = evidence.verificar(archivo)
    assert not ok and "linea 2" in detalle
