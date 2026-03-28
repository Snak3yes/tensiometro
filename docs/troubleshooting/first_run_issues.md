# Resolução de Problemas de Primeira Execucao

## Problema
Na primeira execucao apos um periodo sem trabalhar no projeto, ocorre um `KeyboardInterrupt` durante o carregamento de modulos.

## Causa Raiz
1. **Versoes Python conflitantes**: O sistema tem Python 3.14 instalado, mas o projeto usa Python 3.10 (venv)
2. **Caches incompativeis**: Caches .pyc de versoes diferentes podem causar conflitos
3. **Windows Defender**: Na primeira leitura de arquivos "frios", o antivirus pode bloquear temporariamente

## Solucao

### 1. Sempre usar Python do venv
```powershell
# CORRETO
.venv/Scripts/python.exe main.py

# INCORRETO (usa Python 3.14 do sistema)
python main.py
```

### 2. Limpar cache antes de trabalhar
```powershell
.venv/Scripts/python.exe tools/clear_cache.py
```

### 3. Executar a aplicacao
```powershell
.venv/Scripts/python.exe main.py
```

## Configuracao do VS Code

Certifique-se de que o VS Code esta usando o Python correto:

1. `Ctrl+Shift+P` -> "Python: Select Interpreter"
2. Selecione: `./.venv/Scripts/python.exe` (Python 3.10)

## Verificacao

Para verificar qual Python esta sendo usado:
```powershell
# Python do venv
.venv/Scripts/python.exe --version
# Deve mostrar: Python 3.10.11

# Python do sistema
python --version
# Pode mostrar: Python 3.14.x
```

## Warmup Automatico

O `main.py` agora inclui um mecanismo de "warmup" que pre-carrega os modulos antes de iniciar a aplicacao. Isso permite que o Windows Defender escaneie os arquivos antes da execucao critica.

## Se o problema persistir

1. Adicione a pasta do projeto aos exclusions do Windows Defender
2. Reinicie o terminal/PowerShell
3. Execute `tools/clear_cache.py` novamente