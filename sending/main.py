import time

from selenium import webdriver

nickname = "@James1114"
message = "Алан - хуйлан"


driver = webdriver.Chrome("../chromedriver.exe")
driver.get("https://web.telegram.org/k/")


def set(key, value):
    driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)


def send_message(nickname_, message):
    time.sleep(3)
    search = driver.find_element_by_class_name("input-search-input")
    search.send_keys(nickname_)
    time.sleep(3)

    user = None
    items = driver.find_elements_by_class_name("chatlist-chat")

    for item in items:
        try:
            nick = item.find_element_by_class_name("dialog-subtitle")
            if nick and nick.text == nickname_:
                user = item.find_element_by_class_name("c-ripple")
                break
        except:
            pass

    if not user:
        return

    user.click()
    time.sleep(2)
    driver.find_element_by_class_name("input-message-input").send_keys(message)
    time.sleep(0.5)
    driver.find_element_by_class_name("btn-send").click()


local_storage = open("local_storage.txt", "r").readlines()
local_storage = list(map(lambda x: x.strip().split("\t"), local_storage))

for key, value in local_storage:
    set(key, value)

driver.refresh()


send_message(nickname, message)