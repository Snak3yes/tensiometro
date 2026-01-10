# Initial Concept
E:\PycharmProjects\Tensiometro

# Guia do Produto

## Visão do Produto
Sistema de automação industrial para controle de qualidade de stencils, integrando medição de tensão superficial e inspeção visual automática (AOI). O sistema visa garantir a integridade e limpeza dos stencils através de comparação com arquivos Gerber e controle preciso de hardware via CLP.

## Perfis de Usuário
O sistema adota um modelo de permissões hierárquico:
- **Operadores:** Foco na execução e simplicidade. Apenas selecionam programas/receitas predefinidas e iniciam o processo de inspeção/medição.
- **Qualidade:** Foco em análise e relatórios. Acesso ao histórico de medições para gerar relatórios individuais, de tendências e gráficos temporais.
- **Engenharia:** Acesso irrestrito. Responsáveis pela criação de receitas, configuração de parâmetros de comunicação (CLP), ajustes de eixos e manutenção do sistema.

## Objetivos Principais
1. **Automação de Medição:** Executar medição de tensão em múltiplos pontos predefinidos de forma autônoma.
2. **Inspeção Visual (AOI):** Validar limpeza e desobstrução de furos comparando captura de imagem com arquivos Gerber originais.
3. **Rastreabilidade:** Centralizar o gerenciamento de receitas e garantir rastreabilidade completa através de logs e banco de dados.

## Funcionalidades Chave
- **Interface (GUI):** Design intuitivo para seleção de receitas.
- **Visão Computacional:** Algoritmos precisos para alinhamento via fiduciais e detecção de obstruções.
- **Controle de Hardware:** Comunicação robusta com CLP para controle preciso de eixos e movimentação coordenada.
- **Gestão de Dados e Relatórios:**
    - Armazenamento em banco de dados associado ao código único do stencil.
    - Funcionalidade de busca por medição específica ou período.
    - Geração de relatórios variados: Medição individual, análise de tendência e gráficos de evolução temporal.
