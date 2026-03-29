"""
Script para popular o banco de dados com stencils de teste.

Uso:
    .venv/Scripts/python.exe tools/populate_test_stencils.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aoi_lib.stencil_tracker import StencilTracker, TensionRecord


def create_test_stencils():
    """Cria stencils de teste com dados variados."""
    tracker = StencilTracker()

    # Dados de teste
    stencils_data = [
        {
            "code": "STN-001",
            "description": "Stencil PCB A - Rev 2",
            "recipe_name": "recipe_pcb_a_v2.json",
            "status": "active",
            "tension_avg": 38.5,
            "measurements_count": 47,
            "notes": "Stencil principal da linha A",
        },
        {
            "code": "STN-002",
            "description": "Stencil PCB B",
            "recipe_name": "recipe_pcb_b.json",
            "status": "warning",
            "tension_avg": 27.2,
            "measurements_count": 23,
            "notes": "",
        },
        {
            "code": "STN-003",
            "description": "Stencil PCB C",
            "recipe_name": "recipe_pcb_c.json",
            "status": "active",
            "tension_avg": 40.1,
            "measurements_count": 31,
            "notes": "",
        },
        {
            "code": "STN-004",
            "description": "Stencil PCB D",
            "recipe_name": "recipe_pcb_d.json",
            "status": "active",
            "tension_avg": 36.8,
            "measurements_count": 18,
            "notes": "",
        },
        {
            "code": "STN-005",
            "description": "Stencil PCB E",
            "recipe_name": "recipe_pcb_e.json",
            "status": "retired",
            "tension_avg": None,
            "measurements_count": 0,
            "notes": "Substituído em março/2026",
        },
        {
            "code": "STN-006",
            "description": "Stencil PCB F",
            "recipe_name": "recipe_pcb_f.json",
            "status": "active",
            "tension_avg": 39.2,
            "measurements_count": 28,
            "notes": "",
        },
        {
            "code": "STN-007",
            "description": "Stencil PCB G",
            "recipe_name": "recipe_pcb_g.json",
            "status": "active",
            "tension_avg": 37.5,
            "measurements_count": 35,
            "notes": "",
        },
    ]

    print("Criando stencils de teste...")
    print("=" * 50)

    for i, data in enumerate(stencils_data):
        code = data["code"]

        # Remove se já existir
        if tracker.stencil_exists(code):
            tracker.delete_stencil(code)
            print(f"Removido stencil existente: {code}")

        # Cria o stencil
        stencil = tracker.create_stencil(
            code=code,
            description=data["description"],
            recipe_name=data["recipe_name"],
        )

        # Define status
        stencil.status = data["status"]

        # Cria data de criação (diferentes dias)
        created_days_ago = 60 + (i * 5)
        created_at = datetime.now() - timedelta(days=created_days_ago)
        stencil.created_at = created_at.isoformat()

        # Adiciona medição de tensão se tiver valor
        if data["tension_avg"] is not None:
            # Data da última medição (diferentes dias atrás)
            last_days_ago = [0, 2, 3, 4, 10, 5, 6][i]
            last_measurement = datetime.now() - timedelta(days=last_days_ago)

            # Cria medições simuladas (16 pontos grid 4x4)
            import random
            random.seed(42)  # Reprodutível

            measurements = []
            base_tension = data["tension_avg"]

            for row in range(4):
                for col in range(4):
                    # Tensão com pequena variação
                    variation = random.uniform(-2.0, 2.0)
                    tension = base_tension + variation

                    # Status baseado na tensão
                    if 28 <= tension <= 42:
                        status = "OK"
                    elif 25 <= tension < 28 or 42 < tension <= 45:
                        status = "WARNING"
                    else:
                        status = "NOK"

                    measurements.append({
                        "x": col * 25 + 12.5,
                        "y": row * 25 + 12.5,
                        "tension": round(tension, 1),
                        "status": status,
                    })

            # Cria registro de tensão
            tensions = [m["tension"] for m in measurements]
            ok_count = sum(1 for m in measurements if m["status"] == "OK")
            warn_count = sum(1 for m in measurements if m["status"] == "WARNING")
            nok_count = sum(1 for m in measurements if m["status"] == "NOK")

            record = TensionRecord(
                timestamp=last_measurement.isoformat(),
                measurements=measurements,
                average_tension=data["tension_avg"],
                min_tension=min(tensions),
                max_tension=max(tensions),
                result="WARNING" if warn_count > 0 else "OK",
                ok_count=ok_count,
                warning_count=warn_count,
                nok_count=nok_count,
                operator="Operador Teste",
                recipe_name=data["recipe_name"],
            )

            tracker.add_tension_record(code, record)
            print(f"Criado: {code} - {data['description']} ({data['status']}) - {data['tension_avg']:.1f} N/cm²")
        else:
            # Stencil sem medições (retirado)
            stencil.last_inspection = (datetime.now() - timedelta(days=14)).isoformat()
            tracker._save_stencil(stencil)
            print(f"Criado: {code} - {data['description']} ({data['status']}) - Sem medições")

    print("=" * 50)
    print(f"Total de stencils criados: {len(stencils_data)}")
    print("\nPara ver os stencils, execute a aplicação:")
    print("  .venv/Scripts/python.exe main.py")


if __name__ == "__main__":
    create_test_stencils()
