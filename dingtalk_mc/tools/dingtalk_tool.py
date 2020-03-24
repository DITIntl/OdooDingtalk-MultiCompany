# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone
from odoo import fields, _
from urllib.parse import quote
from dingtalk.client import AppKeyClient
from dingtalk.storage.memorystorage import MemoryStorage
from odoo.http import request

mem_storage = MemoryStorage()
_logger = logging.getLogger(__name__)


def get_client(self, config):
    """
    得到客户端
    :param self: 当自动任务时获取客户端时需传入一个对象，否则会报对象无绑定的错误
    :param config:
    :return:
    """
    corp_id = config.corp_id.replace(' ', '')
    app_key = config.app_key.replace(' ', '')
    app_secret = config.app_secret.replace(' ', '')
    return AppKeyClient(corp_id, app_key, app_secret, storage=mem_storage)


def get_dingtalk_config(self, company):
    """
    获取配置项
    :return:
    """
    config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)])
    if not config:
        raise ValueError("没有为:(%s)配置钉钉参数！" % company.name)
    return config


def get_config_is_delete(self, company):
    """
    返回对应公司钉钉配置项中是否"删除基础数据自动同步"字段
    :return:
    """
    config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)])
    if not config:
        raise ValueError("没有为:(%s)配置钉钉参数！" % company.name)
    return config.delete_is_sy


def timestamp_to_local_date(time_num):
    """
    将13位毫秒时间戳转换为本地日期(+8h)
    :param time_num:
    :return: string datetime
    """
    if not time_num:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    to_local_datetime = fields.Datetime.context_timestamp(request, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return to_str_datetime


def datetime_to_stamp(time_num):
    """
    将时间转成13位时间戳
    :param time_num:
    :return: date_stamp
    """
    date_str = fields.Datetime.to_string(time_num)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)