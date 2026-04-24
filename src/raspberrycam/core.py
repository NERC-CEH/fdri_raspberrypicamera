import logging
import time
import wdt
from datetime import datetime
from dateutil.tz import tzlocal

from raspberrycam import raspberrypi
from raspberrycam.camera import CameraInterface
from raspberrycam.image import S3ImageManager
from raspberrycam.raspberrypi import shutdown
from raspberrycam.scheduler import FdriScheduler, ScheduleState

logger = logging.getLogger(__name__)


class Raspberrycam:
    """Core class for managing a RasberryPi camera deployment"""

    scheduler: FdriScheduler
    """The scheduler used to control the RasberryPi state"""

    camera: CameraInterface
    """A physical/virtual camera to take images"""

    capture_interval: int
    """Frequency of image captures in seconds"""

    image_manager: S3ImageManager
    """Image manager used to manipulate image files"""

    _intervals_since_last_upload: int
    """Tracks how many images have been captured since the last upload,
        Allows the app to bulk upload images"""

    def __init__(
        self,
        scheduler: FdriScheduler,
        camera: CameraInterface,
        image_manager: S3ImageManager,
        capture_interval: int = 300,
        sleep_interval: int = 300,
        debug: bool = False,
        switch_off: bool = False
    ) -> None:
        """
        Args:
            scheduler: The scheduler used to control the RasberryPi state
            camera: The camera interface used
            image_manager: The image management object
            debug: Flag to activate debug mode
        """
        self.scheduler = scheduler
        self.camera = camera
        self.capture_interval = capture_interval
        self.sleep_interval = sleep_interval
        self.image_manager = image_manager
        self._intervals_since_last_upload = 0
        self.debug = debug
        self.switch_off = switch_off

    def run(self) -> None:
        """Runs the main loop of code until exited"""
        # Ensure the watchdog will only restore Raspberry PI at repower event, only if there's power
        wdt.setRepowerOnBattery(1)
        # todo check if the NTP update is complete at this point
        utc_now = datetime.utcnow()
        fifteen_minutes_in_seconds = 15 * 60
        wdt.setRTC(utc_now.year, utc_now.month, utc_now.day, utc_now.hour, utc_now.minute, utc_now.second)
        wdt.setDefaultPeriod(fifteen_minutes_in_seconds) # Set to 15 minutes, if we've locked up for that long, something's very wrong.
        wdt.setPeriod(fifteen_minutes_in_seconds)
        while True:
            raspberrypi.set_governer(raspberrypi.GovernorMode.POWERSAVE, debug=self.debug)
            now = datetime.now(tzlocal())
            state = self.scheduler.get_state(now)

            if state == ScheduleState.OFF:
                sleep_for = self.sleep_interval
                # Instead of exiting, wait until the next ON time
                logger.info("Camera is in OFF state (nighttime), waiting...")
                next_on_time = self.scheduler.get_next_on_time(now)
                logger.info(f"Next ON time: {next_on_time}")

                # Sleep until close to the next ON time
                sleep_duration = (next_on_time - now).total_seconds()
                if sleep_duration > 0:
                    if self.switch_off and sleep_duration > (5 * 60): # Don't bother switching off, if we have less than 5 minutes to wait
                        wdt.setOffInterval(sleep_duration)
                        shutdown()
                    else:
                        # Sleep for most of the duration, but wake up occasionally to check
                        # In case of time changes, system restarts, etc.
                        logger.debug(f"waiting for {sleep_duration}")
                        while sleep_duration > sleep_for:
                            logger.debug(f"sleeping for {sleep_for} seconds")
                            time.sleep(sleep_for)
                            sleep_duration -= sleep_for
                            # Re-check the time in case something changed
                            now = datetime.now(tzlocal())
                            if self.scheduler.get_state(now) == ScheduleState.ON:
                                break
                            next_on_time = self.scheduler.get_next_on_time(now)
                            sleep_duration = (next_on_time - now).total_seconds()
                            logger.debug(f"now waiting for {sleep_duration}")

                        # Sleep the remaining time
                        if sleep_duration > 0:
                            time.sleep(sleep_duration)
                            logger.debug(f"sleeping for {sleep_duration}")
                    continue  # Go back to the start of the loop to check state again

            # Camera is ON - take pictures
            logger.info("Camera is in ON state, capturing image...")
            # Flip the image vertically since the camera is mounted upside down
            self.camera.capture_image(self.image_manager.get_pending_image_path(), vflip=True, hflip=True)

            if len(self.image_manager.get_pending_images()) > 0:
                raspberrypi.set_governer(raspberrypi.GovernorMode.ONDEMAND, debug=self.debug)
                self.image_manager.upload_pending(debug=self.debug)

            if self.switch_off:
                wdt.setOffInterval(self.capture_interval)
                shutdown()
            else:
                time.sleep(self.capture_interval)