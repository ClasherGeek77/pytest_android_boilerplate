import os
import shutil

_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# dynamic, changes between runs or environments
environment_data = {
    "server_url": os.environ.get("SERVER_URL", "http://127.0.0.1:4723"),
    "app_package": os.environ.get("APP_PACKAGE", "com.ted.ted_mobile_app_test"),
    "app_activity": os.environ.get(
        "APP_ACTIVITY", "com.ted.ted_mobile_app_test.MainActivity"
    ),
    "avd_name": os.environ.get("AVD_NAME", "android9"),
    "ui_timeout": int(os.environ.get("UI_TIMEOUT", "20")),
    "new_command_timeout": int(os.environ.get("NEW_COMMAND_TIMEOUT", "300")),
    # the appium server needs the android sdk and an old jdk in its env
    "android_home": os.environ.get(
        "ANDROID_HOME_DIR", os.path.expanduser("~/Library/Android/sdk")
    ),
    "java_home_8": os.environ.get(
        "JAVA_HOME_8", os.path.expanduser("~/Library/Java/jdk8u512-b09/Contents/Home")
    ),
    # only needed when the appium server answers nothing, see README
    "appium_bin": os.environ.get(
        "APPIUM_BIN",
        shutil.which("appium") or os.path.expanduser("~/.local/bin/appium"),
    ),
    "adb": os.path.join(
        os.environ.get("ANDROID_HOME_DIR", os.path.expanduser("~/Library/Android/sdk")),
        "platform-tools",
        "adb",
    ),
    "emulator": os.path.join(
        os.environ.get("ANDROID_HOME_DIR", os.path.expanduser("~/Library/Android/sdk")),
        "emulator",
        "emulator",
    ),
    # the accessibility enabler, see README "why an enabler apk"
    "enabler_apk": os.path.abspath(
        os.path.join(
            _project_dir,
            os.environ.get("ENABLER_APK", "apps/a11y-enabler.apk"),
        )
    ),
    "enabler_id": os.environ.get("ENABLER_ID", "net.ted.a11yenabler/.Enabler"),
    # the app is installed from here when the emulator does not have it yet
    "apk_to_install": os.path.abspath(
        os.path.join(
            _project_dir,
            os.environ.get(
                "APK_TO_INSTALL", "apps/ted_mobile_app_test-v1.0.0-debug.apk"
            ),
        )
    ),
}

# static, never changes between runs or environments
# what the app itself says: the sentences in constant_data are test data,
# the xpaths that use them live in the page files
constant_data = {
    "error_username_required": "Epic sadface: Username is required",
    "error_password_required": "Epic sadface: Password is required",
    "error_locked_out": "Epic sadface: Sorry, this user has been locked out.",
    "error_no_match": (
        "Epic sadface: Username and password do not match any user in this service"
    ),
    "password": "secret_sauce",
    "standard_user": "standard_user",
    "locked_out_user": "locked_out_user",
    "wrong_password": "not_the_real_password",
    "unknown_user": "nobody_at_all",
}
