"""
Consulta de stencils no SFCS para o fluxo de medição de tensão.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, parse, request

from aoi_lib.stencil_tracker import Stencil, normalize_stencil_code

logger = logging.getLogger(__name__)


class SfcsStencilLookupError(Exception):
    """Erro de comunicação ou payload inválido ao consultar o SFCS."""


class SfcsStencilNotFound(SfcsStencilLookupError):
    """Stencil não encontrado/cadastrado no SFCS."""


@dataclass(frozen=True)
class SfcsStencilRecord:
    code: str
    description: str
    grid: str
    sfcs_id: Optional[int]
    stencil_type: Optional[int]
    sfcs_status: str
    raw_payload: Dict[str, Any]

    def to_stencil(self, recipe_name: Optional[str] = None) -> Stencil:
        notes = (
            f"SFCS ID: {self.sfcs_id or ''}; "
            f"Tipo: {self.stencil_type if self.stencil_type is not None else ''}; "
            f"Status SFCS: {self.sfcs_status}; "
            f"Grid: {self.grid}"
        )
        return Stencil(
            code=self.code,
            description=self.description,
            recipe_name=recipe_name or self.grid or None,
            status=_map_sfcs_status(self.sfcs_status),
            notes=notes,
        )


class SfcsStencilLookupService:
    DEFAULT_ENDPOINT_URL = "http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}"
    DEFAULT_TIMEOUT_SEC = 10.0

    def __init__(self, config_manager=None):
        self.config = config_manager

    def is_enabled(self) -> bool:
        if self.config is None:
            return False
        return bool(self.config.get("sfcs_stencil_lookup", "enabled", default=True))

    def lookup(self, code: str) -> SfcsStencilRecord:
        normalized_code = normalize_stencil_code(code)
        if not normalized_code:
            raise SfcsStencilLookupError("Código de stencil vazio.")

        endpoint_url = self._build_endpoint_url(normalized_code)
        http_request = request.Request(
            endpoint_url,
            method="GET",
            headers={"Accept": "application/json"},
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_sec()) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code == 404:
                raise SfcsStencilNotFound(f"Stencil '{normalized_code}' não cadastrado no SFCS.") from exc
            raise SfcsStencilLookupError(f"Falha HTTP ao consultar SFCS: {exc.code}") from exc
        except error.URLError as exc:
            raise SfcsStencilLookupError(f"Não foi possível acessar o SFCS: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise SfcsStencilLookupError("Resposta inválida do SFCS: JSON malformado.") from exc

        if not isinstance(payload, dict) or not payload:
            raise SfcsStencilNotFound(f"Stencil '{normalized_code}' não cadastrado no SFCS.")

        record = self._parse_payload(payload, fallback_code=normalized_code)
        logger.info("Stencil %s consultado no SFCS com sucesso", record.code)
        return record

    def resolve_recipe_name(self, record: SfcsStencilRecord) -> Optional[str]:
        grid = (record.grid or "").strip()
        if not grid or self.config is None:
            return grid or None

        grid_map = self.config.get("sfcs_stencil_lookup", "grid_pattern_map", default={}) or {}
        if isinstance(grid_map, dict):
            configured_pattern = str(
                grid_map.get(grid) or grid_map.get(grid.upper()) or ""
            ).strip()
            if configured_pattern:
                return configured_pattern

        try:
            from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager

            pattern = MeasurementPatternManager().resolve_pattern_for_grid(grid)
            if pattern is not None:
                return pattern.name
        except Exception:
            logger.debug("Falha ao resolver padrão de medição pelo grid '%s'", grid, exc_info=True)

        return grid

    def _build_endpoint_url(self, code: str) -> str:
        endpoint = self._endpoint_url()
        encoded_code = parse.quote(code, safe="")

        if "{codigo_barras}" in endpoint:
            return endpoint.replace("{codigo_barras}", encoded_code)
        if endpoint.endswith("/"):
            return f"{endpoint}{encoded_code}"
        return f"{endpoint}/{encoded_code}"

    def _endpoint_url(self) -> str:
        if self.config is None:
            return self.DEFAULT_ENDPOINT_URL
        configured = self.config.get(
            "sfcs_stencil_lookup",
            "endpoint_url",
            default=self.DEFAULT_ENDPOINT_URL,
        )
        return str(configured or self.DEFAULT_ENDPOINT_URL).strip()

    def _timeout_sec(self) -> float:
        if self.config is None:
            return self.DEFAULT_TIMEOUT_SEC
        try:
            return max(
                0.1,
                float(self.config.get("sfcs_stencil_lookup", "timeout_sec", default=self.DEFAULT_TIMEOUT_SEC)),
            )
        except (TypeError, ValueError):
            return self.DEFAULT_TIMEOUT_SEC

    def _parse_payload(self, payload: Dict[str, Any], fallback_code: str) -> SfcsStencilRecord:
        code = normalize_stencil_code(payload.get("codigo_barras") or fallback_code)
        if not code:
            raise SfcsStencilLookupError("Resposta inválida do SFCS: código de barras ausente.")

        return SfcsStencilRecord(
            code=code,
            description=str(
                payload.get("t2_nmdescmodelo")
                or payload.get("t2_mndescmodelo")
                or ""
            ).strip(),
            grid=str(payload.get("grid") or "").strip(),
            sfcs_id=_to_optional_int(payload.get("idstencil")),
            stencil_type=_to_optional_int(payload.get("tipo")),
            sfcs_status=str(payload.get("stencil_status") or "").strip(),
            raw_payload=payload,
        )


def _to_optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_sfcs_status(status: str) -> str:
    normalized = str(status or "").strip().upper()
    if normalized in {"DISPONIVEL", "DISPONÍVEL", "ATIVO", "ACTIVE"}:
        return "active"
    if normalized in {"ALERTA", "WARNING"}:
        return "warning"
    if normalized in {"RETIRADO", "BLOQUEADO", "INDISPONIVEL", "INDISPONÍVEL", "RETIRED"}:
        return "retired"
    return "active"
