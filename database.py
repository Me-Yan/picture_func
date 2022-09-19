#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import traceback


class Database:

    flag = False

    def __init__(self):

        self.host = "xxxxx"
        self.user = "xxxxx"
        self.password = "xxx"
        self.database = "xxxx"
        self.port = 0000
        self.db = None

    def create_db_connection(self):

        if not Database.flag:
            self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database, port=self.port)
            Database.flag = True

        return self.db

    def execute_sql(self, sql):

        db = self.create_db_connection()

        cursor = db.cursor()

        try:
            cursor.execute(sql)
            db.commit()
        except Exception:
            db.rollback()
            print(traceback.print_exc())
            print("-------执行sql失败。。。%s" % (sql))

        # db.close()

    def select_user(self, sql):

        db = self.create_db_connection()

        cursor = db.cursor()

        user_list = []

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            for user in results:
                temp = {
                    "uid": "%s" % user[3],
                    "phone": "%s" % user[5],
                    "password": "%s" % user[6],
                    "realname": "%s" % user[7],
                    "bankno": "%s" % user[8],
                    "bank": "%s" % user[9]
                }

                user_list.append(temp)

        except Exception:
            db.rollback()
            print(traceback.print_exc())
            print("-------执行sql失败。。。%s" % (sql))

        # db.close()

        return user_list

