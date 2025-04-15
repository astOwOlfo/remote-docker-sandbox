from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from collections.abc import Callable, Iterable
from typing import Any
from beartype import beartype


@beartype
def delayed(function: Callable) -> Callable[..., Callable[[], Any]]:
    def workload(*args, **kwargs) -> Callable:
        return lambda: function(*args, **kwargs)

    return workload


@beartype
def threaded_map(
    delayed_functions: Iterable[Callable[[], Any]],
    max_workers: int,
    tqdm_description: str | None = None,
    verbose: bool = True,
) -> list[Any]:
    """
    Use `threaded_map([delayed(f)(...) for ... in ...])` to run `[f(...) for ... in ...]` in a threaded way.
    """

    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     return list(executor.map(lambda f: f(), delayed_functions))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(lambda f: f(), f) for f in delayed_functions]
        results = []
        for future in tqdm(
            futures, total=len(futures), desc=tqdm_description, disable=not verbose
        ):
            results.append(future.result())
    return results


if __name__ == "__main__":
    from remote_docker_sandbox.client import RemoteDockerSandbox

    sandboxes = [RemoteDockerSandbox() for _ in range(16)]
    threaded_map(
        (delayed(sandbox.run_command)("sleep 1; echo hi") for sandbox in sandboxes),
        max_workers=32,
    )
    for sandbox in sandboxes:
        sandbox.cleanup()
