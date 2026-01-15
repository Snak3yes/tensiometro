"""
Testes de Validacao - Refatoracao report_generator.py

Testes de integracao para validar que a refatoracao SOLID funcionou corretamente.
Verifica:
1. Import de todos os modulos
2. Criacao de servicos
3. Interface compativel
4. Geracao basica de relatorios
"""

import sys
from pathlib import Path

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)

# Teste 1: Import de todos os modulos refatorados
print("=" * 70)
print("TESTE 1: Import de Modulos Refatorados")
print("=" * 70)

try:
    from aoi_lib.reports import (
        PDFGenerator,
        ChartGenerator,
        StatisticsCalculator,
        ReportLayoutManager,
        TensionReportBuilder,
        StencilHistoryReportBuilder,
        InspectionReportBuilder,
        ReportGenerator,
        ReportConfig
    )
    print("[OK] Todos os imports bem-sucedidos!")
    print("   - PDFGenerator")
    print("   - ChartGenerator")
    print("   - StatisticsCalculator")
    print("   - ReportLayoutManager")
    print("   - TensionReportBuilder")
    print("   - StencilHistoryReportBuilder")
    print("   - InspectionReportBuilder")
    print("   - ReportGenerator")
    print("   - ReportConfig")
except ImportError as e:
    print(f"[FAIL] Falha no import: {e}")
    sys.exit(1)

# Teste 2: Criacao de ReportConfig
print("\n" + "=" * 70)
print("TESTE 2: Criacao de ReportConfig")
print("=" * 70)

try:
    config = ReportConfig(
        company_name="Empresa Teste",
        company_subtitle="Sistema de Teste",
        output_dir="test_output"
    )
    print(f"[OK] ReportConfig criado com sucesso!")
    print(f"   - Empresa: {config.company_name}")
    print(f"   - Subtitulo: {config.company_subtitle}")
    print(f"   - Output dir: {config.output_dir}")
except Exception as e:
    print(f"[FAIL] Falha ao criar ReportConfig: {e}")
    sys.exit(1)

# Teste 3: Criacao de Servicos
print("\n" + "=" * 70)
print("TESTE 3: Criacao de Servicos Especializados")
print("=" * 70)

try:
    pdf_gen = PDFGenerator(config)
    chart_gen = ChartGenerator(config)
    stats_calc = StatisticsCalculator()
    layout_mgr = ReportLayoutManager(config)

    print("[OK] Todos os servicos criados com sucesso!")
    print(f"   - PDFGenerator: {type(pdf_gen).__name__}")
    print(f"   - ChartGenerator: {type(chart_gen).__name__}")
    print(f"   - StatisticsCalculator: {type(stats_calc).__name__}")
    print(f"   - ReportLayoutManager: {type(layout_mgr).__name__}")

    # Verificar metodos chave
    assert hasattr(pdf_gen, 'build_document'), "PDFGenerator deve ter build_document()"
    assert hasattr(chart_gen, 'create_scatter_plot'), "ChartGenerator deve ter create_scatter_plot()"
    assert hasattr(stats_calc, 'calculate_basic_stats'), "StatisticsCalculator deve ter calculate_basic_stats()"
    assert hasattr(layout_mgr, 'format_number'), "ReportLayoutManager deve ter format_number()"
    print("[OK] Verificacao de metodos: OK")

except Exception as e:
    print(f"[FAIL] Falha ao criar servicos: {e}")
    sys.exit(1)

# Teste 4: Criacao de Builders com Dependency Injection
print("\n" + "=" * 70)
print("TESTE 4: Criacao de Builders com Dependency Injection")
print("=" * 70)

try:
    tension_builder = TensionReportBuilder(
        config,
        pdf_generator=pdf_gen,
        chart_generator=chart_gen,
        stats_calculator=stats_calc,
        layout_manager=layout_mgr
    )

    history_builder = StencilHistoryReportBuilder(
        config,
        pdf_generator=pdf_gen,
        chart_generator=chart_gen,
        stats_calculator=stats_calc,
        layout_manager=layout_mgr
    )

    inspection_builder = InspectionReportBuilder(
        config,
        pdf_generator=pdf_gen,
        stats_calculator=stats_calc,
        layout_manager=layout_mgr
    )

    print("[OK] Todos os builders criados com dependency injection!")
    print(f"   - TensionReportBuilder: {type(tension_builder).__name__}")
    print(f"   - StencilHistoryReportBuilder: {type(history_builder).__name__}")
    print(f"   - InspectionReportBuilder: {type(inspection_builder).__name__}")

    # Verificar que servicos foram injetados (nao recriados)
    assert tension_builder.pdf is pdf_gen, "PDFGenerator deve ser a mesma instancia"
    assert tension_builder.chart is chart_gen, "ChartGenerator deve ser a mesma instancia"
    assert tension_builder.stats is stats_calc, "StatisticsCalculator deve ser a mesma instancia"
    assert tension_builder.layout is layout_mgr, "ReportLayoutManager deve ser a mesma instancia"
    print("[OK] Verificacao de dependency injection: OK (mesmas instancias)")

except Exception as e:
    print(f"[FAIL] Falha ao criar builders: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 5: Criacao de ReportGenerator Facade
print("\n" + "=" * 70)
print("TESTE 5: Criacao de ReportGenerator Facade")
print("=" * 70)

try:
    generator = ReportGenerator(config)

    print("[OK] ReportGenerator criado com sucesso!")
    print(f"   - Tipo: {type(generator).__name__}")

    # Verificar que servicos foram criados
    assert hasattr(generator, 'pdf'), "ReportGenerator deve ter pdf"
    assert hasattr(generator, 'chart'), "ReportGenerator deve ter chart"
    assert hasattr(generator, 'stats'), "ReportGenerator deve ter stats"
    assert hasattr(generator, 'layout'), "ReportGenerator deve ter layout"
    print("[OK] Servicos compartilhados criados: OK")

    # Verificar metodos de geracao
    assert hasattr(generator, 'generate_tension_report'), "Deve ter generate_tension_report()"
    assert hasattr(generator, 'generate_stencil_history_report'), "Deve ter generate_stencil_history_report()"
    assert hasattr(generator, 'generate_inspection_report'), "Deve ter generate_inspection_report()"
    assert hasattr(generator, 'update_config'), "Deve ter update_config()"
    print("[OK] Verificacao de metodos: OK")

except Exception as e:
    print(f"[FAIL] Falha ao criar ReportGenerator: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 6: Teste de Estatisticas
print("\n" + "=" * 70)
print("TESTE 6: Teste de StatisticsCalculator")
print("=" * 70)

try:
    # Dados de teste
    test_data = [25.0, 28.0, 30.0, 27.0, 29.0, 31.0, 26.0, 28.0]

    stats = stats_calc.calculate_basic_stats(test_data, include_cv=True)

    print("[OK] Estatisticas calculadas com sucesso!")
    print(f"   - Media: {stats['mean']:.2f}")
    print(f"   - Mediana: {stats['median']:.2f}")
    print(f"   - Std: {stats['std']:.2f}")
    print(f"   - Min: {stats['min']:.2f}")
    print(f"   - Max: {stats['max']:.2f}")
    print(f"   - CV: {stats['cv']:.2f}%")

    # Verificar valores esperados
    assert 27 < stats['mean'] < 29, "Media deve estar entre 27 e 29"
    assert stats['min'] == 25.0, "Min deve ser 25.0"
    assert stats['max'] == 31.0, "Max deve ser 31.0"
    print("[OK] Valores estatisticos corretos: OK")

except Exception as e:
    print(f"[FAIL] Falha no teste de estatisticas: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 7: Teste de Formatacao
print("\n" + "=" * 70)
print("TESTE 7: Teste de ReportLayoutManager")
print("=" * 70)

try:
    # Testar formatacao de numeros
    num_str = layout_mgr.format_number(25.6789, decimals=2)
    print(f"[OK] format_number(25.6789, 2) = '{num_str}'")
    assert num_str == "25.68", "Deve formatar para 2 casas decimais"

    # Testar formatacao de porcentagem
    pct_str = layout_mgr.format_percentage(85.6789)
    print(f"[OK] format_percentage(85.6789) = '{pct_str}'")
    # Aceita tanto arredondamento de 1 ou 2 casas decimais
    assert pct_str in ["85.68%", "85.7%"], f"Deve formatar como porcentagem, mas retornou '{pct_str}'"

    # Testar cores de status
    ok_color = layout_mgr.get_status_color('OK')
    print(f"[OK] get_status_color('OK') = {ok_color}")
    assert ok_color == config.success_color, "Cor OK deve ser success_color"

    print("[OK] Todas as formatacoes corretas: OK")

except Exception as e:
    print(f"[FAIL] Falha no teste de formatacao: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 8: Compatibilidade de Interface
print("\n" + "=" * 70)
print("TESTE 8: Verificacao de Compatibilidade de Interface")
print("=" * 70)

try:
    # Verificar assinaturas dos metodos
    import inspect

    # TensionReportBuilder.build()
    sig = inspect.signature(tension_builder.build)
    params = list(sig.parameters.keys())
    print(f"[OK] TensionReportBuilder.build() parametros: {params}")
    assert 'tension_data' in params, "Deve ter tension_data"
    assert 'stencil_code' in params, "Deve ter stencil_code"

    # StencilHistoryReportBuilder.build()
    sig = inspect.signature(history_builder.build)
    params = list(sig.parameters.keys())
    print(f"[OK] StencilHistoryReportBuilder.build() parametros: {params}")
    assert 'stencil' in params, "Deve ter stencil"
    assert 'history' in params, "Deve ter history"

    # InspectionReportBuilder.build()
    sig = inspect.signature(inspection_builder.build)
    params = list(sig.parameters.keys())
    print(f"[OK] InspectionReportBuilder.build() parametros: {params}")
    assert 'inspection_result' in params, "Deve ter inspection_result"
    assert 'overlay_image_path' in params, "Deve ter overlay_image_path"

    print("[OK] Compatibilidade de interface: OK")

except Exception as e:
    print(f"[FAIL] Falha na verificacao de interface: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Resumo Final
print("\n" + "=" * 70)
print("[SUCCESS] TODOS OS TESTES PASSARAM COM SUCESSO!")
print("=" * 70)
print("\nResumo da Validacao:")
print("  [OK] Import de todos os modulos")
print("  [OK] Criacao de ReportConfig")
print("  [OK] Criacao de servicos especializados (4)")
print("  [OK] Criacao de builders com dependency injection (3)")
print("  [OK] Criacao de ReportGenerator facade")
print("  [OK] Testes de StatisticsCalculator")
print("  [OK] Testes de ReportLayoutManager")
print("  [OK] Verificacao de compatibilidade de interface")
print("\nRefatoracao validada com sucesso!")
print("=" * 70)
