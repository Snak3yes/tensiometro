@echo off
REM Script para executar testes do projeto Tensiometro
REM Uso: run_tests.bat [opcoes]

SETLOCAL EnableDelayedExpansion

SET PYTEST_CMD=pytest
SET COVERAGE_FLAG=--cov=aoi_lib --cov=consumo_lib
SET COVERAGE_REPORTS=--cov-report=html:htmlcov --cov-report=term-missing
SET VERBOSE_FLAG=-v
SET MARKERS=

REM Parse argumentos
:parse_args
IF "%1"=="--fast" (
    SET MARKERS=-m "not slow and not hardware"
    echo [INFO] Modo rapido: excluindo testes lentos
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--unit" (
    SET MARKERS=-m unit
    echo [INFO] Executando apenas testes unitarios
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--integration" (
    SET MARKERS=-m integration
    echo [INFO] Executando apenas testes de integracao
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--no-cov" (
    SET COVERAGE_FLAG=
    SET COVERAGE_REPORTS=
    echo [INFO] Coverage desabilitado
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--html" (
    SET OPEN_BROWSER=1
    echo [INFO] Abrira coverage no navegador
    SHIFT
    GOTO :parse_args
)
IF "%1"=="-h" (
    echo Uso: %0 [opcoes]
    echo   --fast      Apenas testes rapidos
    echo   --unit      Apenas testes unitarios
    echo   --integration Apenas testes de integracao
    echo   --no-cov    Desabilita coverage
    echo   --html      Abre coverage no navegador
    echo   -h          Mostra este help
    GOTO :EOF
)

REM Verificar ambiente virtual
IF "%VIRTUAL_ENV%"=="" (
    echo [WARN] Ativando ambiente virtual...
    IF EXIST .venv\Scripts\activate.bat (
        CALL .venv\Scripts\activate.bat
    ) ELSE (
        echo [ERROR] .venv nao encontrado. Crie o ambiente virtual primeiro.
        EXIT /B 1
    )
)

REM Executar testes
echo [INFO] Executando testes...
echo.

%PYTEST_CMD% %VERBOSE_FLAG% %MARKERS% %COVERAGE_FLAG% %COVERAGE_REPORTS%

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo [INFO] ========================================
    echo [INFO] ✅ Todos os testes passaram!
    echo [INFO] ========================================
    IF DEFINED OPEN_BROWSER (
        echo [INFO] Abrindo coverage no navegador...
        start htmlcov\index.html
    )
) ELSE (
    echo.
    echo [INFO] ========================================
    echo [ERROR] ❌ Alguns testes falharam!
    echo [INFO] ========================================
)

ENDLOCAL
