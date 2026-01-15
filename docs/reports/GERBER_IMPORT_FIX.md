# Correção de Bug - Importação Gerber
**Data:** 2026-01-15
**Status:** 🔧 EM INVESTIGAÇÃO

## Problema Reportado

**Erro:** `unsupported operand type(s) for /: 'NoneType' and 'int'`

**Contexto:** Ao tentar carregar um arquivo Gerber.

## Análise Inicial

O erro indica que uma divisão está sendo realizada com `None` como operando. Isso pode ocorrer em vários pontos:

1. **`parse_gerber_config`** pode não estar parseando corretamente o formato
2. **`build_layer_objects_mm`** pode estar tentando dividir por um valor None do `gerber_cfg`
3. **Conversão de coordenadas** pode estar usando valores None

## Correções Aplicadas

### 1. Melhoria no Tratamento de Erros

**Arquivo:** `aoi_lib/gerber_core/file_manager.py`

**Antes:**
```python
except Exception:
    traceback.print_exc()
    QMessageBox.critical(...)
```

**Depois:**
```python
except Exception as e:
    traceback.print_exc()
    QMessageBox.critical(
        self._parent_window,
        "Erro ao gerar camada completa",
        f"Ocorreu um erro ao processar a camada completa.\n\n"
        f"Erro: {e}\n\n"
        f"Veja o terminal para detalhes.",
    )
    return False
```

**Benefício:** Agora a mensagem de erro será exibida com detalhes.

---

### 2. Validação de `gerber_cfg.format`

**Arquivo:** `aoi_lib/gerber_core/file_manager.py`

```python
# Verificar se gerber_cfg tem os campos necessários
print(f"[DEBUG] gerber_cfg: {self.gerber_cfg}")
print(f"[DEBUG] gerber_cfg.format: {getattr(self.gerber_cfg, 'format', 'NOT_SET')}")

if not hasattr(self.gerber_cfg, 'format') or self.gerber_cfg.format is None:
    QMessageBox.critical(
        self._parent_window,
        "Erro de configuração",
        "O arquivo Gerber não possui informações de formato (FS/FSA).\n"
        "Não é possível interpretar as coordenadas.",
    )
    return False
```

**Benefício:**
- Detecta arquivos Gerber malformados
- Fornece mensagem de erro mais clara
- Adiciona logs de debug

---

## Instruções para Teste

### 1. Execute o Aplicativo

```powershell
# No PowerShell (com .venv ativado)
python main.py
```

### 2. Tente Importar o Arquivo Gerber

- Menu: Arquivo → Importar arquivo .gbr
- Selecione o arquivo que causou o erro

### 3. Observe as Mensagens

**Se o erro persistir:**
- Anote a mensagem completa de erro exibida no QMessageBox
- Copie o traceback do terminal
- Preste atenção aos logs `[DEBUG]`

**Informações necessárias:**
1. Mensagem de erro completa
2. Traceback do terminal
3. Linha onde o erro ocorreu
4. Conteúdo do arquivo Gerber (se possível compartilhar)

---

## Possíveis Causas Raiz

### Causa 1: Arquivo Gerber Malformado
O arquivo pode não ter as declarações `FS` (Format Specification) necessárias.

**Solução:** Verificar se o arquivo tem linhas como:
```
%FSLAX23Y23*%
%MOIN*%
```

### Causa 2: Parser `parse_gerber_config` Falhando
O parser pode estar retornando `None` ou um objeto incompleto.

**Solução:** Adicionar validação no parser.

### Causa 3: Campos None em `gerber_cfg`
O `gerber_cfg` pode ter campos obrigatórios como `None`.

**Solução:** Validar todos os campos obrigatórios antes de usar.

---

## Próximos Passos (Dependendo do Resultado)

### Se o Erro Persistir:

1. **Obter Stack Trace Completo**
   - Execute o aplicativo novamente
   - Copie TODO o traceback do terminal
   - Anote a linha exata do erro

2. **Adicionar Mais Validações**
   - Validar `parse_gerber_config` retorno
   - Validar todos os campos de `gerber_cfg`
   - Adicionar try/except em `build_layer_objects_mm`

3. **Investigar Parser**
   - Verificar `aoi_lib/gerber_core/config.py`
   - Adicionar logs no `parse_gerber_config`
   - Testar com diferentes arquivos Gerber

### Se o Erro For Corrigido:

1. ✅ Testar com outros arquivos Gerber
2. ✅ Validar todas as funcionalidades
3. ✅ Remover logs de debug
4. ✅ Documentar a solução

---

## Logs Esperados

### Com Sucesso:
```
[DEBUG] gerber_cfg: GerberConfig(format=Format(n=0, m=2), ...)
[DEBUG] gerber_cfg.format: Format(n=0, m=2)
```

### Com Erro:
```
[DEBUG] gerber_cfg: GerberConfig(format=None, ...)
[DEBUG] gerber_cfg.format: NOT_SET
Erro de configuração: O arquivo Gerber não possui informações de formato...
```

---

**Relatório criado:** 2026-01-15
**Status:** Aguardando feedback do usuário com traceback completo
