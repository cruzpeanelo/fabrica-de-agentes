"""
Seed do Banco de Dados - Fabrica de Agentes
============================================

Popula o banco com dados iniciais:
- Agentes base (19)
- Agentes especializados (53 tecnologias)
- Agentes corporativos (35+ hierarquia)
- Skills multimidia (texto, imagem, audio, video, office)
- Templates de projetos
- Usuario admin

Versao: 3.0 - Hierarquia Corporativa + Skills Multimidia
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal, init_db
from factory.database.models import Agent, Skill, Template, User
from factory.config import AGENTS, MCP_SERVERS, PROJECT_TYPES
from datetime import datetime

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False


def seed_agents(db):
    """Popula agentes base no banco"""
    print("\n[Seed] Criando agentes base...")

    for agent_id, config in AGENTS.items():
        existing = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if existing:
            print(f"  - Agente {agent_id} ja existe, atualizando...")
            existing.name = config.name
            existing.role = config.role
            existing.domain = config.domain.value
            existing.priority = config.priority
            existing.capabilities = config.capabilities
            existing.skills = config.skills
            existing.dependencies = config.dependencies
            existing.can_run_parallel = config.can_run_parallel
            existing.enabled = config.enabled
            continue

        agent = Agent(
            agent_id=config.id,
            name=config.name,
            role=config.role,
            domain=config.domain.value,
            priority=config.priority,
            capabilities=config.capabilities,
            skills=config.skills,
            dependencies=config.dependencies,
            can_run_parallel=config.can_run_parallel,
            enabled=config.enabled,
            status="STANDBY"
        )
        db.add(agent)
        print(f"  + Agente {agent_id}: {config.name} criado")

    db.commit()
    print(f"[Seed] {len(AGENTS)} agentes base processados")


def seed_specialized_agents(db):
    """Popula agentes especializados no banco"""
    print("\n[Seed] Criando agentes especializados...")

    try:
        from factory.agents.specialized_agents import get_all_agents
        specialized = get_all_agents()
    except ImportError:
        print("  ! Modulo specialized_agents nao encontrado, pulando...")
        return

    count = 0
    for spec in specialized:
        existing = db.query(Agent).filter(Agent.agent_id == spec.agent_id).first()
        if existing:
            # Atualiza
            existing.name = spec.name
            existing.description = spec.description
            existing.domain = spec.domain.value
            existing.capabilities = spec.technologies
            existing.skills = spec.skills
            continue

        agent = Agent(
            agent_id=spec.agent_id,
            name=spec.name,
            description=spec.description,
            domain=spec.domain.value,
            role=spec.experience_level,
            capabilities=spec.technologies,
            skills=spec.skills,
            config={
                "knowledge_areas": spec.knowledge_areas,
                "certifications": spec.certifications
            },
            status="STANDBY",
            enabled=True
        )
        db.add(agent)
        count += 1
        print(f"  + {spec.agent_id}: {spec.name}")

    db.commit()
    print(f"[Seed] {count} agentes especializados criados")


def seed_corporate_agents(db):
    """Popula agentes com hierarquia corporativa"""
    print("\n[Seed] Criando agentes corporativos...")

    try:
        from factory.agents.corporate_hierarchy import ALL_CORPORATE_AGENTS
    except ImportError:
        print("  ! Modulo corporate_hierarchy nao encontrado, pulando...")
        return

    count = 0
    for agent_id, corp_agent in ALL_CORPORATE_AGENTS.items():
        # Extrai dept_id do Enum Department
        dept_id = corp_agent.department.dept_id
        dept_display = corp_agent.department.display_name
        dept_area = corp_agent.department.area

        existing = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if existing:
            # Atualiza
            existing.name = corp_agent.name
            existing.role = corp_agent.title
            existing.domain = dept_id
            existing.description = f"{corp_agent.level.title} - {dept_display}"
            existing.skills = corp_agent.skills
            existing.config = {
                "level": corp_agent.level.level_num,
                "level_title": corp_agent.level.title,
                "department": dept_display,
                "area": dept_area,
                "reports_to": corp_agent.reports_to,
                "direct_reports": corp_agent.direct_reports,
                "responsibilities": corp_agent.responsibilities,
                "budget_authority": corp_agent.budget_authority,
                "can_hire": corp_agent.can_hire,
                "can_fire": corp_agent.can_fire,
                "can_approve_projects": corp_agent.can_approve_projects
            }
            continue

        agent = Agent(
            agent_id=agent_id,
            name=corp_agent.name,
            role=corp_agent.title,
            description=f"{corp_agent.level.title} - {dept_display}",
            domain=dept_id,
            priority=11 - corp_agent.level.level_num,  # C-Level tem maior prioridade
            capabilities=corp_agent.responsibilities,
            skills=corp_agent.skills,
            dependencies=[corp_agent.reports_to] if corp_agent.reports_to else [],
            config={
                "level": corp_agent.level.level_num,
                "level_title": corp_agent.level.title,
                "department": dept_display,
                "area": dept_area,
                "reports_to": corp_agent.reports_to,
                "direct_reports": corp_agent.direct_reports,
                "responsibilities": corp_agent.responsibilities,
                "budget_authority": corp_agent.budget_authority,
                "can_hire": corp_agent.can_hire,
                "can_fire": corp_agent.can_fire,
                "can_approve_projects": corp_agent.can_approve_projects
            },
            status="STANDBY",
            enabled=True
        )
        db.add(agent)
        count += 1
        print(f"  + {agent_id}: {corp_agent.name} ({corp_agent.level.title})")

    db.commit()
    print(f"[Seed] {count} agentes corporativos criados")


def seed_multimedia_skills(db):
    """Popula skills de analise multimidia"""
    print("\n[Seed] Criando skills multimidia...")

    multimedia_skills = [
        # Texto
        {
            "skill_id": "text_analysis",
            "name": "Text Analysis",
            "description": "Analise de arquivos de texto (TXT, MD)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "pdf_analysis",
            "name": "PDF Analysis",
            "description": "Analise de documentos PDF",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "document_analysis",
            "name": "Document Analysis",
            "description": "Analise de documentos (DOCX, HTML, XML)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "code_analysis",
            "name": "Code Analysis",
            "description": "Analise de codigo fonte (Python, JS, Java, etc)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "data_analysis",
            "name": "Data File Analysis",
            "description": "Analise de arquivos de dados (JSON, CSV, XLSX)",
            "skill_type": "core",
            "category": "multimedia"
        },

        # Imagem
        {
            "skill_id": "image_analysis",
            "name": "Image Analysis",
            "description": "Analise generica de imagens",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "png_analysis",
            "name": "PNG Analysis",
            "description": "Analise de imagens PNG",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "jpeg_analysis",
            "name": "JPEG Analysis",
            "description": "Analise de imagens JPEG com EXIF",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "gif_analysis",
            "name": "GIF Analysis",
            "description": "Analise de GIFs incluindo animacoes",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "svg_analysis",
            "name": "SVG Analysis",
            "description": "Analise de imagens vetoriais SVG",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "webp_analysis",
            "name": "WebP Analysis",
            "description": "Analise de imagens WebP",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "tiff_analysis",
            "name": "TIFF Analysis",
            "description": "Analise de imagens TIFF",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "bmp_analysis",
            "name": "BMP Analysis",
            "description": "Analise de imagens Bitmap",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "ico_analysis",
            "name": "ICO Analysis",
            "description": "Analise de arquivos de icone",
            "skill_type": "core",
            "category": "multimedia"
        },

        # Office
        {
            "skill_id": "office_analysis",
            "name": "Office Analysis",
            "description": "Analise generica de documentos Office",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "docx_analysis",
            "name": "DOCX Analysis",
            "description": "Analise de documentos Word (DOCX)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "xlsx_analysis",
            "name": "XLSX Analysis",
            "description": "Analise de planilhas Excel (XLSX)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "pptx_analysis",
            "name": "PPTX Analysis",
            "description": "Analise de apresentacoes PowerPoint (PPTX)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "odt_analysis",
            "name": "ODT Analysis",
            "description": "Analise de documentos OpenDocument Text",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "ods_analysis",
            "name": "ODS Analysis",
            "description": "Analise de planilhas OpenDocument",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "rtf_analysis",
            "name": "RTF Analysis",
            "description": "Analise de documentos Rich Text Format",
            "skill_type": "core",
            "category": "multimedia"
        },

        # Audio
        {
            "skill_id": "audio_analysis",
            "name": "Audio Analysis",
            "description": "Analise de arquivos de audio (MP3, WAV, FLAC)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "speech_analysis",
            "name": "Speech Analysis",
            "description": "Analise de fala em arquivos de audio",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "music_analysis",
            "name": "Music Analysis",
            "description": "Analise musical de arquivos de audio",
            "skill_type": "core",
            "category": "multimedia"
        },

        # Video
        {
            "skill_id": "video_analysis",
            "name": "Video Analysis",
            "description": "Analise de arquivos de video (MP4, AVI, MKV)",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "frame_analysis",
            "name": "Frame Analysis",
            "description": "Analise de frames de video",
            "skill_type": "core",
            "category": "multimedia"
        },
        {
            "skill_id": "scene_analysis",
            "name": "Scene Analysis",
            "description": "Analise de cenas em videos",
            "skill_type": "core",
            "category": "multimedia"
        },
    ]

    count = 0
    for skill_data in multimedia_skills:
        existing = db.query(Skill).filter(Skill.skill_id == skill_data["skill_id"]).first()
        if existing:
            # Atualiza
            existing.name = skill_data["name"]
            existing.description = skill_data["description"]
            existing.category = skill_data["category"]
            continue

        skill = Skill(**skill_data)
        db.add(skill)
        count += 1
        print(f"  + {skill_data['skill_id']}")

    db.commit()
    print(f"[Seed] {count} skills multimidia criadas")


def seed_core_skills(db):
    """Popula skills core no banco"""
    print("\n[Seed] Criando skills core...")

    core_skills = [
        {
            "skill_id": "file-read",
            "name": "File Read",
            "description": "Leitura de arquivos do sistema",
            "skill_type": "core",
            "category": "file"
        },
        {
            "skill_id": "file-write",
            "name": "File Write",
            "description": "Escrita de arquivos no sistema",
            "skill_type": "core",
            "category": "file"
        },
        {
            "skill_id": "file-search",
            "name": "File Search",
            "description": "Busca de arquivos com glob/grep",
            "skill_type": "core",
            "category": "file"
        },
        {
            "skill_id": "web-fetch",
            "name": "Web Fetch",
            "description": "Requisicoes HTTP para APIs e paginas",
            "skill_type": "core",
            "category": "web"
        },
        {
            "skill_id": "web-search",
            "name": "Web Search",
            "description": "Busca na web",
            "skill_type": "core",
            "category": "web"
        },
        {
            "skill_id": "bash-execute",
            "name": "Bash Execute",
            "description": "Execucao de comandos shell",
            "skill_type": "core",
            "category": "development"
        },
        {
            "skill_id": "sql-query",
            "name": "SQL Query",
            "description": "Execucao de queries SQL",
            "skill_type": "core",
            "category": "data"
        },
        {
            "skill_id": "data-transform",
            "name": "Data Transform",
            "description": "Transformacao de dados com pandas",
            "skill_type": "core",
            "category": "data"
        }
    ]

    count = 0
    for skill_data in core_skills:
        existing = db.query(Skill).filter(Skill.skill_id == skill_data["skill_id"]).first()
        if existing:
            continue
        skill = Skill(**skill_data)
        db.add(skill)
        count += 1
        print(f"  + {skill_data['skill_id']}")

    db.commit()
    print(f"[Seed] {count} skills core criadas")


def seed_mcp_skills(db):
    """Popula skills MCP no banco"""
    print("\n[Seed] Criando skills MCP...")

    count = 0
    for server_id, server_config in MCP_SERVERS.items():
        skill_id = f"mcp-{server_id}"
        existing = db.query(Skill).filter(Skill.skill_id == skill_id).first()
        if existing:
            continue

        skill = Skill(
            skill_id=skill_id,
            name=server_config["name"],
            description=server_config["description"],
            skill_type="mcp",
            category=server_config["category"],
            server_command=server_config["command"],
            server_args=server_config["args"]
        )
        db.add(skill)
        count += 1
        print(f"  + {skill_id}")

    db.commit()
    print(f"[Seed] {count} skills MCP criadas")


def seed_templates(db):
    """Popula templates no banco"""
    print("\n[Seed] Criando templates...")

    count = 0
    for type_id, type_config in PROJECT_TYPES.items():
        template_id = f"template-{type_id}"
        existing = db.query(Template).filter(Template.template_id == template_id).first()
        if existing:
            continue

        template = Template(
            template_id=template_id,
            name=type_config["name"],
            description=type_config["description"],
            project_type=type_id,
            default_config=type_config.get("default_stack", {}),
            recommended_agents=type_config.get("default_agents", [])
        )
        db.add(template)
        count += 1
        print(f"  + {template_id}")

    db.commit()
    print(f"[Seed] {count} templates criados")


def seed_admin_user(db):
    """Cria usuario admin padrao"""
    print("\n[Seed] Criando usuario admin...")

    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("  - Usuario admin ja existe")
        return

    if HAS_PASSLIB:
        password_hash = pwd_context.hash("admin123")
    else:
        # Fallback simples se passlib nao estiver instalado
        import hashlib
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()

    admin = User(
        username="admin",
        password_hash=password_hash,
        email="admin@fabrica.local",
        role="ADMIN",
        active=True
    )
    db.add(admin)
    db.commit()
    print("  + Usuario admin criado (senha: admin123)")


def run_seed(include_specialized: bool = True, include_corporate: bool = True):
    """Executa todo o seed"""
    print("=" * 70)
    print("SEED - Fabrica de Agentes v3.0")
    print("=" * 70)

    # Inicializa banco
    init_db()

    # Cria sessao
    db = SessionLocal()

    try:
        # Agentes base
        seed_agents(db)

        # Agentes especializados (tecnologias)
        if include_specialized:
            seed_specialized_agents(db)

        # Agentes corporativos (hierarquia)
        if include_corporate:
            seed_corporate_agents(db)

        # Skills
        seed_core_skills(db)
        seed_mcp_skills(db)
        seed_multimedia_skills(db)

        # Templates e Usuario
        seed_templates(db)
        seed_admin_user(db)

        # Estatisticas finais
        total_agents = db.query(Agent).count()
        total_skills = db.query(Skill).count()
        total_templates = db.query(Template).count()

        print("\n" + "=" * 70)
        print("SEED CONCLUIDO COM SUCESSO!")
        print("=" * 70)
        print(f"\nEstatisticas:")
        print(f"  - Agentes: {total_agents}")
        print(f"  - Skills: {total_skills}")
        print(f"  - Templates: {total_templates}")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERRO] {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed do banco de dados")
    parser.add_argument("--no-specialized", action="store_true",
                       help="Nao incluir agentes especializados")
    parser.add_argument("--no-corporate", action="store_true",
                       help="Nao incluir agentes corporativos")

    args = parser.parse_args()

    run_seed(
        include_specialized=not args.no_specialized,
        include_corporate=not args.no_corporate
    )
