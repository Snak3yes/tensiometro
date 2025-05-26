from grbl_streamer import GrblStreamer
import re, logging

log = logging.getLogger("GrblPatched")

class GrblPatched(GrblStreamer):
    """
    Subclasse que corrige o bug do _update_hash_state
    na presença da linha [HLP:...] emitida por Grbl 1.1g.
    """
    _RE_NUMERIC_TUPLE = re.compile(r'^-?\d+(\.\d+)?$')



    #  Construtor: garante hash_state e referencia da serial
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Evita AttributeError no primeiro _onread()
        if not hasattr(self, "hash_state"):
            self.hash_state: dict[str, object] = {}
        # Nome real do atributo onde a lib guarda a porta serial
        self._serial_attrs = (
            "handle_serial", "ser", "_serial", "serial",
            "_GrblStreamer__serial"        # ← possível pelo name-mangling
        )
        # guarda handle descoberto (opcional, para acelerar próximas buscas)
        self._serial_cached = None


    #  Procura dinamicamente o objeto pySerial dentro da instância
    def _find_serial_handle(self):
        # a) já temos cache válido?
        if self._serial_cached and getattr(self._serial_cached, "is_open", False):
            return self._serial_cached

        # b) busca pelos nomes “conhecidos”
        for attr in self._serial_attrs:
            ser = getattr(self, attr, None)
            if ser and getattr(ser, "write", None):
                self._serial_cached = ser
                return ser

        # c) procura qualquer atributo que pareça um Serial
        import serial as _pyserial
        for name, val in self.__dict__.items():
            if isinstance(val, _pyserial.Serial):
                self._serial_cached = val
                # anexa nome novo para acelerar da próxima vez
                if name not in self._serial_attrs:
                    self._serial_attrs += (name,)
                    log.debug("Novo atributo serial descoberto: %s", name)
                return val
        # d) procura dentro do _iface da grbl-streamer ----------------
        iface = getattr(self, "_iface", None)
        if iface:
            # tenta iface.ser / iface.serial primeiro
            for sub in ("ser", "serial", "_serial"):
                ssub = getattr(iface, sub, None)
                if isinstance(ssub, _pyserial.Serial):
                    self._serial_cached = ssub
                    log.debug("Serial encontrado em _iface.%s", sub)
                    return ssub
            # varre demais atributos do _iface
            for subname, subval in iface.__dict__.items():
                if isinstance(subval, _pyserial.Serial):
                    self._serial_cached = subval
                    log.debug("Serial encontrado em _iface.%s", subname)
                    return subval

        # e) procura de forma genérica em objetos com atributo .ser
        for objname, obj in self.__dict__.items():
            maybe_ser = getattr(obj, "ser", None)
            if isinstance(maybe_ser, _pyserial.Serial):
                self._serial_cached = maybe_ser
                log.debug("Serial descoberto em %s.ser", objname)
                return maybe_ser

        # nenhum encontrado
        return None

    def _update_hash_state(self, line):
        """
        Copia e corrige o método original.  Linhas cujo prefixo
        não é numérico (ex.: HLP) são apenas armazenadas em
        self.hash_state_raw e **não** convertem para float().
        """
        if not (line.startswith("[") and line.endswith("]")):
            return  # não é hash-state

        # Remove colchetes e separa chave / valores
        inner = line[1:-1]          # "HLP:$$ $# ..."
        if ':' not in inner:
            return
        key, value = inner.split(':', 1)

        # Se o valor tem vírgulas tenta converter; caso contrário pula
        if ',' in value:
            tpl_str = value.split(',')
            # CONVERTE APENAS SE TODOS OS ITENS SÃO NUMÉRICOS -----------
            if all(self._RE_NUMERIC_TUPLE.fullmatch(v.strip()) for v in tpl_str):
                tpl = tuple(float(x) for x in tpl_str)
                self.hash_state[key] = tpl
            else:
                # mantém como string raw sem estourar excepción
                self.hash_state[key] = value
                log.debug("Ignorando conversão numérica de [%s]", inner)
        else:
            # Mantém valor simples (ex.: PRB ou HLP)
            self.hash_state[key] = value



    # Sobrescreve métodos de envio para preservar os ESPAÇOS
    # ---------- baixo nível -------------------------------------------------
    def _raw_write(self, cmd: str):
        """
        Envia `cmd` exatamente como recebido, mantendo todos os
        espaços (necessário para eixos múltiplos: “Y-30.0 A-30.0”).
        """
        ser = self._find_serial_handle()
        if ser is None:
            # Log detalhado para futura investigação
            log.error("Handle serial não encontrado. Atributos disponíveis: %s",
                      ", ".join(self.__dict__.keys()))
            raise RuntimeError("Handle serial não encontrado em GrblStreamer")
        if not cmd.endswith("\n"):
            cmd += "\n"
        ser.write(cmd.encode("ascii"))
        ser.flush()

    # ---------- comandos em tempo-real / prioridade -------------------------
    def send_immediately(self, cmd: str):
        """
        Override que envia o texto cru.  Se falhar, volta
        para a implementação original.
        """
        try:
            self._raw_write(cmd)
            self.last_sent = cmd
        except Exception as exc:
            log.warning("send_immediately RAW falhou (%s); fallback…", exc)
            super().send_immediately(cmd)

    # ---------- fila normal -------------------------------------------------
    def send(self, cmd: str, *args, **kwargs):
        """
        Mesmo comportamento de preservação de espaços para a
        fila padrão de comandos.
        """
        try:
            self._raw_write(cmd)
        except Exception as exc:
            log.warning("send RAW falhou (%s); fallback…", exc)
            super().send(cmd, *args, **kwargs)
