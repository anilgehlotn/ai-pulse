import logging
import os

logger = logging.getLogger(__name__)

# Load .env if present (very small loader, no extra dependency)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    for line in open(_env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DEV_ONLY_SECRET_KEY = "dev-only-secret-do-not-use-in-production"
SAFE_FALLBACK_ENVS = ("dev", "test")


def resolve_secret_key(secret_key: str, app_env: str) -> str:
    """Use the configured key; only dev and test may run without one."""
    if secret_key:
        return secret_key
    if app_env not in SAFE_FALLBACK_ENVS:
        raise RuntimeError(f"SECRET_KEY must be set when APP_ENV is '{app_env}'")
    logger.warning("SECRET_KEY is not set; using a dev-only key (APP_ENV=%s)", app_env)
    return DEV_ONLY_SECRET_KEY


def check_llm_config(ai_mode: str, api_url: str, model: str) -> None:
    """Refuse to start with an LLM setup that would fail on the first real submission."""
    if ai_mode not in ("mock", "live"):
        raise RuntimeError(f"AI_MODE must be 'mock' or 'live', not '{ai_mode}'")
    if ai_mode == "live":
        missing = [name for name, value in (("LLM_API_URL", api_url), ("LLM_MODEL", model)) if not value]
        if missing:
            raise RuntimeError(f"AI_MODE is 'live' but {', '.join(missing)} is not set")


def parse_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


APP_ENV = os.getenv("APP_ENV", "dev")
SECRET_KEY = resolve_secret_key(os.getenv("SECRET_KEY", ""), APP_ENV)
CORS_ORIGINS = parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aipulse.db")
AI_MODE = os.getenv("AI_MODE", "mock")  # "mock" or "live"
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
# Ask the endpoint for guaranteed-JSON output. Only enable if the provider supports response_format.
LLM_JSON_MODE = os.getenv("LLM_JSON_MODE", "false").lower() == "true"
check_llm_config(AI_MODE, LLM_API_URL, LLM_MODEL)
TOKEN_HOURS = 12
# bcrypt cost factor. Each +1 doubles the work; tests lower it to stay fast.
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
