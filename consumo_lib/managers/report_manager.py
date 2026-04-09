"""
managers/report_manager.py
---------------------------
Gerencia geração de relatórios PDF (ReportGenerator).
"""
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from aoi_lib.report_generator import ReportGenerator, ReportConfig

logger = logging.getLogger(__name__)


class ReportManagerWrapper(QObject):
    """
    Gerencia geração de relatórios PDF.

    Responsabilidades:
        - Gerenciar ReportGenerator
        - Configurar parâmetros de relatório
        - Gerar relatórios de tensão
        - Gerar relatórios de histórico de stencil
        - Gerar relatórios de inspeção visual
        - Emitir signals de eventos
    """

    # Signals
    report_generated = pyqtSignal(str, str)  # report_type, output_path
    report_failed = pyqtSignal(str, str)  # report_type, error_message
    config_changed = pyqtSignal(object)  # ReportConfig

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.report_config = ReportConfig()
        self.generator = ReportGenerator(self.report_config)

        # Carregar configuração salva
        self._load_config()

        logger.info(f"ReportManagerWrapper inicializado. Diretório: {self.report_config.output_dir}")

    def _load_config(self):
        """Carrega configuração de relatórios da configuração."""
        report_config_data = self.config.get("reports", "config", default=None)

        if report_config_data:
            try:
                self.report_config = ReportConfig.from_dict(report_config_data)
                self.generator = ReportGenerator(self.report_config)
                logger.info("Configuração de relatórios carregada")
            except Exception as e:
                logger.warning(f"Erro ao carregar config de relatórios: {e}")
                self.report_config = ReportConfig()
                self.generator = ReportGenerator(self.report_config)
        else:
            self.report_config = ReportConfig()
            self.generator = ReportGenerator(self.report_config)

    def update_config(self, config: ReportConfig, save=True):
        """
        Atualiza configuração de relatórios.

        Args:
            config: Nova configuração
            save: Se True, salva na configuração
        """
        self.report_config = config
        self.generator = ReportGenerator(config)

        if save:
            self.config.set("reports", "config", value=config.to_dict())
            self.config.save()

        self.config_changed.emit(config)
        logger.info("Configuração de relatórios atualizada")

    def get_config(self) -> ReportConfig:
        """Retorna a configuração atual."""
        return self.report_config

    def _get_current_tension_criteria(self) -> dict:
        """Retorna os critérios globais atuais usados nos relatórios."""
        criteria_data = self.config.get("tension_criteria", default=None) or {}
        return {
            "min_tension": float(criteria_data.get("min_tension", 25.0)),
            "max_tension": float(criteria_data.get("max_tension", 45.0)),
            "warning_low": float(criteria_data.get("warning_low", 28.0)),
            "warning_high": float(criteria_data.get("warning_high", 42.0)),
        }

    def _classify_measurement_for_report(self, value: float, criteria: dict) -> str:
        """Classifica medições para relatório com base nos critérios atuais."""
        if value < criteria["min_tension"] or value > criteria["max_tension"]:
            return "NOK"
        if value <= criteria["warning_high"]:
            return "WARNING"
        return "OK"

    def _to_float(self, value, default: float = 0.0) -> float:
        """Converte valores numéricos ou textuais para float."""
        if value in (None, ""):
            return default
        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(str(value).strip().replace(",", "."))
        except (TypeError, ValueError):
            return default

    def _normalize_measurement_for_report(self, measurement: dict, criteria: dict) -> dict:
        """Normaliza uma medição individual aplicando a classificação atual."""
        item = dict(measurement or {})
        tension = self._to_float(item.get("parsed_value", item.get("tension")), 0.0)
        item["x"] = self._to_float(item.get("x"), 0.0)
        item["y"] = self._to_float(item.get("y"), 0.0)
        item["z"] = self._to_float(item.get("z"), 0.0)
        item["parsed_value"] = tension
        item["tension"] = tension
        item["status"] = self._classify_measurement_for_report(tension, criteria)
        return item

    def _apply_current_tension_criteria(self, tension_data: dict) -> dict:
        """Sobrescreve os critérios e reclassifica as medições do relatório."""
        criteria = self._get_current_tension_criteria()
        normalized = dict(tension_data or {})
        normalized["acceptance_criteria"] = criteria
        normalized["measurements"] = [
            self._normalize_measurement_for_report(measurement, criteria)
            for measurement in (tension_data or {}).get("measurements", []) or []
        ]
        return normalized

    def _normalize_history_record_for_report(self, record: dict, criteria: dict) -> dict:
        """Recalcula um registro histórico do stencil com os critérios atuais."""
        normalized = dict(record or {})
        measurements = [
            self._normalize_measurement_for_report(measurement, criteria)
            for measurement in normalized.get("measurements", []) or []
        ]
        normalized["measurements"] = measurements
        normalized["acceptance_criteria"] = criteria
        normalized["operator"] = normalized.get("operator") or "-"

        if not measurements:
            average_tension = self._to_float(normalized.get("average_tension"), 0.0)
            normalized["average_tension"] = average_tension
            normalized["min_tension"] = self._to_float(normalized.get("min_tension"), average_tension)
            normalized["max_tension"] = self._to_float(normalized.get("max_tension"), average_tension)
            normalized["result"] = self._classify_measurement_for_report(average_tension, criteria)
            return normalized

        tensions = [measurement["tension"] for measurement in measurements]
        ok_count = sum(1 for measurement in measurements if measurement["status"] == "OK")
        warning_count = sum(1 for measurement in measurements if measurement["status"] == "WARNING")
        nok_count = sum(1 for measurement in measurements if measurement["status"] == "NOK")

        if nok_count:
            result = "NOK"
        elif warning_count:
            result = "WARNING"
        else:
            result = "OK"

        normalized["average_tension"] = sum(tensions) / len(tensions)
        normalized["min_tension"] = min(tensions)
        normalized["max_tension"] = max(tensions)
        normalized["ok_count"] = ok_count
        normalized["warning_count"] = warning_count
        normalized["nok_count"] = nok_count
        normalized["result"] = result
        return normalized

    def _apply_current_tension_criteria_to_history(self, history: list) -> tuple[list, dict]:
        """Recalcula todo o histórico usando os critérios atuais."""
        criteria = self._get_current_tension_criteria()
        normalized_history = [
            self._normalize_history_record_for_report(
                record.to_dict() if hasattr(record, "to_dict") else record,
                criteria,
            )
            for record in (history or [])
        ]
        return normalized_history, criteria

    def generate_tension_report(
        self,
        tension_data: dict,
        stencil_code: str = None,
        stencil_description: str = None,
        recipe_name: str = None,
        operator: str = None,
    ) -> Optional[str]:
        """
        Gera relatório de tensão.

        Args:
            tension_data: Dados da medição de tensão
            stencil_code: Código do stencil (opcional)
            operator: Nome do operador (opcional)

        Returns:
            Caminho do PDF gerado ou None se falhar
        """
        try:
            report_tension_data = self._apply_current_tension_criteria(tension_data)
            output_path = self.generator.generate_tension_report(
                tension_data=report_tension_data,
                stencil_code=stencil_code,
                stencil_description=stencil_description,
                recipe_name=recipe_name,
                operator=operator
            )
            logger.info(f"Relatório de tensão gerado: {output_path}")
            self.report_generated.emit("tension", output_path)
            return output_path
        except Exception as e:
            error_msg = f"Erro ao gerar relatório de tensão: {e}"
            logger.error(error_msg)
            self.report_failed.emit("tension", error_msg)
            return None

    def generate_stencil_history_report(
        self,
        stencil: dict,
        history: list,
        report_title: str = None,
    ) -> Optional[str]:
        """
        Gera relatório de histórico de medições do stencil.

        Args:
            stencil: Dados do stencil
            history: Histórico de medições de tensão

        Returns:
            Caminho do PDF gerado ou None se falhar
        """
        try:
            normalized_history, criteria = self._apply_current_tension_criteria_to_history(history)
            normalized_stencil = dict(stencil or {})
            normalized_stencil["acceptance_criteria"] = criteria
            output_path = self.generator.generate_stencil_history_report(
                stencil=normalized_stencil,
                history=normalized_history,
                report_title=report_title,
            )
            logger.info(f"Relatório de histórico gerado: {output_path}")
            self.report_generated.emit("stencil_history", output_path)
            return output_path
        except Exception as e:
            error_msg = f"Erro ao gerar relatório de histórico: {e}"
            logger.error(error_msg)
            self.report_failed.emit("stencil_history", error_msg)
            return None

    def get_generator(self) -> ReportGenerator:
        """Retorna o gerador subjacente (para uso avançado)."""
        return self.generator
