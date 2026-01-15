"""
aoi_lib.database.repositories

Pacote para interfaces e implementações de repositórios de banco de dados.
"""

# Interfaces ABC
from .stencil_repository import StencilRepository
from .tension_repository import TensionRepository
from .inspection_repository import InspectionRepository

__all__ = [
    'StencilRepository',
    'TensionRepository',
    'InspectionRepository',
]
