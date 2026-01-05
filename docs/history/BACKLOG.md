# 📋 BACKLOG - Sistema AOI Tensiômetro

**Última atualização:** 12/12/2024  
**Status do Projeto:** ~99.5% concluído

---

## 🎯 Prioridades Imediatas

### 🔴 CRÍTICO - Para Produção

#### 1. **Validação com Hardware Real**
**Descrição:** Testar todas as funcionalidades com stencil real montado na máquina  
**Tasks:**
- [ ] Calibrar FOV com régua/padrão conhecido
- [ ] Testar movimento por clique em diferentes alturas Z
- [ ] Validar homing e limites de software
- [ ] Executar medição de tensão completa (grid NxN)
- [ ] Realizar inspeção visual com fiduciais
- [ ] Verificar precisão de movimento com passo 0.01mm
- [ ] Testar backlight e qualidade de imagem
- [ ] Validar geração de relatórios PDF

**Prioridade:** 🔴 CRÍTICA  
**Estimativa:** 2-3 dias  
**Bloqueadores:** Acesso ao hardware

---

#### 2. **Documentação de Operador**  
**Descrição:** Manual passo-a-passo para operação diária  
**Tasks:**
- [ ] Procedimento de startup (ligar equipamento, conectar)
- [ ] Workflow completo: identificação → medição → inspeção → relatório
- [ ] Troubleshooting de erros comuns
- [ ] Manutenção preventiva (limpeza de câmera, backlight)
- [ ] Calibrações periódicas (FOV, tensiômetro)
- [ ] Guia de interpretação de resultados

**Prioridade:** 🔴 CRÍTICA  
**Estimativa:** 2 dias  
**Formato:** PDF + vídeos curtos

---

#### 3. **Backup Automatizado**
**Descrição:** Sistema de backup dos dados críticos  
**Tasks:**
- [ ] Backup automático diário do banco SQLite
- [ ] Backup das configurações (`aoi_config.json`)
- [ ] Backup de receitas
- [ ] Exportação periódica para CSV
- [ ] Rotação de backups (manter últimos 30 dias)
- [ ] Notificação em caso de falha

**Prioridade:** 🔴 CRÍTICA  
**Estimativa:** 1 dia  
**Tecnologia:** Python `shutil`, `schedule` ou cron

---

## 🟡 IMPORTANTE - Curto Prazo

### 4. **Validação da Calibração FOV**
**Descrição:** Verificar precisão da calibração pixel↔mm  
**Tasks:**
- [ ] Criar padrão de calibração impresso (grid de pontos conhecidos)
- [ ] Medir erro de conversão pixel→mm
- [ ] Documentar valores aceitáveis de erro (±X%)
- [ ] Criar procedimento de re-calibração

**Prioridade:** 🟡 IMPORTANTE  
**Estimativa:** 4 horas  

---

### 5. **Otimização de Performance**
**Descrição:** Melhorar velocidade de operações críticas  
**Tasks:**
- [ ] Perfilar código de geração de mosaico
- [ ] Otimizar renderização Gerber (cache de polígonos)
- [ ] Paralelizar processamento de imagens (ThreadPoolExecutor)
- [ ] Reduzir latência de movimento (otimizar polling do PLC)
- [ ] Benchmark de operações demoradas

**Prioridade:** 🟡 IMPORTANTE  
**Estimativa:** 2 dias  

---

### 6. **Gestão de Erros Melhorada**
**Descrição:** Sistema robusto de tratamento e log de erros  
**Tasks:**
- [ ] Implementar retry automático para conexão PLC
- [ ] Melhorar mensagens de erro para o usuário (menos técnicas)
- [ ] Sistema de logs estruturado (WARNING/ERROR/CRITICAL)
- [ ] Arquivo de log rotativo (evitar crescimento infinito)
- [ ] Exportar logs para diagnóstico remoto

**Prioridade:** 🟡 IMPORTANTE  
**Estimativa:** 1 dia  

---

## 🟢 DESEJÁVEL - Médio Prazo

### 7. **Dashboard de Estatísticas**
**Descrição:** Visão geral de performance dos stencils  
**Features:**
- [ ] Gráfico de tendência de tensão por stencil
- [ ] Ranking de stencils (melhores/piores)
- [ ] Alertas de degradação
- [ ] Estatísticas de uso (quantas medições por stencil)
- [ ] Previsão de vida útil

**Prioridade:** 🟢 DESEJÁVEL  
**Estimativa:** 3 dias  
**Tecnologia:** matplotlib + PyQt6

---

### 8. **Configurações Avançadas de Câmera**
**Descrição:** Controles adicionais para qualidade de imagem  
**Features:**
- [ ] Presets de configuração (Tensão, Inspeção, Calibração)
- [ ] Ajuste automático de exposição por região
- [ ] Correção de distorção (checkerboard calibration)
- [ ] Suporte a múltiplas câmeras (alternância)
- [ ] Gravação de vídeo durante operação (debug)

**Prioridade:** 🟢 DESEJÁVEL  
**Estimativa:** 2 dias  

---

### 9. **Exportação de Dados**
**Descrição:** Formatos adicionais de exportação  
**Features:**
- [ ] Exportar histórico para Excel (.xlsx)
- [ ] API REST para integração com MES/ERP
- [ ] Webhook para notificações em sistemas externos
- [ ] Export batch de todos os stencils (ZIP)
- [ ] Importação de stencils de outro sistema

**Prioridade:** 🟢 DESEJÁVEL  
**Estimativa:** 2 dias  
**Tecnologia:** openpyxl, FastAPI

---

## 🔵 FUTURO - Longo Prazo

### 10. **Machine Learning para Previsão**
**Descrição:** Prever falhas baseado em histórico  
**Features:**
- [ ] Modelo de ML para prever degradação
- [ ] Anomaly detection (detectar comportamentos anormais)
- [ ] Recomendação automática de limpeza/troca
- [ ] Dashboard de confiabilidade

**Prioridade:** 🔵 FUTURO  
**Estimativa:** 1-2 semanas  
**Tecnologia:** scikit-learn ou TensorFlow

---

### 11. **Controle de Acesso e Usuários**
**Descrição:** Sistema multi-usuário com permissões  
**Features:**
- [ ] Login de operadores
- [ ] Níveis de acesso (Operador, Engenheiro, Admin)
- [ ] Auditoria de ações (quem fez o quê)
- [ ] Assinatura eletrônica em relatórios
- [ ] Rastreamento de responsável por calibrações

**Prioridade:** 🔵 FUTURO  
**Estimativa:** 1 semana  

---

### 12. **Modo Offline e Sincronização**
**Descrição:** Operar sem conexão de rede  
**Features:**
- [ ] Armazenar dados localmente durante offline
- [ ] Sincronizar com servidor central quando online
- [ ] Queue de relatórios pendentes
- [ ] Resolução de conflitos de dados

**Prioridade:** 🔵 FUTURO  
**Estimativa:** 1 semana  

---

## 🐛 BUGS CONHECIDOS

### ✅ Resolvidos na Sessão 12/12/2024
1. ~~Movimento invertido no eixo Y ao clicar no vídeo~~ ✅
2. ~~Notação científica no campo Step Size~~ ✅
3. ~~Erro ao salvar calibração FOV (ConfigAdapter)~~ ✅
4. ~~Calibração FOV complexa desnecessária para câmera fixa~~ ✅
5. ~~Step Size limitado a ≥0.1mm~~ ✅

### 🔍 A Investigar
*(Nenhum bug conhecido no momento)*

---

## 🎨 MELHORIAS DE UI/UX

### Interface
- [ ] Modo escuro (dark theme)
- [ ] Atalhos de teclado customizáveis
- [ ] Barra de status mais informativa (% progresso, ETA)
- [ ] Indicador visual de conexão com dispositivos
- [ ] Tooltip com informações de contexto

### Acessibilidade
- [ ] Fontes maiores para operadores com dificuldade visual
- [ ] Contraste ajustável
- [ ] Sons de feedback (opcional)
- [ ] Modo daltonismo

### Produtividade
- [ ] Favoritos de posições CNC
- [ ] Templates de relatório
- [ ] Histórico de comandos (undo/redo limitado)
- [ ] Quick actions (F-keys para ações comuns)

---

## 📊 MÉTRICAS E KPIs

### Implementar Tracking de:
- [ ] Tempo médio de medição completa
- [ ] Taxa de aprovação de stencils (OK/WARNING/NOK)
- [ ] Número de medições por dia
- [ ] Disponibilidade do equipamento (uptime)
- [ ] Frequência de calibrações
- [ ] Stencils mais/menos usados

---

## 🔧 MANUTENÇÃO TÉCNICA

### Código
- [ ] Refatorar `consumo_lib.py` (quebrar em módulos menores)
- [ ] Type hints completos em todos os arquivos
- [ ] Documentação inline (docstrings) completa
- [ ] Testes unitários (pytest)
- [ ] Integração contínua (CI/CD)

### Dependências
- [ ] Atualizar para versões mais recentes (PyQt6, OpenCV)
- [ ] Congelar versões exatas (requirements.txt)
- [ ] Testar compatibilidade com Python 3.11+
- [ ] Remover dependências não utilizadas

---

## 📚 DOCUMENTAÇÃO TÉCNICA

### Pendente
- [ ] Arquitetura do sistema (diagramas UML)
- [ ] Fluxo de dados (diagramas de sequência)
- [ ] API interna (documentação de classes)
- [ ] Protocolo Modbus usado (mapeamento de coils/registros)
- [ ] Especificação de hardware compatível

### Existente
- ✅ ROADMAP_DESENVOLVIMENTO.md
- ✅ CORRECOES_FOV_CALIBRATION.md
- ✅ CROSSHAIR_CONFIG.md
- ✅ CHANGELOG_2025-12-12.md
- ✅ NOTAS_TECNICAS.md
- ✅ GUIA_MIGRACAO_SQLITE.md

---

## 🎓 TREINAMENTO

### Material Necessário
- [ ] Vídeo: Calibração inicial do sistema
- [ ] Vídeo: Execução de medição padrão
- [ ] Vídeo: Como interpretar relatórios
- [ ] Vídeo: Troubleshooting básico
- [ ] FAQ com perguntas comuns
- [ ] Certificação de operadores (opcional)

---

## 🚀 ROADMAP 2025

### Q1 2025 (Jan-Mar)
- Validação completa com hardware
- Documentação de operador
- Backup automatizado
- Dashboard de estatísticas

### Q2 2025 (Abr-Jun)
- API REST básica
- Exportação Excel
- Otimizações de performance
- Testes de stress

### Q3 2025 (Jul-Set)
- Machine Learning (fase exploratória)
- Controle de acesso
- Modo offline

### Q4 2025 (Out-Dez)
- Integração com sistemas externos (MES/ERP)
- Melhorias de UI baseadas em feedback
- Auditoria e compliance

---

## 📝 Notas Importantes

### Decisões de Design
1. **SQLite vs PostgreSQL:** SQLite escolhido por simplicidade e ausência de servidor
2. **PyQt6 vs Web:** Desktop escolhido por ser ambiente industrial (sem navegador)
3. **JSON vs YAML:** JSON para compatibilidade com JavaScript (futuro web dashboard)

### Limitações Conhecidas
1. **Thread-safety:** Alguns widgets PyQt6 não são thread-safe (usar signals)
2. **Modbus timeout:** Conexão pode falhar em redes instáveis
3. **Memória:** Mosaicos muito grandes podem consumir muita RAM

### Dependências Externas
- **Hardware:** PLC Delta, Tensiômetro AS-120N, Câmera USB
- **Rede:** Endereço IP fixo para PLC (recomendado)
- **Sistema:** Windows 10+ (testado), Linux compatível mas não testado

---

**Última revisão:** 12/12/2024  
**Próxima revisão sugerida:** 19/12/2024 (após testes com hardware)
