import subprocess
from pathlib import Path
from os.path import dirname, abspath
from shlex import quote
from argparse import ArgumentParser
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any
from beartype import beartype

from remote_docker_sandbox.rest_server_base import JsonRESTServer


@beartype
@dataclass
class DockerSandboxServer(JsonRESTServer):
    docker_compose_is_up: bool = False
    container_name_to_actual_name: dict[str, str] = {}
    image_name: str = "bash-sandbox"

    def get_response(self, function: str, **kwargs) -> Any:  # type: ignore
        if function not in self.name_to_function:
            raise KeyError(
                f'Invalid function "{function}". Must be one of {", ".join(self.name_to_function.keys())}'
            )

        return self.name_to_function[function](**kwargs)

    @property
    def name_to_function(self) -> dict[str, Callable]:
        return {
            "add_one": self.add_one,
            "start_container": self.start_container,
            "run_command": self.run_command,
            "stop_container": self.stop_container,
        }

    def add_one(self, x: int) -> str:
        return str(x + 1)

    def start_container(
        self, container_name: str, init_command: str | None = None
    ) -> None:
        if not self.docker_compose_is_up:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        i = len(self.container_name_to_actual_name) + 1
        self.container_name_to_actual_name[container_name] = f"docker-test-worker-{i}"

        if init_command is not None:
            self.run_command(container_name, init_command, timeout_seconds=30)

    def run_command(
        self, container_name: str, command: str, timeout_seconds: int | float
    ) -> dict:
        docker_exec_command = [
            "docker",
            "exec",
            self.container_name_to_actual_name[container_name],
            "/bin/bash",
            "-c",
            command,
        ]

        try:
            output = subprocess.run(
                docker_exec_command,
                timeout=timeout_seconds,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return {"returncode": 1, "stdout": "", "stderr": ""}

        return {
            "returncode": output.returncode,
            "stdout": output.stdout,
            "stderr": output.stderr,
        }

    def stop_container(self, container_name: str) -> None:
        del self.container_name_to_actual_name[container_name]

        if len(self.container_name_to_actual_name) == 0:
            subprocess.run(
                ["docker", "compose", "down"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.docker_compose_is_up = False


@beartype
def main():
    parser = ArgumentParser(
        usage="`python -m remote_docker_sandbox.server` to run the server on http://0.0.0.0:8000"
    )
    arguments = parser.parse_args()

    server = DockerSandboxServer()
    server.serve()


if __name__ == "__main__":
    main()
