import time

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chromedriver_path = "./../chromedriver/chromedriver.exe"
nickname = "@James1114"
message = "Алан - хуйлан"


class TelegramMessageSender:
    def __init__(self):
        self.active_account_name = None
        self.active_accounts_names = []
        self.accounts = {}
        self.driver = None

        self.__parse_accounts_yml()
        self.__set_chromedriver()
        self.__auth_active_account()

    def __parse_accounts_yml(self):
        with open("accounts.yml", "r") as stream:
            self.accounts = yaml.safe_load(stream)["list"]

        active_accounts = list(filter(lambda x: x["status"], self.accounts))
        self.active_accounts_names = list(map(lambda x: x["name"], active_accounts))

        assert len(self.active_accounts_names), "В файле accounts.yml нет хотя бы одного активного аккаунта"

        self.active_account_name = self.active_accounts_names[0]
        print("Установлен активный аккаунт. Имя:", self.active_account_name)

    def __set_next_account_name(self):
        self.active_accounts_names.remove(self.active_account_name)
        assert len(self.active_accounts_names), "Все активные аккаунты закончились"
        self.active_account_name = self.active_accounts_names[0]
        print("Установлен активный аккаунт. Имя:", self.active_account_name)

    def __set_chromedriver(self):
        if (self.driver):
            self.driver.close()
            self.driver = None
        self.driver = webdriver.Chrome(chromedriver_path)
        self.driver.get("https://web.telegram.org/k/")

    def __auth_active_account(self):
        local_storage_path = self.__get_account(self.active_account_name)["tokens"]
        local_storage = open(local_storage_path, "r").readlines()
        local_storage = list(map(lambda x: x.strip().split("\t"), local_storage))

        for key, value in local_storage:
            self.set_in_localstorage(key, value)

        self.driver.refresh()

    def __get_account(self, name):
        account = list(filter(lambda x: x["name"] == name, self.accounts))
        assert len(account), f"Аккаунта с именем {name} не найдено"
        return account[0]

    def send_message(self, nickname, message):
        try:
            self.__send_message(nickname, message)
        except:
            self.__set_next_account_name()
            self.__set_chromedriver()
            self.__auth_active_account()
            self.send_message(nickname, message)

    def __send_message(self, nickname, message):
        self.wait_element(By.CLASS_NAME, "input-search-input")
        search = self.driver.find_element_by_class_name("input-search-input")
        search.send_keys(nickname)

        user = None
        time.sleep(2)
        items = self.driver.find_elements_by_class_name("chatlist-chat")

        for item in items:
            try:
                nick = item.find_element_by_class_name("dialog-subtitle")
                if nick and nick.text == nickname:
                    user = item.find_element_by_class_name("c-ripple")
                    break
            except:
                pass

        if not user:
            return

        user.click()
        self.wait_element(By.CLASS_NAME, "new-message-wrapper")
        self.driver.find_element_by_class_name("input-message-input").send_keys(message)
        time.sleep(0.5)
        self.driver.find_element_by_class_name("btn-send").click()
        time.sleep(0.5)

    def set_in_localstorage(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def wait_element(self, type_, name, timeout=10):
        WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((type_, name)))

    def __del__(self):
        self.driver.close()


sender = TelegramMessageSender()
sender.send_message(nickname, message)