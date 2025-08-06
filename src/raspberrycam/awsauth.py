import logging
import re

import requests

from raspberrycam.config import Config

CREDENTIALS_KEYS = ["accessKeyId", "secretAccessKey", "sessionToken"]


class AWSIoTAuth:
    def __init__(self, config: Config):
        self.device_id = config.device_id
        self.public_key = config.public_key
        self.private_key = config.private_key
        self.role_arn = config.role_arn
        self.role_name = config.role_name
        self.endpoint = config.endpoint
        self.certificate_root = config.certificate_root

    def request_keys(self) -> None:
        """Form a request to the IoT credentials service.
        If successful it returns a temporary set of access/secret keys"""

        headers = {"x-amzn-iot-thingname": self.device_id}
        cert = (self.public_key, self.private_key)
        url = f"https://{self.endpoint}/role-aliases/{self.role_name}/credentials"

        try:
            response = requests.get(url, cert=cert, headers=headers, verify=self.certificate_root)
        except ConnectionError:
            # Case in which we can't reach the network,
            # Or the URL is malformed - same error either way
            logging.error(f"Could not connect to {url} to authenticate")
            exit(1)

        credentials = response.json()["credentials"]

        # Set the access key, secret key and session token as our atttributes
        # Convert CamelCase to snake_case :/
        for k in CREDENTIALS_KEYS:
            key = re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower()
            setattr(self, key, credentials[k])
