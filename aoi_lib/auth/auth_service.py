"""
Serviço de Autenticação

Gerencia login, logout e persistência de usuários.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from .user import User, UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço de autenticação de usuários"""

    def __init__(self, users_file: Path = None):
        """
        Inicializa serviço de autenticação

        Args:
            users_file: Caminho para arquivo JSON de usuários
        """
        self.users_file = users_file or Path("data/users/users.json")
        self.current_user: Optional[User] = None
        self._users: dict = {}
        self._load_users()

    def _load_users(self):
        """Carrega usuários do arquivo JSON"""
        try:
            if not self.users_file.exists():
                logger.info(f"Arquivo de usuários não encontrado, criando padrões")
                self._create_default_users()

            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for username, user_data in data['users'].items():
                    self._users[username] = {
                        'password_hash': user_data['password_hash'],
                        'full_name': user_data['full_name'],
                        'role': UserRole(user_data['role']),
                        'is_active': user_data.get('is_active', True)
                    }

            logger.info(f"Carregados {len(self._users)} usuários de {self.users_file}")

        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            self._create_default_users()

    def _create_default_users(self):
        """
        Cria usuários padrão se arquivo não existir

        Usuários padrão:
        - operator / operator123 (Operador)
        - eng / eng123 (Engenharia)
        - admin / admin123 (Administrador)
        """
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

        default_users = {
            "operator": {
                "password_hash": self._hash_password("operator123"),
                "full_name": "Operador Padrão",
                "role": "operator",
                "is_active": True
            },
            "eng": {
                "password_hash": self._hash_password("eng123"),
                "full_name": "Engenheiro de Processo",
                "role": "engineering",
                "is_active": True
            },
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "full_name": "Administrador",
                "role": "admin",
                "is_active": True
            }
        }

        data = {"users": default_users}

        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Criado arquivo de usuários em {self.users_file}")

            # Recarrega usuários
            self._users = {}
            for username, user_data in default_users.items():
                self._users[username] = {
                    'password_hash': user_data['password_hash'],
                    'full_name': user_data['full_name'],
                    'role': UserRole(user_data['role']),
                    'is_active': user_data['is_active']
                }

        except Exception as e:
            logger.error(f"Erro ao criar arquivo de usuários: {e}")

    def _hash_password(self, password: str) -> str:
        """
        Gera hash SHA-256 da senha

        Args:
            password: Senha em texto plano

        Returns:
            Hash SHA-256 da senha
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """
        Autentica usuário

        Args:
            username: Nome de usuário
            password: Senha em texto plano

        Returns:
            True se autenticação bem-sucedida, False caso contrário
        """
        username = username.strip()
        password = password.strip()

        # Verifica se usuário existe
        if username not in self._users:
            logger.warning(f"Tentativa de login com usuário inexistente: {username}")
            return False

        user_data = self._users[username]
        password_hash = self._hash_password(password)

        # Verifica senha
        if user_data['password_hash'] != password_hash:
            logger.warning(f"Senha incorreta para usuário: {username}")
            return False

        # Verifica se usuário está ativo
        if not user_data['is_active']:
            logger.warning(f"Usuário desativado: {username}")
            return False

        # Cria objeto User e define como atual
        self.current_user = User(
            username=username,
            full_name=user_data['full_name'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )

        logger.info(f"Usuário autenticado: {self.current_user}")
        return True

    def logout(self):
        """Logout do usuário atual"""
        if self.current_user:
            logger.info(f"Logout: {self.current_user}")
        self.current_user = None

    def is_authenticated(self) -> bool:
        """
        Verifica se há usuário autenticado

        Returns:
            True se há usuário autenticado
        """
        return self.current_user is not None

    def get_current_user(self) -> Optional[User]:
        """
        Retorna usuário autenticado

        Returns:
            Objeto User ou None se não autenticado
        """
        return self.current_user

    def get_user_list(self) -> List[str]:
        """
        Retorna lista de nomes de usuários

        Returns:
            Lista de usernames
        """
        return list(self._users.keys())
