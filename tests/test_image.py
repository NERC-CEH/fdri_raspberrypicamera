import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from raspberrycam.config import load_config
from raspberrycam.image import ImageManager, S3ImageManager
from raspberrycam.s3 import S3Manager

load_dotenv()
AWS_ROLE_ARN = os.environ["AWS_ROLE_ARN"]
AWS_BUCKET_NAME = os.environ["AWS_BUCKET_NAME"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

s3 = S3Manager(role_arn=AWS_ROLE_ARN, access_key_id=AWS_ACCESS_KEY_ID, secret_access_key=AWS_SECRET_ACCESS_KEY)


# There are two of these Image Managers, one local and one S3 based
# This stores images locally
def test_image_manager(tmp_path: Path, config_file: Path) -> None:
    with pytest.raises(TypeError):
        ImageManager(tmp_path)

    config = load_config(config_file)
    im = ImageManager(tmp_path, config)
    assert im.pending_directory == tmp_path / "pending_uploads"
    assert im.config.site == config.site


# This wraps around ImageManager and uploads to s3, deletes the original
# If upload fails deletion is skipped, we should see a log message
def test_s3_image_manager(tmp_path: Path, config_file: Path) -> None:
    s3 = S3Manager(role_arn=AWS_ROLE_ARN, access_key_id=AWS_ACCESS_KEY_ID, secret_access_key=AWS_SECRET_ACCESS_KEY)
    config = load_config(config_file)
    im = S3ImageManager(AWS_BUCKET_NAME, s3, tmp_path, config)
    assert im.pending_directory == tmp_path / "pending_uploads"


@patch("raspberrycam.s3.upload_to_s3")
def test_upload_deletion(mock_upload: MagicMock, tmp_path: Path, config_file: Path) -> None:
    config = load_config(config_file)

    s3 = S3Manager(role_arn=AWS_ROLE_ARN, access_key_id=AWS_ACCESS_KEY_ID, secret_access_key=AWS_SECRET_ACCESS_KEY)

    s3im = S3ImageManager(AWS_BUCKET_NAME, s3, tmp_path, config)

    # create dummy file in our temp directory
    pending_dir = tmp_path / "pending_uploads"
    filepath = pending_dir / "test.txt"
    # Assume the upload fails, We should keep the file
    mock_upload.return_value = False
    with open(filepath, "w") as out:
        out.write("\n")
    s3im.upload_pending()

    # Default behaviour is to delete the image, in whatever case
    with pytest.raises(AssertionError):
        assert os.path.exists(filepath)

    # Check we could still use the cache if explicitly wanted
    s3im = S3ImageManager(AWS_BUCKET_NAME, s3, tmp_path, config, delete_cache=False)
    with open(filepath, "w") as out:
        out.write("\n")
    s3im.upload_pending()
    assert os.path.exists(filepath)

    # Assume the upload succeeds, the file should be gone
    mock_upload.return_value = True
    with open(filepath, "w") as out:
        out.write("\n")
    s3im.upload_pending()

    assert not os.path.exists(filepath)
