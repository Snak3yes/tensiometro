# teste_seguro_motor.py
# Teste com movimentos muito pequenos para verificar funcionamento
import time
from test_as228p_simple import AS228PFixed

def teste_seguro():
    clp = AS228PFixed("192.168.1.5")
    
    if clp.conectar():
        print("🔧 TESTE SEGURO - MOVIMENTOS MÍNIMOS")
        
        # Teste 1: 1 passo apenas (0.9°)
        print("Teste 1: 1 passo...")
        clp.mover_relativo(dx=1, velocidade=50)  # Muito devagar
        time.sleep(2)
        
        # Teste 2: Volta para origem
        print("Teste 2: Volta 1 passo...")
        clp.mover_relativo(dx=-1, velocidade=50)
        time.sleep(2)
        
        # Teste 3: Movimento um pouco maior
        print("Teste 3: 10 passos...")
        clp.mover_relativo(dx=10, velocidade=100)
        time.sleep(2)
        
        print("✅ Testes básicos concluídos!")
        
    clp.desconectar()
