from uuid import uuid4
from dataclasses import dataclass
from beartype import beartype

from remote_docker_sandbox.rest_client_base import JsonRESTClient


@dataclass
class CompletedProcess:
    returncode: int
    stdout: str
    stderr: str


@beartype
class RemoteDockerSandbox(JsonRESTClient):
    container_name: str

    def __init__(self, server_url: str = "http://16.171.63.45:8000") -> None:
        super().__init__(server_url=server_url)

        self.container_name = f"docker-sandbox-{uuid4()}"

        self.call_server(
            function="start_container", container_name=self.container_name
        )

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