# Authentication Configuration Feature

## Overview
Adicionar configuração de autenticação no menu Engenharia, permitindo que usuários com permissão de Engineering (ou superior) configurem o comportamento de login ao iniciar a aplicação, incluindo a opção de desabilitar a solicitação de senha e definir um login padrão de inicialização.

## Functional Requirements

### FR1: Menu de Configuração
- Localização: Menu Engenharia → "Configurações de Autenticação..."
- Apenas usuários com role `engineering` ou `admin` devem ter acesso a esta opção
- Usuários `operator` ou `quality` não visualizam esta opção de menu

### FR2: Diálogo de Configuração
- Checkbox: "Solicitar login ao iniciar" (default: marcado/True)
- Quando marcado: aplicação exibe diálogo de login normal ao iniciar
- Quando desmarcado: aplicação inicia diretamente no login padrão
- Combo box: "Login padrão" com opções: Operator, Engineering, Quality, Admin (default: Operator)
- Botão "Aplicar" (habilitado apenas quando há mudanças)
- Botão "Cancelar"

### FR3: Confirmação de Modificação
- Quando usuário desmarca "Solicitar login ao iniciar" e clica em "Aplicar":
  1. Sistema exibe novamente o diálogo de login padrão
  2. Usuário deve digitar usuário e senha de confirmação
  3. Sistema valida credenciais
  4. Se válidas, aplicação da configuração
  5. Se inválidas, mensagem de erro e configuração NÃO é aplicada

### FR4: Comportamento ao Iniciar Aplicação
- **Modo normal (login solicitado)**: Aplicação exibe diálogo de login ao iniciar
- **Modo auto-login (não solicitado)**: Aplicação inicia diretamente já logada no login padrão configurado
- Nenhuma notificação ou diálogo adicional é exibido no modo auto-login

### FR5: Armazenamento de Configuração
- Local: `config/aoi_config.json`
- Nova seção: `authentication`
- Campos:
  ```json
  "authentication": {
    "require_login_on_startup": true,
    "default_role": "operator"
  }
  ```

### FR6: Auditoria
- Toda modificação na configuração de autenticação deve ser registrada no log do sistema
- Log deve incluir: timestamp, usuário, ação executada, valores antigo e novo
- Exemplo: `[2026-01-15 10:30:00] AUTH_CONFIG: user=eng, action=change_require_login, old=true, new=false`

### FR7: Validação de Permissões
- Apenas usuários com role `engineering` ou `admin` podem modificar configuração
- Tentativa de modificação por usuário não autorizado deve exibir mensagem:
  ```
  "Permissão Insuficiente"

  Esta configuração requer permissão de Engenharia ou superior.
  ```

## Non-Functional Requirements

### NFR1: Segurança
- Confirmação por senha deve usar o mesmo AuthService do login padrão
- Senha não deve ser armazenada em plaintext no arquivo de configuração
- Apenas a role padrão é persistida, não credenciais

### NFR2: Performance
- Leitura da configuração ao startup deve adicionar <10ms ao tempo de inicialização
- Validação de permissões deve ser instantânea (<5ms)

### NFR3: Usabilidade
- Mudanças na configuração devem ter efeito imediato após confirmação
- Interface deve seguir o padrão visual dos outros diálogos de configuração
- Tooltips devem estar disponíveis para explicar cada opção

### NFR4: Compatibilidade
- Se a seção `authentication` não existir no `aoi_config.json`, usar valores padrão (require_login=true, default_role=operator)
- Configuração deve ser backward compatible com instalações que não têm esta feature

## Acceptance Criteria

### AC1: Menu Acessível
- [ ] Usuário Engineering visualiza opção de menu "Configurações de Autenticação"
- [ ] Usuário Operator NÃO visualiza esta opção
- [ ] Clique na opção abre diálogo de configuração

### AC2: Diálogo Funcional
- [ ] Diálogo exibe checkbox "Solicitar login ao iniciar" (marcado por padrão)
- [ ] Diálogo exibe combo "Login padrão" (Operator por padrão)
- [ ] Botão "Aplicar" habilitado apenas quando há mudanças
- [ ] Botão "Cancelar" fecha diálogo sem salvar

### AC3: Modificação Requer Confirmação
- [ ] Ao desmarcar checkbox e clicar Aplicar, diálogo de login é exibido
- [ ] Senha incorreta não aplica mudança e exibe erro
- [ ] Senha correta aplica mudança e fecha diálogo

### AC4: Auto-Login Funciona
- [ ] Com `require_login_on_startup=false`, aplicação inicia sem diálogo
- [ ] Aplicação inicia diretamente logada na role configurada em `default_role`
- [ ] Log da aplicação confirma auto-login realizado

### AC5: Reversão Funciona
- [ ] Engineering pode reativar login marcando checkbox novamente
- [ ] Reversão também requer confirmação por senha
- [ ] Próximo inicio exibe diálogo de login normalmente

### AC6: Auditoria Funciona
- [ ] Modificações são registradas no log com todos os campos
- [ ] Log inclui valores antigo e novo da configuração

### AC7: Validação de Permissões
- [ ] Operator tentando acessar configuração recebe mensagem de permissão negada
- [ ] Quality recebe mensagem de permissão negada
- [ ] Engineering e Admin podem acessar normalmente

### AC8: Cobertura de Testes
- [ ] Testes unitários para lógica de configuração (AuthConfigManager)
- [ ] Testes de integração para diálogo (AuthenticationSettingsDialog)
- [ ] Testes de validação de permissões
- [ ] Testes de fluxo de confirmação por senha
- [ ] Cobertura mínima de 80%

## Out of Scope

- Não está no escopo:
  - Alteração do diálogo de login existente (LoginDialog)
  - Criação de novos roles ou permissões
  - Sistema de múltiplos usuários simultâneos
  - Timeout de sessão ou auto-logout
  - Integração com LDAP/Active Directory
  - Criptografia de arquivo de configuração
  - Interface para reset de senha

## Implementation Notes

### Componentes a Criar/Modificar:

1. **Novo: `consumo_lib/dialogs/auth_settings_dialog.py`**
   - Dialog de configuração de autenticação
   - Interface com checkbox e combo box
   - Lógica de confirmação por senha

2. **Novo: `consumo_lib/managers/auth_config_manager.py`**
   - Gerenciador de configuração de autenticação
   - Lê/escreve seção `authentication` do aoi_config.json
   - Valida permissões de modificação
   - Registra mudanças no log

3. **Modificar: `aoi_lib/config_manager.py`**
   - Adicionar seção `authentication` ao `_DEFAULT_CFG`
   - Adicionar métodos helpers para ler/escrever config de autenticação

4. **Modificar: `consumo_lib/handlers/menu_handler.py`**
   - Adicionar action "Configurações de Autenticação..." no menu Engenharia
   - Verificar permissões antes de exibir

5. **Modificar: `consumo_lib/coordinators/setup_coordinator.py`**
   - Ler configuração de autenticação ao inicializar
   - Implementar auto-login se configurado

6. **Modificar: `config/aoi_config.json`**
   - Adicionar seção `authentication` (migration automática)

### Arquitetura:

```
AuthenticationSettingsDialog (UI)
    ├── usa → AuthConfigManager (lógica de negócio)
    │   ├── usa → AOIConfigManager (persistência)
    │   └── usa → AuthService (validação de senha)
    └── usa → RoleManager (verificação de permissões)
```
