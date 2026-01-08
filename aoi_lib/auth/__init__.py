"""
Módulo de Autenticação do Sistema Tensiômetro

Este módulo gerencia autenticação de usuários, perfis e permissões.
"""

from .user import User, UserRole, PERMISSIONS
from .auth_service import AuthService

__all__ = ['User', 'UserRole', 'AuthService', 'PERMISSIONS']
