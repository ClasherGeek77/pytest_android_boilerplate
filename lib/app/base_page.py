import logging

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import InvalidElementStateException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger("page")

XPATH = AppiumBy.XPATH


# what every page can do, xpaths only, nothing uiautomator specific, so
# the same shape fits any app whose screen the engine can read
class BasePage:
    def __init__(self, driver, timeout):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def click(self, xpath):
        logger.info(f"clicking {xpath}")
        self.wait.until(EC.element_to_be_clickable((XPATH, xpath))).click()

    def send_text(self, xpath, value):
        logger.info(f"typing into {xpath}")
        field = self.wait.until(EC.presence_of_element_located((XPATH, xpath)))
        # the field must be focused before anything may put text in it
        field.click()
        try:
            field.send_keys(value)
        except InvalidElementStateException:
            # the accessibility node refused setText, and this device has
            # no IME connected, so paste it the way a person long-presses
            self._paste_into(field, value)

    # long press opens the edit toolbar, paste fills from the clipboard,
    # and the toolbar closing is the proof the paste took
    def _paste_into(self, field, value):
        logger.info(f"pasting into the focused field instead: {value!r}")
        # driver.tap([...], duration) stopped registering as a long press on
        # fresh emulator boots; this w3c action chain does, every time
        ActionChains(self.driver).click_and_hold(field).pause(2.0).release().perform()
        paste = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((XPATH, "//*[@content-desc='Paste']")),
            message="paste toolbar did not open",
        )
        self.driver.set_clipboard(value.encode("utf-8"))
        paste.click()
        # the node's @text reads "value, label" on flutter widgets, so the
        # closing of the toolbar is the deterministic proof the paste took
        WebDriverWait(self.driver, self.timeout).until(
            EC.invisibility_of_element_located((XPATH, "//*[@content-desc='Paste']")),
            message=f"paste toolbar did not close after pasting {value!r}",
        )

    # a wait: this thing is on screen or the test fails on TimeoutException
    def wait_shown(self, xpath):
        logger.info(f"waiting for {xpath}")
        self.wait.until(EC.presence_of_element_located((XPATH, xpath)))

    # a probe, not a wait: is this thing on screen right now, True or False
    def is_shown(self, xpath, seconds=10):
        logger.info(f"checking shown: {xpath}")
        try:
            WebDriverWait(self.driver, seconds).until(
                EC.presence_of_element_located((XPATH, xpath))
            )
            return True
        except TimeoutException:
            return False
