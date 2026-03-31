import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
for noise in ["LiteLLM", "openai"]:
    logging.getLogger(noise).setLevel(logging.WARNING)

logger = logging.getLogger("MessageAnalyzer")
logger.setLevel(logging.INFO)