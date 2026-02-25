import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("numadd")


class LogService:
    def log_request(self, endpoint: str, payload: dict):
        logger.info(f"REQUEST {endpoint} | payload={payload}")

    def log_response(self, result: dict):
        logger.info(f"RESPONSE | result={result}")

    def log_error(self, error: Exception):
        logger.error(f"ERROR | {error}")
