from lib.app.base_page import BasePage


# the fields are addressed by position, their @text carries the label only
# while empty and the typed value afterwards, so it cannot identify them
class LoginLocators:
    username_field = "(//android.widget.EditText)[1]"
    # an xpath, not a secret
    password_field = "(//android.widget.EditText)[2]"  # nosec B105
    sign_in_button = "//*[@content-desc='Sign In']"
    back_button = "//*[@content-desc='Back']"
    # the error line is a view whose a11y name is the app's own sentence
    error = '//*[@content-desc="{message}"]'


class LoginPage(BasePage):
    def wait_here(self):
        self.wait_shown(LoginLocators.username_field)
        return self

    def enter(self, username=None, password=None):
        if username is not None:
            self.send_text(LoginLocators.username_field, username)
        if password is not None:
            self.send_text(LoginLocators.password_field, password)
        return self

    def sign_in(self):
        self.click(LoginLocators.sign_in_button)
        return self

    # an error the app shows is a widget carrying the exact sentence,
    # patience is the full timeout here, a refused login needs a moment
    def error_shown(self, message):
        return self.is_shown(LoginLocators.error.format(message=message))

    def is_still_here(self):
        return self.is_shown(LoginLocators.sign_in_button, seconds=3)

    def is_displayed(self):
        return self.is_shown(LoginLocators.username_field) and self.is_shown(
            LoginLocators.password_field
        )

    # the back arrow pops this screen without touching the session
    # import here, the two pages reference each other
    def leave(self):
        from lib.app.pages.home_page import HomePage, HomeLocators

        self.click(LoginLocators.back_button)
        home = HomePage(self.driver, self.timeout)
        home.wait_shown(HomeLocators.login_button)
        return home
