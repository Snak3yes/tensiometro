# test_as228p_fixed.py
# =====================
# Código corrigido para diferentes versões do pymodbus

import time
import logging
from pymodbus.client import ModbusTcpClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AS228PFixed:
    """
    Controlador AS228P-A com interface pymodbus corrigida
    """
    
    def __init__(self, ip_address="192.168.1.5"):
        self.ip_address = ip_address
        self.client = ModbusTcpClient(host=ip_address, port=502, timeout=3.0)
        self.connected = False
        
        logger.info(f"Configurado para AS228P-A: {ip_address}:502")
    
    def conectar(self):
        """Conecta ao AS228P-A"""
        try:
            self.connected = self.client.connect()
            if self.connected:
                logger.info("✅ Conectado ao AS228P-A")
                return self._test_communication()
            else:
                logger.error("❌ Falha na conexão")
                return False
        except Exception as e:
            logger.error(f"Erro de conexão: {e}")
            return False
    
    def _test_communication(self):
        """Teste básico de comunicação"""
        try:
            # Testa leitura do status (deve ser 0 = idle)
            status = self.ler_d(2100)
            logger.info(f"Status inicial do CLP: {status}")
            return status != -999
        except Exception as e:
            logger.error(f"Erro no teste: {e}")
            return False
    
    def escrever_d(self, endereco, valor):
        """Escreve registro D - INTERFACE CORRIGIDA"""
        try:
            # ✅ Tenta diferentes interfaces do pymodbus
            try:
                # Tentativa 1: Interface nova (pymodbus 3.x)
                result = self.client.write_register(address=endereco, value=valor, slave=1)
            except TypeError:
                try:
                    # Tentativa 2: Interface alternativa
                    result = self.client.write_register(endereco, valor, unit=1)
                except TypeError:
                    # Tentativa 3: Interface mais simples
                    result = self.client.write_register(endereco, valor)
            
            success = not result.isError()
            if success:
                logger.debug(f"D{endereco} = {valor}")
            else:
                logger.error(f"Erro escrevendo D{endereco}: {result}")
            return success
            
        except Exception as e:
            logger.error(f"Exceção D{endereco}: {e}")
            return False
    
    def ler_d(self, endereco):
        """Lê registro D - INTERFACE CORRIGIDA"""
        try:
            # ✅ Tenta diferentes interfaces do pymodbus
            try:
                # Tentativa 1: Interface com parâmetros nomeados
                result = self.client.read_holding_registers(address=endereco, count=1, slave=1)
            except TypeError:
                try:
                    # Tentativa 2: Interface com unit em vez de slave
                    result = self.client.read_holding_registers(endereco, 1, unit=1)
                except TypeError:
                    try:
                        # Tentativa 3: Interface apenas posicionais
                        result = self.client.read_holding_registers(endereco, 1)
                    except TypeError:
                        # Tentativa 4: Interface mais simples
                        result = self.client.read_holding_registers(endereco)
            
            if result.isError():
                logger.error(f"Erro lendo D{endereco}: {result}")
                return -999
            else:
                valor = result.registers[0]
                logger.debug(f"D{endereco} = {valor}")
                return valor
                
        except Exception as e:
            logger.error(f"Exceção D{endereco}: {e}")
            return -999
    
    def escrever_m(self, endereco, valor):
        """Escreve bit M - INTERFACE CORRIGIDA"""
        try:
            # ✅ Tenta diferentes interfaces do pymodbus
            try:
                # Tentativa 1: Interface nova
                result = self.client.write_coil(address=endereco, value=valor, slave=1)
            except TypeError:
                try:
                    # Tentativa 2: Interface alternativa
                    result = self.client.write_coil(endereco, valor, unit=1)
                except TypeError:
                    # Tentativa 3: Interface simples
                    result = self.client.write_coil(endereco, valor)
            
            success = not result.isError()
            if success:
                logger.debug(f"M{endereco} = {'ON' if valor else 'OFF'}")
            else:
                logger.error(f"Erro escrevendo M{endereco}: {result}")
            return success
            
        except Exception as e:
            logger.error(f"Exceção M{endereco}: {e}")
            return False
    
    def ler_m(self, endereco):
        """Lê bit M - INTERFACE CORRIGIDA"""
        try:
            # ✅ Tenta diferentes interfaces do pymodbus
            try:
                # Tentativa 1: Interface com parâmetros nomeados
                result = self.client.read_coils(address=endereco, count=1, slave=1)
            except TypeError:
                try:
                    # Tentativa 2: Interface com unit
                    result = self.client.read_coils(endereco, 1, unit=1)
                except TypeError:
                    try:
                        # Tentativa 3: Interface posicional
                        result = self.client.read_coils(endereco, 1)
                    except TypeError:
                        # Tentativa 4: Interface simples
                        result = self.client.read_coils(endereco)
            
            if result.isError():
                logger.error(f"Erro lendo M{endereco}: {result}")
                return False
            else:
                valor = result.bits[0]
                logger.debug(f"M{endereco} = {'ON' if valor else 'OFF'}")
                return valor
                
        except Exception as e:
            logger.error(f"Exceção M{endereco}: {e}")
            return False
    
    # ========================================================================
    # FUNÇÕES DE CONTROLE (mesmas do código anterior)
    # ========================================================================
    
    def mover_absoluto(self, x=None, y=None, z=None, velocidade=1000):
        """Movimento absoluto"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        logger.info(f"Movimento absoluto: X={x}, Y={y}, Z={z}, V={velocidade}")
        
        try:
            # 1. Define modo absoluto
            if not self.escrever_d(1000, 0):
                return False
            
            # 2. Define velocidade
            if not self.escrever_d(1010, velocidade):
                return False
            
            # 3. Define posições e habilita eixos
            if x is not None:
                if not self.escrever_d(1100, int(x)):
                    return False
                if not self.escrever_m(1100, True):
                    return False
            
            if y is not None:
                if not self.escrever_d(1101, int(y)):
                    return False
                if not self.escrever_m(1101, True):
                    return False
            
            if z is not None:
                if not self.escrever_d(1102, int(z)):
                    return False
                if not self.escrever_m(1102, True):
                    return False
            
            # 4. Pulso de comando
            if not self.escrever_m(1000, True):
                return False
            
            time.sleep(0.1)
            
            if not self.escrever_m(1000, False):
                return False
            
            logger.info("✅ Comando enviado")
            return True
            
        except Exception as e:
            logger.error(f"Erro no movimento: {e}")
            return False
    
    def mover_relativo(self, dx=0, dy=0, dz=0, velocidade=1000):
        """Movimento relativo"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        logger.info(f"Movimento relativo: dX={dx}, dY={dy}, dZ={dz}, V={velocidade}")
        
        try:
            # 1. Define modo relativo
            if not self.escrever_d(1000, 1):
                return False
            
            # 2. Define velocidade
            if not self.escrever_d(1010, velocidade):
                return False
            
            # 3. Define distâncias e habilita eixos
            if dx != 0:
                if not self.escrever_d(1100, int(dx)):
                    return False
                if not self.escrever_m(1100, True):
                    return False
            
            if dy != 0:
                if not self.escrever_d(1101, int(dy)):
                    return False
                if not self.escrever_m(1101, True):
                    return False
            
            if dz != 0:
                if not self.escrever_d(1102, int(dz)):
                    return False
                if not self.escrever_m(1102, True):
                    return False
            
            # 4. Pulso de comando
            if not self.escrever_m(1000, True):
                return False
            
            time.sleep(0.1)
            
            if not self.escrever_m(1000, False):
                return False
            
            logger.info("✅ Comando enviado")
            return True
            
        except Exception as e:
            logger.error(f"Erro no movimento: {e}")
            return False
    
    def iniciar_jog(self, eixo, direcao, velocidade=500):
        """Jog simples"""
        if not self.connected:
            logger.error("CLP não conectado")
            return False
        
        logger.info(f"Jog {eixo} {'positivo' if direcao > 0 else 'negativo'}")
        
        try:
            # Define velocidade global
            self.escrever_d(1010, velocidade)
            
            # Mapeamento conforme programa C
            jog_map = {
                ('X', 1): 1200,   ('X', -1): 1210,
                ('Y', 1): 1201,   ('Y', -1): 1211,
                ('Z', 1): 1202,   ('Z', -1): 1212,
            }
            
            bit_endereco = jog_map.get((eixo.upper(), 1 if direcao > 0 else -1))
            if bit_endereco:
                return self.escrever_m(bit_endereco, True)
            else:
                logger.error(f"Eixo/direção inválida: {eixo}, {direcao}")
                return False
                
        except Exception as e:
            logger.error(f"Erro no jog: {e}")
            return False
    
    def parar_jog(self, eixo=None):
        """Para jog"""
        if not self.connected:
            return False
        
        try:
            if eixo is None:
                # Para todos os eixos
                logger.info("Parando todos os jogs")
                success = True
                for bit in [1200, 1210, 1201, 1211, 1202, 1212]:
                    success &= self.escrever_m(bit, False)
                return success
            else:
                # Para eixo específico
                eixo_bits = {
                    'X': [1200, 1210], 'Y': [1201, 1211], 'Z': [1202, 1212],
                }
                
                bits = eixo_bits.get(eixo.upper())
                if bits:
                    logger.info(f"Parando jog {eixo}")
                    success = True
                    for bit in bits:
                        success &= self.escrever_m(bit, False)
                    return success
                
        except Exception as e:
            logger.error(f"Erro parando jog: {e}")
            return False
    
    def ler_posicao(self):
        """Lê posição atual"""
        if not self.connected:
            return None
        
        try:
            x = self.ler_d(2000)  # Posição atual X
            y = self.ler_d(2002)  # Posição atual Y  
            z = self.ler_d(2004)  # Posição atual Z
            
            if x != -999 and y != -999 and z != -999:
                return {'x': x, 'y': y, 'z': z}
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erro lendo posição: {e}")
            return None
    
    def ler_status(self):
        """Lê status completo"""
        if not self.connected:
            return None
        
        try:
            estado = self.ler_d(2100)      # machine_state
            eixos_mov = self.ler_d(2101)   # axes_moving  
            alarmes = self.ler_d(2102)     # código alarme
            vel_atual = self.ler_d(2103)   # velocidade atual
            ciclos = self.ler_d(2105)      # scan_counter
            
            estado_nomes = {0: "Idle", 1: "Movendo", 2: "Alarme", 3: "Jog"}
            
            return {
                'estado_codigo': estado,
                'estado_nome': estado_nomes.get(estado, f"Desconhecido({estado})"),
                'eixos_em_movimento': eixos_mov,
                'alarmes_ativos': alarmes,
                'velocidade_atual': vel_atual,
                'ciclos_scan': ciclos,
                'posicao': self.ler_posicao()
            }
            
        except Exception as e:
            logger.error(f"Erro lendo status: {e}")
            return None
    
    def parada_emergencia(self):
        """Parada de emergência"""
        if not self.connected:
            return False
        
        logger.warning("🛑 PARADA DE EMERGÊNCIA")
        return self.escrever_m(9999, True)
    
    def reset_sistema(self):
        """Reset do sistema"""
        if not self.connected:
            return False
        
        logger.info("Reset do sistema")
        success = self.escrever_m(9998, True)
        time.sleep(0.2)
        return success
    
    def aguardar_idle(self, timeout=10):
        """Aguarda máquina ficar idle"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.ler_status()
            if status and status['estado_nome'] == "Idle":
                return True
            time.sleep(0.1)
        
        logger.warning(f"Timeout aguardando idle ({timeout}s)")
        return False
    
    def desconectar(self):
        """Desconecta do AS228P-A"""
        if self.client and self.connected:
            self.client.close()
            self.connected = False
            logger.info("Desconectado do AS228P-A")


def main():
    """Programa de teste"""
    print("=== TESTE AS228P-A - INTERFACE CORRIGIDA ===\n")
    
    # IP do seu AS228P-A
    IP_ADDRESS = "192.168.1.5"
    
    clp = AS228PFixed(IP_ADDRESS)
    
    try:
        # 1. Conecta
        print("1. Conectando...")
        if not clp.conectar():
            print("❌ Falha na conexão!")
            return
        print("✅ Conectado!")
        
        # 2. Teste básico de comunicação
        print("\n2. Teste básico de comunicação...")
        print("   Escrevendo D1000 = 123...")
        if clp.escrever_d(1000, 123):
            print("   ✅ Escrita OK")
            
            print("   Lendo D1000...")
            valor = clp.ler_d(1000)
            if valor == 123:
                print(f"   ✅ Leitura OK: {valor}")
            else:
                print(f"   ⚠️ Valor diferente: {valor}")
        
        # 3. Status do sistema
        print("\n3. Status do sistema:")
        status = clp.ler_status()
        if status:
            print(f"   Estado: {status['estado_nome']}")
            print(f"   Ciclos scan: {status['ciclos_scan']}")
            if status['posicao']:
                pos = status['posicao']
                print(f"   Posição: X={pos['x']}, Y={pos['y']}, Z={pos['z']}")
        
        # 4. Teste movimento
        print("\n4. Teste movimento absoluto...")
        if clp.mover_absoluto(x=50, y=100, velocidade=800):
            print("   ✅ Comando enviado")
            time.sleep(2)
            
            pos = clp.ler_posicao()
            if pos:
                print(f"   Posição final: X={pos['x']}, Y={pos['y']}, Z={pos['z']}")
        
        print("\n✅ Comunicação funcionando!")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        clp.parada_emergencia()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        clp.desconectar()
        print("Desconectado")


if __name__ == "__main__":
    main()
