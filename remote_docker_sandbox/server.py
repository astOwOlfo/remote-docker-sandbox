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
    starting_container_processes: dict[str, subprocess.Popen] = field(
        default_factory=lambda: {}
    )
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

    def start_container(self, container_name: str) -> None:
        sandbox_path = Path(dirname(abspath(__file__)) + "/sandbox")
        if not sandbox_path.is_dir():
            raise FileNotFoundError(f"Sandbox directory '{sandbox_path}' not found.")

        start_command = f"docker build -t {quote(self.image_name)} {quote(str(sandbox_path))}; docker run -d --name {quote(container_name)} --tty {quote(self.image_name)} /bin/bash -c 'sleep infinity'"

        print("docker start command:", start_command)

        start_process = subprocess.Popen(
            start_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
        )

        self.starting_container_processes[container_name] = start_process

    def _wait_until_started(self, container_name: str) -> None:
        start_process = self.starting_container_processes.get(container_name)
        if start_process is None:
            return
        stdout, stderr = start_process.communicate()
        if start_process.returncode != 0:
            raise Exception(
                f"Error starting sandbox:\nstart process exit code: {start_process.returncode} \n\nstart process stdout: {stdout}\n\nstart process stderr {stderr}"
            )

    def run_command(
        self, container_name: str, command: str, timeout_seconds: int | float
    ) -> dict:
        self._wait_until_started(container_name)

        docker_exec_command = [
            "docker",
            "exec",
            container_name,
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
        self._wait_until_started(container_name)

        stop_container_command = (
            f"docker stop {quote(container_name)}; docker rm {quote(container_name)}"
        )

        print("stop contianer command:", stop_container_command)

        subprocess.Popen(
            stop_container_command,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            shell=True,
        )


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
