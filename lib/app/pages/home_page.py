from lib.app.base_page import BasePage
from lib.app.pages.login_page import LoginPage


# locators as xpaths on the accessibility attributes uiautomator2 reads,
# this app's widgets carry their a11y name in @content-desc
class HomeLocators:
    login_button = "//*[@content-desc='Login']"
    logout_button = "//*[@content-desc='Logout']"
    # the signed-in label is a widget whose a11y name IS the username
    user_label = "//*[@content-desc='{user}']"
    counter_text = "//*[@content-desc='You have pushed the button this many times:']"


# the counter page, the app's root; login state only changes the app bar
class HomePage(BasePage):
    def wait_here(self):
        # one of the two app bar states proves the home screen is showing
        if not self.is_shown(HomeLocators.login_button, seconds=3):
            self.wait_shown(HomeLocators.logout_button)
        return self

    def is_logged_in(self):
        return self.is_shown(HomeLocators.logout_button)

    def is_signed_out(self):
        return self.is_shown(HomeLocators.login_button)

    def user_shown(self, user):
        return self.is_shown(HomeLocators.user_label.format(user=user))

    def counter_shown(self):
        return self.is_shown(HomeLocators.counter_text)

    def open_login(self):
        self.click(HomeLocators.login_button)
        login = LoginPage(self.driver, self.timeout)
        login.wait_here()
        return login

    def logout(self):
        self.click(HomeLocators.logout_button)
        self.wait_shown(HomeLocators.login_button)
        return self
