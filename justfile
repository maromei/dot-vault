check:
    uv run ruff check
    uv run basedpyright
test:
    uv run pytest
env:
    scripts/activate_venv.sh
