# Análise de Dependências - aoi_lib

**Data:** 10/01/2026
**Autor:** Conductor Agent

## Visão Geral
A biblioteca `aoi_lib` contém o núcleo da lógica de controle e regras de negócio.

## Estrutura de Dependências

### Módulos Principais
- `aoi_controller.py`: Orquestrador. Importa drivers e gerenciadores.
- `plc_axis_controller.py`: Driver de comunicação com CLP (Modbus).
- `camera_controller.py`: Abstração da câmera.
- `config_manager.py`: Gerenciamento de configurações (JSON).
- `stencil_database.py`: Persistência SQLite.
- `stencil_tracker.py`: Regras de negócio de stencils e histórico.

### Pontos de Atenção

1.  **aoi_controller.py -> config_manager.py**:
    Existe uma importação local dentro do `__init__` de `CNCAOIController`:
    ```python
    from .config_manager import AOIConfigManager
    ```
    Isso sugere uma tentativa de evitar ciclo de importação ou carregamento tardio. `config_manager.py` parece independente, não importando `aoi_controller`.

2.  **stencil_database.py -> stencil_tracker.py**:
    O banco de dados importa os modelos de dados (`Stencil`, `TensionRecord`) do tracker. Esta é uma dependência natural.

## Conclusão
A arquitetura não apresenta ciclos rígidos impeditivos para testes unitários.
- `config_manager.py` é um bom candidato para começar os testes, pois é independente.
- `stencil_tracker.py` também é independente e contém lógica de negócio pura (cálculos de tendência, modelos).
- `stencil_database.py` pode ser testado com um banco SQLite em memória.

## Próximos Passos
1. Criar testes para `config_manager.py`.
2. Criar testes para `stencil_tracker.py` e `stencil_database.py`.
