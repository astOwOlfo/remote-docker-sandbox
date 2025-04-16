import os
from uuid import uuid4
from shlex import quote
import base64
from dataclasses import dataclass
from beartype import beartype

from remote_docker_sandbox.rest_client_base import JsonRESTClient


@dataclass
class CompletedProcess:
    returncode: int
    stdout: str
    stderr: str


server_url_counter = 0

blacklisted_server_urls = []


MAX_CREATE_RETRIES = 64


@beartype
class RemoteDockerSandbox(JsonRESTClient):
    container_name: str

    def __init__(
        self,
        server_urls: str | list[str] | None = None,
        init_command: str | None = None,
        ignore_failed_server_calls: bool = True,
        memory_gb: int | float = 1,
        cpus: int = 1,
    ) -> None:
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
        global blacklisted_server_urls

        assert set(server_urls) != set(blacklisted_server_urls), (
            "All server URLs are blacklisted."
        )

        while server_urls[server_url_counter] in blacklisted_server_urls:
            server_url_counter = (server_url_counter + 1) % len(server_urls)

        super().__init__(
            server_url=server_urls[server_url_counter],
            ignore_failed_server_calls=ignore_failed_server_calls,
        )
        server_url_counter = (server_url_counter + 1) % len(server_urls)

        self.container_name = f"docker-sandbox-{uuid4()}"

        start_response = self.call_server(
            function="start_container",
            container_name=self.container_name,
            init_command=init_command,
            memory_gb=memory_gb,
            cpus=cpus,
        )

        error = isinstance(start_response, dict) and set(start_response.keys()) == {
            "error"
        }
        if error:
            print(
                f"ERROR CREATING SANDBOX WITH SERVER URL {self.server_url}!! THIS SERVER WILL NEVER BE USED AGAIN!!"
            )
            blacklisted_server_urls.append(self.server_url)

    def run_command(
        self, command: str, timeout_seconds: float | int = 1
    ) -> CompletedProcess:
        response = self.call_server(
            function="run_command",
            container_name=self.container_name,
            command=command,
            timeout_seconds=timeout_seconds,
        )

        invalid_response = not (
            isinstance(response, dict)
            and set(response.keys()) == {"returncode", "stdout", "stderr"}
            and isinstance(response["returncode"], int)
            and (response["stdout"], str)
            and isinstance(response["stderr"], str)
        )
        if invalid_response:
            error_message = f"RemoteDockerSandbox.run_command: Got invalid response from server. The response json is: {response}"
            if not self.ignore_failed_server_calls:
                raise ValueError(error_message)
            print(error_message)
            return CompletedProcess(
                returncode=1,
                stdout="",
                stderr="Received invalid response from the remote docker server.",
            )

        return CompletedProcess(**response)

    def run_commands_sequentially(
        self,
        commands: list[str],
        total_timeout_seconds: float | int = 5,
        per_command_timeout_seconds: float | int = 4,
    ) -> list[CompletedProcess]:
        response = self.call_server(
            function="run_commands_sequentially",
            container_name=self.container_name,
            commands=commands,
            total_timeout_seconds=total_timeout_seconds,
            per_command_timeout_seconds=per_command_timeout_seconds,
        )

        invalid_response = not (
            isinstance(response, list)
            and all(
                isinstance(r, dict)
                and set(r.keys()) == {"returncode", "stdout", "stderr"}
                and isinstance(r["returncode"], int)
                and (r["stdout"], str)
                and isinstance(r["stderr"], str)
                for r in response
            )
        )
        if invalid_response:
            error_message = f"RemoteDockerSandbox.run_commands_sequentially: Got invalid response from server. The response json is: {response}"
            if not self.ignore_failed_server_calls:
                raise ValueError(error_message)
            print(error_message)
            return [
                CompletedProcess(
                    returncode=1,
                    stdout="",
                    stderr="Received invalid response from the remote docker server.",
                )
                for _ in commands
            ]

        return [CompletedProcess(**r) for r in response]

    def upload_file(self, filename: str, content: str) -> CompletedProcess:
        return self.run_command(
            RemoteDockerSandbox.upload_file_command(filename=filename, content=content)
        )

    @staticmethod
    def upload_file_command(filename: str, content: str) -> str:
        encoded_data = base64.b64encode(content.encode()).decode()
        return f"echo {encoded_data} | base64 -d > {quote(filename)}"

    def cleanup(self) -> None:
        self.call_server(function="stop_container", container_name=self.container_name)

    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.cleanup()
