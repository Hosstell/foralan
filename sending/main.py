import time
import re

import yaml
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

chromedriver_path = "./../chromedriver/chromedriver.exe"
people_ids_path = "people.txt"
used_people_ids_path = "used_people.txt"
message = open("message.txt", "r", encoding="utf8").read()
group_id = open("group_id.txt", "r").read().strip()


class BanException(Exception):
    pass


class TelegramMessageSender:
    def __init__(self):
        self.active_account_name = None
        self.active_accounts_names = []
        self.accounts = {}
        self.driver = None
        self.active_chat_index = 0
        self.used_people_ids = []
        self.people_ids = open(people_ids_path, 'r').read().split("\n")
        self.people_load_status = [False for _ in range(len(self.people_ids))]

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
        if not len(self.active_accounts_names):
            self.driver.close()
            raise BanException("Все активные аккаунты закончились")
        self.active_account_name = self.active_accounts_names[0]
        print("Установлен активный аккаунт. Имя:", self.active_account_name)

    def __set_chromedriver(self):
        if (self.driver):
            self.driver.close()
            self.driver = None
        self.driver = webdriver.Chrome(chromedriver_path)
        self.driver.set_window_position(400, 1500)
        self.driver.maximize_window()
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

    def update_used_people(self):
        self.used_people_ids = open(used_people_ids_path, "r").read().split("\n")

    def is_people_id_used(self, people_id):
        return people_id in self.used_people_ids

    def save_in_store(self, people_id):
        used_people_ids = open(used_people_ids_path, "r").read().split("\n")
        used_people_ids.append(people_id)
        used_people_ids = list(set(used_people_ids))

        file = open(used_people_ids_path, 'w')
        file.write("\n".join(used_people_ids))
        file.close()

        self.update_used_people()

    def send_message(self, user_id):
        time.sleep(0.2)
        self.driver.find_elements_by_class_name("input-message-input")[2].send_keys(message)
        time.sleep(0.5)
        self.driver.find_elements_by_class_name("btn-send")[1].click()
        time.sleep(1)
        self.check_message()

    def check_message(self, retry=3):
        chat = self.driver.find_elements_by_class_name("bubbles-inner")[1]
        message = chat.find_element_by_class_name("inner")
        script = "return window.getComputedStyle(arguments[0], '::after').getPropertyValue('content')"
        icon = self.driver.execute_script(script, message).strip()
        if icon == '"\ue99a"':
            if retry > 0:
                time.sleep(1)
                self.check_message(retry=retry-1)
            else:
                raise BanException()

    def set_in_localstorage(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def wait_element(self, type_, name, timeout=10):
        WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((type_, name)))

    def __del__(self):
        self.driver.close()

    def get_people(self):
        people = self.driver.find_element_by_class_name("search-super-content-members")
        return people.find_elements_by_class_name("chatlist-chat")

    def run(self):
        while True:
            try:
                self.__run()
            except Exception as ex:
                self.__set_next_account_name()
                self.__set_chromedriver()
                self.__auth_active_account()

    def __run(self):
        time.sleep(5)
        self.open_group()
        time.sleep(2)
        self.open_chat_info()
        time.sleep(2)

        for user_id in self.get_next_people_ids():
            if not self.is_people_id_used(user_id):
                try:
                    self.open_group()
                    self.open_chat_info()
                    self.open_chat(user_id)
                    self.send_message(user_id)
                    self.save_in_store(user_id)
                except BanException as ex:
                    raise Exception("Ban")
                except Exception as e:
                    print("Ошибка отправки сообщения. user id = ", user_id)
                    print("Ошибка: ", e)
                    print("\n\n")
            else:
                print("Пользователю уже было отправлено сообщение. user id = ", user_id)

        print("Всё!")

    def open_group(self):
        groups = self.driver.find_elements_by_class_name("chatlist-chat")
        for group in groups:
            if group_id == group.get_attribute("data-peer-id"):
                group.click()
                break

    def open_chat_info(self):
        time.sleep(0.2)
        self.driver.find_element_by_class_name("chat-info").click()

    def get_next_people_ids(self):
        people_ids = []
        last_counts = []
        while True:
            ids = self.get_current_people_ids()
            ids = list(set(ids).difference(set(self.used_people_ids)))
            people_ids.extend(ids)
            if len(people_ids) > 200:
                return people_ids

            last_counts.append(len(people_ids))

            if len(last_counts) > 2 and last_counts[-1] == 0 and last_counts[-2] == 0 and last_counts[-3] == 0:
                raise Exception("Не осталось больше пользователей кому можно отправить сообщение")

            if len(last_counts) > 2 and last_counts[-1] == last_counts[-2] and last_counts[-2] == last_counts[-3]:
                return people_ids

    def get_current_people_ids(self):
        users_list = self.driver.find_element_by_class_name("search-super-content-members")
        return self.get_ids(users_list)

    def open_chat(self, user_id):
        people = self.driver.find_element_by_class_name("search-super-content-members")
        user_item = people.find_elements_by_class_name("chatlist-chat")[0]
        self.set_attribute(user_item, "data-peer-id", user_id)
        self.scroll_to_element(user_item)
        user_item.click()

    def load_user(self, user_id):
        index = self.people_ids.index(user_id)
        if self.people_load_status[index]:
            return

        users_count = []
        while True:
            users_list = self.driver.find_element_by_class_name("search-super-content-members")
            ids = self.get_ids(users_list)
            for id_ in ids:
                if id_ in self.people_ids:
                    index = self.people_ids.index(id_)
                    self.people_load_status[index] = True

            index = self.people_ids.index(user_id)
            if self.people_load_status[index]:
                return

            users = users_list.find_elements_by_class_name("chatlist-chat")
            users_count.append(len(users))

            if len(users_count) >= 3 and users_count[-1] == users_count[-2] and users_count[-2] == users_count[-3]:
                raise Exception("Пользователя нет в списке участников группы. user id = ", user_id)

            self.scroll_to_element(users[-1])
            time.sleep(1)

    def clone_element(self, element, into=None):
        if into:
            self.driver.execute_script("""
                var element = arguments[0];
                var into = arguments[1];
                var clone = element.cloneNode(true);
                into.appendChild(clone)
            """, element, into)
        else:
            self.driver.execute_script("""
                var element = arguments[0];
                var clone = element.cloneNode(true);
                document.body.appendChild(clone)
            """, element)

    def set_attribute(self, item, name, value):
        self.driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2])", item, name, value)

    def get_ids(self, element):
        html = element.get_attribute("innerHTML")
        ids = re.findall('data-peer-id="\d+"', html)
        ids = [re.search("\d+", id_).group() for id_ in ids]
        return ids

    def scroll_to_element(self, element):
        ActionChains(self.driver).move_to_element(element).perform()

    def remove_element(self, element):
        self.driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
        """, element)


sender = TelegramMessageSender()
sender.run()
