#!/usr/bin/env python3
"""
Conductor Planning Agent

This agent orchestrates the creation of new tracks for the Conductor system.
It generates specifications (spec.md) and implementation plans (plan.md).

Usage:
    python planning_agent.py --description "Add OAuth2 authentication"

Or programmatically:
    from planning_agent import PlanningAgent
    agent = PlanningAgent()
    result = agent.create_track(description="...", responses={...})
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class PlanningAgent:
    """Orchestrates track creation with spec and plan generation."""

    def __init__(self, project_root: str = None, conductor_dir: str = None):
        """Initialize the planning agent.

        Args:
            project_root: Path to project root. If None, auto-detect.
            conductor_dir: Path to conductor directory. Defaults to project_root/conductor.
        """
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root)

        if conductor_dir is None:
            self.conductor_dir = self.project_root / "conductor"
        else:
            self.conductor_dir = Path(conductor_dir)

        self.claude_conductor_dir = self.project_root / "claude-conductor"
        self.templates_dir = self.claude_conductor_dir / "templates"
        self.interview_templates_dir = self.claude_conductor_dir / "interview_templates"

    def generate_track_id(self, description: str, track_type: str = "feature") -> str:
        """Generate a unique track ID from description.

        Args:
            description: Track description
            track_type: Type of track (feature, bugfix, refactor, docs)

        Returns:
            Track ID in format: <type>_<sanitized_name>_<YYYYMMDD>
        """
        # Extract key words from description
        words = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())

        # Take first 2-3 meaningful words
        if len(words) >= 2:
            name_part = "_".join(words[:3])
        else:
            name_part = "track"

        # Sanitize
        name_part = re.sub(r'[^a-z0-9_]', '', name_part)

        # Add date
        date_part = datetime.now().strftime("%Y%m%d")

        return f"{track_type}_{name_part}_{date_part}"

    def load_context_docs(self) -> Dict[str, str]:
        """Load context documentation (product, tech-stack, workflow).

        Returns:
            Dictionary with document contents.
        """
        docs = {}

        # Load from conductor/ (generated docs)
        for doc_name in ['product.md', 'product-guidelines.md', 'tech-stack.md', 'workflow.md']:
            doc_path = self.conductor_dir / doc_name
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    docs[doc_name] = f.read()

        return docs

    def load_track_spec_template(self) -> str:
        """Load track spec template."""
        template_path = self.templates_dir / "track_spec_template.md"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_track_plan_template(self) -> str:
        """Load track plan template."""
        template_path = self.templates_dir / "track_plan_template.md"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def analyze_codebase(self, focus_area: str = None) -> Dict[str, Any]:
        """Analyze codebase to understand architecture.

        Args:
            focus_area: Optional area to focus analysis (e.g., 'auth', 'database')

        Returns:
            Dictionary with architecture insights.
        """
        # Basic codebase structure
        analysis = {
            "main_packages": [],
            "test_structure": {},
            "key_files": [],
            "imports_summary": {},
            "focus_area": focus_area
        }

        # Analyze main packages
        for pkg_dir in ['aoi_lib', 'consumo_lib', 'claude-conductor']:
            pkg_path = self.project_root / pkg_dir
            if pkg_path.exists() and pkg_path.is_dir():
                analysis["main_packages"].append(pkg_dir)

                # Count Python files
                py_files = list(pkg_path.rglob("*.py"))
                analysis[f"{pkg_dir}_files"] = len(py_files)

        # Test structure
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for test_type in ['unit', 'integration']:
                test_path = tests_dir / test_type
                if test_path.exists():
                    test_files = list(test_path.rglob("test_*.py"))
                    analysis["test_structure"][test_type] = len(test_files)

        return analysis

    def generate_spec(
        self,
        track_id: str,
        track_name: str,
        track_type: str,
        responses: Dict[str, Any],
        context_docs: Dict[str, str]
    ) -> str:
        """Generate specification document (spec.md).

        Args:
            track_id: Unique track identifier
            track_name: Human-readable track name
            track_type: Type of track (feature, bugfix, refactor, docs)
            responses: Interview responses
            context_docs: Context documentation

        Returns:
            Generated spec markdown content.
        """
        template = self.load_track_spec_template()

        # Extract product context
        product_context = context_docs.get('product.md', 'N/A')

        # Build objective
        if track_type == 'feature':
            objective = f"Implementar nova funcionalidade: {responses.get('description', track_name)}"
        elif track_type == 'bugfix':
            objective = f"Corrigir problema: {responses.get('description', track_name)}"
        elif track_type == 'refactor':
            objective = f"Refatorar código: {responses.get('description', track_name)}"
        else:
            objective = f"{track_type.capitalize()}: {responses.get('description', track_name)}"

        # Build scope
        scope = responses.get('scope_included', 'To be defined').strip()

        # Build acceptance criteria
        acceptance = responses.get('acceptance_criteria', 'To be defined').strip()
        if acceptance and not acceptance.startswith('-'):
            # Convert to list if not already
            lines = acceptance.split('\n')
            acceptance = '\n'.join([f"- {line.strip()}" if not line.strip().startswith('-') else line.strip()
                                   for line in lines if line.strip()])

        # Build technical considerations
        tech_considerations = responses.get('technical_considerations', 'Nenhuma restrição específica').strip()

        # Build risks
        risks = responses.get('risks', 'Nenhum risco identificado').strip()
        if risks:
            lines = risks.split('\n')
            risks = '\n'.join([f"- {line.strip()}" if not line.strip().startswith('-') else line.strip()
                             for line in lines if line.strip()])
        else:
            risks = "- Nenhum risco identificado"

        # Build dependencies
        dependencies = responses.get('dependencies', 'Nenhuma').strip()

        # Build out of scope
        out_of_scope = responses.get('scope_excluded', 'Nenhum item explicitamente excluído').strip()
        if out_of_scope:
            lines = out_of_scope.split('\n')
            out_of_scope = '\n'.join([f"- {line.strip()}" if not line.strip().startswith('-') else line.strip()
                                      for line in lines if line.strip()])

        # Fill template
        content = template.format(
            track_name=track_name,
            track_id=track_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            objective=objective,
            context=f"**Priority:** {responses.get('priority', 'Medium').capitalize()}\n\n{product_context[:500]}...",
            scope=scope,
            acceptance_criteria=acceptance,
            technical_considerations=tech_considerations,
            risks_mitigations=risks,
            dependencies=dependencies,
            out_of_scope=out_of_scope
        )

        return content

    def generate_plan(
        self,
        track_id: str,
        track_name: str,
        track_type: str,
        responses: Dict[str, Any],
        codebase_analysis: Dict[str, Any],
        context_docs: Dict[str, str]
    ) -> str:
        """Generate implementation plan (plan.md).

        Args:
            track_id: Unique track identifier
            track_name: Human-readable track name
            track_type: Type of track
            responses: Interview responses
            codebase_analysis: Codebase structure analysis
            context_docs: Context documentation

        Returns:
            Generated plan markdown content.
        """
        template = self.load_track_plan_template()

        # Determine number of phases based on complexity
        complexity = responses.get('estimated_phases', 'Medium (3-4 phases)')

        if 'Simple' in complexity:
            num_phases = 2
        elif 'Complex' in complexity:
            num_phases = 5
        else:
            num_phases = 3

        # Generate phases
        phases = self._generate_phases(
            track_type=track_type,
            responses=responses,
            codebase_analysis=codebase_analysis,
            num_phases=num_phases
        )

        # Build overview
        description = responses.get('description', track_name)
        user_value = responses.get('user_value', 'Melhoria geral do sistema')

        overview = f"""**Description:** {description}

**User Value:** {user_value}

**Priority:** {responses.get('priority', 'Medium')}

**Type:** {track_type.capitalize()}

**Estimated Phases:** {num_phases}"""

        # Get coverage target from workflow
        workflow = context_docs.get('workflow.md', '')
        coverage_target = "80% or higher"
        if '95%' in workflow:
            coverage_target = "95% or higher"
        elif '70%' in workflow:
            coverage_target = "70% or higher"

        # Estimate duration
        duration_map = {2: "1-2 days", 3: "3-5 days", 4: "1 week", 5: "2+ weeks"}
        estimated_duration = duration_map.get(num_phases, "TBD")

        # Fill template
        content = template.format(
            track_name=track_name,
            track_id=track_id,
            track_type=track_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            estimated_duration=estimated_duration,
            coverage_target=coverage_target,
            overview=overview,
            phases=phases
        )

        return content

    def _generate_phases(
        self,
        track_type: str,
        responses: Dict[str, Any],
        codebase_analysis: Dict[str, Any],
        num_phases: int
    ) -> str:
        """Generate phase breakdown for plan.

        Args:
            track_type: Type of track
            responses: Interview responses
            codebase_analysis: Codebase analysis
            num_phases: Number of phases to generate

        Returns:
            Formatted phases markdown.
        """
        phases = []

        if track_type == 'feature':
            phases.extend(self._generate_feature_phases(responses, codebase_analysis, num_phases))
        elif track_type == 'bugfix':
            phases.extend(self._generate_bugfix_phases(responses, num_phases))
        elif track_type == 'refactor':
            phases.extend(self._generate_refactor_phases(responses, num_phases))
        else:  # docs
            phases.extend(self._generate_docs_phases(responses, num_phases))

        # Format as markdown
        formatted = []
        for i, phase in enumerate(phases, 1):
            formatted.append(f"## Fase {i}: {phase['name']}\n")
            for task in phase['tasks']:
                formatted.append(f"- [ ] {task}\n")
            formatted.append("\n")

        return ''.join(formatted)

    def _generate_feature_phases(
        self,
        responses: Dict[str, Any],
        codebase_analysis: Dict[str, Any],
        num_phases: int
    ) -> List[Dict]:
        """Generate phases for feature track."""
        phases = []

        # Phase 1: Setup & Foundation
        phases.append({
            'name': 'Configuração e Fundação',
            'tasks': [
                'Tarefa: Criar estrutura básica de módulos/pacotes',
                'Tarefa: Instalar dependências necessárias (se aplicável)',
                'Tarefa: Escrever testes de aceitação para critérios principais',
                'Tarefa: Conductor - User Manual Verification \'Fase 1\''
            ]
        })

        if num_phases >= 3:
            # Phase 2: Core Implementation
            phases.append({
                'name': 'Implementação Core',
                'tasks': [
                    'Tarefa: Implementar funcionalidade principal',
                    'Tarefa: Escrever testes unitários para módulos criados',
                    'Tarefa: Integrar com código existente',
                    'Tarefa: Conductor - User Manual Verification \'Fase 2\''
                ]
            })

        # Phase 3: Integration & UI (or Final for 2 phases)
        if num_phases == 2:
            phase_name = 'Integração e Testes'
        else:
            phase_name = 'Integração e Interface'

        phases.append({
            'name': phase_name,
            'tasks': [
                'Tarefa: Conectar funcionalidade com interface do usuário (se aplicável)',
                'Tarefa: Implementar tratamento de erros',
                'Tarefa: Escrever testes de integração',
                'Tarefa: Conductor - User Manual Verification \'Fase 3\''
            ]
        })

        if num_phases >= 4:
            # Phase 4: Testing & Validation
            phases.append({
                'name': 'Testes e Validação',
                'tasks': [
                    'Tarefa: Executar suite completa de testes',
                    'Tarefa: Verificar cobertura de código',
                    'Tarefa: Testar manualmente fluxo completo',
                    'Tarefa: Conductor - User Manual Verification \'Fase 4\''
                ]
            })

        if num_phases >= 5:
            # Phase 5: Polish & Documentation
            phases.append({
                'name': 'Refinamento e Documentação',
                'tasks': [
                    'Tarefa: Otimizar performance',
                    'Tarefa: Atualizar documentação',
                    'Tarefa: Code review e refatoração',
                    'Tarefa: Conductor - User Manual Verification \'Fase 5\''
                ]
            })

        return phases

    def _generate_bugfix_phases(
        self,
        responses: Dict[str, Any],
        num_phases: int
    ) -> List[Dict]:
        """Generate phases for bugfix track."""
        phases = []

        # Phase 1: Investigation & Reproduction
        phases.append({
            'name': 'Investigação e Reprodução',
            'tasks': [
                'Tarefa: Reproduzir o bug em ambiente controlado',
                'Tarefa: Escrever teste que falha devido ao bug',
                'Tarefa: Identificar a causa raiz',
                'Tarefa: Conductor - User Manual Verification \'Fase 1\''
            ]
        })

        # Phase 2: Fix & Verification
        if num_phases == 2:
            phase_name = 'Correção e Validação'
        else:
            phase_name = 'Correção'

        phases.append({
            'name': phase_name,
            'tasks': [
                'Tarefa: Implementar correção do bug',
                'Tarefa: Verificar que teste de falha agora passa',
                'Tarefa: Escrever testes adicionais para prevenir regressão',
                'Tarefa: Conductor - User Manual Verification \'Fase 2\''
            ]
        })

        if num_phases >= 3:
            # Phase 3: Validation & Regression Testing
            phases.append({
                'name': 'Validação e Testes de Regressão',
                'tasks': [
                    'Tarefa: Executar suite completa de testes',
                    'Tarefa: Verificar que correção não quebrou outras funcionalidades',
                    'Tarefa: Testar manualmente cenários relacionados',
                    'Tarefa: Conductor - User Manual Verification \'Fase 3\''
                ]
            })

        return phases

    def _generate_refactor_phases(
        self,
        responses: Dict[str, Any],
        num_phases: int
    ) -> List[Dict]:
        """Generate phases for refactor track."""
        phases = []

        # Phase 1: Analysis & Planning
        phases.append({
            'name': 'Análise e Planejamento',
            'tasks': [
                'Tarefa: Analisar código a ser refatorado',
                'Tarefa: Escrever testes para comportamento existente',
                'Tarefa: Documentar estrutura atual',
                'Tarefa: Conductor - User Manual Verification \'Fase 1\''
            ]
        })

        # Phase 2: Refactoring
        phases.append({
            'name': 'Refatoração',
            'tasks': [
                'Tarefa: Aplicar refatorações planejadas',
                'Tarefa: Garantir que todos os testes continuam passando',
                'Tarefa: Atualizar documentação afetada',
                'Tarefa: Conductor - User Manual Verification \'Fase 2\''
            ]
        })

        if num_phases >= 3:
            # Phase 3: Validation
            phases.append({
                'name': 'Validação',
                'tasks': [
                    'Tarefa: Executar suite completa de testes',
                    'Tarefa: Verificar cobertura de código',
                    'Tarefa: Comparar performance antes/depois',
                    'Tarefa: Conductor - User Manual Verification \'Fase 3\''
                ]
            })

        return phases

    def _generate_docs_phases(
        self,
        responses: Dict[str, Any],
        num_phases: int
    ) -> List[Dict]:
        """Generate phases for documentation track."""
        phases = []

        # Phase 1: Planning & Outline
        phases.append({
            'name': 'Planejamento e Estrutura',
            'tasks': [
                'Tarefa: Definir estrutura da documentação',
                'Tarefa: Criar esboço dos tópicos principais',
                'Tarefa: Identificar diagramas e exemplos necessários',
                'Tarefa: Conductor - User Manual Verification \'Fase 1\''
            ]
        })

        # Phase 2: Content Creation
        phases.append({
            'name': 'Criação de Conteúdo',
            'tasks': [
                'Tarefa: Escrever documentação principal',
                'Tarefa: Adicionar exemplos de código',
                'Tarefa: Criar diagramas (se necessário)',
                'Tarefa: Conductor - User Manual Verification \'Fase 2\''
            ]
        })

        if num_phases >= 3:
            # Phase 3: Review & Publishing
            phases.append({
                'name': 'Revisão e Publicação',
                'tasks': [
                    'Tarefa: Revisar documentação por completo',
                    'Tarefa: Verificar clareza e completude',
                    'Tarefa: Publicar/atualizar arquivos de documentação',
                    'Tarefa: Conductor - User Manual Verification \'Fase 3\''
                ]
            })

        return phases

    def create_metadata(
        self,
        track_id: str,
        track_name: str,
        track_type: str,
        responses: Dict[str, Any],
        status: str = "planning"
    ) -> Dict[str, Any]:
        """Create metadata for track.

        Args:
            track_id: Unique track identifier
            track_name: Human-readable name
            track_type: Type of track
            responses: Interview responses
            status: Initial status (default: planning)

        Returns:
            Metadata dictionary.
        """
        return {
            "track_id": track_id,
            "name": track_name,
            "type": track_type,
            "priority": responses.get('priority', 'Medium'),
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "description": responses.get('description', ''),
            "estimated_duration": responses.get('estimated_phases', 'Medium (3-4 phases)')
        }

    def create_track_directory(
        self,
        track_id: str,
        spec_content: str,
        plan_content: str,
        metadata: Dict[str, Any]
    ) -> Path:
        """Create track directory with all files.

        Args:
            track_id: Track identifier
            spec_content: Generated spec content
            plan_content: Generated plan content
            metadata: Track metadata

        Returns:
            Path to created track directory.
        """
        # Create track directory in conductor/tracks/
        track_dir = self.conductor_dir / "tracks" / track_id
        track_dir.mkdir(parents=True, exist_ok=True)

        # Write spec.md
        spec_path = track_dir / "spec.md"
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        # Write plan.md
        plan_path = track_dir / "plan.md"
        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(plan_content)

        # Write metadata.json
        metadata_path = track_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return track_dir

    def update_tracks_registry(
        self,
        track_id: str,
        track_name: str,
        track_type: str
    ) -> None:
        """Update conductor/tracks.md registry.

        Args:
            track_id: Track identifier
            track_name: Track name
            track_type: Type of track
        """
        tracks_file = self.conductor_dir / "tracks.md"

        # Read existing or create new
        if tracks_file.exists():
            with open(tracks_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = """# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---
"""

        # Append new track
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_entry = f"""
## [ ] {track_name} ({track_type.capitalize()})
- **Track ID:** {track_id}
- **Status:** Planning
- **Created:** {timestamp}
- **Plan:** ./tracks/{track_id}/plan.md
- **Spec:** ./tracks/{track_id}/spec.md

---
*Last updated: {timestamp}*
"""

        # Write updated content
        with open(tracks_file, 'w', encoding='utf-8') as f:
            f.write(content + new_entry)

    def create_track(
        self,
        description: str,
        responses: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new track with spec and plan.

        Args:
            description: Brief description of the track
            responses: Pre-collected interview responses (for automated mode)

        Returns:
            Dictionary with creation result and track info.
        """
        print(f"\n{'='*60}")
        print(f"CONDUCTOR NEW TRACK - {description[:50]}...")
        print(f"{'='*60}\n")

        # If no responses provided, return interview template
        if responses is None:
            interview_template = self.load_interview_template()
            return {
                "status": "ready_for_interview",
                "interview": interview_template,
                "description": description
            }

        # Extract track info from responses
        track_type = responses.get('track_type', 'feature').lower()
        priority = responses.get('priority', 'Medium')

        # Generate track ID
        track_id = self.generate_track_id(description, track_type)

        # Generate track name from description
        track_name = self._generate_track_name(description)

        print(f"[INFO] Track ID: {track_id}")
        print(f"[INFO] Track Type: {track_type}")
        print(f"[INFO] Priority: {priority}")
        print(f"[INFO] Name: {track_name}")

        # Load context docs
        print("[INFO] Loading context documentation...")
        context_docs = self.load_context_docs()

        # Analyze codebase
        print("[INFO] Analyzing codebase structure...")
        codebase_analysis = self.analyze_codebase()

        # Generate spec
        print("[INFO] Generating specification (spec.md)...")
        spec_content = self.generate_spec(
            track_id=track_id,
            track_name=track_name,
            track_type=track_type,
            responses=responses,
            context_docs=context_docs
        )

        # Generate plan
        print("[INFO] Generating implementation plan (plan.md)...")
        plan_content = self.generate_plan(
            track_id=track_id,
            track_name=track_name,
            track_type=track_type,
            responses=responses,
            codebase_analysis=codebase_analysis,
            context_docs=context_docs
        )

        # Create metadata
        metadata = self.create_metadata(
            track_id=track_id,
            track_name=track_name,
            track_type=track_type,
            responses=responses
        )

        # Create track directory and files
        print(f"[INFO] Creating track directory: conductor/tracks/{track_id}/")
        track_dir = self.create_track_directory(
            track_id=track_id,
            spec_content=spec_content,
            plan_content=plan_content,
            metadata=metadata
        )

        # Update tracks registry
        print("[INFO] Updating tracks registry (tracks.md)...")
        self.update_tracks_registry(track_id, track_name, track_type)

        print(f"\n[SUCCESS] Track created successfully!")
        print(f"\nLocation: {track_dir}")
        print(f"Files created:")
        print(f"  - spec.md")
        print(f"  - plan.md")
        print(f"  - metadata.json")

        return {
            "status": "created",
            "track_id": track_id,
            "track_name": track_name,
            "track_dir": str(track_dir),
            "spec_file": str(track_dir / "spec.md"),
            "plan_file": str(track_dir / "plan.md"),
            "metadata_file": str(track_dir / "metadata.json")
        }

    def load_interview_template(self) -> Dict[str, Any]:
        """Load new track interview template."""
        template_path = self.interview_templates_dir / "new_track.json"
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generate_track_name(self, description: str) -> str:
        """Generate human-readable track name from description."""
        # Capitalize first letter
        name = description.strip().capitalize()
        # Remove trailing punctuation
        name = re.sub(r'[.!?,;:]+$', '', name)
        # Limit length
        if len(name) > 80:
            name = name[:77] + "..."
        return name


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a new Conductor track")
    parser.add_argument("description", help="Brief description of the track")
    parser.add_argument("--type", choices=["feature", "bugfix", "refactor", "docs"],
                       default="feature", help="Type of track")
    parser.add_argument("--priority", choices=["Critical", "High", "Medium", "Low"],
                       default="Medium", help="Priority level")

    args = parser.parse_args()

    # Create minimal responses for CLI usage
    responses = {
        "track_type": args.type,
        "priority": args.priority,
        "description": args.description,
        "user_value": "To be defined",
        "acceptance_criteria": "To be defined",
        "technical_considerations": "None specified",
        "scope_included": "To be defined",
        "scope_excluded": "None specified",
        "dependencies": "None",
        "risks": "None identified",
        "estimated_phases": "Medium (3-4 phases)",
        "verification_approach": "Yes (Recommended)"
    }

    agent = PlanningAgent()
    result = agent.create_track(args.description, responses=responses)

    if result.get("status") == "created":
        print(f"\nNext steps:")
        print(f"1. Review generated spec: {result['spec_file']}")
        print(f"2. Review generated plan: {result['plan_file']}")
        print(f"3. Start implementation with: /conductor:implement {result['track_id']}")
