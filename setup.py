from setuptools import setup, find_packages

setup(
    name="remote_docker_sandbox",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["Flask==3.1.0", "Requests==2.32.3", "beartype", "setuptools", "plotly", "numpy"],
    include_package_data=True,
)
