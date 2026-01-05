"""
Teste de validação para as correções da calibração FOV
"""

import sys
sys.path.insert(0, r'c:\Users\sense\PycharmProjects\Tensiometro')

from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter

def test_fixed_camera_fov():
    """Testa que FOV é constante para câmera fixa"""
    print("=" * 60)
    print("Teste 1: FOV Constante (Câmera Fixa)")
    print("=" * 60)
    
    fov = FOVCalibration(
        z0_z_pulses=0,
        z0_width_mm=50.0,
        z0_height_mm=37.5
    )
    
    # Verifica que z1 = z0 (forçado pela classe)
    assert fov.z0_width_mm == fov.z1_width_mm, "z0_width deve ser igual a z1_width"
    assert fov.z0_height_mm == fov.z1_height_mm, "z0_height deve ser igual a z1_height"
    print("✅ FOV mantém valores constantes entre z0 e z1")
    
    # Testa conversor
    converter = CameraFOVConverter(fov)
    converter.set_frame_size(640, 480)
    converter.set_axis_calibration("X", 100.0)  # 100 pulsos/mm
    converter.set_axis_calibration("Y", 100.0)
    
    # FOV deve ser o mesmo em qualquer Z
    fov_z0 = converter.get_fov_at_z(0)
    fov_z100 = converter.get_fov_at_z(100)
    fov_z200 = converter.get_fov_at_z(200)
    
    print(f"  FOV em Z=0:   {fov_z0}")
    print(f"  FOV em Z=100: {fov_z100}")
    print(f"  FOV em Z=200: {fov_z200}")
    
    assert fov_z0 == fov_z100 == fov_z200, "FOV deve ser constante em todas as alturas Z"
    print("✅ FOV constante em todas as alturas Z confirmado!")
    print()

def test_y_inversion():
    """Testa a inversão correta do eixo Y"""
    print("=" * 60)
    print("Teste 2: Inversão Correta do Eixo Y")
    print("=" * 60)
    
    fov = FOVCalibration(
        z0_z_pulses=0,
        z0_width_mm=50.0,
        z0_height_mm=37.5
    )
    
    converter = CameraFOVConverter(fov)
    converter.set_frame_size(640, 480)  # Frame da câmera
    converter.set_axis_calibration("X", 100.0)  # 100 pulsos/mm
    converter.set_axis_calibration("Y", 100.0)
    
    # Simula clique abaixo do centro (Y maior)
    # Center: (320, 240)
    # Click:  (320, 340) - 100 pixels abaixo do centro
    display_w, display_h = 640, 480
    
    print("Cenário 1: Clique ABAIXO do centro (sem espelhamento)")
    click_x, click_y = 320, 340
    dx_pulses, dy_pulses = converter.video_click_to_movement(
        click_x, click_y,
        display_w, display_h,
        z_pulses=0,
        invert_y=False  # Comportamento padrão
    )
    print(f"  Clique: ({click_x}, {click_y})")
    print(f"  Movimento: dx={dx_pulses} pulsos, dy={dy_pulses} pulsos")
    print(f"  ✅ Esperado: dx≈0, dy<0 (câmera move para BAIXO)")
    assert abs(dx_pulses) < 10, f"dx deveria ser ~0, mas é {dx_pulses}"
    assert dy_pulses < 0, f"dy deveria ser negativo (câmera para baixo), mas é {dy_pulses}"
    print()
    
    print("Cenário 2: Clique ACIMA do centro (sem espelhamento)")
    click_x, click_y = 320, 140
    dx_pulses, dy_pulses = converter.video_click_to_movement(
        click_x, click_y,
        display_w, display_h,
        z_pulses=0,
        invert_y=False  # Comportamento padrão
    )
    print(f"  Clique: ({click_x}, {click_y})")
    print(f"  Movimento: dx={dx_pulses} pulsos, dy={dy_pulses} pulsos")
    print(f"  ✅ Esperado: dx≈0, dy>0 (câmera move para CIMA)")
    assert abs(dx_pulses) < 10, f"dx deveria ser ~0, mas é {dx_pulses}"
    assert dy_pulses > 0, f"dy deveria ser positivo (câmera para cima), mas é {dy_pulses}"
    print()
    
    print("Cenário 3: Clique à DIREITA do centro (sem espelhamento)")
    click_x, click_y = 420, 240
    dx_pulses, dy_pulses = converter.video_click_to_movement(
        click_x, click_y,
        display_w, display_h,
        z_pulses=0,
        invert_y=False  # Comportamento padrão
    )
    print(f"  Clique: ({click_x}, {click_y})")
    print(f"  Movimento: dx={dx_pulses} pulsos, dy={dy_pulses} pulsos")
    print(f"  ✅ Esperado: dx>0 (mover para DIREITA), dy≈0")
    assert dx_pulses > 0, f"dx deveria ser positivo (mover para direita), mas é {dx_pulses}"
    assert abs(dy_pulses) < 10, f"dy deveria ser ~0, mas é {dy_pulses}"
    print()
    
    print("Cenário 4: Clique à ESQUERDA do centro (sem espelhamento)")
    click_x, click_y = 220, 240
    dx_pulses, dy_pulses = converter.video_click_to_movement(
        click_x, click_y,
        display_w, display_h,
        z_pulses=0,
        invert_y=False  # Comportamento padrão
    )
    print(f"  Clique: ({click_x}, {click_y})")
    print(f"  Movimento: dx={dx_pulses} pulsos, dy={dy_pulses} pulsos")
    print(f"  ✅ Esperado: dx<0 (mover para ESQUERDA), dy≈0")
    assert dx_pulses < 0, f"dx deveria ser negativo (mover para esquerda), mas é {dx_pulses}"
    assert abs(dy_pulses) < 10, f"dy deveria ser ~0, mas é {dy_pulses}"
    print()

def main():
    print()
    print("🧪 VALIDAÇÃO DAS CORREÇÕES FOV")
    print()
    
    try:
        test_fixed_camera_fov()
        test_y_inversion()
        
        print("=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print()
        print("Resumo das correções validadas:")
        print("1. ✅ FOV é constante (câmera fixa)")
        print("2. ✅ Movimento Y correto (mesmo sentido do clique)")
        print("3. ✅ Movimento X correto (mesmo sentido do clique)")
        print()
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("❌ FALHA NO TESTE!")
        print("=" * 60)
        print(f"Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
