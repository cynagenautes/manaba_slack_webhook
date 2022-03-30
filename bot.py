# macOS Catalinaで検証、Win Linuxでは動作確認してません
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from bs4 import BeautifulSoup
from time import sleep
from slack_sdk.webhook import WebhookClient


user = "YOUR_RAINBOW_ID"
password = "YOUR_RAINBOW_PW"
query = "_query"
survey = "_survey"
report = "_report"

# WebHook関連初期化
webhook_url = "YOUR_WEBHOOK_URL"
webhook = WebhookClient(webhook_url)

# Qiitaとかでよくみられるヘッドレスト起動だとDeprecationWarningがでるのでこのやり方がいいらしい
opts = Options()
# opts.headless = True
driver = webdriver.Firefox(options=opts)

driver.get("https://ct.ritsumei.ac.jp/ct/home_course")

# 立命館のSSOにリダイレクトされるので少々遅延を入れないとサインインできない
sleep(5)

user_box = driver.find_element_by_name("USER")
user_box.send_keys(user)
password_box = driver.find_element_by_name("PASSWORD")
password_box.send_keys(password)
password_box.submit()

# ここも同様に遅延入れたほうが成功率が上がったので入れておく
sleep(3)

course_name_list = []
course_url_list = []
for course in driver.find_elements_by_xpath('//td[@class="course  course-cell"]//a'):
    # <a>が他にもあるけどテキスト含んでないので文字列がある確認だけでOK
    if len(course.text) != 0:
        course_name_list.append(course.text)
        course_url_list.append(course.get_attribute('href'))


def get_elem_date(elem_img):
    date_list = []
    for elem_date in elem_img.find_elements_by_xpath('../../../td[contains(text(), "-")]'):
        if len(elem_date.text) != 0:
            date_list.append(elem_date.text)
    return date_list


def get_elem():
    for elem_img in driver.find_elements_by_xpath('//img[@src="/icon-deadline-on.png"]'):
        for elem_a in elem_img.find_elements_by_xpath('../a'):
            # その場しのぎ感あるけどこれ以上質問用の窓口が生えることはないと思った
            if elem_a.text != '質問専用' and elem_a.text != '質問受付':
                print(course_name + "：", end='')
                print(elem_a.text, end='')
                date_list = get_elem_date(elem_img)
                if len(date_list) != 1:
                    print(" 受付開始：", end='')
                    print(date_list[0], end='')
                    print(" 受付終了：", end='')
                    print(date_list[1])
                else:
                    print(" 受付終了：", end='')
                    print(date_list[0])


def webhook(date_list):
    response = webhook.send(text=date_list)
    assert response.status_code == 200
    assert response.body == "ok"


for(url, course_name) in zip(course_url_list, course_name_list):
    # 遅延入れないと流石にいろいろ多方面に迷惑かけそうなので1秒ずつ遅延入れた
    driver.get(url + query)
    sleep(1)
    get_elem()
    driver.get(url + survey)
    get_elem()
    sleep(1)
    driver.get(url + report)
    get_elem()
    sleep(1)

# 終了処理を書いてあげないとプロセスが大量に残ってメモリ枯渇するのでその処理を入れた
driver.close()
driver.quit()
