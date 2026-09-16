"""ext_guard: compara las extensiones instaladas en el Codespace contra
policy/allowlist.yaml, registra evidencia y, en modo enforce, revierte.

Es un control DETECTIVO/CORRECTIVO. No es una barrera: el usuario tiene sudo
dentro del contenedor y puede detenerlo. Su valor es dejar rastro y acotar
la ventana de exposicion.
"""

__version__ = "0.1.0"
