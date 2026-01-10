# Stack Tecnológica

## Core
- **Linguagem:** Python 3.x
- **Interface Gráfica (GUI):** PyQt6 (Framework principal para desenvolvimento da interface moderna e minimalista).
- **Arquitetura de Serviços:** Implementada camada de orquestração (MovementOrchestrator, InspectionFlowService) para desacoplar lógica de negócio da interface Qt.

## Hardware & Automação
- **Comunicação CLP:** PyModbus (Protocolo Modbus TCP/RTU para interação com o CLP e controle de eixos).
- **Comunicação Serial:** PySerial (Para periféricos ou sensores que utilizam interface serial).

## Processamento & Visão
- **Visão Computacional:** OpenCV (Processamento de imagens para alinhamento e detecção de obstruções).
- **Cálculo Numérico:** NumPy (Suporte para operações matriciais e processamento de dados).
- **Visualização de Dados:** Matplotlib (Geração de gráficos para análise de tendências e medições).

## Utilitários & Relatórios
- **Gerador de PDF:** ReportLab (Criação de relatórios de inspeção e medição personalizados).

## Qualidade & Desenvolvimento
- **Framework de Testes:** Pytest (Testes unitários e de integração).
- **Cobertura de Testes:** Coverage.py.
- **Testes Unitários:** Implementada suite de testes unitários para gerenciamento de configuração e persistência de dados.
