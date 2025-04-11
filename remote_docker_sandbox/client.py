import os
from uuid import uuid4
from dataclasses import dataclass
from beartype import beartype

from remote_docker_sandbox.rest_client_base import JsonRESTClient


@dataclass
class CompletedProcess:
    returncode: int
    stdout: str
    stderr: str


server_url_counter = 0


@beartype
class RemoteDockerSandbox(JsonRESTClient):
    container_name: str

    def __init__(self, server_urls: str | list[str] | None = None, init_command: str | None = None) -> None:
        if isinstance(server_urls, str):
            server_urls = [server_urls]

        if server_urls is None:
            server_urls = os.environ.get("REMOTE_DOCKER_SANDBOX_SERVER_URL")
            if server_urls is not None:
                server_urls = server_urls.split(",")

        if server_urls is None:
            raise ValueError(
                "To initialize a JsonRESTClient, you must provide a server url, either with the server_url argument to the contructor or the REMOTE_DOCKER_SANDBOX_SERVER_URL environment variable."
            )

        global server_url_counter
        super().__init__(server_url=server_urls[server_url_counter])
        server_url_counter = (server_url_counter + 1) % len(server_urls)

        self.container_name = f"docker-sandbox-{uuid4()}"

        self.call_server(function="start_container", container_name=self.container_name, init_command=init_command)

    def run_command(
        self, command: str, timeout_seconds: float | int = 30
    ) -> CompletedProcess:
        response = self.call_server(
            function="run_command",
            container_name=self.container_name,
            command=command,
            timeout_seconds=timeout_seconds,
        )

        assert set(response.keys()) == {"returncode", "stdout", "stderr"}
        assert isinstance(response["returncode"], int)
        assert isinstance(response["stdout"], str)
        assert isinstance(response["stderr"], str)

        return CompletedProcess(**response)

    def cleanup(self) -> None:
        self.call_server(function="stop_container", container_name=self.container_name)


@beartype
def main() -> None:
    sandbox = RemoteDockerSandbox()
    print(sandbox.run_command("echo hi; ls; pwd"))
    sandbox.cleanup()


if __name__ == "__main__":
    main()
