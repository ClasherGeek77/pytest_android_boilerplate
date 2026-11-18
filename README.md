# pytest_android_boilerplate

## what it is

a starter project for Android app tests with Python, pytest and Appium 2 (UiAutomator2 driver). it ships with 10 working tests against a small Flutter demo app (login errors, login, logout, home screen) running on an Android emulator, so you can run a real mobile suite and then copy the structure for your own app.

- the app under test is downloaded for you by `./fetch_app.sh` (no Flutter, no compiling): https://github.com/ClasherGeek77/mobile_app_mock/releases/tag/v1.0.0
- locators are plain xpaths on `content-desc`, kept in `Locators` classes inside the page files
- one Appium session per run, an automatic reset before every test
- the session fixtures start what is missing: the Appium server and the emulator

source: https://github.com/ClasherGeek77/pytest_android_boilerplate

## when to use it

use it when you want to learn or start an Android suite in Python with a clean layout (fixtures, page objects, constants, reports).

not for:

- iOS: use https://github.com/ClasherGeek77/pytest_ios_boilerplate (same tests, same layout)
- the same tests in Katalon Studio: use https://github.com/ClasherGeek77/katalon_android_boilerplate
- browser tests: https://github.com/ClasherGeek77/pytest_web_boilerplate; api tests: https://github.com/ClasherGeek77/pytest_api_boilerplate
- real devices, parallel sessions, docker, ci: left out on purpose, this repo is the simple one-emulator version

## what you need

| thing | version | where |
|---|---|---|
| Python | 3.11 (the line in `.python-version`, 3.11.14; `first_setup.sh` refuses other lines) | https://www.python.org/downloads/ |
| Node.js | 18 or newer (Appium 2.11.5 declares `^14.17 || ^16.13 || >=18` and npm 8+; Node 22 was used) | https://nodejs.org/ |
| Appium | 2.11.5 | `npm install -g appium@2.11.5` |
| Appium driver | uiautomator2 4.2.9 | `appium driver install uiautomator2@4.2.9` |
| Android SDK | platform-tools (adb), emulator, `platforms;android-28`, `system-images;android-28;google_apis;x86_64` | https://developer.android.com/studio (command line tools are enough) |
| an AVD | named `android9` (Android 9, x86_64) | see "create the AVD" |
| JDK | a JDK on the machine for the Appium server environment; JDK 8 (`JAVA_HOME_8`) is what this suite was run with | https://adoptium.net/ |
| git, bash, curl | any | Mac and Linux |

the x86_64 image needs an Intel or AMD computer with hardware acceleration (HAXM / Hypervisor framework on macOS, KVM on Linux). on Apple silicon you would need an arm64 image and a matching AVD: not verified here. python packages (Appium-Python-Client 3.1.1, selenium 4.52.0, pytest 7.4.4, pytest-html, requests, black, bandit, pylint) are pinned in `requirements.pip`.

### install Appium 2 and the driver

```bash
npm install -g appium@2.11.5
appium driver install uiautomator2@4.2.9
appium driver list --installed
```

you should see `uiautomator2@4.2.9 [installed (npm)]`. check the server: `appium --version` prints `2.11.5`.

### create the AVD

the suite boots an emulator by the name in `AVD_NAME` (default `android9`) when no device is attached. create it once with the SDK command line tools (paths assume the SDK's `cmdline-tools/latest/bin` and `platform-tools` are on your PATH):

```bash
sdkmanager "platform-tools" "emulator" "platforms;android-28" "system-images;android-28;google_apis;x86_64"
echo no | avdmanager create avd -n android9 -k "system-images;android-28;google_apis;x86_64"
emulator -list-avds
```

you should see `android9`. you can also create it in Android Studio (Device Manager, any phone profile, system image Android 9 / API 28, Google APIs, x86_64) and name it `android9`. a small screen and about 1.5 GB of RAM are enough: the suite starts the emulator with `-memory 1536`. any other AVD name works if you set `AVD_NAME` in `test.env`.

## quick start

```bash
git clone https://github.com/ClasherGeek77/pytest_android_boilerplate.git
cd pytest_android_boilerplate
./first_setup.sh
```

`first_setup.sh` builds `.venv`, installs `requirements.pip` and runs `./fetch_app.sh`, which downloads into `apps/` (git-ignored) and checks against the release `SHA256SUMS.txt`:

- `ted_mobile_app_test-v1.0.0-debug.apk` (the app, package `com.ted.ted_mobile_app_test`)
- `a11y-enabler.apk` (the accessibility helper, see below)

you should see `ok  ted_mobile_app_test-v1.0.0-debug.apk`, `ok  a11y-enabler.apk`, `app ready in apps/`, then `Setup done, next run ./run_test.sh`. `APP_VERSION=<tag> ./fetch_app.sh` picks another release tag.

check what exists without a device:

```bash
.venv/bin/python -m pytest --collect-only -q
```

you should see `10 tests collected` (login errors 7, session 3).

then run one test (this boots the emulator if none is running, about 90 seconds on a cold boot):

```bash
./run_test.sh tests/test_login_errors.py::test_opening_login_shows_the_form
```

you should see the log lines `starting the appium server` (if none answers), `booting the android9 emulator` (if none is attached), `installing the accessibility enabler`, then `1 passed`. the HTML report is `reports/report_<timestamp>_<test path>.html`. the whole suite:

```bash
./run_test.sh
```

ends in `10 passed`. the emulator is left running afterwards, close it with `adb emu kill`. these runs were not repeated while writing this README (collection was).

## run one test, or a few

`run_test.sh` takes any pytest argument; an argument replaces the default `TEST_PATH="tests/"` at the top of the script. the variants:

```bash
./run_test.sh tests/test_login_errors.py                                        # one file
./run_test.sh tests/test_login_errors.py::test_opening_login_shows_the_form     # one test
./run_test.sh "tests/test_login_errors.py::test_refused_logins_show_their_own_error[locked-out]"   # one row of a table test
./run_test.sh tests/ -k locked                                                  # names containing "locked"
./run_test.sh tests/ -x                                                         # stop at the first failure
```

edit `TEST_PATH` or `REPORT_NAME` (for example `smoke.html`) at the top of `run_test.sh` to change the defaults. `./checks.sh` runs bandit, black and pylint.

## settings

plain `KEY=value` lines in `test.env`, loaded by `run_test.sh`; the tests read them through `lib/constants.py`.

| key | default | meaning |
|---|---|---|
| `SERVER_URL` | `http://127.0.0.1:4723` | the Appium server. if nothing answers on `/status` the session starts `appium` on that port and stops it after the run |
| `APP_PACKAGE`, `APP_ACTIVITY` | `com.ted.ted_mobile_app_test`, `com.ted.ted_mobile_app_test.MainActivity` | the app under test |
| `AVD_NAME` | `android9` | the AVD to boot when no device is attached |
| `UI_TIMEOUT` | `20` | seconds a normal wait accepts |
| `NEW_COMMAND_TIMEOUT` | `300` | Appium session idle timeout |
| `ANDROID_HOME_DIR` | `~/Library/Android/sdk` (the macOS location) | your SDK folder; set it on Linux, usually `~/Android/Sdk` |
| `JAVA_HOME_8` | a macOS JDK 8 path under `~/Library/Java` | set to your JDK home; given to the Appium server the suite starts |
| `APPIUM_BIN` | `appium` from PATH, else `~/.local/bin/appium` | path of the Appium executable |
| `ENABLER_APK`, `ENABLER_ID` | `apps/a11y-enabler.apk`, `net.ted.a11yenabler/.Enabler` | the accessibility helper |
| `APK_TO_INSTALL` | `apps/ted_mobile_app_test-v1.0.0-debug.apk` | installed when the emulator does not have the app yet |

lines starting with `#` in `test.env` are commented out; uncomment and edit the ones you need. if you start Appium yourself instead, export `ANDROID_HOME` (your SDK folder) and `JAVA_HOME` first, then run `appium`.

## why there is an accessibility enabler app

Flutter draws its whole screen into one view, so the UiAutomator hierarchy that Appium reads is empty until an Android accessibility service is running on the device. `a11y-enabler.apk` (package `net.ted.a11yenabler`) is a tiny accessibility service that does nothing but exist; with it enabled, Flutter publishes its widget tree (`content-desc` nodes) and xpath locators work. the `a11y_enabler` session fixture in `conftest.py` installs it, switches it on through `adb shell settings put secure enabled_accessibility_services`, and restarts the app so Flutter starts while the service is running. a native Android app does not need it. its source is in the https://github.com/ClasherGeek77/mobile_app_mock repo under `tools/a11y-enabler`.

one more thing specific to Flutter: its text fields refuse UiAutomator's `setText` and the emulator has no keyboard connected, so `BasePage.send_text` tries `send_keys` first and on refusal long-presses the field, sets the clipboard and taps `Paste` (this needs the `appium:allowInsecure=["clipboard"]` capability, already set in `conftest.py`). a native app's fields take the fast `send_keys` path.

## how to read the code

```
conftest.py                    fixtures: appium_server, emulator, a11y_enabler, driver, home_page, login_page, signed_out (autouse), testdata, assertion, logger
lib/constants.py               environment_data (from test.env) and constant_data (the app's own error sentences, users, password)
lib/assertion.py               the only place with a bare `assert`; every check is logged
lib/app/base_page.py           BasePage: click, send_text (+ paste fallback), wait_shown, is_shown; xpaths only
lib/app/pages/home_page.py     HomePage and HomeLocators (Login / Logout buttons, user label, counter)
lib/app/pages/login_page.py    LoginPage and LoginLocators (fields, Sign In, Back, error line)
tests/test_login_errors.py     form shown, refused logins as one table, still on the login screen
tests/test_session.py          login shows the user, logout, counter page is home
apps/                          downloaded app and enabler (git-ignored)
```

the fixture chain: `appium_server` -> `emulator` -> `a11y_enabler` -> `driver` (one session for the whole run, `forceAppLaunch` restarts the app). `signed_out` runs before every test: it closes a login screen left open (Back) and logs out if logged in, so tests do not depend on each other. a test asks for `signed_out` (it returns the `HomePage`) and `testdata` and `assertion`.

locators: `@content-desc` carries every widget's accessibility name (`Login`, `Sign In`, `Logout`, the exact error sentences). the two text fields have no name, so they are addressed by position:

```python
class LoginLocators:
    username_field = "(//android.widget.EditText)[1]"
    sign_in_button = "//*[@content-desc='Sign In']"
    error = '//*[@content-desc="{message}"]'
```

## how to add a test

example: after logging in, the app bar shows the user name (this is `test_logging_in_shows_the_user_in_the_app_bar`).

1. value: add anything static to `constant_data` in `lib/constants.py` and expose it in `TestData` in `conftest.py` (copy a line, `self.x = constant_data["x"]`). users, password and the error sentences are already there.
2. locator: add the xpath to the page's `Locators` class, e.g. `HomeLocators` in `lib/app/pages/home_page.py` (`user_label = "//*[@content-desc='{user}']"` is already there).
3. action: add a method on the page class that uses the `BasePage` verbs (`click`, `send_text`, `wait_shown`, `is_shown`). see `user_shown` in `home_page.py`:

```python
def user_shown(self, user):
    return self.is_shown(HomeLocators.user_label.format(user=user))
```

4. test: add a function in `tests/test_session.py` (or a new `tests/test_<area>.py`), asking for the fixtures it needs:

```python
def test_logging_in_shows_the_user_in_the_app_bar(signed_out, testdata, assertion):
    login = signed_out.open_login()

    login.enter(username=testdata.standard_user, password=testdata.password).sign_in()

    assertion.assert_true(
        actual_result=signed_out.is_logged_in(), label="logged in after sign in"
    )
    assertion.assert_true(
        actual_result=signed_out.user_shown(testdata.standard_user),
        label="user label shows the name",
    )
```

   several refusals of one rule go in one `@pytest.mark.parametrize` table, see `test_refused_logins_show_their_own_error` in `tests/test_login_errors.py`.
5. run just that test, then the checks:

```bash
./run_test.sh tests/test_session.py::test_logging_in_shows_the_user_in_the_app_bar
./checks.sh
```

a new screen means a new file in `lib/app/pages/` (copy `login_page.py`).

## if it breaks

| symptom | cause | fix |
|---|---|---|
| `no python 3.11 found` | `first_setup.sh` needs the Python 3.11 line | install it, or `TEST_PYTHON=/path/to/python3.11 ./first_setup.sh` |
| `checksum mismatch for apps/...` or a failed download | interrupted download, no internet | run `./fetch_app.sh` again (it deleted the bad file) |
| `the appium server did not answer within 30 seconds` | `appium` not found, or its env is wrong | `appium --version`; set `APPIUM_BIN`, `ANDROID_HOME_DIR`, `JAVA_HOME_8` in `test.env` |
| `the emulator did not boot within 180 seconds` | no AVD with that name, no acceleration, or too little RAM | `emulator -list-avds` must show `AVD_NAME`; boot it by hand once and see the error |
| `the accessibility enabler is not installed and ... is missing` | `apps/` is empty | run `./fetch_app.sh` |
| every find times out, hierarchy looks empty | the enabler is not enabled, or the app started before it | `adb shell settings get secure enabled_accessibility_services` must contain `net.ted.a11yenabler/.Enabler`; re-run so the fixture restarts the app |
| `paste toolbar did not open` | long press did not register on that boot | re-run that one test; if it repeats, reboot the emulator |
| `Could not find a connected Android device` or an adb error from Appium | adb not reachable by the server | set `ANDROID_HOME_DIR`; `adb devices` must list `emulator-5554` |
| weird failures after you ran `adb shell uiautomator dump` during a session | a manual dump collides with the session's UiAutomation | do not mix them; reboot the emulator |

debugging many failures: reproduce one failing interaction as a small standalone snippet, fix it, re-run only that test, and run the whole suite last. a full run costs minutes.

## next

- the iOS twin: https://github.com/ClasherGeek77/pytest_ios_boilerplate
- the app under test and its releases: https://github.com/ClasherGeek77/mobile_app_mock
- the same app in Katalon Studio: https://github.com/ClasherGeek77/katalon_android_boilerplate
- the same layout for api and web: https://github.com/ClasherGeek77/pytest_api_boilerplate and https://github.com/ClasherGeek77/pytest_web_boilerplate
