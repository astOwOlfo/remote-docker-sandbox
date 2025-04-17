import subprocess
from pathlib import Path
from os.path import dirname, abspath
from shlex import quote
from argparse import ArgumentParser
from dataclasses import dataclass, field
from collections.abc import Callable
from time import perf_counter
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
            "stop_container": self.stop_container,
            "run_command": self.run_command,
            "run_commands_sequentially": self.run_commands_sequentially,
        }

    def add_one(self, x: int) -> str:
        return str(x + 1)

    def start_container(
        self,
        container_name: str,
        init_command: str | None,
        memory_gb: int | float,
        cpus: int,
    ) -> None:
        sandbox_path = Path(dirname(abspath(__file__)) + "/sandbox")
        if not sandbox_path.is_dir():
            raise FileNotFoundError(f"Sandbox directory '{sandbox_path}' not found.")

        build_command = (
            f"docker build -t {quote(self.image_name)} {quote(str(sandbox_path))}"
        )
        start_command = f"docker run -d --name {quote(container_name)} --memory {memory_gb}gb --cpus {cpus} --tty {quote(self.image_name)} /bin/bash -c 'sleep infinity'"
        if init_command is not None:
            exec_init_command = f"docker exec {quote(container_name)} /bin/bash -c {quote(init_command)}"
        else:
            exec_init_command = "true"

        start_process = subprocess.Popen(
            f"{build_command} && {start_command} && {exec_init_command}",
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

    def stop_container(self, container_name: str) -> None:
        self._wait_until_started(container_name)

        stop_container_command = (
            f"docker stop {quote(container_name)}; docker rm {quote(container_name)}"
        )

        subprocess.Popen(
            stop_container_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
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
            return {"returncode": 1, "stdout": "", "stderr": "timed out"}

        return {
            "returncode": output.returncode,
            "stdout": output.stdout,
            "stderr": output.stderr,
        }

    def run_commands_sequentially(
        self,
        container_name: str,
        commands: list[str],
        total_timeout_seconds: float | int,
        per_command_timeout_seconds: float | int,
    ) -> list[dict]:
        self._wait_until_started(container_name)

        responses: list[dict] = []
        remaining_time = total_timeout_seconds
        for command in commands:
            if remaining_time <= 0:
                responses.append({"returncode": 1, "stdout": "", "stderr": "timed out"})
                continue

            start_time = perf_counter()
            responses.append(
                self.run_command(
                    container_name=container_name,
                    command=command,
                    timeout_seconds=min(per_command_timeout_seconds, remaining_time),
                )
            )
            end_time = perf_counter()
            remaining_time -= end_time - start_time

        return responses


@beartype
def main():
    parser = ArgumentParser(
        description="Run a docker server. You can the use the docker client on by givin a http://your_ip:port base url."
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    arguments = parser.parse_args()

    server = DockerSandboxServer(host=arguments.host, port=arguments.port)
    server.serve()


if __name__ == "__main__":
    main()
