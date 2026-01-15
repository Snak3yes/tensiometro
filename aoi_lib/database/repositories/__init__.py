"""
aoi_lib.database.repositories

Pacote para interfaces e implementações de repositórios de banco de dados.
"""

# Interfaces ABC
from .stencil_repository import StencilRepository
from .tension_repository import TensionRepository
from .inspection_repository import InspectionRepository

# Implementações SQLite
from .sqlite_stencil_repository import SqliteStencilRepository
from .sqlite_tension_repository import SqliteTensionRepository
from .sqlite_inspection_repository import SqliteInspectionRepository

__all__ = [
    # Interfaces
    'StencilRepository',
    'TensionRepository',
    'InspectionRepository',
    # Implementações
    'SqliteStencilRepository',
    'SqliteTensionRepository',
    'SqliteInspectionRepository',
]
