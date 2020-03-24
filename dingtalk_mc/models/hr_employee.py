# -*- coding: utf-8 -*-
import base64
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    OfficeStatus = [
        ('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')
    ]

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_unionid = fields.Char(string='Union标识', index=True)
    din_jobnumber = fields.Char(string='员工工号')
    ding_avatar = fields.Html('钉钉头像', compute='_compute_ding_avatar')
    ding_avatar_url = fields.Char('头像url')
    din_hiredDate = fields.Date(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", default=True)
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=OfficeStatus, default='-1')
    department_ids = fields.Many2many('hr.department', 'emp_dept_dingtalk_rel', string='所属部门')

    @api.depends('ding_avatar_url')
    def _compute_ding_avatar(self):
        for res in self:
            if res.ding_avatar_url:
                res.ding_avatar = """
                <img src="{avatar_url}" style="width:80px; height=80px;">""".format(avatar_url=res.ding_avatar_url)
            else:
                res.ding_avatar = False

    def create_ding_employee(self):
        """
        上传员工到钉钉
        :return:
        """
        for res in self:
            print(res.name)
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            data = {
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else res.work_phone,  # 手机
                'tel': res.work_phone if res.work_phone else res.mobile_phone,  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'hiredDate': dt.datetime_to_stamp(res.din_hiredDate) if res.din_hiredDate else '',  # 入职日期
            }
            try:
                result = client.user.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"已上传至钉钉", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def update_ding_employee(self):
        """
        修改员工时同步至钉钉
        :return:
        """
        for res in self:
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                if res.department_id.ding_id not in res.department_ids.mapped('ding_id'):
                    department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            data = {
                'userid': res.ding_id,  # userid
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else res.work_phone,  # 手机
                'tel': res.work_phone if res.work_phone else '',  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'isSenior': res.din_isSenior,  # 高管模式
                'isHide': res.din_isHide,  # 隐藏手机号
            }
            if res.din_hiredDate:
                hiredDate = dt.datetime_to_stamp(res.din_hiredDate)
                data.update({'hiredDate': hiredDate})
            try:
                result = client.user.update(data)
                _logger.info(_(result))
                res.message_post(body=u"已成功更新至钉钉", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_employee(self):
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_employee_by_id(res.ding_id, res.company_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除员工。 *_*!", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def _delete_dingtalk_employee_by_id(self, ding_id, company):
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.user.delete(ding_id)
            _logger.info(_("已在钉钉上删除Id:{}的员工".format(result)))
        except Exception as e:
            raise UserError(e)
        return

    def unlink(self):
        for res in self:
            if res.ding_id and dt.get_config_is_delete(self, res.company_id):
                self._delete_dingtalk_employee_by_id(res.ding_id, res.company_id)
        return super(HrEmployee, self).unlink()

    def using_dingtalk_avatar(self):
        """
        替换为钉钉头像
        :return:
        """
        for emp in self:
            if emp.ding_avatar_url:
                binary_data = base64.b64encode(requests.get(emp.ding_avatar_url).content)
                emp.sudo().write({'image': binary_data})

