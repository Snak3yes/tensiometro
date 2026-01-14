"""
Measurement Orchestrator for Tension Measurement System

Coordinates the complete measurement workflow including:
- Parameter validation
- Grid calculation
- Thread management
- Result persistence
- Progress callbacks

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
"""

import logging
import json
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from .models import (
    GridPoint,
    GridParameters,
    TensionMeasurement,
    MeasurementSession
)
from .measurement_service import (
    GridCalculationService,
    MeasurementAnalysisService,
    ValidationError
)
from .measurement_thread import TensionMeasurementThread

logger = logging.getLogger(__name__)


class MeasurementOrchestrator:
    """
    Orchestrates the complete tension measurement workflow.

    This class coordinates:
    - Parameter validation
    - Grid calculation
    - Thread lifecycle
    - Progress callbacks
    - Result persistence

    It acts as a facade between the UI and the measurement subsystem,
    hiding complexity and providing a clean interface.

    Attributes:
        cnc: CNC controller for movement
        tensiometer: TensiometerSerialManager for reading values
        save_directory: Directory where results are saved
    """

    def __init__(self, cnc, tensiometer, save_directory: Optional[Path] = None):
        """
        Initialize orchestrator.

        Args:
            cnc: CNC controller (must have move_to_absolute_position, wait_for_idle)
            tensiometer: TensiometerSerialManager instance
            save_directory: Where to save JSON results (default: ./tension_routines/)
        """
        self.cnc = cnc
        self.tensiometer = tensiometer

        # Default save directory
        if save_directory is None:
            save_directory = Path(__file__).parent.parent.parent / "tension_routines"

        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)

        # State
        self.session: Optional[MeasurementSession] = None
        self.thread: Optional[TensionMeasurementThread] = None

        # Callbacks (optional UI hooks)
        self._on_progress: Optional[Callable[[int, int, str], None]] = None
        self._on_measurement: Optional[Callable[[Dict], None]] = None
        self._on_complete: Optional[Callable[[Dict], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

    def prepare_measurement(
        self,
        start_point: tuple,
        end_point: tuple,
        grid_size: int,
        z_height: float,
        z_move: float = 5.0,
        user_feed: float = 1000.0,
        stabilization_time_ms: int = 500
    ) -> Dict[str, Any]:
        """
        Prepare measurement parameters and validate.

        Args:
            start_point: (x, y) starting position in mm
            end_point: (x, y) ending position in mm
            grid_size: N for NxN grid
            z_height: Z measurement height in mm
            z_move: Safe Z height for movement
            user_feed: Feed rate in mm/min
            stabilization_time_ms: Stabilization delay in ms

        Returns:
            Dictionary with preparation results:
            - success: bool
            - session: MeasurementSession (if success)
            - points: List[GridPoint] (if success)
            - error: str (if failed)
            - statistics: Grid statistics (if success)

        Example:
            >>> result = orchestrator.prepare_measurement(
            ...     start_point=(0, 0), end_point=(100, 100),
            ...     grid_size=3, z_height=5.0
            ... )
            >>> if result['success']:
            ...     print(f"Prepared {result['statistics']['total_points']} points")
        """
        try:
            logger.info("Preparando medição de tensão")

            # Create parameters object
            parameters = GridParameters(
                start_point=start_point,
                end_point=end_point,
                grid_size=grid_size,
                z_height=z_height,
                z_move=z_move
            )

            # Validate and calculate grid points
            points = GridCalculationService.calculate_grid_points(parameters)

            # Get grid statistics
            stats = GridCalculationService.get_grid_statistics(points)

            # Create session
            session = MeasurementSession(
                parameters=parameters,
                measurements=[],
                user_feed=user_feed,
                stabilization_time_ms=stabilization_time_ms
            )

            # Store session
            self.session = session

            logger.info(f"Preparação completa: {len(points)} pontos")

            return {
                "success": True,
                "session": session,
                "points": points,
                "statistics": stats,
                "parameters": {
                    "start": start_point,
                    "end": end_point,
                    "grid_size": grid_size,
                    "z_height": z_height,
                    "z_move": z_move,
                    "feed": user_feed,
                    "stabilization_ms": stabilization_time_ms
                }
            }

        except ValidationError as e:
            logger.error(f"Validação falhou: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation"
            }
        except Exception as e:
            logger.error(f"Erro na preparação: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "unknown"
            }

    def start_measurement(
        self,
        points: list,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_measurement: Optional[Callable[[Dict], None]] = None,
        on_complete: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Start measurement in background thread.

        Args:
            points: List of GridPoint objects
            on_progress: Callback(current, total, message)
            on_measurement: Callback(measurement_dict)
            on_complete: Callback(results_dict)
            on_error: Callback(error_message)

        Returns:
            True if started successfully, False otherwise

        Example:
            >>> def on_progress(cur, total, msg):
            ...     print(f"{cur}/{total}: {msg}")
            >>> orchestrator.start_measurement(points, on_progress=on_progress)
        """
        if self.session is None:
            logger.error("Session não preparada. Chame prepare_measurement() primeiro.")
            return False

        if self.thread is not None and self.thread.isRunning():
            logger.warning("Medição já em andamento")
            return False

        try:
            logger.info("Iniciando medição em background thread")

            # Store callbacks
            self._on_progress = on_progress
            self._on_measurement = on_measurement
            self._on_complete = on_complete
            self._on_error = on_error

            # Create thread
            self.thread = TensionMeasurementThread(
                cnc=self.cnc,
                tensiometer=self.tensiometer,
                points=points,
                z_height=self.session.parameters.z_height,
                z_move=self.session.parameters.z_move,
                user_feed=self.session.user_feed,
                stabilization_time_ms=self.session.stabilization_time_ms
            )

            # Connect signals
            self.thread.progress_updated.connect(self._handle_progress)
            self.thread.measurement_completed.connect(self._handle_measurement)
            self.thread.finished.connect(self._handle_finished)
            self.thread.error_occurred.connect(self._handle_error)

            # Start thread
            self.thread.start()

            logger.info("Thread de medição iniciada")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar medição: {e}", exc_info=True)
            return False

    def stop_measurement(self) -> None:
        """Request graceful stop of measurement."""
        if self.thread and self.thread.isRunning():
            logger.info("Solicitando parada da medição")
            self.thread.request_stop()

    def _handle_progress(self, current: int, total: int, message: str) -> None:
        """Handle progress update from thread."""
        logger.debug(f"Progress: {current}/{total} - {message}")

        # Call user callback if provided
        if self._on_progress:
            try:
                self._on_progress(current, total, message)
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")

    def _handle_measurement(self, measurement_dict: Dict) -> None:
        """Handle individual measurement completion."""
        logger.debug(f"Medição recebida: ponto {measurement_dict.get('x', 0)}, {measurement_dict.get('y', 0)}")

        # Add to session
        if self.session:
            # Reconstruct measurement object from dict
            from .models import GridPoint, TensionMeasurement
            point = GridPoint(
                x=measurement_dict['x'],
                y=measurement_dict['y'],
                index=0,  # Will be updated
                grid_position=(0, 0)
            )
            measurement = TensionMeasurement(
                point=point,
                z_height=measurement_dict['z'],
                tension_value=measurement_dict['tension']
            )
            self.session.add_measurement(measurement)

        # Call user callback if provided
        if self._on_measurement:
            try:
                self._on_measurement(measurement_dict)
            except Exception as e:
                logger.error(f"Erro no callback de medição: {e}")

    def _handle_finished(self, measurements_list: list) -> None:
        """Handle measurement completion."""
        logger.info(f"Medição finalizada: {len(measurements_list)} pontos")

        # Complete session
        if self.session:
            self.session.complete_session()

        # Analyze results
        analysis = None
        if self.session:
            analysis = MeasurementAnalysisService.analyze_session(self.session)

        # Prepare results
        results = {
            "success": True,
            "measurements": measurements_list,
            "session": self.session.to_dict() if self.session else None,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

        # Save to file
        if self.session:
            saved_path = self.save_results(self.session)
            results['saved_to'] = str(saved_path) if saved_path else None

        # Call user callback if provided
        if self._on_complete:
            try:
                self._on_complete(results)
            except Exception as e:
                logger.error(f"Erro no callback de complete: {e}")

    def _handle_error(self, error_message: str) -> None:
        """Handle measurement error."""
        logger.error(f"Erro na medição: {error_message}")

        # Call user callback if provided
        if self._on_error:
            try:
                self._on_error(error_message)
            except Exception as e:
                logger.error(f"Erro no callback de erro: {e}")

    def save_results(self, session: MeasurementSession) -> Optional[Path]:
        """
        Save measurement results to JSON file.

        Args:
            session: MeasurementSession to save

        Returns:
            Path to saved file, or None if failed
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tension_measurement_{timestamp}.json"
            filepath = self.save_directory / filename

            # Save
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=4, ensure_ascii=False)

            logger.info(f"Resultados salvos em: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}", exc_info=True)
            return None

    def get_report(self) -> str:
        """
        Generate human-readable report of current session.

        Returns:
            Formatted report string
        """
        if self.session is None:
            return "Nenhuma sessão disponível para relatório"

        return MeasurementAnalysisService.generate_report(self.session)

    @property
    def is_measuring(self) -> bool:
        """Check if measurement is currently running."""
        return self.thread is not None and self.thread.isRunning()

    @property
    def progress(self) -> float:
        """Get current progress percentage (0-100)."""
        if self.session is None:
            return 0.0
        return self.session.progress_percentage

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.thread and self.thread.isRunning():
            logger.warning("Interrompendo medição ativa durante cleanup")
            self.stop_measurement()
            # Wait a bit for graceful shutdown
            import time
            time.sleep(0.5)

        self.thread = None
        self.session = None

        # Clear callbacks
        self._on_progress = None
        self._on_measurement = None
        self._on_complete = None
        self._on_error = None

        logger.debug("Cleanup completo")
