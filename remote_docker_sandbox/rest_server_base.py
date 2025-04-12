from flask import Flask, request, jsonify
import json
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from beartype import beartype


@beartype
@dataclass
class JsonRESTServer(ABC):
    host: str = "0.0.0.0"
    port: int = 8080

    def serve(self) -> None:
        app = Flask(__name__)

        @app.route("/process", methods=["POST"])
        def process():
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()
            result, status_code = self._get_response_or_error(data)

            return jsonify(result), status_code

        app.run(host=self.host, debug=True, port=self.port)

    def _get_response_or_error(self, arguments: Any) -> tuple[Any, int]:
        try:
            result = self.get_response(**arguments)
        except Exception as e:
            return {
                "error": f"Uncaught exception:\n\n{e}\n{traceback.format_exc()}"
            }, 400

        try:
            return json.dumps(result), 200
        except Exception:
            return {"error": f"Unable to convert response to json. {str(result)=}"}, 400

    @abstractmethod
    def get_response(self, **kwargs) -> Any:
        pass


@beartype
class DummyJsonRESTServer(JsonRESTServer):
    def get_response(self, **kwargs) -> Any:
        return {"received": kwargs}


if __name__ == "__main__":
    # Use host='0.0.0.0' to make the server accessible from other machines
    server = DummyJsonRESTServer()
    server.serve()
