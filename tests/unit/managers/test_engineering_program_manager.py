"""
Testes unitários para EngineeringProgramManager

Testa operações CRUD de programas de inspeção:
- Salvar programas
- Carregar programas
- Listar programas
- Deletar programas
- Verificar existência
- Auto-save
- Exportar/Importar
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from consumo_lib.managers.engineering_program_manager import EngineeringProgramManager
from consumo_lib.models.engineering.program_config import (
    ProgramConfig,
    FiducialConfig,
    MosaicConfig,
    AlignmentConfig,
    InspectionGroupConfig
)


class TestEngineeringProgramManagerCreation:
    """Testes para criação do gerenciador."""

    def test_create_with_default_directory(self):
        """Testa criação com diretório padrão."""
        manager = EngineeringProgramManager()

        assert manager.programs_dir == Path("data/inspection_programs")
        assert manager.autosaves_dir == manager.programs_dir / ".autosaves"

    def test_create_with_custom_directory(self, tmp_path):
        """Testa criação com diretório customizado."""
        custom_dir = tmp_path / "custom_programs"
        manager = EngineeringProgramManager(programs_dir=custom_dir)

        assert manager.programs_dir == custom_dir
        assert manager.programs_dir.exists()

    def test_directories_created_on_init(self, tmp_path):
        """Testa se diretórios são criados na inicialização."""
        programs_dir = tmp_path / "programs"
        manager = EngineeringProgramManager(programs_dir=programs_dir)

        assert programs_dir.exists()
        assert manager.autosaves_dir.exists()


class TestSaveProgram:
    """Testes para salvamento de programas."""

    @pytest.fixture
    def sample_program(self):
        """Cria programa de exemplo."""
        return ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test Program",
            description="Test program for unit tests",
            version="v1.0",
            gerber_file="test.ger",
            aperture_count=100,
            fiducials=FiducialConfig(
                fiducial1={"x": 10.0, "y": 20.0},
                fiducial2={"x": 30.0, "y": 40.0}
            ),
            mosaic=MosaicConfig(
                grid_rows=4,
                grid_cols=4,
                total_fovs=16
            ),
            alignment=AlignmentConfig(
                translation_x=1.0,
                translation_y=2.0,
                rotation=0.5,
                scale=1.0,
                alignment_score=95.0
            ),
            inspection_groups=[
                InspectionGroupConfig(
                    name="0.5mm Circle",
                    aperture_count=50,
                    confirmed=True
                )
            ],
            created_by="test_user"
        )

    def test_save_program(self, tmp_path, sample_program):
        """Testa salvamento de programa."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)
        filepath = manager.save_program(sample_program)

        assert filepath.exists()
        assert filepath.suffix == ".json"

    def test_save_program_with_custom_filename(self, tmp_path, sample_program):
        """Testa salvamento com nome customizado."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)
        filepath = manager.save_program(sample_program, filename="custom.json")

        assert filepath.name == "custom.json"

    def test_save_program_updates_modified_at(self, tmp_path, sample_program):
        """Testa se modified_at é atualizado ao salvar."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        original_modified = sample_program.modified_at
        filepath = manager.save_program(sample_program)

        # Recarrega para verificar
        loaded = manager.load_program(filepath.name)
        assert loaded.modified_at != original_modified


class TestLoadProgram:
    """Testes para carregamento de programas."""

    @pytest.fixture
    def saved_program(self, tmp_path):
        """Salva um programa de exemplo."""
        program = ProgramConfig(
            stencil_code="STENCIL-002",
            program_name="Load Test",
            version="v1.0"
        )
        manager = EngineeringProgramManager(programs_dir=tmp_path)
        filepath = manager.save_program(program)
        return filepath.name, program

    def test_load_program(self, tmp_path, saved_program):
        """Testa carregamento de programa."""
        filename, original = saved_program
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        loaded = manager.load_program(filename)

        assert loaded.stencil_code == original.stencil_code
        assert loaded.program_name == original.program_name
        assert loaded.version == original.version

    def test_load_program_without_json_extension(self, tmp_path, saved_program):
        """Testa carregamento sem extensão .json."""
        filename, original = saved_program
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Remove .json
        name_without_ext = filename.replace('.json', '')
        loaded = manager.load_program(name_without_ext)

        assert loaded.program_name == original.program_name

    def test_load_nonexistent_program(self, tmp_path):
        """Testa carregamento de programa inexistente."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            manager.load_program("nonexistent.json")


class TestListPrograms:
    """Testes para listagem de programas."""

    @pytest.fixture
    def multiple_programs(self, tmp_path):
        """Cria múltiplos programas."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        programs = []
        for i in range(3):
            program = ProgramConfig(
                stencil_code=f"STENCIL-{i:03d}",
                program_name=f"Program {i}",
                version="v1.0"
            )
            filepath = manager.save_program(program)
            programs.append(filepath.name)

        return manager, programs

    def test_list_programs(self, multiple_programs):
        """Testa listagem de programas."""
        manager, program_names = multiple_programs
        programs = manager.list_programs()

        assert len(programs) == 3
        assert all("name" in p for p in programs)
        assert all("program_name" in p for p in programs)

    def test_list_programs_sorting(self, multiple_programs):
        """Testa se programas são ordenados por nome."""
        manager, program_names = multiple_programs
        programs = manager.list_programs()

        names = [p["name"] for p in programs]
        assert names == sorted(names)

    def test_list_empty_directory(self, tmp_path):
        """Testa listagem de diretório vazio."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)
        programs = manager.list_programs()

        assert len(programs) == 0


class TestDeleteProgram:
    """Testes para deleção de programas."""

    def test_delete_program(self, tmp_path):
        """Testa deleção de programa."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="To Delete",
            version="v1.0"
        )
        filepath = manager.save_program(program)

        # Verifica que existe
        assert filepath.exists()

        # Deleta
        manager.delete_program(filepath.name)

        # Verifica que não existe mais
        assert not filepath.exists()

    def test_delete_nonexistent_program(self, tmp_path):
        """Testa deleção de programa inexistente."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            manager.delete_program("nonexistent.json")


class TestProgramExists:
    """Testes para verificação de existência."""

    def test_program_exists_true(self, tmp_path):
        """Testa verificação de existência (True)."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Exists Test",
            version="v1.0"
        )
        filepath = manager.save_program(program)

        assert manager.program_exists(filepath.name)

    def test_program_exists_false(self, tmp_path):
        """Testa verificação de existência (False)."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        assert not manager.program_exists("nonexistent.json")

    def test_program_exists_without_extension(self, tmp_path):
        """Testa verificação sem extensão .json."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Exists Test",
            version="v1.0"
        )
        filepath = manager.save_program(program)

        # Remove .json
        name_without_ext = filepath.name.replace('.json', '')
        assert manager.program_exists(name_without_ext)


class TestUpdateProgram:
    """Testes para atualização de programas."""

    def test_update_program(self, tmp_path):
        """Testa atualização de programa."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Salva programa original
        original = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Update Test",
            description="Original description",
            version="v1.0"
        )
        filepath = manager.save_program(original)

        # Atualiza
        updated = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Update Test",
            description="Updated description",
            version="v1.0"
        )
        manager.update_program(filepath.name, updated)

        # Recarrega e verifica
        loaded = manager.load_program(filepath.name)
        assert loaded.description == "Updated description"

    def test_update_nonexistent_program(self, tmp_path):
        """Testa atualização de programa inexistente."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Nonexistent",
            version="v1.0"
        )

        with pytest.raises(FileNotFoundError):
            manager.update_program("nonexistent.json", program)


class TestGetProgramInfo:
    """Testes para obter informações de programa."""

    def test_get_program_info(self, tmp_path):
        """Testa obtenção de metadados."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Info Test",
            version="v2.0"
        )
        filepath = manager.save_program(program)

        info = manager.get_program_info(filepath.name)

        assert info["stencil_code"] == "STENCIL-001"
        assert info["program_name"] == "Info Test"
        assert info["version"] == "v2.0"
        assert "filepath" in info


class TestAutosave:
    """Testes para funcionalidade de auto-save."""

    def test_save_autosave(self, tmp_path):
        """Testa salvamento de auto-save."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        state = {"current_tab": 2, "data": "test"}
        filepath = manager.save_autosave(state)

        assert filepath.exists()
        assert filepath.name.startswith(".autosave_")

        # Verifica conteúdo
        with open(filepath, 'r') as f:
            loaded_state = json.load(f)
        assert loaded_state == state

    def test_get_latest_autosave(self, tmp_path):
        """Testa obtenção do auto-save mais recente."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Salva múltiplos autosaves
        state1 = {"tab": 1}
        state2 = {"tab": 2}

        manager.save_autosave(state1)
        # Pequeno delay para garantir timestamps diferentes
        import time
        time.sleep(0.01)
        manager.save_autosave(state2)

        # Deve retornar o mais recente
        latest = manager.get_latest_autosave()
        assert latest["tab"] == 2

    def test_get_latest_autosave_empty(self, tmp_path):
        """Testa get_latest_autosave quando não há autosaves."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        assert manager.get_latest_autosave() is None

    def test_cleanup_autosaves(self, tmp_path):
        """Testa limpeza de autosaves antigos."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Salva 10 autosaves
        for i in range(10):
            manager.save_autosave({"index": i})

        # Mantém apenas 5 mais recentes
        manager.cleanup_autosaves(keep_latest=5)

        # Conta arquivos restantes
        remaining = list(manager.autosaves_dir.glob(".autosave_*.json"))
        assert len(remaining) == 5

    def test_clear_autosaves(self, tmp_path):
        """Testa limpeza de todos os autosaves."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Salva alguns autosaves
        for i in range(3):
            manager.save_autosave({"index": i})

        # Limpa todos
        manager.clear_autosaves()

        # Verifica que não há mais autosaves
        remaining = list(manager.autosaves_dir.glob(".autosave_*.json"))
        assert len(remaining) == 0


class TestExportImport:
    """Testes para exportação/importação."""

    def test_export_program(self, tmp_path):
        """Testa exportação de programa."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Export Test",
            version="v1.0"
        )
        filepath = manager.save_program(program)

        # Exporta
        export_path = tmp_path / "exported" / "exported.json"
        exported = manager.export_program(filepath.name, str(export_path))

        assert exported.exists()
        assert exported == export_path

    def test_import_program(self, tmp_path):
        """Testa importação de programa."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Cria arquivo para importar
        import_path = tmp_path / "to_import.json"
        program = ProgramConfig(
            stencil_code="STENCIL-IMPORT",
            program_name="Imported",
            version="v1.0"
        )
        program.save_to_file(str(import_path))

        # Importa
        imported = manager.import_program(str(import_path))

        assert imported.exists()
        assert imported.name == "to_import.json"

    def test_import_program_with_new_name(self, tmp_path):
        """Testa importação com novo nome."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Cria arquivo para importar
        import_path = tmp_path / "to_import.json"
        program = ProgramConfig(
            stencil_code="STENCIL-IMPORT",
            program_name="Original",
            version="v1.0"
        )
        program.save_to_file(str(import_path))

        # Importa com novo nome
        imported = manager.import_program(str(import_path), new_name="renamed.json")

        assert imported.name == "renamed.json"


class TestGenerateFilename:
    """Testes para geração de nome de arquivo."""

    def test_generate_filename(self, tmp_path):
        """Testa geração de nome de arquivo."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test Program",
            version="v1.0"
        )

        filename = manager._generate_filename(program)

        assert "STENCIL-001" in filename
        assert "Test_Program" in filename
        assert "v1_0" in filename
        assert filename.endswith(".json")

    def test_generate_filename_sanitizes(self, tmp_path):
        """Testa se nome é sanitizado (remove espaços e caracteres especiais)."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        program = ProgramConfig(
            stencil_code="STENCIL / 001",
            program_name="Test / Program",
            version="v1.0"
        )

        filename = manager._generate_filename(program)

        assert "/" not in filename
        assert " " not in filename


class TestRoundtrip:
    """Testes de salvamento e carregamento (roundtrip)."""

    def test_roundtrip_preserves_data(self, tmp_path):
        """Testa se salvamento e carregamento preservam dados."""
        manager = EngineeringProgramManager(programs_dir=tmp_path)

        # Cria programa completo
        original = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Roundtrip Test",
            description="Test roundtrip",
            version="v2.0",
            recipe_name="Recipe-001",
            gerber_file="test.ger",
            aperture_count=150,
            detected_fiducials=2,
            fiducials=FiducialConfig(
                fiducial1={"x": 10.5, "y": 20.5},
                fiducial2={"x": 30.5, "y": 40.5}
            ),
            mosaic=MosaicConfig(
                corner1={"x": 0.0, "y": 0.0},
                corner2={"x": 100.0, "y": 100.0},
                grid_rows=5,
                grid_cols=5,
                total_fovs=25
            ),
            alignment=AlignmentConfig(
                translation_x=1.5,
                translation_y=2.5,
                rotation=0.8,
                scale=1.02,
                alignment_score=92.5
            ),
            inspection_groups=[
                InspectionGroupConfig(
                    name="Group 1",
                    aperture_count=75,
                    ok_threshold=95.0,
                    partial_threshold=75.0,
                    confirmed=True
                ),
                InspectionGroupConfig(
                    name="Group 2",
                    aperture_count=75,
                    ok_threshold=90.0,
                    partial_threshold=70.0,
                    confirmed=False
                )
            ],
            created_by="test_user",
            notes="Test notes"
        )

        # Salva
        filepath = manager.save_program(original)

        # Carrega
        loaded = manager.load_program(filepath.name)

        # Verifica todos os campos
        assert loaded.stencil_code == original.stencil_code
        assert loaded.program_name == original.program_name
        assert loaded.description == original.description
        assert loaded.version == original.version
        assert loaded.recipe_name == original.recipe_name
        assert loaded.gerber_file == original.gerber_file
        assert loaded.aperture_count == original.aperture_count

        # Fiduciais
        assert loaded.fiducials.fiducial1 == original.fiducials.fiducial1
        assert loaded.fiducials.fiducial2 == original.fiducials.fiducial2

        # Mosaico
        assert loaded.mosaic.grid_rows == original.mosaic.grid_rows
        assert loaded.mosaic.grid_cols == original.mosaic.grid_cols

        # Alinhamento
        assert loaded.alignment.translation_x == original.alignment.translation_x
        assert loaded.alignment.rotation == original.alignment.rotation

        # Grupos de inspeção
        assert len(loaded.inspection_groups) == len(original.inspection_groups)
        for loaded_group, original_group in zip(loaded.inspection_groups, original.inspection_groups):
            assert loaded_group.name == original_group.name
            assert loaded_group.aperture_count == original_group.aperture_count
