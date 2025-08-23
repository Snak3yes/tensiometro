from __future__ import annotations
import json, typing as _t
from pathlib import Path
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal

_FILE = Path(__file__).with_name("dot_patterns.json")

@dataclass
class DotPattern:
    id:   int
    name: str
    qty:  int = 1
    height: int = 0    # altura de aplicação

class DotPatternManager(QObject):
    """
    Singleton simples que mantém a lista de DotPattern e a persiste
    em dot_patterns.json.  Qualquer mudança emite patternsChanged().
    """
    patternsChanged = pyqtSignal()
    _instance: "DotPatternManager | None" = None
    _patterns: list[DotPattern] = [] 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            super(DotPatternManager, cls._instance).__init__()
            cls._instance._patterns = []
            cls._instance._load()
        return cls._instance

    # --------------------------------------------------------------
    def _load(self):
        if _FILE.exists():
            try:
                raw = json.loads(_FILE.read_text("utf-8"))
                self._patterns = [DotPattern(**d) for d in raw]
            except Exception:
                self._patterns = []

    def _save(self):
        _FILE.write_text(json.dumps([asdict(p) for p in self._patterns],
                                    indent=2), encoding="utf-8")

    # ------------------ API pública --------------------------------
    def patterns(self) -> list[DotPattern]:
        return list(self._patterns)

    def add(self, name: str, qty: int, height: int = 0) -> DotPattern:
        next_id = (max((p.id for p in self._patterns), default=0)) + 1
        p = DotPattern(next_id, name, qty, height)
        self._patterns.append(p)
        self._save(); self.patternsChanged.emit()
        return p

    def remove(self, dot_id:int):
        self._patterns = [p for p in self._patterns if p.id != dot_id]
        self._save(); self.patternsChanged.emit()