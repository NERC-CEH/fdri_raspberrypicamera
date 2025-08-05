"""
Test the simplest workflow for mTLS certificate based authentication.
"""

from pathlib import Path

import requests


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
