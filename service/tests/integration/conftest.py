import os

import pytest
import requests
from requests.exceptions import ConnectionError

from service.source.repository import MessageRepository


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir), "integration", "docker-compose.integration.yml"
    )


@pytest.fixture(scope="session")
def message_repository(docker_ip, docker_services):
    port = docker_services.port_for("healthcheck", 80)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )

    return MessageRepository(
        db_host="localhost",
        db_port=int(os.environ["MESSENGER_DB_PORT"]),
        db_name=os.environ["MESSENGER_DB_NAME"],
        db_username=os.environ["MESSENGER_DB_USERNAME"],
        db_password=os.environ["MESSENGER_DB_PASSWORD"],
    )
