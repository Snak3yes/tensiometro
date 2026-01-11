# Technology Stack

## Core Technology

### Primary Language
**Language:** Python 3.x

### Frameworks & Libraries
- PyQt6 (GUI framework - modern and minimalista)
- OpenCV (Computer vision for inspection)
- NumPy (Numerical operations and array processing)
- Matplotlib (Charts and trend visualization)
- PyModbus (Modbus TCP communication with PLC)
- PySerial (RS-232 serial communication with tensiometer)
- ReportLab (PDF report generation)

### Database
**Database:** Multiple (SQLite + JSON)

Hybrid approach: SQLite for structured stencil data and history, JSON files for configuration and recipes. Migration to full SQLite in progress.

## Development & Quality

### Testing Framework
**Testing:** pytest

### Package Manager
**Package Manager:** pip (requirements.txt)

## Additional Tools & Constraints
Hardware Integration:
- Delta PLC (CLP): Modbus TCP @ 192.168.1.5:502 for 3-axis (X,Y,Z) CNC control
- AS-120N Tensiometer: RS-232 serial @ 2400 baud, 9-byte binary protocol
- USB Camera: OpenCV-compatible for real-time preview and capture

Specialized Libraries:
- pymodbus: PLC communication
- pyserial: Serial protocol handling
- opencv-python: Image processing and computer vision
- reportlab: Professional PDF generation

---
*This document is managed by Conductor. Last updated: 2026-01-11 12:25:33*
