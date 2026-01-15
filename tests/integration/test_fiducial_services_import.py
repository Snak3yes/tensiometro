"""
Teste de Validação de Imports e Funcionalidade Básica - Fiducial Services

Este teste valida que todos os módulos criados na Phase 5B.1 podem ser
importados corretamente e têm funcionalidade básica funcionando.

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B.1
"""

import sys
import os
from pathlib import Path

# Adiciona diretório raiz ao sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np

# Teste 1: Import de Models
print("[Teste 1] Importando fiducial_models...")
try:
    from aoi_lib.fiducial_models import (
        FiducialPoint,
        AlignmentTransform,
        AlignmentState,
        FiducialConfig,
        FiducialType,
        MatchingMethod
    )
    print("  [OK] Todos os models importados com sucesso")
except Exception as e:
    print(f"  [ERRO] Falha ao importar models: {e}")
    sys.exit(1)

# Teste 2: Criação de FiducialPoint
print("\n[Teste 2] Criando FiducialPoint...")
try:
    fiducial = FiducialPoint(
        gerber_x=10.0,
        gerber_y=20.0,
        fiducial_type=FiducialType.TEMPLATE,
        window_size=50
    )
    print(f"  [OK] FiducialPoint criado: ({fiducial.gerber_x}, {fiducial.gerber_y})")
except Exception as e:
    print(f"  [ERRO] Falha ao criar FiducialPoint: {e}")
    sys.exit(1)

# Teste 3: Criação de AlignmentTransform
print("\n[Teste 3] Criando AlignmentTransform...")
try:
    transform = AlignmentTransform(
        tx=5.0,
        ty=10.0,
        angle=2.5,
        scale_x=1.0,
        scale_y=1.0
    )
    print(f"  [OK] AlignmentTransform criado: {transform}")
except Exception as e:
    print(f"  [ERRO] Falha ao criar AlignmentTransform: {e}")
    sys.exit(1)

# Teste 4: Criação de AlignmentState
print("\n[Teste 4] Criando AlignmentState...")
try:
    state = AlignmentState(
        fiducials=[fiducial],
        transform=transform,
        config=FiducialConfig()
    )
    print(f"  [OK] AlignmentState criado com {len(state.fiducials)} fiduciais")
except Exception as e:
    print(f"  [ERRO] Falha ao criar AlignmentState: {e}")
    sys.exit(1)

# Teste 5: Import de FiducialMatchingService
print("\n[Teste 5] Importando FiducialMatchingService...")
try:
    from aoi_lib.fiducial_matching_service import (
        FiducialMatchingService,
        MatchingError
    )
    print("  [OK] FiducialMatchingService importado com sucesso")
except Exception as e:
    print(f"  [ERRO] Falha ao importar FiducialMatchingService: {e}")
    sys.exit(1)

# Teste 6: Criação de FiducialMatchingService
print("\n[Teste 6] Criando FiducialMatchingService...")
try:
    matching_service = FiducialMatchingService(config=FiducialConfig())
    print("  [OK] FiducialMatchingService criado")
except Exception as e:
    print(f"  [ERRO] Falha ao criar FiducialMatchingService: {e}")
    sys.exit(1)

# Teste 7: Import de AlignmentTransformService
print("\n[Teste 7] Importando AlignmentTransformService...")
try:
    from aoi_lib.alignment_transform_service import (
        AlignmentTransformService,
        TransformError
    )
    print("  [OK] AlignmentTransformService importado com sucesso")
except Exception as e:
    print(f"  [ERRO] Falha ao importar AlignmentTransformService: {e}")
    sys.exit(1)

# Teste 8: Criação de AlignmentTransformService
print("\n[Teste 8] Criando AlignmentTransformService...")
try:
    transform_service = AlignmentTransformService()
    print("  [OK] AlignmentTransformService criado")
except Exception as e:
    print(f"  [ERRO] Falha ao criar AlignmentTransformService: {e}")
    sys.exit(1)

# Teste 9: Import de AlignmentStateService
print("\n[Teste 9] Importando AlignmentStateService...")
try:
    from aoi_lib.alignment_state_service import (
        AlignmentStateService,
        StateError
    )
    print("  [OK] AlignmentStateService importado com sucesso")
except Exception as e:
    print(f"  [ERRO] Falha ao importar AlignmentStateService: {e}")
    sys.exit(1)

# Teste 10: Criação de AlignmentStateService
print("\n[Teste 10] Criando AlignmentStateService...")
try:
    state_service = AlignmentStateService()
    print("  [OK] AlignmentStateService criado")
except Exception as e:
    print(f"  [ERRO] Falha ao criar AlignmentStateService: {e}")
    sys.exit(1)

# Teste 11: Serialização/Desserialização de Estado
print("\n[Teste 11] Testando serialização de estado...")
try:
    json_str = state_service.serialize_state(state)
    restored_state = state_service.deserialize_state(json_str)

    if len(restored_state.fiducials) == len(state.fiducials):
        print("  [OK] Serialização/desserialização funcionando corretamente")
    else:
        print(f"  [ERRO] Número de fiduciais não coincide: {len(restored_state.fiducials)} != {len(state.fiducials)}")
        sys.exit(1)
except Exception as e:
    print(f"  [ERRO] Falha na serialização: {e}")
    sys.exit(1)

# Teste 12: Cálculo de Translação
print("\n[Teste 12] Testando cálculo de translação...")
try:
    tx, ty = transform_service.calculate_translation(
        src_point=(0, 0),
        dst_point=(10, 20)
    )
    if abs(tx - 10) < 0.01 and abs(ty - 20) < 0.01:
        print(f"  [OK] Translação calculada corretamente: ({tx:.1f}, {ty:.1f})")
    else:
        print(f"  [ERRO] Translação incorreta: ({tx}, {ty}) != (10, 20)")
        sys.exit(1)
except Exception as e:
    print(f"  [ERRO] Falha no cálculo de translação: {e}")
    sys.exit(1)

# Teste 13: Validação de Estado
print("\n[Teste 13] Testando validação de estado...")
try:
    is_valid, message = state_service.validate_state(state)
    print(f"  [OK] Validação executada: is_valid={is_valid}, message='{message}'")
except Exception as e:
    print(f"  [ERRO] Falha na validação: {e}")
    sys.exit(1)

# Resumo Final
print("\n" + "=" * 70)
print("[SUCCESS] TODOS OS TESTES PASSARAM!")
print("=" * 70)
print("\nResumo da Validação:")
print("  [OK] Import de todos os módulos (models + services)")
print("  [OK] Criação de todas as classes de dados")
print("  [OK] Criação de todos os serviços")
print("  [OK] Serialização/desserialização de estado")
print("  [OK] Cálculo de translação")
print("  [OK] Validação de estado")
print("\nPhase 5B.1 (Criação de Models e Services) validada com sucesso!")
