"""
Test the simplest workflow for mTLS certificate based authentication.
"""
import requests
import pytest


def test_auth_flow(cert_file, key_file, cert_root, endpoint, device_id, alias):
    """We make a signed request to the IoT credentials endpoint
    It returns a temporary set of keys and session token.

    https://docs.aws.amazon.com/iot/latest/developerguide/authorizing-direct-aws.html
    """

    #  curl --cacert CARoot.pem --cert [device id]-certificate.pem.crt --key [device id]-private.pem.key -H "x-amzn-iot-thingname: [device id]" https://[our endpoint]/role-aliases/[alias name]/credentials ## noqa: E501
   
    headers = {'x-amzn-iot-thingname': device_id}
    cert = (cert_file, key_file)
    url = f"https://{endpoint}/role-aliases/{alias}/credentials"
    response = requests.get(url,cert=cert,headers=headers,verify=cert_root)
    assert response.status_code == 200
    assert 'credentials' in response.json()
