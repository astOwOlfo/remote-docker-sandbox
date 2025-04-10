import requests
import json
import os
from typing import Any
from beartype import beartype


@beartype
class JsonRESTClient:
    server_url: str

    def __init__(self, server_url: str | None = None) -> None:
        if server_url is None:
            server_url = os.environ.get("REMOTE_DOCKER_SANDBOX_SERVER_URL")

        if server_url is None:
            raise ValueError(
                "To initialize a JsonRESTClient, you must provide a server url, either with the server_url argument to the contructor or the REMOTE_DOCKER_SANDBOX_SERVER_URL environment variable."
            )

        self.server_url = server_url

    @property
    def endpoint(self):
        return f"{self.server_url}/process"

    def call_server(self, **kwargs) -> Any:
        response = requests.post(
            self.endpoint, json=kwargs, headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()

        response = response.json()
        response = json.loads(response)
        return response


# Example usage
if __name__ == "__main__":
    server_url = "http://16.171.63.45:8000"
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
