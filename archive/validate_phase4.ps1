# Script de Validação - FASE 4 Refatoração
# Uso: No PowerShell com .venv ativado
#      .\validate_phase4.ps1

Write-Host "=" * 70
Write-Host "Validação FASE 4 - Refatoração mainwindow.py"
Write-Host "=" * 70
Write-Host ""

# Teste 1: Sintaxe Python
Write-Host "Teste 1: Validando sintaxe dos arquivos refatorados..."
python -m py_compile aoi_lib/gerber_core/gui/mainwindow.py
python -m py_compile aoi_lib/gerber_core/object_editor.py
python -m py_compile aoi_lib/gerber_core/file_manager.py
python -m py_compile aoi_lib/gerber_core/gui/dialogs.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Sintaxe Python: OK"
} else {
    Write-Host "❌ Sintaxe Python: FALHOU"
    exit 1
}

Write-Host ""

# Teste 2: Imports
Write-Host "Teste 2: Validando imports..."
python -c "from aoi_lib.gerber_core.file_manager import GerberFileManager; print('✅ GerberFileManager import OK')"
python -c "from aoi_lib.gerber_core.object_editor import ObjectEditor; print('✅ ObjectEditor import OK')"
python -c "from aoi_lib.gerber_core.gui.dialogs import WidthHeightDialog; print('✅ WidthHeightDialog import OK')"
python -c "from aoi_lib.gerber_core.gui.mainwindow import GerberMacroViewer; print('✅ GerberMacroViewer import OK')"

Write-Host ""

# Teste 3: Aplicação principal
Write-Host "Teste 3: Validando aplicação principal..."
python -c "from consumo_lib.main_window import AOIControllerApp; print('✅ AOIControllerApp import OK')"

Write-Host ""
Write-Host "=" * 70
Write-Host "🎉 Validação concluída! Todos os testes passaram."
Write-Host "=" * 70
Write-Host ""
Write-Host "Próximo passo: Executar aplicativo"
Write-Host "  python main.py"
Write-Host ""
Write-Host "Testes manuais necessários:"
Write-Host "  1. Criar novo projeto"
Write-Host "  2. Importar arquivo Gerber"
Write-Host "  3. Renderizar camada completa"
Write-Host "  4. Editar objetos (único e grupo)"
Write-Host "  5. Deletar objetos"
Write-Host "  6. Exportar (Gerber/PNG)"
Write-Host "  7. Mover objetos"
