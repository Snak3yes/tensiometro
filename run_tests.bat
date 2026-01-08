@echo off
REM Wrapper para executar testes do projeto Tensiometro
REM Este arquivo chama o script principal em tests/scripts/

REM Executar o script principal
CALL tests\scripts\run_tests.bat %*
