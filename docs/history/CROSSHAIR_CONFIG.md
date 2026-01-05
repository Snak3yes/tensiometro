# Configuração da Cruz de Centralização

## Funcionalidade

Permite personalizar a aparência da cruz de centralização exibida no preview da câmera.

## Como Acessar

**Menu:** Ferramentas → ✛ Configurar Cruz de Centralização

## Configurações Disponíveis

### 1. **Cor da Linha**
- Seletor de cor visual
- Suporta qualquer cor RGB
- Padrão: Vermelho (R:0, G:0, B:255)

### 2. **Espessura**
- Faixa: 1 a 10 pixels
- Padrão: 2 pixels
- **Recomendação para calibração**: 3-5 pixels

### 3. **Comprimento**
- Faixa: 1% a 50% da menor dimensão da imagem
- Padrão: 5%
- **Recomendação para calibração**: 15-25%

## Caso de Uso: Calibração FOV

Para facilitar a calibração do campo de visão (FOV) com régua:

1. **Abra o diálogo de configuração:**
   - Menu → Ferramentas → ✛ Configurar Cruz de Centralização

2. **Configure para calibração:**
   - **Comprimento**: 20-25% (cruz mais longa)
   - **Espessura**: 4-5 px (mais visível)
   - **Cor**: Verde ou Azul (contraste com régua vermelha)

3. **Use para calibração:**
   - Posicione a régua alinhada com a cruz horizontal
   - Meça a largura visível
   - A cruz longa facilita o alinhamento preciso

4. **Após calibração:**
   - Restaure para valores padrão (botão "Restaurar Padrão")
   - Ou mantenha se preferir uma cruz mais visível

## Valores Recomendados

### Uso Normal
- Comprimento: 5%
- Espessura: 2 px
- Cor: Vermelho

### Calibração/Alinhamento
- Comprimento: 20-25%
- Espessura: 4-5 px
- Cor: Verde ou Azul (contraste)

### Inspeção Visual
- Comprimento: 10-15%
- Espessura: 2-3 px
- Cor: Contraste com o material (branco/preto)

## Arquivos Modificados

- `aoi_lib/config_manager.py` - Adicionada seção `camera.crosshair`
- `consumo_lib.py` - Método `display_image` usa configurações
- `aoi_lib/crosshair_settings.py` - Diálogo de configuração (NOVO)

## Armazenamento

As configurações são salvas em `aoi_config.json`:
```json
{
  "camera": {
    "crosshair": {
      "color_r": 0,
      "color_g": 0,
      "color_b": 255,
      "thickness": 2,
      "length_percent": 5
    }
  }
}
```
