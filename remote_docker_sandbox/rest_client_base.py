import requests
import traceback
import json
import os
from typing import Any
from beartype import beartype


@beartype
class JsonRESTClient:
    server_url: str

    def __init__(
        self, server_url: str | None = None, ignore_failed_server_calls: bool = True
    ) -> None:
        if server_url is None:
            server_url = os.environ.get("REMOTE_DOCKER_SANDBOX_SERVER_URL")

        if server_url is None:
            raise ValueError(
                "To initialize a JsonRESTClient, you must provide a server url, either with the server_url argument to the contructor or the REMOTE_DOCKER_SANDBOX_SERVER_URL environment variable."
            )

        self.server_url = server_url
        self.ignore_failed_server_calls = ignore_failed_server_calls

    @property
    def endpoint(self):
        return f"{self.server_url}/process"

    def call_server(self, **kwargs) -> Any:
        try:
            response = requests.post(
                self.endpoint, json=kwargs, headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            if not self.ignore_failed_server_calls:
                raise e
            error_message = f"Error communicating with server: {e} {traceback.format_exc()}"
            print(error_message)
            return {"error": error_message}

        if response.status_code != 200:
            error_message = f"Error communicating with server.\nStatus code: {response.status_code}.\nResponse json: {response.json()}"
            if self.ignore_failed_server_calls:
                print(error_message)
                return
            else:
                raise requests.HTTPError(error_message)

        response = response.json()
        if response is not None:
            response = json.loads(response)
        return response


# Example usage
if __name__ == "__main__":
    server_url = "http://16.171.63.45:8080"
    print(f"Connecting to server at {server_url}")
    client = JsonRESTClient(server_url)

    container_name = "test-container-1"

    print(client.call_server(function="start_container", container_name=container_name))

    print(
        client.call_server(
            function="run_command",
            container_name=container_name,
            command="echo hi; ls; pwd",
            timeout_seconds=30,
        )
    )

    print(client.call_server(function="stop_container", container_name=container_name))
