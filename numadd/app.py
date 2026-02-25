from flask import Flask, request, jsonify
from addition_service import AdditionService
from input_validator import InputValidator
from cache_service import CacheService
from log_service import LogService

app = Flask(__name__)

addition_service = AdditionService()
input_validator = InputValidator()
cache_service = CacheService()
log_service = LogService()


@app.route("/add", methods=["GET"])
def add():
    a = request.args.get("a")
    b = request.args.get("b")

    log_service.log_request("/add", {"a": a, "b": b})

    if not input_validator.validate(a, b):
        return jsonify({"error": "Invalid input. Provide two valid numbers within range."}), 400

    a, b = float(a), float(b)

    cached = cache_service.get(a, b)
    if cached is not None:
        result = {"a": a, "b": b, "result": cached, "cached": True}
        log_service.log_response(result)
        return jsonify(result)

    result_value = addition_service.add(a, b)
    cache_service.set(a, b, result_value)

    result = {"a": a, "b": b, "result": result_value, "cached": False}
    log_service.log_response(result)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
