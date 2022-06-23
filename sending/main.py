# -*- coding: cp1251 -*-
import random
import time
import re
import glob

import yaml
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from names import get_name

chromedriver_path = "./../chromedriver/chromedriver.exe"
people_ids_path = "people.txt"
used_people_ids_path = "used_people.txt"
group_id = open("group_id.txt", "r").read().strip()


class Messenger:
    def __init__(self):
        self.current_message_index_filename = "current_message_index.txt"
        self.current_message_with_name_index_filename = "current_message_with_name_index.txt"
        self.current_message_index = 0
        self.current_message_with_name_index = 0

    def get_index(self, filename):
        try:
            return int(open(filename, 'r').read())
        except:
            file = open(filename, 'w')
            file.write("0")
            file.close()
            return 0

    def get_message(self):
        try:
            file = glob.glob('./messages/*')[self.current_message_index_filename]
            message = open(file, 'r', encoding="utf8").read()
            self.current_message_index_filename += 1
            return message
        except:
            if self.current_message_index_filename == 0:
                raise Exception("Нет сообщений в папке")

            self.current_message_index_filename = 0
            return self.get_message()

    def get_message_with_name(self):
        try:
            file = glob.glob('./messages_with_names/*')[self.current_message_with_name_index_filename]
            message = open(file, 'r', encoding="utf8").read()
            self.current_message_with_name_index_filename += 1
            return message
        except:
            if self.current_message_with_name_index_filename == 0:
                raise Exception("Нет сообщений в папке")

            self.current_message_with_name_index_filename = 0
            return self.get_message_with_name()


class MessagerPlus(Messenger):
    def __init__(self):
        super(MessagerPlus, self).__init__()

    def handler(self, text):
        map_ = {
            "а": "a",
            "В": "B",
            "с": "c",
            "С": "C",
            "Е": "E",
            "е": "e",
            "К": "K",
            "М": "M",
            "Н": "H",
            "О": "O",
            "о": "o",
            "Р": "P",
            "р": "p",
            "Т": "T",
            "у": "y",
            "Х": "X",
            "х": "x",
        }
        keys = map_.keys()
        text = list(text)
        for i in range(len(text)):
            if text[i] in keys:
                if random.random() > 0.5:
                    text[i] = map_[text[i]]
        return "".join(text)

    def get_message(self):
        return self.handler(super(MessagerPlus, self).get_message())

    def get_message_with_name(self):
        return self.handler(super(MessagerPlus, self).get_message_with_name())



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
        self.messenger = MessagerPlus()

        self.__parse_accounts_yml()
        self.__set_chromedriver()

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

        active_account = self.__get_active_account()
        profile_path = active_account["profile_path"]
        profile_name = profile_path.split("/")[-1]
        profile_dir = "/".join(profile_path.split("/")[:-1])

        print(f"profile_name = '{profile_name}'")
        print(f"profile_dir ='{profile_dir}'")

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        self.driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
        self.driver.set_window_position(400, 1500)
        self.driver.maximize_window()
        self.driver.get("https://web.telegram.org/k/")

    def __get_active_account(self):
        return self.__get_account(self.active_account_name)

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
        if self.is_message_sended():
            return

        time.sleep(0.2)
        message = self.get_message()
        self.put_text_to_input(message)
        time.sleep(0.5)
        self.driver.find_elements_by_class_name("btn-send")[1].click()
        time.sleep(1)
        self.check_message()

    def put_text_to_input(self, message):
        for part in message.split("\n"):
            self.driver.find_elements_by_class_name("input-message-input")[2].send_keys(part)
            ActionChains(self.driver)\
                .key_down(Keys.SHIFT)\
                .key_down(Keys.ENTER)\
                .key_up(Keys.SHIFT)\
                .key_up(Keys.ENTER)\
                .perform()

    def get_message(self):
        user_name = self.driver.find_elements_by_class_name("chat-info")[1].find_element_by_class_name("user-title").text
        rus_user_name = get_name(user_name)
        return self.messenger.get_message_with_name().format(name=rus_user_name) if rus_user_name else self.messenger.get_message()

    def is_message_sended(self):
        chat = self.driver.find_elements_by_class_name("bubbles-inner")[1]
        message = chat.find_elements_by_class_name("inner")
        return len(message)

    def check_message(self, retry=3):
        chat = self.driver.find_elements_by_class_name("bubbles-inner")[1]
        message = chat.find_elements_by_class_name("inner")[-1]
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

    def __run(self):
        time.sleep(10)
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
        while True:
            groups = self.driver.find_elements_by_class_name("chatlist-chat")
            for group in groups:
                if group_id == group.get_attribute("data-peer-id"):
                    self.scroll_to_element(group)
                    group.click()
                    return
            self.scroll_to_element(groups[-1])
            time.sleep(0.5)

    def open_chat_info(self):
        time.sleep(0.2)
        self.driver.find_element_by_class_name("chat-info").click()

    def get_next_people_ids(self):
        self.open_group()
        time.sleep(2)
        self.open_chat_info()
        time.sleep(2)

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

            self.scroll_to_element(self.get_current_people()[-1])
            time.sleep(0.3)

    def get_current_people(self):
        users_list = self.driver.find_element_by_class_name("search-super-content-members")
        return users_list.find_elements_by_class_name("chatlist-chat")

    def get_current_people_ids(self):
        return self.get_ids(self.driver.find_element_by_class_name("search-super-content-members"))

    def open_chat(self, user_id):
        people = self.driver.find_element_by_class_name("search-super-content-members")
        user_item = people.find_elements_by_class_name("chatlist-chat")[0]
        self.set_attribute(user_item, "data-peer-id", user_id)
        self.scroll_to_element(user_item)
        user_item.click()

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
