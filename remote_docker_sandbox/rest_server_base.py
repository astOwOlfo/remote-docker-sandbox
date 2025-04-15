from threading import Lock
from flask import Flask, request, jsonify
from time import perf_counter
import json
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from beartype import beartype


@beartype
@dataclass(frozen=True)
class Timestamp:
    start: float
    end: float


@beartype
@dataclass
class JsonRESTServer(ABC):
    host: str = "0.0.0.0"
    port: int = 8080
    _call_timestamps: list[Timestamp] = field(default_factory=lambda: [])
    _call_timestamps_lock: Lock = field(default_factory=lambda: Lock())

    def serve(self) -> None:
        app = Flask(__name__)

        @app.route("/process", methods=["POST"])
        def process():
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()
            result, status_code = self._get_response_or_error(data)

            return jsonify(result), status_code
        
        @app.route("/get_call_timestamps", methods=["GET"])
        def get_call_timestamps():
            with self._call_timestamps_lock:
                response = [
                    {"start": timestamp.start, "end": timestamp.end}
                    for timestamp in self._call_timestamps
                ]
            return response, 400

        app.run(host=self.host, debug=True, port=self.port)

    def _get_response_or_error(self, arguments: Any) -> tuple[Any, int]:
        start_time = perf_counter()
        try:
            result = self.get_response(**arguments)
        except Exception as e:
            result = {
                "error": f"Uncaught exception:\n\n{e}\n{traceback.format_exc()}"
            }, 400
        end_time = perf_counter()

        with self._call_timestamps_lock:
            self._call_timestamps.append(Timestamp(start=start_time, end=end_time))

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
