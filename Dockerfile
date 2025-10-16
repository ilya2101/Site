FROM python:3.13-alpine

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN apk add --no-cache uv
RUN uv sync --frozen --dev

COPY . .

CMD ["uv", "run", "python", "app.py"]
