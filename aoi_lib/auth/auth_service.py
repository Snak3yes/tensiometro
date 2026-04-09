"""
Servico de autenticacao.

Suporta dois fluxos:
- Operador: valida DRT via endpoint interno da Digiboard
- Eng/Admin: valida senha unica e registra o DRT localmente

Mantem tambem a autenticacao local legada para compatibilidade com partes
antigas do sistema que ainda confirmam credenciais locais.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib import error, parse, request

from .user import User, UserRole

logger = logging.getLogger(__name__)


@dataclass
class DigiboardLookupResult:
    """Resultado da consulta de usuario no endpoint interno."""

    success: bool
    payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class AuthService:
    """Servico central de autenticacao do aplicativo."""

    ADMIN_OVERRIDE_PASSWORD = "administrador@@digiboard"
    DIGIBOARD_LOOKUP_URL = (
        "http://147.1.0.100:3075/sfcs-print/tbusuario/consultar/matricula/{drt}"
    )
    DIGIBOARD_TIMEOUT_SEC = 8.0

    def __init__(self, users_file: Path = None):
        """
        Inicializa o servico.

        Args:
            users_file: Caminho para o arquivo JSON de usuarios legados
        """
        self.users_file = users_file or Path("data/users/users.json")
        self.current_user: Optional[User] = None
        self.current_mode: str = "logged_out"
        self.current_user_metadata: dict[str, Any] = {}
        self.last_error_message: str = ""
        self._users: dict[str, dict[str, Any]] = {}
        self._load_users()

    def _load_users(self):
        """Carrega usuarios legados do arquivo JSON."""
        try:
            if not self.users_file.exists():
                logger.info("Arquivo de usuarios nao encontrado, criando padroes")
                self._create_default_users()

            with open(self.users_file, "r", encoding="utf-8") as stream:
                data = json.load(stream)
                for username, user_data in data["users"].items():
                    self._users[username] = {
                        "password_hash": user_data["password_hash"],
                        "full_name": user_data["full_name"],
                        "role": UserRole(user_data["role"]),
                        "is_active": user_data.get("is_active", True),
                    }

            logger.info("Carregados %s usuarios legados de %s", len(self._users), self.users_file)
        except Exception as exc:
            logger.error("Erro ao carregar usuarios legados: %s", exc)
            self._create_default_users()

    def _create_default_users(self):
        """Cria usuarios padrao para compatibilidade com fluxos legados."""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

        default_users = {
            "operator": {
                "password_hash": self._hash_password("operator123"),
                "full_name": "Operador Padrao",
                "role": "operator",
                "is_active": True,
            },
            "eng": {
                "password_hash": self._hash_password("eng123"),
                "full_name": "Engenharia",
                "role": "engineering",
                "is_active": True,
            },
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "full_name": "Administrador",
                "role": "admin",
                "is_active": True,
            },
        }

        with open(self.users_file, "w", encoding="utf-8") as stream:
            json.dump({"users": default_users}, stream, indent=2, ensure_ascii=False)

        self._users = {}
        for username, user_data in default_users.items():
            self._users[username] = {
                "password_hash": user_data["password_hash"],
                "full_name": user_data["full_name"],
                "role": UserRole(user_data["role"]),
                "is_active": user_data["is_active"],
            }

    def _hash_password(self, password: str) -> str:
        """Gera hash SHA-256."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """
        Autenticacao legada.

        Se a senha for a senha mestre de Eng/Admin, autentica nesse modo.
        Caso contrario, tenta o arquivo local legado.
        """
        username = (username or "").strip()
        password = (password or "").strip()
        self.last_error_message = ""

        if password == self.ADMIN_OVERRIDE_PASSWORD:
            return self.authenticate_eng_admin(username, password)

        if username not in self._users:
            self.last_error_message = "Usuario ou senha incorretos."
            logger.warning("Tentativa de login local com usuario inexistente: %s", username)
            return False

        user_data = self._users[username]
        password_hash = self._hash_password(password)

        if user_data["password_hash"] != password_hash:
            self.last_error_message = "Usuario ou senha incorretos."
            logger.warning("Senha incorreta para usuario local: %s", username)
            return False

        if not user_data["is_active"]:
            self.last_error_message = "Usuario desativado."
            logger.warning("Usuario local desativado: %s", username)
            return False

        self.current_user = User(
            username=username,
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=user_data["is_active"],
        )
        self.current_mode = "legacy"
        self.current_user_metadata = {}
        logger.info("Usuario autenticado via fluxo legado: %s", self.current_user)
        return True

    def authenticate_operator(self, drt: str) -> bool:
        """Autentica operador consultando o endpoint interno da Digiboard."""
        drt = (drt or "").strip()
        self.last_error_message = ""

        lookup = self._lookup_user_by_drt(drt)
        if not lookup.success:
            self.last_error_message = lookup.error_message or "Nao foi possivel validar o DRT informado."
            return False

        payload = lookup.payload or {}
        full_name = (payload.get("nmnomeusuario") or f"Operador {drt}").strip()

        self.current_user = User(
            username=drt,
            full_name=full_name,
            role=UserRole.OPERATOR,
            is_active=True,
        )
        self.current_mode = "operator"
        self.current_user_metadata = payload
        logger.info("Usuario autenticado via Digiboard: DRT=%s nome=%s", drt, full_name)
        return True

    def authenticate_eng_admin(self, drt: str, password: str) -> bool:
        """Autentica o modo Eng/Admin usando senha unica."""
        drt = (drt or "").strip()
        password = (password or "").strip()
        self.last_error_message = ""

        if not drt:
            self.last_error_message = "Informe o DRT."
            return False

        if password != self.ADMIN_OVERRIDE_PASSWORD:
            self.last_error_message = "Senha de Eng/Admin incorreta."
            logger.warning("Senha invalida para modo Eng/Admin: DRT=%s", drt)
            return False

        self.current_user = User(
            username=drt,
            full_name=f"Eng/Admin {drt}",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.current_mode = "eng_admin"
        self.current_user_metadata = {"drt": drt, "mode": "eng_admin"}
        logger.info("Usuario autenticado em modo Eng/Admin: DRT=%s", drt)
        return True

    def get_last_error(self) -> str:
        """Retorna a ultima mensagem de erro de autenticacao."""
        return self.last_error_message

    def get_current_mode(self) -> str:
        """Retorna o modo atual de autenticacao."""
        return self.current_mode

    def is_eng_admin_mode(self) -> bool:
        """Retorna True quando o login atual esta em modo Eng/Admin."""
        return self.current_mode == "eng_admin"

    def get_current_user_metadata(self) -> dict[str, Any]:
        """Retorna metadados do usuario autenticado."""
        return dict(self.current_user_metadata)

    def get_external_user_id(self) -> Any:
        """Retorna o idusuario obtido da validacao do DRT, quando existir."""
        metadata = self.current_user_metadata or {}
        if isinstance(metadata, dict):
            external_user_id = metadata.get("idusuario")
            if external_user_id not in (None, "", 0):
                return external_user_id
        return None

    def _lookup_user_by_drt(self, drt: str) -> DigiboardLookupResult:
        """Consulta o endpoint interno para validar o DRT informado."""
        if not drt:
            return DigiboardLookupResult(False, error_message="Informe o DRT.")

        if not drt.isdigit():
            return DigiboardLookupResult(False, error_message="O campo DRT deve conter apenas numeros.")

        endpoint = self.DIGIBOARD_LOOKUP_URL.format(drt=parse.quote(drt, safe=""))
        http_request = request.Request(endpoint, method="GET")

        try:
            with request.urlopen(http_request, timeout=self.DIGIBOARD_TIMEOUT_SEC) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            logger.warning("Falha ao consultar DRT %s na Digiboard: HTTP %s", drt, exc.code)
            if exc.code in (400, 404):
                return DigiboardLookupResult(False, error_message="DRT invalido ou nao encontrado.")
            return DigiboardLookupResult(
                False,
                error_message=f"Falha ao consultar o sistema interno (HTTP {exc.code}).",
            )
        except error.URLError as exc:
            logger.error("Erro de rede ao consultar DRT %s: %s", drt, exc)
            return DigiboardLookupResult(
                False,
                error_message="Nao foi possivel conectar ao sistema interno da Digiboard.",
            )
        except Exception as exc:
            logger.error("Erro inesperado ao consultar DRT %s: %s", drt, exc)
            return DigiboardLookupResult(
                False,
                error_message="Erro inesperado ao validar o DRT no sistema interno.",
            )

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Resposta invalida ao consultar DRT %s: %s", drt, body[:200])
            return DigiboardLookupResult(
                False,
                error_message="Resposta invalida recebida do sistema interno.",
            )

        if not self._is_valid_digiboard_payload(payload):
            logger.warning("Resposta sem usuario valido para DRT %s: %s", drt, payload)
            return DigiboardLookupResult(False, error_message="DRT invalido ou nao encontrado.")

        return DigiboardLookupResult(True, payload=payload)

    @staticmethod
    def _is_valid_digiboard_payload(payload: Any) -> bool:
        """Valida se a resposta recebida representa um usuario existente."""
        if not isinstance(payload, dict):
            return False

        if payload.get("idusuario") in (None, "", 0):
            return False

        full_name = str(payload.get("nmnomeusuario") or "").strip()
        badge = str(payload.get("nmcracha") or "").strip()
        return bool(full_name or badge)

    def logout(self):
        """Logout do usuario atual."""
        if self.current_user:
            logger.info("Logout: %s", self.current_user)
        self.current_user = None
        self.current_mode = "logged_out"
        self.current_user_metadata = {}
        self.last_error_message = ""

    def is_authenticated(self) -> bool:
        """Verifica se ha usuario autenticado."""
        return self.current_user is not None

    def get_current_user(self) -> Optional[User]:
        """Retorna o usuario autenticado."""
        return self.current_user

    def get_user_list(self) -> list[str]:
        """Retorna a lista de usuarios legados conhecidos."""
        return list(self._users.keys())
