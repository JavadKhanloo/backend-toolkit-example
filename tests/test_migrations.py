from pathlib import Path


def test_alembic_project_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "alembic.ini").is_file()
    assert (root / "alembic" / "env.py").is_file()
    assert (root / "alembic" / "versions" / "0001_notes_and_attachments.py").is_file()
    ini = (root / "alembic.ini").read_text(encoding="utf-8")
    assert "models = app.models" in ini
