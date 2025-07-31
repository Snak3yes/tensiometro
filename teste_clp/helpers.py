"""
helpers.py – utilitários de alinhamento fiducial
"""

import base64
import time
from typing import Tuple, List

import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication

# ------------------------------------------------------------------
#  LEITURA DE FIDUCIAIS (edição off-line)
# ------------------------------------------------------------------
def read_fiducials(ctrl,
                   positions,
                   camera,
                   current_offset: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
    """
    Percorre a lista `positions` procurando aqueles cujo
    meta['action'] == 'fiducial'.  

    Para cada fiducial:
        1. Move X/Y SEM aplicar offset algum;
        2. Captura frame da câmera;
        3. Faz template-matching;
        4. Converte Δpx → Δpulsos via  ctrl.pulses_from_pixels();
    Retorna (dx_total, dy_total) em pulsos.
    Caso não haja fiducial → devolve (0,0).
    """
    fid_pos = [p for p in positions
               if (getattr(p, "meta", {}) or {}).get("action") == "fiducial"]
    if not fid_pos:
       return 0, 0

    dx_sum = dy_sum = 0
    ox_prev, oy_prev = current_offset
    matched_cnt = 0
    for p in fid_pos:
        # --------------------------------------------------------------
        #  Determina qual eixo Y físico está ativo nesta execução.
        #  PlateFlowManager define   ctrl._active_plate_y   antes de
        #  disparar SequenceRunnerThread, evitando a dependência
        #  da aba visível (que causava AttributeError quando
        #  currentWidget() era AxesControlTab).
        # --------------------------------------------------------------
        axis_y = getattr(ctrl, "_active_plate_y", "Y1")
        # ---------- MOVE X,Y,Z  (usa Z do próprio fiducial) ----------
        ctrl.pulsos_spin_X.setValue(int(p.x + ox_prev))
        
        getattr(ctrl, f'pulsos_spin_{axis_y}').setValue(
            int((p.y1 if axis_y == 'Y1' else p.y2) + oy_prev))
        ctrl.pulsos_spin_Z.setValue(int(p.z))
        # Comando de movimento (X e Y) --------------------------
        ctrl.move_axis_absolute("X")
        ctrl.move_axis_absolute(axis_y)
        ctrl.move_axis_absolute("Z")

        # --------------------------------------------------------------
        # Aguarda CHEGAR ao alvo sem depender de wait_for_idle()
        # (que usa internamente _targets do backend e aqui estamos
        #  chamando o controlador diretamente).
        # Critério simples:
        #     • lê posição física a cada 100 ms;
        #     • quando |pos-alvo| ≤ 2 pulsos para ambos os eixos
        #       durante 3 leituras consecutivas → considera parado;
        #     • abandona após 5 s para não travar a edição.
        # --------------------------------------------------------------
        tgt_x = int(p.x + ox_prev)
        tgt_y = int((p.y1 if axis_y == 'Y1' else p.y2) + oy_prev)
        tgt_z = int(p.z)
        stable_cnt = 0
        t0 = time.time()
        while time.time() - t0 < 5.0:
            # actualiza dict current_positions
            if hasattr(ctrl, "read_current_positions"):
                ctrl.read_current_positions()
            cur_x = ctrl.current_positions.get('X', tgt_x+9999)
            cur_y = ctrl.current_positions.get(axis_y, tgt_y+9999)
            cur_z = ctrl.current_positions.get('Z', tgt_z+9999)
            if (abs(cur_x - tgt_x) <= 2 and
                abs(cur_y - tgt_y) <= 2 and
                abs(cur_z - tgt_z) <= 1):
                stable_cnt += 1
                if stable_cnt >= 3:
                    break
            else:
                stable_cnt = 0
            time.sleep(0.1)
            QApplication.processEvents()
        else:
            # timeout: apenas avisa no log e segue (evita travar GUI)
            ctrl.log("⚠️  Timeout esperando parada durante leitura de fiducial")
 
         

        time.sleep(0.1)                 # estabiliza 100 ms
        ok, frame = camera._cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        meta = p.meta
        tmpl_png = base64.b64decode(meta['template_png_b64'])
        tmpl = cv2.imdecode(np.frombuffer(tmpl_png, np.uint8),
                            cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, sim, _, loc = cv2.minMaxLoc(res)
        if sim*100 < meta.get('threshold', 70):
            continue
        h, w = tmpl.shape
        cx_t = loc[0] + w//2
        cy_t = loc[1] + h//2
        cx_i, cy_i = gray.shape[1]//2, gray.shape[0]//2
        dx_pix = cx_t - cx_i
        dy_pix = cy_t - cy_i
        z_cur  = ctrl.current_positions['Z']
        dx_p, dy_p = ctrl.pulses_from_pixels(dx_pix, dy_pix, z_cur, axis_y)
        dx_sum += dx_p
        dy_sum += dy_p
        matched_cnt += 1

    # ------------------------------------------------------------------
    # Offset = MÉDIA dos deslocamentos medidos nos n fiduciais
    # (soma duplicaria a correção quando existem 2 ou mais pontos)
    # ------------------------------------------------------------------
    if matched_cnt == 0:
        raise ValueError("Nenhum fiducial pôde ser lido (similaridade abaixo do limiar).")

    dx_avg = int(round(dx_sum / matched_cnt))
    dy_avg = int(round(dy_sum / matched_cnt))
    return dx_avg, dy_avg