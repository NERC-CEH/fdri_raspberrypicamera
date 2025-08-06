"""
Test the simplest workflow for mTLS certificate based authentication.
"""

import logging
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

from raspberrycam.config import load_config
from raspberrycam.s3 import S3Manager

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

# Keys in the JSON that's returned if we successfully auth
CREDENTIALS_KEYS = ["accessKeyId", "secretAccessKey", "sessionToken"]


def test_auth_flow(
    cert_file: Path, key_file: Path, cert_root: Path, endpoint: str, device_id: str, alias: str, tmp_path: Path
) -> None:
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
    credentials = response.json()["credentials"]
    for k in CREDENTIALS_KEYS:
        assert k in credentials

    options = {}

    # Convert CamelCase to snake_case :/
    # Note - these are passed to S3Manager which has an assume_role method
    # Its output is equivalent to the credentials we've already got
    # from the IoT credentials endpoint - we can pass them directly
    # Note - the image upload code calls assume_role explicitly
    for k in CREDENTIALS_KEYS:
        key = re.sub(r"(?<!^)(?=[A-Z])", "_", k).lower()
        options[key] = credentials[k]

    # This is the ARN of the role we are _assuming_
    # The alias in the URL above is the _name_ of the role alias in IoT Core
    # - that points to this role
    config = load_config("config/config.yaml")
    options["iot_auth"] = config.iot_auth

    s3 = S3Manager(**options)
    assert s3
    # This now checks whether we want iot_auth, specified in config.yaml
    s3.assume_role()

    test_txt = tmp_path / "test.txt"
    with open(test_txt, "w") as out:
        out.write("testing")

    # Try an upload!
    # Question about whether to put this in the config file
    bucket_name = os.environ.get("AWS_BUCKET_NAME", "")

    result = s3.upload(test_txt, bucket_name, "test.txt")
    print(result)
