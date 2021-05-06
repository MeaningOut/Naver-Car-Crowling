#!/usr/bin/env python
# coding: utf-8
from bs4 import BeautifulSoup
import urllib.request as req
import os
import re
from selenium import webdriver
from pandas import DataFrame

imgUrl = 'https://imgauto-phinf.pstatic.net/20200407_83/auto_1586224660124AeA76_PNG/20200407105739_PTJdAJWW.png?type=f152_110'
req.urlretrieve(imgUrl, '자동차.jpg')


# In[294]:


def download_img(img_url, big_title, sub_title):
    dir_name = 'images/' + big_title
    
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        req.urlretrieve(img_url, dir_name + '/' + sub_title + '.jpg')
    except Exception as e:
        print(e)


def get_car_list(car_url, big_title, company, origin, car_type):
    res = req.urlopen(car_url)
    soup = BeautifulSoup(res, 'html.parser')

    cars = []
    limit = 0

    # 라인업 상단
    line_up = soup.select('#container > div.lineup_top > div > div.col_wrap > div.col_contents > div.col')
    for idx, col in enumerate(line_up):
        print(col)
        if col.find('span', {'class': 'blank'}) != None: break
        sub_title = col.find('dt').get_text()

        # 가격
        prices = col.find('dd').get_text().split('~')
        m_type = get_money_type(col.find('dd').get_text())

        if (prices[0] == '가격정보없음'):
            min_price = None
            max_price = None
        elif (len(prices) > 1):  # 최소~최대
            min_price = change_price(prices[0], m_type)
            max_price = change_price(prices[1], m_type)
        else:  # 하나
            min_price = change_price(prices[0], m_type)
            max_price = change_price(prices[0], m_type)

        # 이미지 다운로드
        #download_img(col.img['src'], big_title, sub_title)
        img_src = col.img['src']

        # print(col.img['src'])
        # print(col.find('dt').get_text())
        # print(col.find('dd').get_text())

        cars.append([big_title, sub_title, min_price, max_price, company, origin, car_type, img_src])
        limit += 1

    # 라인업 하단
    # container > div.lineup_btm > div > div.col_wrap > div > div:nth-child(1) > div.btm_col.main_info
    line_down = soup.select('.btm_col.main_info > ul')
    for idx, col in enumerate(line_down):
        info = []
        for li in col.find_all('li'):
            tmp = li.get_text().replace(' ', '').splitlines()
            tmp = [i for i in tmp if i != '']
            full_text = ' '.join(tmp).replace(' ,\xa0', ',').replace(') ', ')\n')
            full_text = full_text.replace('(정보없음)', '').replace('정보없음', '')
            info.append(full_text)

        if (idx < limit):
            # 엔진형식, 과급방식, 배기량, 연료, 연비, 승차인원, 구동방식, 변속기
            cars[idx] += info

    return cars


# In[301]:


def get_car_info(yearsId):
    main_url = "https://auto.naver.com/car/main.nhn?yearsId=" + yearsId
    line_url = "https://auto.naver.com/car/lineup.nhn?yearsId=" + yearsId
    print('line url : ', line_url)

    res = req.urlopen(main_url)
    soup = BeautifulSoup(res, 'html.parser')

    # 모델명, 회사, 원산지, 차종
    big_title = soup.select_one('#container > div.spot_end.new_end > div.info_group > div.end_model > h3').string
    company = soup.select_one('#container > div.spot_end.new_end > div.info_group > span > a.brand').string
    origin = soup.select_one('#container > div.spot_end.new_end > div.info_group > span > a.location').string
    car_type = soup.select_one('#container > div.spot_end.new_end > div.info_group > span > a.weight').string

    cars = get_car_list(line_url, big_title, company, origin, car_type)
    print(cars)
    return cars


# In[302]:


def get_ids(car_url):
    res = req.urlopen(car_url)
    soup = BeautifulSoup(res, 'html.parser')

    value = []

    # yearsId 찾기
    links = soup.select('.model_name')
    for l in links:
        href = l['href']
        tmp = href.find('yearsId=')
        # print(href[tmp:].replace('yearsId=', ''))

        value.append(href[tmp:].replace('yearsId=', ''))

    return value


def change_price(price, m_value):
    value = 0

    # 억 단위
    index = price.find('억')
    if index > 0:
        tmp = price[:index]
        price = price[index + 1:]
        value += 100000000 * int(tmp)

    # 숫자 추출
    price = price.replace(',', '')
    nums = re.findall("\d+", price)[0]
    # print('nums : ', nums)

    price = price.replace(nums, '')
    # print('price', price)
    value += int(nums) * m_value
    # print(value)

    return round(value, 2)

# In[295]:

def get_money_type(price):
    money_type = {'만원': 10000.0, '파운드': 1552.10, '유로': 1347.06, '루피': 14.91, '달러': 1117.52, '엔': 10.35, '호주달러': 863.93}

    m_type = ''
    for i in money_type.keys():
        if i in price:
            m_type = i
            break

    if len(m_type) <= 0:
        m_type = '만원'
    print('money type : ', price, ', ', m_type)

    return money_type[m_type]


# In[345]:
def make_csv(data):
    columns = ['big_title', 'sub_title', 'min_price', 'max_price', 'company', 'origin', 'car_type', 'img_src', 'engine',
               'charger', 'emission', 'fuel', 'fuel_efficiency', 'occupancy', 'drive_type', 'gearshift']

    df = DataFrame(data, columns=columns)
    df.to_csv('naver_import_cars.csv', index=False, mode='w', encoding='utf-8-sig')



driver = webdriver.Chrome(r"C:\Users\jeewo\Downloads\chromedriver_win32\chromedriver.exe"'')
samples = ['경형', '소형', '준중형', '중형', '중대형', '준대형', '대형', '스포츠카']

car_data = []

#driver.get('https://auto.naver.com/car/mainList.nhn')
driver.get('https://auto.naver.com/car/mainList.nhn?importYn=Y')
while True:
    try:
        print(driver.current_url)
        ids = get_ids(driver.current_url)
        for i in ids:
            car_data += get_car_info(i)

        # 다음 버튼 클릭
        if driver.find_elements_by_css_selector('#content > div.paginate2 > a.next'):
            driver.find_element_by_css_selector('#content > div.paginate2 > a.next').click()
        else:
            break
    except Exception as e:
        print('에러 남 : ', e)
        print('에러난 후 current url : ', driver.current_url)
        make_csv(car_data)
        break

driver.close()

# In[346]:
print('에러 안나고 잘 수행됨. ', len(car_data))
make_csv(car_data)
