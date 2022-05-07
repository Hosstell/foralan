import time
import re

import yaml
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chromedriver_path = "./../chromedriver/chromedriver.exe"
group_id = open("group_id.txt", "r").read()


class TelegramMessageSender:
    def __init__(self):
        self.active_account_name = None
        self.active_accounts_names = []
        self.accounts = {}
        self.driver = None
        self.active_chat_index = 0

        self.__set_chromedriver()
        self.__auth_active_account()

    def __set_chromedriver(self):
        if (self.driver):
            self.driver.close()
            self.driver = None
        self.driver = webdriver.Chrome(chromedriver_path)
        self.driver.set_window_position(400, 1500)
        self.driver.maximize_window()
        self.driver.get("https://web.telegram.org/k/")

    def __auth_active_account(self):
        local_storage = open("account.txt", "r").readlines()
        local_storage = list(map(lambda x: x.strip().split("\t"), local_storage))

        for key, value in local_storage:
            self.set_in_localstorage(key, value)

        self.driver.refresh()

    def __get_account(self, name):
        account = list(filter(lambda x: x["name"] == name, self.accounts))
        assert len(account), f"Аккаунта с именем {name} не найдено"
        return account[0]

    # system methods
    def __set_next_account_name(self):
        self.active_accounts_names.remove(self.active_account_name)
        assert len(self.active_accounts_names), "Все активные аккаунты закончились"
        self.active_account_name = self.active_accounts_names[0]
        print("Установлен активный аккаунт. Имя:", self.active_account_name)

    def set_in_localstorage(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def wait_element(self, type_, name, timeout=10):
        WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((type_, name)))

    def __del__(self):
        self.driver.close()

    def get_people(self):
        people = self.driver.find_element_by_class_name("search-super-content-members")
        return people.find_elements_by_class_name("chatlist-chat")

    # entry point
    def run(self):
        time.sleep(5)
        self.open_group()
        self.parse_group_users()
        print("Я кончил")

    def parse_group_users(self):
        time.sleep(5)
        self.driver.find_element_by_class_name("chat-info").click()
        time.sleep(1)

        count = 1000

        ids_history = []
        while True:
            time.sleep(2)
            users_list = self.driver.find_element_by_class_name("search-super-content-members")
            people = users_list.find_elements_by_class_name("chatlist-chat")

            print(f"В телешрамме загружано {len(people)} пользователей")
            ids_history.append(len(people))
            if len(people) > count:
                ids = self.get_ids(users_list)
                self.save_in_store(ids)
                count += 1000

            if len(ids_history) >= 3 and ids_history[-1] == ids_history[-2] and ids_history[-2] == ids_history[-3]:
                ids = self.get_ids(users_list)
                self.save_in_store(ids)
                break

            self.scroll_to_element(people[-1])

    def save_in_store(self, new_ids):
        ids = open("people.txt", "r").readlines()
        ids = list(map(lambda x: x.strip(), ids))
        ids.extend(new_ids)
        ids = list(set(ids))

        file = open("people.txt", 'w')
        file.write("\n".join(ids))
        file.close()

        print(f"Я сохранил {len(ids)} ids в файле people.txt")

    def scroll_to_element(self, element):
        ActionChains(self.driver).move_to_element(element).perform()

    def open_group(self):
        groups = self.driver.find_elements_by_class_name("chatlist-chat")
        for group in groups:
            if group_id == group.get_attribute("data-peer-id"):
                group.click()
                break

    def get_ids(self, element):
        html = element.get_attribute("innerHTML")
        ids = re.findall('data-peer-id="\d+"', html)
        ids = [re.search("\d+", id_).group() for id_ in ids]
        return ids

sender = TelegramMessageSender()
sender.run()
