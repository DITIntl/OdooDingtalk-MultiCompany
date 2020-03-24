# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DingTalkConfig(models.Model):
    _name = 'dingtalk.mc.config'
    _description = "参数配置"
    _rec_name = 'name'

    company_id = fields.Many2one('res.company', string='关联公司', default=lambda self: self.env.user.company_id, index=True)
    name = fields.Char(string='钉钉企业名称', index=True, required=True)
    agent_id = fields.Char(string=u'AgentId')
    corp_id = fields.Char(string=u'CorpId')
    app_key = fields.Char(string=u'AppKey')
    app_secret = fields.Char(string=u'AppSecret')
    login_id = fields.Char(string=u'用于登录AppId')
    login_secret = fields.Char(string=u'用于登录AppSecret')
    token = fields.Boolean(string="Token")
    delete_is_sy = fields.Boolean(string=u'删除基础数据自动同步?')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', '钉钉企业名称已存在，请更换！'),
        ('company_id_uniq', 'UNIQUE (company_id)', '该企业对应的公司存在，请更换！'),
    ]

