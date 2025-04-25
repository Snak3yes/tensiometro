; AOI Inspection Sequence Generated G-CODE
; Date: 2025-04-24 18:00:55
;AOI_SEQUENCE_NAME: Sequência PCB
; Total positions: 4
; Feed rate: 1000 mm/min
;
G21 ; Set units to mm
G90 ; Set absolute positioning
F1000 ; Set feed rate

; Position 1: a
;AOI_POSITION_NAME: a
;AOI_CAMERA_PARAMS: has_image:True
G0 X-10.000 Y0.000 ; Move to position
;AOI_CAPTURE_IMAGE ; Capture image at this position

; Position 2: b
;AOI_POSITION_NAME: b
;AOI_CAMERA_PARAMS: has_image:True
G0 X-20.000 Y0.000 ; Move to position
;AOI_CAPTURE_IMAGE ; Capture image at this position

; Position 3: c
;AOI_POSITION_NAME: c
;AOI_CAMERA_PARAMS: has_image:True
G0 X-20.000 Y10.000 ; Move to position
;AOI_CAPTURE_IMAGE ; Capture image at this position

; Position 4: d
;AOI_POSITION_NAME: d
;AOI_CAMERA_PARAMS: has_image:True
G0 X-10.000 Y10.000 ; Move to position
;AOI_CAPTURE_IMAGE ; Capture image at this position

; Position 5: e
;AOI_POSITION_NAME: d
;AOI_CAMERA_PARAMS: has_image:True
G0 X-15.000 Y15.000 ; Move to position
;AOI_CAPTURE_IMAGE ; Capture image at this position


M2 ; End program