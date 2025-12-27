up:
	docker compose up -d

upb:
	docker compose up -d --build

lint-fix: # Lint with fixes
	@uv run ruff check . && \
	uv run ruff format . && \
	uv run isort .
