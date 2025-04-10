from beartype import beartype

from server import DockerSandboxServer

@beartype
def main() -> None:
    server = DockerSandboxServer()
    server.serve()


if __name__ == "__main__":
    main()
