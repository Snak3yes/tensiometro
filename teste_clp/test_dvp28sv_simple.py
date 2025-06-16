# test_dvp28sv_simple.py
# ======================
# Teste básico para validar comunicação e movimento

import time
import logging
from pymodbus.client import ModbusSerialClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DVP28SVSimpleTest:
    """Teste simples para DVP28SV com código funcional completo"""
    
    def __init__(self, port="COM3", baudrate=9600):
        # ✅ Interface corrigida para pymodbus 3.x
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=2.0
        )
        self.connected = False
        
    def conectar(self):
        """Conecta ao CLP"""
        try:
            self.connected = self.client.connect()
            if self.connected:
                logger.info("Conectado ao DVP28SV com sucesso")
                # Teste de comunicação básico
                return True
            else:
                logger.error("Falha na conexão")
                return False
        except Exception as e:
            logger.error(f"Erro de conexão: {e}")
            return False
    
    def escrever_d(self, endereco, valor):
        """Escreve em registro D"""
        try:
            # ✅ Interface corrigida - sem .isError()
            result = self.client.write_register(endereco, valor, slave=1)
            if result.isError():
                logger.error(f"Erro escrevendo D{endereco}: {result}")
                return False
            else:
                logger.info(f"D{endereco} = {valor}")
                return True
        except Exception as e:
            logger.error(f"Exceção ao escrever D{endereco}: {e}")
            return False
    
    def ler_d(self, endereco):
        """Lê registro D"""
        try:
            # ✅ Interface corrigida - parâmetro slave em vez de unit
            result = self.client.read_holding_registers(endereco, 1, slave=1)
            if result.isError():
                logger.error(f"Erro lendo D{endereco}: {result}")
                return -999
            else:
                valor = result.registers[0]
                logger.debug(f"D{endereco} = {valor}")
                return valor
        except Exception as e:
            logger.error(f"Exceção ao ler D{endereco}: {e}")
            return -999
    
    def ligar_m(self, endereco):
        """Liga bit M"""
        try:
            result = self.client.write_coil(endereco, True, slave=1)
            if result.isError():
                logger.error(f"Erro ligando M{endereco}: {result}")
                return False
            else:
                logger.info(f"M{endereco} = ON")
                return True
        except Exception as e:
            logger.error(f"Exceção ao ligar M{endereco}: {e}")
            return False
    
    def desligar_m(self, endereco):
        """Desliga bit M"""
        try:
            result = self.client.write_coil(endereco, False, slave=1)
            if result.isError():
                logger.error(f"Erro desligando M{endereco}: {result}")
                return False
            else:
                logger.info(f"M{endereco} = OFF")
                return True
        except Exception as e:
            logger.error(f"Exceção ao desligar M{endereco}: {e}")
            return False
    
    def mover_absoluto(self, x=None, y=None, velocidade=1000):
        """Move para posição absoluta"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        logger.info(f"Movimento absoluto: X={x}, Y={y}, V={velocidade}")
        
        try:
            # 1. Define modo absoluto
            if not self.escrever_d(120, 0):  # D120 = 0 (absoluto)
                return False
            
            # 2. Define velocidade
            if not self.escrever_d(110, velocidade):  # D110 = velocidade
                return False
            
            # 3. Define posições (se especificadas)
            if x is not None:
                if not self.escrever_d(100, int(x)):  # D100 = posição X
                    return False
            
            if y is not None:
                if not self.escrever_d(101, int(y)):  # D101 = posição Y
                    return False
            
            # 4. Define comando de movimento
            if not self.escrever_d(130, 1):  # D130 = 1 (mover)
                return False
            
            # 5. Pulso de execução
            if not self.ligar_m(100):  # M100 = ON
                return False
            
            time.sleep(0.1)  # Pulso de 100ms
            
            if not self.desligar_m(100):  # M100 = OFF
                return False
            
            logger.info("Comando de movimento enviado")
            return True
            
        except Exception as e:
            logger.error(f"Erro no movimento absoluto: {e}")
            return False
    
    def mover_relativo(self, dx=0, dy=0, velocidade=1000):
        """Move relativo à posição atual"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        logger.info(f"Movimento relativo: dX={dx}, dY={dy}, V={velocidade}")
        
        try:
            # 1. Define modo relativo
            if not self.escrever_d(120, 1):  # D120 = 1 (relativo)
                return False
            
            # 2. Define velocidade
            if not self.escrever_d(110, velocidade):
                return False
            
            # 3. Define distâncias
            if dx != 0:
                if not self.escrever_d(100, int(dx)):
                    return False
            
            if dy != 0:
                if not self.escrever_d(101, int(dy)):
                    return False
            
            # 4. Executa movimento
            if not self.escrever_d(130, 1):
                return False
            
            # 5. Pulso de execução
            if not self.ligar_m(100):
                return False
            
            time.sleep(0.1)
            
            if not self.desligar_m(100):
                return False
            
            logger.info("Comando de movimento relativo enviado")
            return True
            
        except Exception as e:
            logger.error(f"Erro no movimento relativo: {e}")
            return False
    
    def iniciar_jog(self, eixo, direcao, velocidade=500):
        """Inicia jog contínuo"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        # Mapeia comando de jog
        comandos_jog = {
            ('X', 1): 2,   # X+
            ('X', -1): 3,  # X-
            ('Y', 1): 4,   # Y+
            ('Y', -1): 5,  # Y-
        }
        
        cmd = comandos_jog.get((eixo.upper(), 1 if direcao > 0 else -1))
        if cmd is None:
            logger.error(f"Comando de jog inválido: {eixo}, {direcao}")
            return False
        
        logger.info(f"Iniciando jog {eixo} {'positivo' if direcao > 0 else 'negativo'}")
        
        try:
            # Define velocidade
            if not self.escrever_d(110, velocidade):
                return False
             
            # Define comando de jog
            if not self.escrever_d(130, cmd):
                return False
            return True
        except Exception as e:
            logger.error(f"Erro no jog: {e}")
            return False

    def parar_jog(self):
        """Para jog contínuo"""
        if not self.connected:
            return False

        logger.info("Parando jog")
        return self.escrever_d(130, 6)  # D130 = 6 (parar jog)
     
    def ler_posicao(self):
        """Lê posição atual"""
        if not self.connected:
            return None
        
        try:
            x = self.ler_d(200)  # D200 = posição X
            y = self.ler_d(201)  # D201 = posição Y
            
            if x != -999 and y != -999:
                return {'x': x, 'y': y}
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erro lendo posição: {e}")
            return None
     
    def ler_status(self):
        """Lê status da máquina"""
        if not self.connected:
            return None
        
        try:
            status_code = self.ler_d(210)  # D210 = status
            
            status_names = {
                0: "Idle",
                1: "Movendo",
                2: "Alarme", 
                3: "Jog"
            }
            
            return {
                'codigo': status_code,
                'nome': status_names.get(status_code, f"Desconhecido({status_code})"),
                'posicao': self.ler_posicao()
            }
            
        except Exception as e:
            logger.error(f"Erro lendo status: {e}")
            return None
     
    def desconectar(self):
         """Desconecta do CLP"""
         if self.client:
             self.client.close()
             self.connected = False
             logger.info("Desconectado do DVP28SV")


def main():
    """Programa principal de teste"""
    print("=== TESTE DVP28SV - MOVIMENTO DE MOTORES ===\n")
    
    # AJUSTE A PORTA CONFORME SEU SETUP
    PORT = "COM3"  # Windows
    # PORT = "/dev/ttyUSB0"  # Linux
    
    dvp = DVP28SVSimpleTest(PORT, 9600)
    
    try:
        # 1. Conecta
        print("1. Conectando...")
        if not dvp.conectar():
            print("❌ Falha na conexão!")
            print("   Verifique:")
            print("   - Porta COM correta (Windows: COM1, COM2, etc.)")
            print("   - CLP ligado e cabo conectado")
            print("   - Conversor USB-RS485 funcionando")
            return
        print("✅ Conectado!")
        
        # 2. Teste comunicação básica
        print("\n2. Teste de comunicação...")
        print("   Testando escrita em D100...")
        if dvp.escrever_d(100, 12345):
            print("   ✅ Escrita OK")
            
            print("   Testando leitura de D100...")
            valor = dvp.ler_d(100)
            if valor == 12345:
                print(f"   ✅ Leitura OK: D100 = {valor}")
            else:
                print(f"   ⚠️ Valor lido diferente: {valor} (esperado: 12345)")
        else:
            print("   ❌ Falha na escrita")
        
        # 3. Teste movimento absoluto
        print("\n3. Teste movimento absoluto...")
        print("   Movendo para X=100, Y=200 (em pulsos)")
        if dvp.mover_absoluto(x=100, y=200, velocidade=1000):
            print("   ✅ Comando enviado")
            time.sleep(2)  # Aguarda movimento
            
            pos = dvp.ler_posicao()
            if pos:
                print(f"   Posição atual: X={pos['x']}, Y={pos['y']}")
        else:
            print("   ❌ Falha no comando")
        
        # 4. Teste movimento relativo
        print("\n4. Teste movimento relativo...")
        print("   Movendo +50 em X, -30 em Y")
        if dvp.mover_relativo(dx=50, dy=-30, velocidade=800):
            print("   ✅ Comando enviado")
            time.sleep(2)
            
            pos = dvp.ler_posicao()
            if pos:
                print(f"   Posição atual: X={pos['x']}, Y={pos['y']}")
        
        # 5. Teste jog
        print("\n5. Teste jog contínuo...")
        print("   Jog Xpor 2 segundos")
        if dvp.iniciar_jog('X', 1, velocidade=300):
            print("   ✅ Jog iniciado")
            time.sleep(2)
            dvp.parar_jog()
            print("   ✅ Jog parado")
            
            pos = dvp.ler_posicao()
            if pos:
                print(f"   Posição final: X={pos['x']}, Y={pos['y']}")
        
        print("\n✅ Todos os testes concluídos!")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        print("Detalhes do erro:")
        traceback.print_exc()
        
    finally:
        dvp.desconectar()
        print("Desconectado")


if __name__ == "__main__":
    main()
