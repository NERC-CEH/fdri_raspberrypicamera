AWS Authentication
==================

Here we cover setting up the client (this program) to authenticate with Amazon Web Services to upload images to an s3 storage bucket.

Access Keys
-----------

*This is not recommended*.

Given an IAM user with restricted privileges, issue an access key and a secret key. (There is a limit of two pairs of these per user).

Create a file called ``.env`` in the root of the project - this holds environment variables.

.. code:: bash

    AWS_BUCKET_NAME="our_bucket_name"
    AWS_ROLE_ARN="ARN for the role that has upload permissions"
    AWS_ACCESS_KEY_ID="the visible part of the key"
    AWS_SECRET_ACCESS_KEY="the hidden part of the key"


IoT Core Certificates
---------------------

When we create an "IoT Core Thing" for each Raspberry Pi, we issue it certificates which are used to do secure mutual authentication with AWS services. This is how the `Campbell datalogger <https://github.com/NERC-CEH/campbell-mqtt-control>`_ project works.

The same certificates can be used to grant temporary keys to upload image data. Each Raspberry Pi or other field device gets its own unique identifier and set of certificates. 

To authenticate, we pass them to an "IoT credentials endpoint" (different from the usual IoT endpoint for MQTT messages).

In this case, you need:

- a copy of the private and public certificates in the root of this project
- the address of the endpoint
- the **name** of the **role alias** within IoT core which allows image upload to select devices
- the **device id** to which the certificates are issued.
- an extended configuration file, which looks like this:

.. code:: yaml

    site: TEST 
    lat: 51.8626453
    lon: -0.2031049
    catchment: SE
    direction: E
    interval: 10800
    iot_auth: true
    private_key: default-private.key
    public_key: default-certificate.key
    endpoint: iot_credentials_endpoint
    role_name: upload_role
    device_id: default

Testing IoT Core authentication
-------------------------------

There is a test script provided, written as a unit test.

.. code:: bash

    py.test --endpoint credentials_endpoint --alias role_alias_name tests/integration/auth.py

If you don't know the endpoint but have got access to the ``aws`` commandline interface, you can learn it by

.. code:: bash

    aws iot describe-endpoint --endpoint-type iot:CredentialProvider

Note that this is not the regular IoT endpoint, but a specific credentials management one.

Please see the document on "policy" for how this is set up, and if you need a role aliasname and don't know what it is, contact a friendly AWS administrator.
