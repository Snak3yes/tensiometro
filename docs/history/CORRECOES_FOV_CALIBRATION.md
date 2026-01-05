# Correções na Calibração de Campo de Visão (FOV)

## Data: 2025-12-12

## Problemas Identificados

### 1. Calibração desnecessária com múltiplas alturas Z
**Problema Original:**
- A calibração FOV foi inspirada na aplicação "adesivadora"
- Na adesivadora, a câmera está posicionada na **parte móvel** do eixo Z
- No tensiômetro, a câmera está posicionada na **parte fixa** do eixo Z
- Portanto, no tensiômetro o FOV **NÃO varia** com a altura Z
- A calibração em dois pontos (Z alto e Z baixo) era desnecessária

### 2. Movimento invertido no eixo Y
**Problema Original:**
- Quando o usuário clicava sobre uma posição, a head se movia no sentido **oposto** em Y
- O movimento em X estava correto
- **Causa raiz:** Sistema de coordenadas de imagem vs CNC
  - Coordenadas de imagem: origem no topo-esquerdo, Y cresce para **baixo**
  - Coordenadas CNC: Y cresce para **cima**
  - A inversão estava sendo aplicada incorretamente

---

## Correções Implementadas

### 1. Simplificação da Calibração FOV

#### Arquivo: `aoi_lib/fov_calibration.py`

**Mudanças na classe `FOVCalibration`:**
- Atualizada a documentação para indicar que a câmera é fixa
- z1_z_pulses, z1_width_mm, z1_height_mm agora são iguais a z0 (câmera fixa)
- O método `from_dict()` força z1 = z0 para garantir FOV constante

**Mudanças no `FOVCalibrationDialog`:**
- Removida a segunda coluna "Ponto 2 (Z baixo)"
- Removidos os campos de entrada para Z1
- Interface simplificada mostra apenas:
  - Largura visível (mm)
  - Altura visível (mm)
- Atualizada a dica de calibração
- Função `_save()` atualizada para usar apenas os valores z0

**Mudanças na documentação do módulo:**
- Atualizado header do arquivo para distinguir:
  - TENSIÔMETRO: Câmera fixa → FOV constante
  - ADESIVADORA: Câmera móvel → FOV varia linearmente
- Atualizado "Uso típico" para refletir calibração em ponto único

### 2. Correção da Inversão do Eixo Y

#### Arquivo: `aoi_lib/fov_calibration.py`

**Mudança na função `video_click_to_movement()`:**

**ANTES:**
```python
# Inversão de Y se necessário (câmera invertida)
if invert_y:
    dy_pixels = -dy_pixels
```

**PROBLEMA:** Quando o usuário clicava ABAIXO do centro, a head se movia para CIMA (oposto)

**DEPOIS:**
```python
# CORREÇÃO DA INVERSÃO Y:
# - Em coordenadas de imagem: Y cresce para BAIXO (click abaixo = dy > 0)
# - Para centralizar: se clicou abaixo, câmera tem que DESCER
# - Movimento CNC para DESCER: dy NEGATIVO
# - Portanto: SEMPRE negamos dy, exceto se invert_y=True (câmera já invertida)
if not invert_y:
    dy_pixels = -dy_pixels
```

**Lógica Corrigida:**
- **Por padrão (invert_y=False):** Y é **sempre** NEGADO
  - Clique ABAIXO do centro (dy_pixels=+100) → dy_pixels=-100 → movimento NEGATIVO → câmera DESCE ✅
  - Clique ACIMA do centro (dy_pixels=-100) → dy_pixels=+100 → movimento POSITIVO → câmera SOBE ✅
- **Com invert_y=True:** Y **NÃO** é NEGADO
  - Para casos especiais onde a imagem está com espelhamento vertical

#### Arquivo: `consumo_lib.py`

**Mudança no `CameraPreviewWidget._on_video_click()`:**
- Adicionados comentários explicativos sobre a nova semântica do `invert_y`
- Clarificado que `_camera_mirror_y=True` cancela a inversão padrão

**Correção no `ConfigAdapter` (bug de salvamento):**
- Linha 2683: Corrigido `self._cfg.set("camera", "fov_calibration", value)` 
- Para: `self._cfg.set("camera", "fov_calibration", value=value)`
- **Motivo:** O método `set()` do `AOIConfigManager` requer `value` como keyword-only argument
- **Sintoma:** `TypeError: AOIConfigManager.set() missing 1 required keyword-only argument: 'value'`

---

## Resumo das Diferenças

### Antes das Correções:
1. ❌ Calibração complexa com dois pontos Z (desnecessária)
2. ❌ Movimento Y invertido (oposto ao esperado)
3. ❌ Parâmetro `invert_y` com semântica confusa

### Depois das Correções:
1. ✅ Calibração simplificada com um único ponto (câmera fixa)
2. ✅ Movimento Y correto (mesmo sentido do clique)
3. ✅ Parâmetro `invert_y` com semântica clara:
   - `False` (padrão): inverte Y (comportamento normal)
   - `True`: não inverte Y (para câmera com espelhamento vertical)

---

## Como Usar a Nova Calibração

1. **Abrir diálogo de calibração:**
   - Menu: Ferramentas → 📐 Calibração de FOV (Campo de Visão)

2. **Calibrar:**
   - Posicione uma régua ou objeto de dimensões conhecidas no plano focal
   - Observe a largura e altura visível na imagem da câmera
   - Digite os valores em mm nos campos correspondentes
   - Clique em "Salvar"

3. **Usar movimento por clique:**
   - Na aba "Câmera & Movimento"
   - Marque a opção "Mover head ao clicar"
   - Clique em qualquer ponto da imagem
   - A head se moverá para centralizar o ponto clicado

---

## Testes Recomendados

1. **Teste de calibração:**
   - Calibre com uma régua de 50mm x 37.5mm
   - Verifique se os valores são salvos corretamente

2. **Teste de movimento X:**
   - Clique à direita do centro → head deve mover para a direita ✅
   - Clique à esquerda do centro → head deve mover para a esquerda ✅

3. **Teste de movimento Y (CORRIGIDO):**
   - Clique abaixo do centro → câmera deve DESCER (centralizar o ponto) ✅
   - Clique acima do centro → câmera deve SUBIR (centralizar o ponto) ✅

4. **Teste de precisão:**
   - Clique em um ponto conhecido
   - Verifique se o movimento centraliza corretamente o ponto

## Validação Automatizada

Execute o script de teste:
```bash
python test_fov_corrections.py
```

O script testa:
- ✅ FOV constante em diferentes alturas Z (câmera fixa)
- ✅ Movimento correto em X (esquerda/direita)
- ✅ Movimento correto em Y (cima/baixo)
