import requests
from http import cookiejar
from fake_useragent import UserAgent
import pandas as pd
import json
import os
import time
import random

# 最主要的问题是集中访问会使网站崩溃，想想有什么办法可以解决

# 应对反爬虫机制之一，禁用cookie
# 效果不太好，第一次使用能够后获取完数据，第二次使用只能获取46条数据
class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False

# 使用requests改写后的函数
def getElec(userFj):

    random_sleep(1, 15)
    elec, status = postRequest(userFj)
    print(status)
    
    # # 判断数据获取是否正常，若不正常则加量等待一段时间重新获取
    # # 判断字符串是否相等可以用is或==，get到了
    epoch = 0
    while((status == "数据获取异常") and epoch<5):
        print(epoch, "数据获取异常")
        epoch = epoch+1
        time.sleep(30*epoch)
        elec, status = postRequest(userFj)

    # 等待一段时间后仍未解决异常，则放弃此段查询
    if status is "正常供电":
        raise Exception("The website has been crashed")

    # 当获取数据异常时，执行三次等待，若还不行则认为网站崩溃，发送错误
    return elec

# 发送请求，获取数据
def postRequest(userFj):
    url = "http://www.sdsddk.sdnu.edu.cn/wxapp/pay/queryElectricity"
    data=  {
        "userXq": "长清湖校区",
        "userFj": userFj,
        "payType": 1
    }

    # 伪装User-agent 使用fake_useragent伪装，由于一直被禁止爬取，效果未知
    ua = UserAgent()
    headers = { "User-Agent": ua.chrome}

    s = requests.Session()
    s.cookies.set_policy(BlockAll())
    response = requests.post(url, data=data, headers=headers)

    print(response.text)

    elec = json.loads(response.text)["message"]["plusElec"]
    status = json.loads(response.text)["message"]["status"]

    return elec, status

def main():
    filePath = r"A:\desktop\room.csv"

    df = pd.read_csv(filePath)
    df.drop(axis = 0, index=6, inplace=True)
    
    # 输入楼号与房间号，转化为userFj所需要的输入形式
    id_rooms = []
    for i, j in zip(df.iloc[:,0].values, df.iloc[:,1].values):
        building_num = '{:0>2d}'.format(int(i))
        s = '{:0>4d}'.format(int(j))
        l = list(s)
        l.insert(2,'0')
        floor_num = ''.join(l)
        id_rooms.append(building_num+floor_num)

    # 获取空调电费
    elec_list = []
    for roomid in id_rooms:
        elec = getElec(roomid)
        elec_list.append([roomid, elec])
        # print(elec)

    pd.DataFrame(elec_list).to_csv(os.path.join(filePath,"..", "elec1.csv"),index=False)

# 转化楼号与房间号的格式为接口的输入模式，即16#301->1603001
def transform(building, room):
    building_num = '{:0>2d}'.format(int(building))
    s = '{:0>4d}'.format(int(room))
    l = list(s)
    l.insert(2,'0')
    floor_num = ''.join(l)
    return building_num+floor_num

# 用于降低访问频率，以1/10的概率进行长睡眠, 9/10的概率进行短睡眠
def random_sleep(short_time, long_time):
    if random.randint(0,10)==0 :
        print('-'*10,"sleep 10s", '-'*10)
        time.sleep(long_time)
    else:
        time.sleep(short_time)

if __name__ == '__main__':
    main()