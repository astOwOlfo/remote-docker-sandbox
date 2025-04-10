from setuptools import setup, find_packages
import os

setup(
    name="remote_docker_sandbox",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["Flask==3.1.0", "Requests==2.32.3", "beartype", "setuptools"],
    # package_data={
    #     "remote_docker_sandbox.sandbox": ["Dockerfile"],
    # },
    data_files=[
        (
            os.path.join("remote_docker_sandbox", "sandbox"),
            ["remote_docker_sandbox/sandbox/Dockerfile"],
        ),
    ],
)
