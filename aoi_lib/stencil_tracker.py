"""
stencil_tracker.py
-------------------
Gerenciamento de stencils individuais e seu histórico de inspeções.

Este módulo permite:
- Cadastrar e gerenciar stencils por código de barras
- Associar stencils a receitas
- Registrar histórico de medições de tensão
- Analisar tendência de degradação ao longo do tempo

Estrutura de dados (JSON):
    data/stencils/
    ├── index.json          # Índice de todos os stencils
    └── {codigo}/           # Pasta por stencil
        ├── info.json       # Metadados do stencil
        └── history/        # Histórico de medições
            ├── 2024-12-11_093000_tension.json
            └── ...

NOTA: Para sistemas com grande volume de dados, considerar migração 
      para SQLite. Ver ROADMAP_DESENVOLVIMENTO.md.
"""

import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path

log = logging.getLogger(__name__)


# ============================================================================
#  MODELOS DE DADOS
# ============================================================================

@dataclass
class Stencil:
    """
    Representa um stencil físico individual.
    
    Attributes:
        code: Código de barras (identificador único)
        description: Descrição auxiliar para identificação
        recipe_name: Nome da receita associada
        created_at: Data de cadastro no sistema
        last_inspection: Data/hora da última inspeção
        inspection_count: Número total de inspeções realizadas
        status: Estado atual ("active", "warning", "retired")
        notes: Observações do operador/engenharia
    """
    code: str
    description: str = ""
    recipe_name: Optional[str] = None
    created_at: str = ""  # ISO format
    last_inspection: Optional[str] = None  # ISO format
    inspection_count: int = 0
    status: str = "active"  # "active", "warning", "retired"
    notes: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stencil":
        return cls(
            code=data.get("code", ""),
            description=data.get("description", ""),
            recipe_name=data.get("recipe_name"),
            created_at=data.get("created_at", ""),
            last_inspection=data.get("last_inspection"),
            inspection_count=data.get("inspection_count", 0),
            status=data.get("status", "active"),
            notes=data.get("notes", ""),
        )


@dataclass
class TensionRecord:
    """
    Registro de uma medição de tensão.
    
    Attributes:
        timestamp: Data/hora da medição
        measurements: Lista de pontos medidos [{x, y, tension, status}, ...]
        average_tension: Tensão média
        min_tension: Tensão mínima
        max_tension: Tensão máxima
        result: Resultado geral ("OK", "WARNING", "NOK")
        ok_count: Quantidade de pontos OK
        warning_count: Quantidade de pontos WARNING
        nok_count: Quantidade de pontos NOK
        operator: Nome do operador (opcional)
        recipe_name: Nome da receita usada
    """
    timestamp: str  # ISO format
    measurements: List[Dict[str, Any]] = field(default_factory=list)
    average_tension: float = 0.0
    min_tension: float = 0.0
    max_tension: float = 0.0
    result: str = "OK"  # "OK", "WARNING", "NOK"
    ok_count: int = 0
    warning_count: int = 0
    nok_count: int = 0
    operator: Optional[str] = None
    recipe_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TensionRecord":
        return cls(
            timestamp=data.get("timestamp", ""),
            measurements=data.get("measurements", []),
            average_tension=data.get("average_tension", 0.0),
            min_tension=data.get("min_tension", 0.0),
            max_tension=data.get("max_tension", 0.0),
            result=data.get("result", "OK"),
            ok_count=data.get("ok_count", 0),
            warning_count=data.get("warning_count", 0),
            nok_count=data.get("nok_count", 0),
            operator=data.get("operator"),
            recipe_name=data.get("recipe_name"),
        )
    
    @classmethod
    def from_tension_data(cls, tension_data: Dict[str, Any], 
                          recipe_name: str = None,
                          operator: str = None) -> "TensionRecord":
        """
        Cria TensionRecord a partir dos dados de medição existentes.
        
        Args:
            tension_data: Dados do formato stencil_tension_measurements.json
            recipe_name: Nome da receita usada
            operator: Nome do operador
        """
        measurements = tension_data.get("measurements", [])
        
        if not measurements:
            return cls(
                timestamp=datetime.now().isoformat(),
                recipe_name=recipe_name,
                operator=operator,
            )
        
        tensions = [float(m.get("tension", 0)) for m in measurements]
        
        # Conta resultados por status
        ok_count = sum(1 for m in measurements if m.get("status") == "OK")
        warning_count = sum(1 for m in measurements if m.get("status") == "WARNING")
        nok_count = sum(1 for m in measurements if m.get("status") == "NOK")
        
        # Determina resultado geral
        if nok_count > 0:
            result = "NOK"
        elif warning_count > len(measurements) * 0.2:  # Mais de 20% warning
            result = "WARNING"
        else:
            result = "OK"
        
        return cls(
            timestamp=datetime.now().isoformat(),
            measurements=measurements,
            average_tension=sum(tensions) / len(tensions) if tensions else 0,
            min_tension=min(tensions) if tensions else 0,
            max_tension=max(tensions) if tensions else 0,
            result=result,
            ok_count=ok_count,
            warning_count=warning_count,
            nok_count=nok_count,
            operator=operator,
            recipe_name=recipe_name,
        )


@dataclass
class TrendAnalysis:
    """Resultado da análise de tendência de um stencil."""
    stencil_code: str
    record_count: int
    first_average: float  # Média da primeira medição
    last_average: float   # Média da última medição
    moving_average: float  # Média móvel das últimas N medições
    variation_percent: float  # Variação % em relação à primeira
    trend: str  # "stable", "degrading", "improving"
    alert: Optional[str] = None  # Mensagem de alerta se houver


# ============================================================================
#  GERENCIADOR DE STENCILS
# ============================================================================

class StencilTracker:
    """
    Gerencia cadastro e histórico de stencils.
    
    Responsabilidades:
    - CRUD de stencils (criar, ler, atualizar, listar)
    - Registrar histórico de medições de tensão
    - Analisar tendência de degradação
    - Persistir dados em JSON
    """
    
    MOVING_AVERAGE_WINDOW = 5  # Janela para média móvel
    DEGRADATION_THRESHOLD = 0.10  # 10% de queda = alerta
    
    def __init__(self, data_dir: str = None):
        """
        Inicializa o tracker.
        
        Args:
            data_dir: Diretório para armazenar dados. 
                      Default: ./data/stencils
        """
        if data_dir is None:
            # Usa diretório relativo ao projeto
            base = Path(__file__).parent.parent
            data_dir = base / "data" / "stencils"
        
        self.data_dir = Path(data_dir)
        self._ensure_directories()
        
        # Cache de stencils carregados
        self._cache: Dict[str, Stencil] = {}
        
        log.info(f"StencilTracker inicializado em: {self.data_dir}")
    
    def _ensure_directories(self):
        """Garante que os diretórios necessários existem."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_stencil_dir(self, code: str) -> Path:
        """Retorna diretório de um stencil específico."""
        # Sanitiza código para uso como nome de pasta
        safe_code = "".join(c if c.isalnum() or c in "-_" else "_" for c in code)
        return self.data_dir / safe_code
    
    def _get_stencil_info_path(self, code: str) -> Path:
        """Retorna caminho do arquivo info.json de um stencil."""
        return self._get_stencil_dir(code) / "info.json"
    
    def _get_history_dir(self, code: str) -> Path:
        """Retorna diretório de histórico de um stencil."""
        return self._get_stencil_dir(code) / "history"
    
    # -------------------------------------------------------------------------
    #  CRUD DE STENCILS
    # -------------------------------------------------------------------------
    
    def stencil_exists(self, code: str) -> bool:
        """Verifica se um stencil existe."""
        return self._get_stencil_info_path(code).exists()
    
    def get_stencil(self, code: str) -> Optional[Stencil]:
        """
        Obtém um stencil pelo código.
        
        Args:
            code: Código de barras do stencil
            
        Returns:
            Stencil se encontrado, None caso contrário
        """
        # Verifica cache primeiro
        if code in self._cache:
            return self._cache[code]
        
        info_path = self._get_stencil_info_path(code)
        
        if not info_path.exists():
            return None
        
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            stencil = Stencil.from_dict(data)
            self._cache[code] = stencil
            return stencil
            
        except Exception as e:
            log.error(f"Erro ao carregar stencil {code}: {e}")
            return None
    
    def create_stencil(self, code: str, 
                       description: str = "",
                       recipe_name: str = None) -> Stencil:
        """
        Cria um novo stencil.
        
        Args:
            code: Código de barras (obrigatório)
            description: Descrição auxiliar
            recipe_name: Nome da receita associada
            
        Returns:
            Stencil criado
            
        Raises:
            ValueError: Se stencil já existir
        """
        if self.stencil_exists(code):
            raise ValueError(f"Stencil '{code}' já existe")
        
        stencil = Stencil(
            code=code,
            description=description,
            recipe_name=recipe_name,
        )
        
        # Cria diretórios
        stencil_dir = self._get_stencil_dir(code)
        stencil_dir.mkdir(parents=True, exist_ok=True)
        (stencil_dir / "history").mkdir(exist_ok=True)
        
        # Salva info.json
        self._save_stencil(stencil)
        
        log.info(f"Stencil criado: {code}")
        return stencil
    
    def update_stencil(self, stencil: Stencil) -> None:
        """
        Atualiza dados de um stencil existente.
        
        Args:
            stencil: Stencil com dados atualizados
        """
        if not self.stencil_exists(stencil.code):
            raise ValueError(f"Stencil '{stencil.code}' não existe")
        
        self._save_stencil(stencil)
        log.info(f"Stencil atualizado: {stencil.code}")
    
    def _save_stencil(self, stencil: Stencil) -> None:
        """Salva stencil em disco."""
        info_path = self._get_stencil_info_path(stencil.code)
        info_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(stencil.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Atualiza cache
        self._cache[stencil.code] = stencil
    
    def list_stencils(self, status: str = None) -> List[Stencil]:
        """
        Lista todos os stencils cadastrados.
        
        Args:
            status: Filtrar por status ("active", "warning", "retired")
                    None = todos
                    
        Returns:
            Lista de stencils
        """
        stencils = []
        
        if not self.data_dir.exists():
            return stencils
        
        for item in self.data_dir.iterdir():
            if item.is_dir():
                info_path = item / "info.json"
                if info_path.exists():
                    try:
                        with open(info_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        stencil = Stencil.from_dict(data)
                        
                        if status is None or stencil.status == status:
                            stencils.append(stencil)
                            
                    except Exception as e:
                        log.warning(f"Erro ao carregar {info_path}: {e}")
        
        # Ordena por último uso (mais recente primeiro)
        stencils.sort(
            key=lambda s: s.last_inspection or s.created_at,
            reverse=True
        )
        
        return stencils
    
    def delete_stencil(self, code: str) -> bool:
        """
        Remove um stencil e todo seu histórico.
        
        ⚠️ ATENÇÃO: Esta operação é irreversível!
        
        Args:
            code: Código do stencil
            
        Returns:
            True se removido, False se não existia
        """
        import shutil
        
        stencil_dir = self._get_stencil_dir(code)
        
        if not stencil_dir.exists():
            return False
        
        try:
            shutil.rmtree(stencil_dir)
            self._cache.pop(code, None)
            log.info(f"Stencil removido: {code}")
            return True
        except Exception as e:
            log.error(f"Erro ao remover stencil {code}: {e}")
            return False
    
    # -------------------------------------------------------------------------
    #  HISTÓRICO DE MEDIÇÕES
    # -------------------------------------------------------------------------
    
    def add_tension_record(self, code: str, record: TensionRecord) -> None:
        """
        Adiciona registro de medição de tensão ao histórico.
        
        Args:
            code: Código do stencil
            record: Registro de medição
        """
        stencil = self.get_stencil(code)
        if not stencil:
            raise ValueError(f"Stencil '{code}' não encontrado")
        
        # Cria diretório de histórico se não existir
        history_dir = self._get_history_dir(code)
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo: YYYY-MM-DD_HHMMSS_tension.json
        timestamp = datetime.fromisoformat(record.timestamp)
        filename = timestamp.strftime("%Y-%m-%d_%H%M%S_tension.json")
        filepath = history_dir / filename
        
        # Salva registro
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Atualiza stencil
        stencil.last_inspection = record.timestamp
        stencil.inspection_count += 1
        
        # Atualiza status baseado no resultado
        if record.result == "NOK":
            stencil.status = "warning"
        
        self._save_stencil(stencil)
        
        log.info(f"Registro de tensão adicionado para {code}: {record.result}")
    
    def get_tension_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        """
        Obtém histórico de medições de tensão.
        
        Args:
            code: Código do stencil
            limit: Número máximo de registros (mais recentes primeiro)
            
        Returns:
            Lista de registros de tensão
        """
        history_dir = self._get_history_dir(code)
        
        if not history_dir.exists():
            return []
        
        records = []
        
        # Lista arquivos de tensão
        files = sorted(
            [f for f in history_dir.glob("*_tension.json")],
            reverse=True  # Mais recente primeiro
        )
        
        for filepath in files[:limit]:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                records.append(TensionRecord.from_dict(data))
            except Exception as e:
                log.warning(f"Erro ao carregar {filepath}: {e}")
        
        return records
    
    # -------------------------------------------------------------------------
    #  ANÁLISE DE TENDÊNCIA
    # -------------------------------------------------------------------------
    
    def get_trend_analysis(self, code: str, 
                           warning_low: float = None) -> TrendAnalysis:
        """
        Analisa tendência de degradação de um stencil.
        
        Args:
            code: Código do stencil
            warning_low: Limite inferior de warning da receita
                         (para determinar alertas)
        
        Returns:
            TrendAnalysis com dados da análise
        """
        history = self.get_tension_history(code, limit=20)
        
        if not history:
            return TrendAnalysis(
                stencil_code=code,
                record_count=0,
                first_average=0,
                last_average=0,
                moving_average=0,
                variation_percent=0,
                trend="stable",
            )
        
        # Inverte para ordem cronológica (mais antigo primeiro)
        history = list(reversed(history))
        
        averages = [r.average_tension for r in history]
        
        first_avg = averages[0]
        last_avg = averages[-1]
        
        # Média móvel das últimas N medições
        window = min(self.MOVING_AVERAGE_WINDOW, len(averages))
        moving_avg = sum(averages[-window:]) / window
        
        # Variação percentual
        if first_avg > 0:
            variation = (last_avg - first_avg) / first_avg
        else:
            variation = 0
        
        # Determina tendência
        if variation < -self.DEGRADATION_THRESHOLD:
            trend = "degrading"
        elif variation > self.DEGRADATION_THRESHOLD:
            trend = "improving"
        else:
            trend = "stable"
        
        # Verifica alertas
        alert = None
        if warning_low and moving_avg < warning_low:
            alert = f"⚠️ Tensão média ({moving_avg:.1f}) abaixo do limite ({warning_low:.1f})"
        elif trend == "degrading":
            alert = f"📉 Tendência de queda: {abs(variation)*100:.1f}% desde primeira medição"
        
        return TrendAnalysis(
            stencil_code=code,
            record_count=len(history),
            first_average=first_avg,
            last_average=last_avg,
            moving_average=moving_avg,
            variation_percent=variation * 100,
            trend=trend,
            alert=alert,
        )
    
    def check_degradation_alert(self, code: str, 
                                 warning_low: float = None) -> Optional[str]:
        """
        Verifica se há alerta de degradação para um stencil.
        
        Args:
            code: Código do stencil
            warning_low: Limite inferior de warning da receita
            
        Returns:
            Mensagem de alerta ou None
        """
        analysis = self.get_trend_analysis(code, warning_low)
        return analysis.alert
