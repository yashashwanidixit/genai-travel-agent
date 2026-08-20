import os
from typing import Optional, Dict, Any


class AppiumClient:
    """Manages connection and automation session with an Appium server."""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
        self.driver = None

    def start_session(self, capabilities: Dict[str, Any]):
        try:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options()
            options.load_capabilities(capabilities)
            self.driver = webdriver.Remote(command_executor=self.server_url, options=options)
            return self.driver
        except Exception as e:
            # Gracefully handle Appium not running in test/mock environments
            print(f"[AppiumClient] Warning: Could not connect to Appium at {self.server_url}: {e}")
            return None

    def find_element(self, by: str, value: str):
        if self.driver:
            return self.driver.find_element(by=by, value=value)
        return None

    def click(self, by: str, value: str):
        el = self.find_element(by, value)
        if el:
            el.click()
            return True
        return False

    def send_keys(self, by: str, value: str, text: str):
        el = self.find_element(by, value)
        if el:
            el.send_keys(text)
            return True
        return False

    def stop_session(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
