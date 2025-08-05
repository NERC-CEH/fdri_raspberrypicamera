import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

from raspberrycam.config import Config
from raspberrycam.s3 import S3Manager

logger = logging.getLogger(__name__)


class ImageManager:
    """Class for managing images"""

    base_directory: Path
    """Base directory of program"""
    pending_directory: Path
    """Directory of images to be uploaded"""
    log_directory: Path
    """Directory for logs"""

    def __init__(self, base_directory: Path, config: Config, delete_cache: bool = True) -> None:
        """
        Args:
            base_directory: Base directory of the program
        """
        if not isinstance(base_directory, Path):
            base_directory = Path(base_directory)
        self.base_directory = base_directory
        self.pending_directory = base_directory / "pending_uploads"
        self.log_directory = base_directory / "logs"
        self.log_file = self.log_directory / "log.log"
        # Whether to keep a local cache in event of network / service failure
        self.delete_cache = delete_cache
        # Installation-specific file naming conventions set in config.yaml
        self.config = config

        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Creates app directories if they don't exist already"""
        for path in [self.base_directory, self.pending_directory, self.log_directory]:
            if not path.exists():
                os.makedirs(path)

    def get_pending_image_path(self, *args, **kwargs) -> Path:
        """Gets a new image filepath with a timestamp
        Returns:
            A path in the pending image folder
        """
        return self.pending_directory / self.get_image_name(*args, **kwargs)

    def get_pending_images(self) -> List[Path]:
        """Get a list of pending paths
        Returns:
            A list of Path objects
        """
        return [self.pending_directory / x for x in os.listdir(self.pending_directory.absolute())]

    def get_image_name(self) -> str:
        """Gets a filename using the SE_CARGN_01_PCAM_E format with timestamp
        Returns:
            A filename string in format: SE_CARGN_01_PCAM_E_YYYYMMDD_HHMMSS
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config = self.config
        # TODO should 01 be part of the camera ID?
        # https://github.com/NERC-CEH/FDRI_RaspberryPi_Scripts/issues/12
        return f"{config.catchment}_{config.site}_01_PCAM_{config.direction}_{timestamp}.jpg"


class S3ImageManager(ImageManager):
    """Image manager that writes to S3"""

    bucket_name: str
    """S3 bucket that gets written"""
    s3_manager: S3Manager
    """S3 manager object for handling credentials and uploads"""

    def __init__(self, bucket_name: str, s3_manager: S3Manager, *args, **kwargs) -> None:
        """
        Args:
            bucket_name: S3 bucket that is written to
            s3_manager: The S3 management object

        """
        self.bucket_name = bucket_name
        self.s3_manager = s3_manager
        super().__init__(*args, **kwargs)

    def partition_path(self, image: str) -> None:
        """Accepts an absolute path to the image
        Returns the partitioned path with just the filename appended"""
        config = self.config
        filename = Path(image).name
        return f"catchment={config.catchment}/site={config.site}/compound=01/type=PCAM/direction={config.direction}/date={datetime.now().strftime('%Y-%m-%d')}/{filename}"  # noqa: E501

    def upload_pending(self, debug: bool = False) -> None:
        """Upload files from the pending directory to S3
        Files are deleted after a successful upload

        Unless delete=False is passed (the defautl) then they're deleted in any case

        Args:
            debug: Flag to enable debugging mode
        """
        pending_images = self.get_pending_images()
        if len(pending_images) > 0:
            self.s3_manager.assume_role()
            for image in pending_images:
                try:
                    bucket_path = self.partition_path(image)

                    upload_successful = False
                    if debug:
                        logger.debug(f"Pretended to upload image {image} to bucket {self.bucket_name}")
                    else:
                        upload_successful = self.s3_manager.upload(image, self.bucket_name, bucket_path)
                    if upload_successful or self.delete_cache:
                        os.remove(image)

                except Exception as e:
                    logger.exception(f"Failed to upload image: {image}", exc_info=e)
        # Note on removing images due to size constraint as images are <200 kb with 10 gb it would take
        # ~20 years to fill
        else:
            logger.info("No images to upload")
