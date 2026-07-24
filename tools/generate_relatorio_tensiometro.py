from __future__ import annotations

import html
import json
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "relatorio_projeto_tensiometro"
OUT.mkdir(parents=True, exist_ok=True)

HTML_PATH = OUT / "relatorio_tensiometro_visual.html"
DOCX_PATH = OUT / "relatorio_tensiometro.docx"
FUTURE_WORK_MD_PATH = OUT / "trabalhos_futuros_relatorio_tensiometro.md"

DATE = "03 de julho de 2026"
TITLE = "Relatório sobre o Projeto Tensiômetro"
SUBTITLE = "Medição automatizada de tensão de stencil, inspeção visual e integração industrial"
AUTHOR = "Equipe CTD/DGB"

LOGO_REL = "../../resources/app_icon.png"
ENDPOINT_IMAGE = ROOT / "resources" / "endpoint.png"
IMAGE_DIR = OUT / "Imagens"

PHOTO_IMAGES = [
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.35.jpeg",
        "caption": "Figura 2 - Operador acompanhando a interface do Tensiômetro durante operação na estação de medição.",
    },
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.35 (1).jpeg",
        "caption": "Figura 3 - Visão frontal da estação, com monitor, teclado, área de stencil, eixo Z e medidor de tensão.",
    },
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.36.jpeg",
        "caption": "Figura 4 - Conjunto mecânico principal com estrutura de alumínio, sinalização e área útil para posicionamento do stencil.",
    },
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.36 (1).jpeg",
        "caption": "Figura 5 - Detalhe do tensiômetro acoplado ao eixo Z realizando leitura sobre o stencil.",
    },
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.36 (2).jpeg",
        "caption": "Figura 6 - Operador posicionando o quadro/stencil na área de medição antes da execução do ciclo.",
    },
    {
        "filename": "WhatsApp Image 2026-07-03 at 13.52.37.jpeg",
        "caption": "Figura 7 - Operação com acompanhamento da IHM, evidenciando interação entre usuário, software e máquina.",
    },
]


SECTIONS = [
    (
        "Resumo",
        [
            "Este relatório apresenta uma análise do projeto Tensiômetro, aplicação desktop industrial desenvolvida em Python e PyQt6 para controle de qualidade de stencils. O sistema combina medição automatizada de tensão superficial, inspeção visual com câmera e comparação por arquivos Gerber, integração com PLC Delta por Modbus, comunicação serial com tensiômetro AS-120N, consulta de stencils no SFCS, persistência de resultados e geração de relatórios.",
            "A evolução observada no workspace indica uma arquitetura em refatoração progressiva, com separação entre a camada de domínio e hardware em `aoi_lib` e a camada de interface, coordenação e serviços em `consumo_lib`. As melhorias recentes reforçam pontos de confiabilidade operacional: retentativa e reteste físico quando o medidor retorna `0.00`, consulta de stencil sempre ativa por endpoint configurável, payload externo com campo `aprovado`, geração automática de relatório de tensão, build externo validado e testes unitários voltados a integração e regras de medição.",
        ],
    ),
    (
        "Palavras-chave",
        [
            "Tensiômetro; stencil; automação industrial; PyQt6; Modbus; visão computacional; Gerber; SFCS; rastreabilidade."
        ],
    ),
    (
        "1. Introdução",
        [
            "O Tensiômetro é um sistema de automação para medir a tensão superficial de stencils em pontos predefinidos e apoiar a inspeção visual dos furos por meio de câmera e comparação com dados Gerber. Em contexto produtivo, o objetivo é garantir que o stencil esteja íntegro, limpo e apto para uso, reduzindo risco de falhas de processo causadas por obstruções, deformações ou perda de tensão.",
            "A aplicação opera como interface homem-máquina em ambiente Windows, controlando movimentos por PLC, capturando imagens, acionando fluxo de medição e registrando resultados para rastreabilidade. O sistema também possui camadas de autenticação, permissões, configuração de endpoints, geração de PDF e armazenamento local de medições.",
            "Este relatório consolida as principais características técnicas do projeto e as melhorias registradas nos documentos locais. O foco é explicar o software, o hardware integrado e a relação operacional entre interface, medição, inspeção e rastreabilidade.",
        ],
    ),
    (
        "2. Metodologia",
        [
            "A metodologia consistiu em revisão documental e técnica do workspace do projeto. Foram examinados `README.md`, `AGENTS.md`, `CLAUDE.md`, documentos em `.planning/`, `conductor/`, `docs/`, `MAPA.txt`, `requirements.txt`, testes automatizados, módulos centrais e evidências visuais existentes em `resources/`.",
            "As informações foram agrupadas em eixos: caracterização do sistema, arquitetura de software, medição de tensão, inspeção visual, integração com SFCS, controle de hardware, geração de relatórios, validação e principais melhorias recentes. Trechos de código foram selecionados como registros visuais de implementação para demonstrar funções e decisões técnicas relevantes.",
            "Não foram realizados novos ensaios em máquina durante a elaboração deste relatório. As evidências de validação citadas correspondem a registros documentais do projeto, testes existentes e validações recentes descritas em `.planning/STATE.md`.",
        ],
    ),
    (
        "3. Caracterização do Sistema",
        [
            "A aplicação é um sistema desktop industrial com ponto de entrada em `main.py`. A stack observada inclui Python 3.13 no snapshot atual, PyQt6 para interface gráfica, OpenCV e NumPy para visão computacional, pymodbus para comunicação com PLC, pyserial para comunicação serial com o medidor, matplotlib para visualização e reportlab para geração de relatórios PDF.",
            "O hardware descrito inclui PLC Delta para controle de eixos X, Y e Z, câmera USB/OpenCV para captura e inspeção visual, tensiômetro AS-120N por serial, sinalização, iluminação e intertravamentos. O arquivo `MAPA.txt` documenta entradas, saídas, memórias e registradores relevantes, incluindo emergência, cortina de segurança, homing, JOG, movimento absoluto e comandos do tensiômetro.",
            "A estrutura do código separa responsabilidades: `aoi_lib/` concentra domínio, hardware, persistência, tensiômetro, PLC, câmera e inspeção; `consumo_lib/` concentra interface, controllers, coordinators, services, factories, facades, dialogs e widgets. Essa separação reduz o acoplamento direto com a janela principal e facilita a manutenção de fluxos complexos.",
        ],
    ),
    (
        "4. Melhorias de Software",
        [
            "O projeto passou por melhorias de organização arquitetural, com uso de coordinators, factories, services e facades para reduzir lógica concentrada em `main_window.py`. A medição de tensão, antes descrita como um fluxo extenso misturado à interface, passou a contar com `TensionCoordinator` e `MeasurementOrchestrator`, responsáveis por coordenar grid, movimento, leitura serial, progresso e persistência.",
            "O startup foi reforçado com pré-carregamento de módulos críticos antes da criação do `QApplication`. Esse warmup reduz problemas de primeira execução em Windows, especialmente quando o antivírus bloqueia arquivos `.pyc` temporariamente, e melhora a previsibilidade do início da aplicação.",
            "A medição de tensão ganhou tratamento mais rigoroso para leituras `0.00`. O sistema não aceita esse valor como medida válida; após tentativas de leitura, realiza reteste físico do ponto, subindo e descendo o eixo Z antes de tentar novamente. Se o valor continuar zerado, a falha é reportada explicitamente.",
            "A integração SFCS foi aprimorada com endpoint final de consulta de stencil, opção administrativa para alterar a URL pela interface e resolução do padrão local a partir do grid retornado. O serviço de consulta permanece sempre ativo, eliminando ambiguidade de configuração legada.",
            "O envio externo de resultados de tensão passou a construir payload estruturado com `codigo_stencil`, `idusuario`, `nmlinha` nulo, `idstencil_status`, `aprovado` e `log_tensao`. Medições NOK também podem ser enviadas com `aprovado: false`, enquanto medições sem pontos não devem ser enviadas.",
            "O design system evoluiu para uma versão baseada em Material Design 3, com variantes de botão, pesos tipográficos, família Segoe UI e tamanhos padronizados. Essa melhoria torna a interface mais coerente e reduz estilos inline dispersos.",
        ],
    ),
    (
        "5. Hardware, Mecânica e CLP",
        [
            "A integração com o PLC é central para a operação. O mapeamento em `MAPA.txt` identifica sinais de segurança, como emergência e cortina, confirmações de homing, sensores de home e limite dos eixos, saídas de pulso e direção e registradores de posição e limite. Essa documentação reduz risco de inferência incorreta ao alterar movimentos ou endereços.",
            "O fluxo mecânico envolve posicionamento de stencil, movimentação coordenada X/Y, aproximação segura do eixo Z, contato para leitura da tensão e retorno para altura segura. O sistema utiliza parâmetros de grid, altura de medição, altura segura, velocidade e tempo de estabilização para manter repetibilidade.",
            "O tensiômetro é controlado por comunicação serial e por sinais do PLC, com mapeamento de ligar/desligar, calibrar e zerar. A documentação recente indica que a calibração automática liga e zera o medidor após home inicial e retorna para home ao final.",
        ],
    ),
    (
        "6. Inspeção Visual e Gerber",
        [
            "Além da medição de tensão, o projeto possui fluxo de inspeção visual para validar limpeza e desobstrução dos furos do stencil. O pipeline envolve carregamento de Gerber, renderização, captura de imagem, alinhamento por fiduciais e análise de resultados.",
            "A presença de módulos como `gerber_parser`, `gerber_renderer`, `stencil_inspector`, `fiducial_alignment` e testes de renderização indica preocupação com a rastreabilidade entre o modelo digital do stencil e a imagem capturada. Esse componente é complementar à medição de tensão, pois avalia condição visual e não apenas resposta mecânica.",
        ],
    ),
    (
        "7. Integração, Dados e Relatórios",
        [
            "O sistema realiza consulta de stencil no SFCS por código de barras, com endpoint padrão final `147.1.0.100`. A resposta esperada inclui dados como `idstencil`, grid, status e descrição do modelo. A simulação documentada consultou o stencil `32B01A642723416`, resolveu grid `3x3` para o padrão local `Teste1_V14_V5` e aprovou 9 pontos em medição simulada.",
            "Os resultados de medição são persistidos em `tension_routines/`, e há evidências de relatórios PDF gerados em `reports/tension/` e históricos por stencil em `reports/stencil/`. A geração automática de relatório após salvar medição melhora rastreabilidade e reduz dependência de operação manual posterior.",
            "A imagem `resources/endpoint.png` documenta um teste de endpoint com retorno HTTP 200 e payload JSON, servindo como evidência visual da camada de integração externa.",
        ],
    ),
    (
        "8. Resultados e Validação",
        [
            "O projeto possui suíte de testes unitários e de integração distribuída em `tests/`, cobrindo configuração, design system, Gerber, PLC, inspeção, tensiômetro, medição, integração externa, payloads, relatórios, autenticação e persistência. A documentação de estado registra execução recente de 15 testes focados em configuração de endpoint e consulta SFCS, todos aprovados.",
            "Também há evidência de build externo gerado em 17 de junho de 2026 com validação por existência do executável e conferência de `config/aoi_config.json` copiado para o pacote. O processo evita gerar `build/` ou `dist/` dentro do worktree, preservando limpeza do repositório.",
            "Como ocorre em sistemas industriais, a validação automatizada reduz regressões de regra de negócio, mas não substitui validação em máquina com PLC, sensores, câmera, tensiômetro, movimento real e condições físicas de operação.",
        ],
    ),
    (
        "9. Discussão",
        [
            "O Tensiômetro é um exemplo de sistema em que software, hardware e processo de qualidade precisam evoluir juntos. A confiabilidade não depende apenas da interface ou do algoritmo: depende de endereços corretos no PLC, movimentação segura do eixo Z, comunicação serial estável, interpretação correta do Gerber, consulta de dados externos e persistência rastreável.",
            "As melhorias recentes mostram amadurecimento operacional. A leitura `0.00` deixou de ser tratada como valor aceitável, o endpoint de consulta passou a ser administrável pela interface, o payload externo ficou alinhado com regras de aprovação/reprovação e o design system reduziu inconsistências visuais.",
            "A arquitetura ainda carrega compatibilidades e histórico de refatoração, mas já apresenta direção clara: regras em serviços, coordenação em coordinators, composição em factories e interface em widgets/dialogs. Essa direção é adequada para uma aplicação industrial que precisa continuar evoluindo sem ampliar excessivamente o acoplamento da janela principal.",
        ],
    ),
    (
        "10. Conclusão",
        [
            "O projeto Tensiômetro consolida uma solução de controle de qualidade de stencils que une medição física, inspeção visual e integração de dados. A aplicação controla hardware, coleta medidas, consulta informações externas, gera evidências e organiza o fluxo do operador em uma interface desktop.",
            "As melhorias registradas aumentam robustez, rastreabilidade e manutenção. O tratamento de leituras zeradas, a integração SFCS configurável, o payload externo padronizado, a geração de relatórios e a evolução do design system demonstram avanço tanto na operação quanto na engenharia do software.",
            "O relatório atual serve como base documental para apresentações e manutenção, reunindo descrição técnica, evidências visuais da máquina, registros de software e pontos de apoio para futuras validações em produção.",
        ],
    ),
]

TABLES = {
    "evidence": (
        "Tabela 1 - Fontes documentais utilizadas.",
        ["Fonte", "Contribuição"],
        [
            ["README.md", "Descrição do objetivo da máquina e escopo de medição/inspeção."],
            ["AGENTS.md", "Mapa operacional do repositório, arquitetura e fluxos críticos."],
            [".planning/", "Mudanças recentes, requisitos, estado de validação, build e integrações."],
            ["MAPA.txt", "Mapeamento de sinais, registradores, homing, eixos e comandos do tensiômetro."],
            ["docs/CHANGELOG.md", "Histórico de evolução do design system e padrões de interface."],
            ["tests/", "Evidência de cobertura unitária e de integração para serviços críticos."],
        ],
    ),
    "architecture": (
        "Tabela 2 - Componentes principais do sistema.",
        ["Componente", "Responsabilidade"],
        [
            ["aoi_lib", "Domínio, hardware, tensiômetro, PLC, câmera, Gerber, inspeção e persistência."],
            ["consumo_lib", "Interface, controllers, coordinators, services, factories, dialogs e widgets."],
            ["config", "Configurações locais sensíveis da máquina e endpoints."],
            ["tension_routines", "Resultados de medição, payloads e logs de envio."],
            ["reports", "Relatórios PDF de tensão e históricos de stencil."],
        ],
    ),
    "hardware": (
        "Tabela 3 - Integrações físicas e externas.",
        ["Item", "Tecnologia", "Função"],
        [
            ["PLC Delta", "Modbus TCP/RTU", "Controle de eixos, homing, intertravamentos e sinais do tensiômetro."],
            ["Tensiômetro AS-120N", "Serial + sinais de controle", "Leitura de tensão e rotinas de ligar, calibrar e zerar."],
            ["Câmera USB", "OpenCV", "Captura para inspeção visual e alinhamento."],
            ["SFCS", "HTTP/JSON", "Consulta de stencil e envio de resultado de tensão."],
            ["ReportLab", "PDF", "Relatórios de medição e histórico."],
        ],
    ),
    "validation": (
        "Tabela 4 - Evidências de validação.",
        ["Área", "Evidência"],
        [
            ["Endpoint SFCS", "15 testes recentes passaram para configurações de endpoint e serviço de consulta."],
            ["Medição", "Testes de measurement thread, measurement orchestrator e serviços de medição."],
            ["Payload externo", "Testes de política de envio e estrutura do payload de tensão."],
            ["Relatórios", "PDFs existentes em reports/tension e reports/stencil."],
            ["Build", "Pacote externo gerado em 2026-06-17 e conferido com config atual."],
        ],
    ),
}

CODE_SNIPPETS = [
    {
        "title": "Warmup de inicialização",
        "source": "main.py",
        "caption": "Pré-carregamento de módulos críticos antes do QApplication para reduzir instabilidade na primeira execução em Windows.",
        "code": '''def warmup_imports():
    print("[WARMUP] Pre-carregando módulos...")
    warmup_modules = [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "consumo_lib.ui.design_tokens",
        "consumo_lib.ui.theme_manager",
        "consumo_lib.handlers.keyboard_handler",
        "aoi_lib.config_manager",
        "aoi_lib.plc_axis_controller",
        "aoi_lib.tensiometer",
        "consumo_lib.main_window",
    ]
    for module_name in warmup_modules:
        try:
            importlib.import_module(module_name)
        except Exception:
            pass''',
    },
    {
        "title": "Grid de medição em zig-zag",
        "source": "consumo_lib/coordinators/tension_coordinator.py",
        "caption": "Geração dos pontos de medição com alternância de sentido por linha para reduzir deslocamentos desnecessários.",
        "code": '''def _generate_grid(self):
    grid = self._current_config.grid_size
    step_x = self._current_config.step_x
    step_y = self._current_config.step_y

    points = []
    for row in range(grid):
        cols = range(grid) if row % 2 == 0 else range(grid - 1, -1, -1)
        for col in cols:
            points.append(TensionPoint(
                x=col * step_x,
                y=row * step_y,
                status="pending",
            ))

    self._grid_points = points
    self.grid_generated.emit(points)''',
    },
    {
        "title": "Reteste físico de leitura 0.00",
        "source": "aoi_lib/tensiometer/measurement_thread.py",
        "caption": "A medição não aceita leitura zerada como válida; o ponto é retestado fisicamente com subida e descida do Z.",
        "code": '''def _read_tension_value_with_zero_retest(self, point_index, total_points, stabilization_sec):
    try:
        return self._read_tension_value_with_retries(point_index, total_points)
    except ZeroTensionReadError as first_error:
        if self._stop_requested:
            raise RuntimeError("Medição interrompida pelo usuário") from first_error

        self.progress_updated.emit(
            point_index,
            total_points,
            f"Retestando ponto {point_index}/{total_points} por leitura 0.00",
        )

        self._move_abs(z=self.z_move, feed=self.user_feed)
        time.sleep(ZERO_TENSION_RETEST_SETTLE_SEC)
        self._move_abs(z=self.z_height, feed=self.user_feed)
        return self._read_tension_value_with_retries(point_index, total_points)''',
    },
    {
        "title": "Consulta de stencil no SFCS",
        "source": "consumo_lib/services/sfcs_stencil_lookup_service.py",
        "caption": "Consulta HTTP por código de barras, com endpoint configurável e tratamento de 404, URL inválida e JSON malformado.",
        "code": '''class SfcsStencilLookupService:
    DEFAULT_ENDPOINT_URL = (
        "http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}"
    )

    def lookup(self, code: str) -> SfcsStencilRecord:
        normalized_code = normalize_stencil_code(code)
        if not normalized_code:
            raise SfcsStencilLookupError("Código de stencil vazio.")

        endpoint_url = self._build_endpoint_url(normalized_code)
        http_request = request.Request(
            endpoint_url,
            method="GET",
            headers={"Accept": "application/json"},
        )
        with request.urlopen(http_request, timeout=self._timeout_sec()) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return self._parse_payload(payload, fallback_code=normalized_code)''',
    },
    {
        "title": "Payload externo de tensão",
        "source": "consumo_lib/services/tension_external_payload_service.py",
        "caption": "Estrutura enviada para API externa, incluindo aprovação/reprovação e log ordenado das medições.",
        "code": '''def build_payload(self, *, stencil_code, measurements, user_id=None,
                  stencil_status=None, approved=None):
    ordered_measurements = sorted(measurements, key=self._measurement_sort_key)
    tension_log = [
        self._build_log_entry(measurement)
        for measurement in ordered_measurements
    ]

    return {
        "codigo_stencil": normalize_stencil_code(stencil_code),
        "idusuario": self._normalize_user_id(user_id),
        "nmlinha": None,
        "idstencil_status": stencil_status,
        "aprovado": bool(approved),
        "log_tensao": tension_log,
    }''',
    },
]

FUTURE_WORK = [
    "Complementar o registro fotográfico com imagens específicas do painel elétrico, câmera, iluminação interna e detalhes de fixação mecânica do stencil.",
    "Inserir fluxogramas visuais do ciclo de medição e do fluxo de inspeção Gerber/câmera.",
    "Registrar evidências de validação em máquina com tempo de ciclo, repetibilidade, taxa de falhas e exemplos de relatórios finais.",
    "Atualizar o relatório quando houver novo build posterior às mudanças de 2026-06-24.",
]


def available_photos() -> list[dict[str, str | Path]]:
    photos = []
    for item in PHOTO_IMAGES:
        path = IMAGE_DIR / item["filename"]
        if path.exists():
            photos.append({**item, "path": path})
    return photos


def image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        index = 2
        while index < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            while marker == 0xFF:
                marker = data[index]
                index += 1
            if marker in (0xD8, 0xD9):
                continue
            segment_length = struct.unpack(">H", data[index:index + 2])[0]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", data[index + 3:index + 7])
                return width, height
            index += segment_length
    raise ValueError(f"Formato de imagem não suportado: {path}")


def render_table(key: str) -> str:
    caption, headers, rows = TABLES[key]
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<figure class='data-table'><figcaption>{html.escape(caption)}</figcaption><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></figure>"


def render_code_section_html() -> str:
    cards = []
    for index, snippet in enumerate(CODE_SNIPPETS, start=1):
        cards.append(
            "<article class='code-shot'>"
            "<div class='code-bar'><span></span><span></span><span></span></div>"
            f"<h3>{html.escape(snippet['title'])}</h3>"
            f"<p>{html.escape(snippet['caption'])}</p>"
            f"<small>{html.escape(snippet['source'])}</small>"
            f"<pre><code>{html.escape(snippet['code'])}</code></pre>"
            f"<figcaption>Fonte {index} - Fragmento de código representativo.</figcaption>"
            "</article>"
        )
    return (
        "<section class='code-section'><h2>Fragmentos de Código Representativos</h2>"
        "<p>Os blocos abaixo funcionam como registros visuais de implementação, conectando o relatório a funções reais do projeto.</p>"
        "<div class='code-grid'>"
        + "".join(cards)
        + "</div></section>"
    )


def render_photo_gallery_html() -> str:
    photos = available_photos()
    if not photos:
        return ""
    cards = []
    for item in photos:
        src = f"Imagens/{html.escape(str(item['filename']))}"
        caption = html.escape(str(item["caption"]))
        alt = caption.split(" - ", 1)[-1]
        cards.append(
            "<figure class='photo-card'>"
            f"<img src='{src}' alt='{alt}'>"
            f"<figcaption>{caption}</figcaption>"
            "</figure>"
        )
    return (
        "<section class='photo-section'>"
        "<h2>Registro Fotográfico da Máquina</h2>"
        "<p>O registro fotográfico apresenta a estação física, a interação do operador com a IHM e o conjunto mecânico responsável pela medição de tensão do stencil.</p>"
        "<div class='photo-grid'>"
        + "".join(cards)
        + "</div></section>"
    )


def render_html() -> str:
    blocks: list[str] = []
    table_after = {
        "2. Metodologia": "evidence",
        "3. Caracterização do Sistema": "architecture",
        "5. Hardware, Mecânica e CLP": "hardware",
        "8. Resultados e Validação": "validation",
    }
    for title, paragraphs in SECTIONS:
        blocks.append(
            "<section class='paper-section'>"
            f"<h2>{html.escape(title)}</h2>"
            + "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)
            + "</section>"
        )
        if title == "4. Melhorias de Software":
            blocks.append(render_code_section_html())
        if title.startswith("3."):
            blocks.append(render_photo_gallery_html())
        if title == "7. Integração, Dados e Relatórios" and ENDPOINT_IMAGE.exists():
            blocks.append(
                "<figure class='endpoint-shot'>"
                "<img src='../../resources/endpoint.png' alt='Teste visual do endpoint de stencil'>"
                "<figcaption>Figura 1 - Registro visual de teste do endpoint de consulta de stencil com resposta HTTP 200.</figcaption>"
                "</figure>"
            )
        if title in table_after:
            blocks.append(render_table(table_after[title]))

    metrics = [
        ("Medição", "Grid automatizado, leitura serial e reteste físico de valores 0.00."),
        ("Inspeção", "Câmera, Gerber, fiduciais e validação visual de obstruções."),
        ("Integração", "Consulta SFCS, payload externo e logs de envio."),
        ("Rastreabilidade", "Relatórios PDF, histórico de stencil e testes automatizados."),
    ]
    metric_cards = "".join(
        f"<article><span>{html.escape(label)}</span><strong>{html.escape(text)}</strong></article>"
        for label, text in metrics
    )
    timeline = "".join(
        f"<li><time>{date}</time><p>{html.escape(text)}</p></li>"
        for date, text in [
            ("20/01", "Design System v2.0 com variantes de botões e tipografia."),
            ("09/04", "Relatórios de tensão e históricos de stencil gerados em PDF."),
            ("17/06", "Build externo validado com configuração atual."),
            ("24/06", "Endpoint SFCS configurável e consulta sempre ativa."),
            ("03/07", "Relatório consolidado do projeto gerado neste workspace."),
        ]
    )
    refs = "".join(
        f"<li>{html.escape(ref)}</li>"
        for ref in [
            "README.md",
            "AGENTS.md",
            "MAPA.txt",
            ".planning/PROJECT.md",
            ".planning/RECENT_CHANGES.md",
            ".planning/STATE.md",
            "docs/CHANGELOG.md",
            "docs/architecture/TENSION_COORDINATOR.md",
            "Código-fonte local em aoi_lib/, consumo_lib/ e tests/.",
        ]
    )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(TITLE)}</title>
<style>
:root{{--paper:#f5f1e8;--ink:#151713;--muted:#60665f;--line:#d7cfbf;--steel:#264852;--oxide:#a3422b;--signal:#d79b25;--green:#4d846f;--panel:#fffaf0;--shadow:0 18px 60px rgba(21,23,19,.14)}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(90deg,rgba(38,72,82,.08) 1px,transparent 1px),linear-gradient(0deg,rgba(38,72,82,.08) 1px,transparent 1px),radial-gradient(circle at 18% 8%,rgba(215,155,37,.24),transparent 28%),var(--paper);background-size:28px 28px,28px 28px,auto;color:var(--ink);font-family:Cambria,Georgia,'Times New Roman',serif;line-height:1.55}}
.top{{position:sticky;top:0;z-index:5;background:rgba(245,241,232,.92);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}} .top-inner{{max-width:1180px;margin:auto;padding:14px 22px;display:flex;gap:18px;align-items:center;justify-content:space-between}} .brand{{display:flex;gap:20px;align-items:center;min-width:0}} .brand-logo{{width:260px;height:auto;max-height:132px;object-fit:contain;display:block;flex:0 0 auto}} .brand-copy{{margin:0}} .brand strong{{font-size:16px;letter-spacing:.08em;text-transform:uppercase;color:var(--steel)}} .brand span{{font-size:15px;color:var(--muted)}} nav{{display:flex;gap:8px;flex-wrap:wrap}} nav a{{color:var(--steel);text-decoration:none;font-size:13px;padding:6px 9px;border:1px solid transparent}} nav a:hover{{border-color:var(--steel);background:var(--panel)}}
.hero{{min-height:74vh;max-width:1180px;margin:auto;padding:72px 22px 36px;display:grid;grid-template-columns:minmax(0,1fr) minmax(340px,.9fr);gap:42px;align-items:center}} .kicker{{color:var(--oxide);font-weight:700;text-transform:uppercase;letter-spacing:.12em;font-size:13px}} h1{{font-size:clamp(48px,8vw,96px);line-height:.9;margin:14px 0 22px;font-weight:800}} .subtitle{{font-size:22px;color:var(--steel);max-width:760px;text-align:left}} .meta{{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}} .meta span{{border:1px solid var(--line);background:rgba(255,250,240,.75);padding:8px 10px;font-size:14px;color:var(--muted)}}
.schematic{{background:linear-gradient(145deg,rgba(255,250,240,.92),rgba(234,225,205,.8));border:1px solid var(--line);box-shadow:var(--shadow);padding:24px}} .grid-machine{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:20px 0}} .grid-machine span{{border:2px solid var(--steel);min-height:70px;display:grid;place-items:center;font-weight:800;color:var(--steel);background:rgba(255,255,255,.42)}} .sensor{{border:2px solid var(--oxide);color:var(--oxide);padding:14px;text-align:center;font-weight:800;margin-bottom:14px}} .flow-line{{height:4px;background:repeating-linear-gradient(90deg,var(--signal),var(--signal) 12px,transparent 12px,transparent 22px);margin:18px 0}} .board{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}} .board span{{border-left:4px solid var(--green);background:rgba(77,132,111,.1);padding:10px;font-size:14px;color:var(--steel)}}
main{{max-width:1180px;margin:auto;padding:0 22px 72px}} .metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:10px 0 42px}} .metrics article{{background:var(--panel);border:1px solid var(--line);padding:18px;box-shadow:8px 8px 0 rgba(38,72,82,.12)}} .metrics span{{display:block;color:var(--oxide);font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}} .metrics strong{{font-size:16px;font-weight:600}}
.timeline{{margin:30px 0 48px;padding:26px;background:var(--steel);color:#fffaf0;box-shadow:var(--shadow)}} .timeline h2{{color:#fffaf0;border-color:rgba(255,250,240,.22)}} .timeline ol{{list-style:none;padding:0;margin:0;display:grid;gap:12px}} .timeline li{{display:grid;grid-template-columns:84px 1fr;gap:14px}} .timeline time{{color:var(--signal);font-weight:800;font-size:18px}} .timeline p{{margin:0;text-align:left}}
.paper-section{{background:rgba(255,250,240,.82);border-top:3px solid var(--steel);padding:30px;margin:18px 0;box-shadow:0 1px 0 var(--line)}} h2{{font-size:clamp(26px,4vw,42px);line-height:1.05;margin:0 0 18px;color:var(--steel);border-bottom:1px solid var(--line);padding-bottom:12px}} p{{font-size:18px;margin:0 0 14px;text-align:justify}} .data-table{{margin:22px 0 34px;background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);padding:16px;overflow-x:auto}} figcaption{{color:var(--oxide);font-weight:800;margin-top:10px}} table{{width:100%;border-collapse:collapse;min-width:720px}} th,td{{border:1px solid var(--line);padding:10px 12px;vertical-align:top;text-align:left}} th{{background:rgba(38,72,82,.12);color:var(--steel)}}
.photo-section{{background:var(--panel);border:1px solid var(--line);padding:24px;margin:24px 0 34px;box-shadow:var(--shadow)}} .photo-section>p{{max-width:940px;text-align:left;color:var(--muted)}} .photo-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}} .photo-card{{margin:0;background:#fdf8ec;border:1px solid var(--line);padding:10px;display:flex;flex-direction:column;gap:8px}} .photo-card img{{width:100%;aspect-ratio:4/5;object-fit:cover;display:block;border:1px solid rgba(38,72,82,.22);background:#e7dfcf}} .photo-card:nth-child(4) img{{aspect-ratio:16/9}} .photo-card figcaption{{font-size:13px;line-height:1.35;margin:0;color:var(--steel)}} .endpoint-shot{{background:var(--panel);border:1px solid var(--line);padding:12px;box-shadow:var(--shadow);margin:22px 0}} .endpoint-shot img{{width:100%;display:block;border:1px solid rgba(38,72,82,.22)}} .code-section{{background:#151713;color:#fffaf0;padding:30px;margin:24px 0;box-shadow:var(--shadow)}} .code-section h2{{color:#fffaf0;border-color:rgba(255,250,240,.22)}} .code-section>p{{color:#d9d0bf;text-align:left;max-width:920px}} .code-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:20px}} .code-shot{{background:#0d0f0d;border:1px solid rgba(255,250,240,.18);box-shadow:8px 8px 0 rgba(215,155,37,.18);padding:14px;overflow:hidden}} .code-bar{{display:flex;gap:6px;margin-bottom:12px}} .code-bar span{{width:10px;height:10px;border-radius:50%;background:var(--oxide);display:block}} .code-bar span:nth-child(2){{background:var(--signal)}} .code-bar span:nth-child(3){{background:var(--green)}} .code-shot h3{{font-size:20px;margin:0 0 8px;color:#fffaf0}} .code-shot p{{font-size:14px;color:#d9d0bf;text-align:left;margin:0 0 8px}} .code-shot small{{display:block;color:var(--signal);font-size:12px;margin-bottom:10px;word-break:break-word}} .code-shot pre{{margin:0;padding:14px;background:#050605;border:1px solid rgba(255,250,240,.12);overflow:auto;max-height:430px}} .code-shot code{{font-family:'Cascadia Mono','Consolas','Courier New',monospace;font-size:12px;line-height:1.55;color:#f7f3ea;white-space:pre}} .code-shot figcaption{{font-size:12px;color:#bcb39f;margin:10px 0 0}} .refs{{background:var(--ink);color:#fffaf0;padding:30px;margin-top:28px}} .refs h2{{color:#fffaf0;border-color:rgba(255,250,240,.18)}} .refs li{{margin:0 0 10px;font-size:15px}}
@media(max-width:900px){{.hero{{grid-template-columns:1fr;min-height:auto;padding-top:48px}}.metrics,.code-grid,.photo-grid{{grid-template-columns:1fr}}.top-inner{{align-items:flex-start;flex-direction:column}}.brand-logo{{width:220px;max-width:100%}}}} @media print{{body{{background:white;color:black}}.paper-section,.data-table,.refs{{box-shadow:none;background:white;color:black}}nav{{display:none}}}}
</style></head>
<body><header class="top"><div class="top-inner"><div class="brand"><img class="brand-logo" src="{LOGO_REL}" alt="Logo do Tensiômetro"><p class="brand-copy"><strong>Tensiômetro</strong><br><span>Relatório</span></p></div><nav><a href="#software">Software</a><a href="#hardware">Hardware</a><a href="#integracao">Integração</a><a href="#referencias">Referências</a></nav></div></header>
<section class="hero"><div><div class="kicker">{html.escape(AUTHOR)} · {html.escape(DATE)}</div><h1>Tensiômetro</h1><p class="subtitle">{html.escape(SUBTITLE)}.</p><div class="meta"><span>Python + PyQt6</span><span>PLC Delta</span><span>AS-120N serial</span><span>Gerber + câmera</span></div></div><aside class="schematic"><div class="sensor">Sensor de tensão + eixo Z</div><div class="grid-machine"><span>1</span><span>2</span><span>3</span><span>6</span><span>5</span><span>4</span><span>7</span><span>8</span><span>9</span></div><div class="flow-line"></div><div class="board"><span>Grid zig-zag</span><span>Reteste 0.00</span><span>Consulta SFCS</span><span>Relatório PDF</span></div></aside></section>
<main><section class="metrics">{metric_cards}</section><section class="timeline"><h2>Linha do tempo técnica</h2><ol>{timeline}</ol></section><div id="software"></div>{''.join(blocks)}<section id="referencias" class="refs"><h2>Referências documentais</h2><ol>{refs}</ol></section></main>
</body></html>"""


def r(text: str, bold: bool = False, italic: bool = False, size: int = 24, font: str = "Times New Roman") -> str:
    props = [
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>',
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>',
    ]
    if bold:
        props.append("<w:b/><w:bCs/>")
    if italic:
        props.append("<w:i/><w:iCs/>")
    return f'<w:r><w:rPr>{"".join(props)}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def p(text: str = "", style: str | None = None, align: str = "both", indent: bool = True, bold: bool = False, italic: bool = False, size: int = 24, before: int = 0, after: int = 120, line: int = 360, font: str = "Times New Roman") -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    props.append(f'<w:jc w:val="{align}"/>')
    props.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>')
    if indent:
        props.append('<w:ind w:firstLine="708"/>')
    return f'<w:p><w:pPr>{"".join(props)}</w:pPr>{r(text, bold=bold, italic=italic, size=size, font=font)}</w:p>'


def heading(text: str) -> str:
    return p(text, style="Heading1", align="left", indent=False, bold=True, size=28, before=360, after=160, line=276)


def code_line(text: str) -> str:
    props = '<w:jc w:val="left"/><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:shd w:fill="F3F0E8"/>'
    return f'<w:p><w:pPr>{props}</w:pPr>{r(text, size=18, font="Courier New")}</w:p>'


def word_table(key: str) -> str:
    caption, headers, rows = TABLES[key]
    width = max(1200, int(9026 / len(headers)))
    borders = "".join(f'<w:{side} w:val="single" w:sz="6" w:space="0" w:color="8B8577"/>' for side in ["top", "left", "bottom", "right", "insideH", "insideV"])
    grid_cols = "".join(f'<w:gridCol w:w="{width}"/>' for _ in headers)
    out = [p(caption, style="Caption", align="left", indent=False, italic=True, size=20, after=80, line=240)]
    out.append(f'<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>{borders}</w:tblBorders><w:tblCellMar><w:top w:w="90" w:type="dxa"/><w:left w:w="90" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>{grid_cols}</w:tblGrid>')

    def row(cells: list[str], header: bool = False) -> str:
        cells_xml = []
        for cell in cells:
            shade = '<w:shd w:fill="D9E2E5"/>' if header else ""
            cells_xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>{p(cell, align="left", indent=False, bold=header, size=20, after=60, line=240)}</w:tc>')
        return f'<w:tr>{"".join(cells_xml)}</w:tr>'

    out.append(row(headers, True))
    out.extend(row(row_data) for row_data in rows)
    out.append("</w:tbl>")
    return "".join(out)


def image_paragraph(rel_id: str, doc_pr_id: int, filename: str, caption: str) -> str:
    image_path = ROOT / filename
    width_px, height_px = image_size(image_path)
    max_width = 5.85 * 914400
    max_height = 6.8 * 914400
    scale = min(max_width / width_px, max_height / height_px)
    cx = int(width_px * scale)
    cy = int(height_px * scale)
    name = escape(caption.split(" - ", 1)[0])
    drawing = f'''<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="180" w:after="80"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="{doc_pr_id}" name="{name}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{doc_pr_id}" name="{escape(filename)}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
    return drawing + p(caption, style="Caption", align="center", indent=False, italic=True, size=20, after=120, line=240)


def code_section_xml() -> str:
    body = [heading("4.1 Fragmentos de Código Representativos")]
    body.append(p("Os fragmentos a seguir conectam o relatório a funções reais do projeto, com foco em inicialização, grid de medição, leitura do tensiômetro e integrações externas."))
    for index, snippet in enumerate(CODE_SNIPPETS, start=1):
        body.append(p(f"Fonte {index} - {snippet['title']}", style="Caption", align="left", indent=False, italic=True, size=20, before=160, after=60, line=240))
        body.append(p(f"Arquivo: {snippet['source']}", align="left", indent=False, italic=True, size=20, after=60, line=240))
        body.append(p(snippet["caption"], size=22, after=80, line=300))
        body.extend(code_line(line) for line in snippet["code"].splitlines())
    return "".join(body)


def photo_section_xml() -> str:
    photos = available_photos()
    if not photos:
        return ""
    body = [heading("3.1 Registro Fotográfico da Máquina")]
    body.append(p("O registro fotográfico apresenta a estação física do Tensiômetro, incluindo estrutura mecânica, área de medição, interação do operador com a IHM, posicionamento do stencil e detalhe do medidor acoplado ao eixo Z."))
    for index, item in enumerate(photos, start=1):
        relative_path = item["path"].relative_to(ROOT).as_posix()
        body.append(image_paragraph(f"rId{4 + index}", index + 1, relative_path, str(item["caption"])))
    return "".join(body)


def document_xml() -> str:
    body = [
        p(TITLE, style="Title", align="center", indent=False, bold=True, size=34, before=1200, after=240, line=300),
        p(SUBTITLE, align="center", indent=False, italic=True, size=24, after=360, line=300),
        p(AUTHOR, align="center", indent=False, size=24, before=360, after=120, line=300),
        p(DATE, align="center", indent=False, size=24, after=900, line=300),
    ]
    table_after = {
        "2. Metodologia": "evidence",
        "3. Caracterização do Sistema": "architecture",
        "5. Hardware, Mecânica e CLP": "hardware",
        "8. Resultados e Validação": "validation",
    }
    for title, paragraphs in SECTIONS:
        body.append(heading(title))
        body.extend(p(text) for text in paragraphs)
        if title == "4. Melhorias de Software":
            body.append(code_section_xml())
        if title.startswith("3."):
            body.append(photo_section_xml())
        if title == "7. Integração, Dados e Relatórios" and ENDPOINT_IMAGE.exists():
            body.append(image_paragraph("rId4", 1, "resources/endpoint.png", "Figura 1 - Registro visual de teste do endpoint de consulta de stencil com resposta HTTP 200."))
        if title in table_after:
            body.append(word_table(table_after[title]))
    body.append(heading("Referências documentais"))
    refs = [
        "README.md.",
        "AGENTS.md.",
        "MAPA.txt.",
        ".planning/PROJECT.md, RECENT_CHANGES.md, REQUIREMENTS.md e STATE.md.",
        "docs/CHANGELOG.md.",
        "docs/architecture/TENSION_COORDINATOR.md.",
        "Código-fonte local em aoi_lib/, consumo_lib/ e tests/.",
    ]
    body.extend(p(ref, indent=False, after=120, line=300) for ref in refs)
    section = '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1701" w:right="1134" w:bottom="1134" w:left="1701" w:header="708" w:footer="708" w:gutter="0"/><w:cols w:space="708"/><w:docGrid w:linePitch="360"/></w:sectPr>'
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 wp14"><w:body>{"".join(body)}{section}</w:body></w:document>'''


def styles_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="pt-BR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:line="360" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="both"/><w:spacing w:line="360" w:lineRule="auto" w:after="120"/><w:ind w:firstLine="708"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="34"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:jc w:val="left"/><w:spacing w:before="360" w:after="160" w:line="276" w:lineRule="auto"/></w:pPr><w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="28"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="left"/><w:spacing w:after="80" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:i/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr></w:style></w:styles>'''


def write_docx(path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    image_rel = '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/endpoint.png"/>' if ENDPOINT_IMAGE.exists() else ""
    photos = available_photos()
    photo_rels = "".join(
        f'<Relationship Id="rId{4 + index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/photo{index}.jpeg"/>'
        for index, _ in enumerate(photos, start=1)
    )
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="jpeg" ContentType="image/jpeg"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>',
        "word/_rels/document.xml.rels": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>{image_rel}{photo_rels}</Relationships>',
        "word/document.xml": document_xml(),
        "word/styles.xml": styles_xml(),
        "word/settings.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:zoom w:percent="100"/><w:defaultTabStop w:val="708"/><w:themeFontLang w:val="pt-BR"/></w:settings>',
        "word/fontTable.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:font w:name="Times New Roman"><w:charset w:val="00"/><w:family w:val="roman"/><w:pitch w:val="variable"/></w:font><w:font w:name="Courier New"><w:charset w:val="00"/><w:family w:val="modern"/><w:pitch w:val="fixed"/></w:font></w:fonts>',
        "docProps/core.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>{escape(TITLE)}</dc:title><dc:creator>{escape(AUTHOR)}</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified><dc:language>pt-BR</dc:language></cp:coreProperties>',
        "docProps/app.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex OOXML Generator</Application><Company>CTD/DGB</Company></Properties>',
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        for name, content in files.items():
            docx.writestr(name, content)
        if ENDPOINT_IMAGE.exists():
            docx.write(ENDPOINT_IMAGE, "word/media/endpoint.png")
        for index, item in enumerate(photos, start=1):
            docx.write(item["path"], f"word/media/photo{index}.jpeg")


def write_future_work_md() -> None:
    content = "# Trabalhos futuros para atualização do relatório\n\n" + "\n".join(
        f"- {item}" for item in FUTURE_WORK
    ) + "\n"
    FUTURE_WORK_MD_PATH.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    HTML_PATH.write_text(render_html(), encoding="utf-8", newline="\n")
    write_docx(DOCX_PATH)
    write_future_work_md()
    print(HTML_PATH)
    print(DOCX_PATH)
    print(FUTURE_WORK_MD_PATH)
    print(json.dumps({"sections": len(SECTIONS), "snippets": len(CODE_SNIPPETS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
