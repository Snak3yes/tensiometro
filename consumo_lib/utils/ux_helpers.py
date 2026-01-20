"""
UX Helpers - Utilitários para melhorar a experiência do usuário

Fornece funções para adicionar tooltips, atalhos de teclado,
e melhorias visuais na interface do Engineering Wizard.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

from typing import Optional, List, Dict
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

from consumo_lib.ui import COLORS


# ========================
# Tooltips do Engineering Wizard
# ========================

ENGINEERING_WIZARD_TOOLTIPS = {
    # Aba 1: Dados do Programa
    'stencil_code': (
        "Código do Stencil\n\n"
        "Exemplo: STENCIL-ABC-123\n"
        "• Use o código gravado no stencil\n"
        "• Este código identificará o programa"
    ),
    'program_name': (
        "Nome do Programa\n\n"
        "Exemplo: Inspeção Stencil ABC-123\n\n"
        "• Nome descritivo para o programa\n"
        "• Será usado ao criar a Recipe"
    ),
    'description': (
        "Descrição (opcional)\n\n"
        "• Adicione detalhes adicionais\n"
        "• Ex: 'Primeira inspeção do novo stencil'"
    ),
    'version': (
        "Versão do Programa\n\n"
        "Exemplo: v1.0, v1.1, v2.0\n\n"
        "• Use controle de versão semântico\n"
        "• Incremente a versão para modificações"
    ),
    'created_by': (
        "Criado por\n\n"
        "• Nome do operador ou engenheiro\n"
        "• Ex: João Silva"
    ),

    # Aba 2: Carregar Gerber
    'gerber_file': (
        "Arquivo Gerber\n\n"
        "• Formato RS-274X (Extended Gerber)\n"
        "• Contém o design do stencil\n"
        "• Usado para alinhamento e inspeção"
    ),
    'load_gerber_btn': (
        "Carregar Arquivo Gerber\n\n"
        "• Clique para selecionar o arquivo .ger ou .gtl\n"
        "• O arquivo será processado automaticamente"
    ),

    # Aba 3: Definir Fiduciais
    'fiducial_info': (
        "Marcas de Referência (Fiduciais)\n\n"
        "• Capture 2 fiduciais do stencil\n"
        "• Clique na visualização da câmera\n"
        "• Os fiduciais são usados para alinhamento"
    ),
    'capture_fiducial_btn': (
        "Capturar Fiducial\n\n"
        "Atalho: F\n\n"
        "1. Mova a câmera para o fiducial\n"
        "2. Clique neste botão\n"
        "3. Repita para o segundo fiducial"
    ),

    # Aba 4: Capturar Mosaico
    'mosaic_info': (
        "Mosaico de Inspeção\n\n"
        "• Define a área que será inspecionada\n"
        "• Capture múltiplas imagens em grid\n"
        "• Use as dimensões do Gerber como referência"
    ),
    'corner1': (
        "Canto Superior Esquerdo\n\n"
        "• Posição inicial do mosaico\n"
        "• Geralmente (0, 0) ou canto do stencil"
    ),
    'corner2': (
        "Canto Inferior Direito\n\n"
        "• Posição final do mosaico\n"
        "• Use dimensões do Gerber"
    ),
    'grid_size': (
        "Tamanho do Grid\n\n"
        "• Número de linhas e colunas\n"
        "• Grid 3x3 = 9 imagens\n"
        "• Grid 5x5 = 25 imagens"
    ),
    'capture_mosaic_btn': (
        "Capturar Mosaico\n\n"
        "Atalho: M\n\n"
        "• O PLC moverá automaticamente\n"
        "• Câmera captura em cada ponto\n"
        "• Aguarde conclusão"
    ),

    # Aba 5: Alinhamento
    'alignment_info': (
        "Alinhamento Gerber ↔ Imagem\n\n"
        "• O sistema busca fiduciais na imagem\n"
        "• Calcula transformação (translação, rotação, escala)\n"
        "• Score > 70% é considerado bom"
    ),
    'run_alignment_btn': (
        "Executar Alinhamento\n\n"
        "Atalho: A\n\n"
        "• Template matching automático\n"
        "• Resultado mostra transformação\n"
        "• Verifique se overlay está correto"
    ),

    # Aba 6: Janelas de Inspeção
    'inspection_groups_info': (
        "Grupos de Inspeção\n\n"
        "• Agrupe aperturas por tipo/tamanho\n"
        "• Cada grupo pode ter threshold diferente\n"
        "• Ex: 0.5mm círculos, 0.8mm obrounds"
    ),
    'add_group_btn': (
        "Adicionar Grupo\n\n"
        "Atalho: G\n\n"
        "• Cria novo grupo de inspeção\n"
        "• Configure aperturas e threshold"
    ),
    'ok_threshold': (
        "Threshold OK (%)\n\n"
        "• Porcentagem mínima de pixels claros\n"
        "• Recomendado: 85-95%\n"
        "• Abaixo = PARTIAL ou BLOCKED"
    ),

    # Aba 7: Confirmar e Salvar
    'summary_info': (
        "Resumo do Programa\n\n"
        "• Revise todos os dados antes de salvar\n"
        "• Verifique se todas as etapas estão completas\n"
        "• Clique em Concluir para criar o programa"
    ),
    'save_btn': (
        "Concluir e Salvar\n\n"
        "Atalho: Ctrl+Enter\n\n"
        "• Salva o programa de inspeção\n"
        "• Opcionalmente cria uma Recipe\n"
        "• Programa fica disponível para uso"
    ),
}


def set_tooltip(widget: QWidget, key: str, tooltip_dict: Dict = None):
    """
    Define tooltip de um widget usando dicionário de tooltips.

    Args:
        widget: Widget para adicionar tooltip
        key: Chave do dicionário de tooltips
        tooltip_dict: Dicionário customizado (opcional)
    """
    tooltips = tooltip_dict or ENGINEERING_WIZARD_TOOLTIPS
    if key in tooltips:
        widget.setToolTip(tooltips[key])


def set_validation_tooltip(widget: QWidget, is_valid: bool, message: str = ""):
    """
    Define tooltip de validação com indicador visual.

    Args:
        widget: Widget para adicionar tooltip
        is_valid: Se o estado é válido
        message: Mensagem adicional (opcional)
    """
    if is_valid:
        widget.setToolTip(f"✓ Válido{message and ': ' + message or ''}")
    else:
        widget.setToolTip(f"⚠ {message or 'Pendente de validação'}")


# ========================
# Atalhos de Teclado
# ========================

def setup_shortcut(parent: QWidget, key_sequence: str, callback, description: str = ""):
    """
    Configura atalho de teclado.

    Args:
        parent: Widget pai
        key_sequence: Sequência de teclas (ex: "Ctrl+S", "F")
        callback: Função a ser chamada
        description: Descrição do atalho (apenas para documentação)

    Returns:
        QShortcut criado
    """
    shortcut = QShortcut(QKeySequence(key_sequence), parent)
    shortcut.activated.connect(callback)

    # Nota: QShortcut não tem setToolTip, a descrição é apenas para documentação

    return shortcut


def setup_engineering_wizard_shortcuts(dialog):
    """
    Configura atalhos de teclado para o Engineering Wizard.

    Args:
        dialog: Instância de EngineeringWizardDialog
    """
    # Atalho: Próximo aba (Ctrl+Right ou Tab)
    setup_shortcut(
        dialog,
        "Ctrl+Right",
        dialog._on_next,
        "Avançar para próxima aba"
    )

    # Atalho: Aba anterior (Ctrl+Left)
    setup_shortcut(
        dialog,
        "Ctrl+Left",
        dialog._on_previous,
        "Voltar para aba anterior"
    )

    # Atalho: Cancelar (Esc)
    setup_shortcut(
        dialog,
        "Esc",
        dialog._on_cancel,
        "Cancelar wizard"
    )

    # Atalho: Concluir (Ctrl+Enter)
    setup_shortcut(
        dialog,
        "Ctrl+Return",
        dialog._on_finish,
        "Concluir e salvar programa"
    )


# ========================
# Indicadores Visuais
# ========================

def update_validation_indicator(label: QLabel, is_valid: bool, field_name: str = ""):
    """
    Atualiza label com indicador de validação.

    Args:
        label: QLabel para atualizar
        is_valid: Se o campo está válido
        field_name: Nome do campo (opcional, para mensagem)
    """
    if is_valid:
        label.setText("✓")
        label.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
        label.setToolTip(f"{field_name} válido" if field_name else "Válido")
    else:
        label.setText("⚠")
        label.setStyleSheet(f"color: {COLORS.WARNING}; font-weight: bold;")
        label.setToolTip(f"{field_name} pendente" if field_name else "Pendente")


def create_progress_label(current: int, total: int, step_name: str = "") -> str:
    """
    Cria texto de progresso formatado.

    Args:
        current: Etapa atual
        total: Total de etapas
        step_name: Nome da etapa atual

    Returns:
        String formatada: "Etapa X de Y: Nome"
    """
    text = f"Etapa {current} de {total}"
    if step_name:
        text += f": {step_name}"
    return text


def get_tab_emoji(is_valid: bool, is_current: bool = False) -> str:
    """
    Retorna emoji apropriado para estado da aba.

    Args:
        is_valid: Se a aba está válida
        is_current: Se é a aba atual

    Returns:
        String com emoji: "✓", "▶", ou ""
    """
    if is_current:
        return "▶"
    elif is_valid:
        return "✓"
    else:
        return ""


# ========================
# Helpers de UI
# ========================

def set_widget_enabled_recursively(widget: QWidget, enabled: bool):
    """
    Habilita/desabilita widget e todos os filhos recursivamente.

    Args:
        widget: Widget pai
        enabled: Se deve habilitar
    """
    widget.setEnabled(enabled)
    for child in widget.findChildren(QWidget):
        child.setEnabled(enabled)


def add_required_indicator(label: QLabel):
    """
    Adiciona indicador de campo obrigatório (*) ao label.

    Args:
        label: QLabel para adicionar indicador
    """
    current_text = label.text()
    if not current_text.endswith("*"):
        label.setText(f"{current_text} *")
        label.setToolTip(label.toolTip() + "\n\nCampo obrigatório")


def format_file_size(size_bytes: int) -> str:
    """
    Formata tamanho de arquivo para formato humano.

    Args:
        size_bytes: Tamanho em bytes

    Returns:
        String formatada: "1.5 MB", "500 KB", etc.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """
    Formeta duração em formato humano.

    Args:
        seconds: Duração em segundos

    Returns:
        String formatada: "2:30", "1:05:20", etc.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
