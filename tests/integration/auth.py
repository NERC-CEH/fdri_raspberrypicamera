"""
Test the simplest workflow for mTLS certificate based authentication.
"""

import re
from pathlib import Path

import requests

from raspberrycam.s3 import S3Manager

CREDENTIALS_KEYS = ["accessKeyId", "secretAccessKey", "sessionToken"]


def test_auth_flow(cert_file: Path, key_file: Path, cert_root: Path, endpoint: str, device_id: str, alias: str) -> None:
    """We make a signed request to the IoT credentials endpoint
    It returns a temporary set of keys and session token.

    https://docs.aws.amazon.com/iot/latest/developerguide/authorizing-direct-aws.html
    """

    #  curl --cacert CARoot.pem --cert [device id]-certificate.pem.crt --key [device id]-private.pem.key -H "x-amzn-iot-thingname: [device id]" https://[our endpoint]/role-aliases/[alias name]/credentials ## noqa: E501

    headers = {"x-amzn-iot-thingname": device_id}
    cert = (cert_file, key_file)
    url = f"https://{endpoint}/role-aliases/{alias}/credentials"
    response = requests.get(url, cert=cert, headers=headers, verify=cert_root)
    assert response.status_code == 200

    assert "credentials" in response.json()
    creds = response.json()["credentials"]
    for k in CREDENTIALS_KEYS:
        assert k in creds

    options = {}
    # Convert CamelCase to snake_case :/
    for k in CREDENTIALS_KEYS:
        key = re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower()
        options[key] = creds[k]

    options["role_arn"] = "aws:arn:like:that"
    s3 = S3Manager(**options)
    assert s3
