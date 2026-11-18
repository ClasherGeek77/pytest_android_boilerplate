import logging
import os
import subprocess  # nosec B404
import time

import pytest
import requests
from appium import webdriver
from appium.options.android import UiAutomator2Options

from lib.app.pages.home_page import HomePage
from lib.app.pages.login_page import LoginLocators
from lib.assertion import Assertion
from lib.constants import constant_data, environment_data

logger = logging.getLogger(__name__)

# toolchain binaries live outside the usual PATH on this machine
EXTRA_PATH = os.pathsep.join(
    [os.path.dirname(environment_data["appium_bin"]), "/usr/local/bin"]
)


def appium_is_up():
    try:
        answer = requests.get(environment_data["server_url"] + "/status", timeout=3)
        return answer.json()["value"]["ready"]
    except (requests.RequestException, ValueError, KeyError):
        return False


# normally the appium server of this machine runs already, when it does not
# the session starts it itself (with the env the android driver needs) and
# stops it again after the run
@pytest.fixture(scope="session")
def appium_server():
    if appium_is_up():
        logger.info(f"appium server is answering on {environment_data['server_url']}")
        yield
        return
    server_env = dict(os.environ)
    server_env["PATH"] = EXTRA_PATH + os.pathsep + server_env.get("PATH", "")
    server_env["ANDROID_HOME"] = environment_data["android_home"]
    server_env["JAVA_HOME"] = environment_data["java_home_8"]
    port = environment_data["server_url"].rsplit(":", 1)[-1]
    logger.info(f"starting the appium server on port {port}")
    # one local server with fixed arguments, nothing from user input
    # the process must outlive this line, the yield and terminate end it
    process = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec B603
        [environment_data["appium_bin"], "--port", port],
        env=server_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 30
    while time.time() < deadline and not appium_is_up():
        time.sleep(1)
    if not appium_is_up():
        process.terminate()
        raise RuntimeError("the appium server did not answer within 30 seconds")
    yield
    process.terminate()
    process.wait(timeout=10)


def adb(*args):
    return subprocess.run(  # nosec B603 - fixed arguments, local device tooling
        [environment_data["adb"], *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


# the emulator: reuse the running one, boot the pinned AVD if it is down
# (about 90 seconds here, the 1.5 gb lean size of this 8 gb machine),
# leave it up afterwards, a cold boot should be opt-in, not a per-run tax
@pytest.fixture(scope="session")
def emulator(appium_server):  # pylint: disable=unused-argument
    if "emulator-" not in adb("devices").stdout:
        logger.info(f"booting the {environment_data['avd_name']} emulator")
        subprocess.Popen(  # pylint: disable=consider-using-with  # nosec B603
            [
                environment_data["emulator"],
                "-avd",
                environment_data["avd_name"],
                "-gpu",
                "host",
                "-no-boot-anim",
                "-memory",
                "1536",
                "-no-snapshot-save",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        deadline = time.time() + 180
        while (
            time.time() < deadline
            and adb("shell", "getprop", "sys.boot_completed").stdout.strip() != "1"
        ):
            time.sleep(5)
        if adb("shell", "getprop", "sys.boot_completed").stdout.strip() != "1":
            raise RuntimeError("the emulator did not boot within 180 seconds")


# without an enabled accessibility service flutter keeps its widgets in
# one opaque view, so the tree this suite reads would be empty; the enabler
# apk is installed and switched on here, and the app is restarted because
# the engine only bridges to services that are running when it starts
@pytest.fixture(scope="session")
def a11y_enabler(emulator):  # pylint: disable=unused-argument
    if (
        environment_data["enabler_id"].split("/")[0]
        not in adb("shell", "pm", "list", "packages").stdout
    ):
        apk = environment_data["enabler_apk"]
        if not os.path.isfile(apk):
            raise RuntimeError(
                f"the accessibility enabler is not installed and {apk} is missing, "
                "run ./fetch_app.sh to download it"
            )
        logger.info(f"installing the accessibility enabler from {apk}")
        adb("install", apk)
    enabled = adb(
        "shell", "settings", "get", "secure", "enabled_accessibility_services"
    )
    if environment_data["enabler_id"] not in enabled.stdout:
        logger.info("enabling the accessibility enabler")
        adb(
            "shell",
            "settings",
            "put",
            "secure",
            "enabled_accessibility_services",
            environment_data["enabler_id"],
        )
        adb("shell", "settings", "put", "secure", "accessibility_enabled", "1")
    if (
        environment_data["app_package"]
        not in adb("shell", "pm", "list", "packages").stdout
    ):
        apk = environment_data["apk_to_install"]
        if not os.path.isfile(apk):
            raise RuntimeError(
                f"{environment_data['app_package']} is not installed and {apk} "
                "is missing, run ./fetch_app.sh to download it"
            )
        logger.info(f"installing {apk}")
        adb("install", "-r", apk)
    # restart the app so the engine starts while the service is running
    adb("shell", "am", "force-stop", environment_data["app_package"])
    time.sleep(1)


def caps():
    options = UiAutomator2Options()
    options.load_capabilities(
        {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:appPackage": environment_data["app_package"],
            "appium:appActivity": environment_data["app_activity"],
            "appium:forceAppLaunch": True,
            "appium:newCommandTimeout": environment_data["new_command_timeout"],
            # typing falls back to clipboard paste on this app
            "appium:allowInsecure": ["clipboard"],
        }
    )
    return options


# one appium session for the whole run, creating one costs seconds and the
# independence comes from the state reset below, not from a new session
@pytest.fixture(scope="session")
def driver(a11y_enabler):  # pylint: disable=unused-argument
    client = webdriver.Remote(environment_data["server_url"], options=caps())
    yield client
    client.quit()


# a page object is the driver plus the patience it may use
@pytest.fixture(scope="session")
def home_page(driver):
    return HomePage(driver, environment_data["ui_timeout"])


@pytest.fixture(scope="session")
def login_page(driver):
    from lib.app.pages.login_page import LoginPage

    return LoginPage(driver, environment_data["ui_timeout"])


# runs before every test: the app is on the home page and signed out, so
# no test depends on what the test before it left open
@pytest.fixture(autouse=True)
def signed_out(home_page, login_page):
    if login_page.is_shown(LoginLocators.sign_in_button, seconds=2):
        logger.info("reset, closing a login screen left open by the last test")
        login_page.leave()
    home_page.wait_here()
    if home_page.is_logged_in():
        logger.info("reset, logging out before the test")
        home_page.logout()
    return home_page


class TestData:
    def __init__(self):
        self.password = constant_data["password"]
        self.standard_user = constant_data["standard_user"]
        self.locked_out_user = constant_data["locked_out_user"]
        self.wrong_password = constant_data["wrong_password"]
        self.unknown_user = constant_data["unknown_user"]
        self.error_username_required = constant_data["error_username_required"]
        self.error_password_required = constant_data["error_password_required"]
        self.error_locked_out = constant_data["error_locked_out"]
        self.error_no_match = constant_data["error_no_match"]


@pytest.fixture
def testdata():
    return TestData()


@pytest.fixture
def assertion():
    return Assertion()


@pytest.fixture(name="logger")
def step_logger():
    return logging.getLogger("test")
