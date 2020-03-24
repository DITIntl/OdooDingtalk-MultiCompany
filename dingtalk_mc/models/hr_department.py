# -*- coding: utf-8 -*-
import logging
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _name = 'hr.department'

    ding_id = fields.Char(string='钉钉Id', index=True)
    manager_user_ids = fields.Many2many('hr.employee', 'hr_dept_manage_user_emp_rel', string=u'部门主管')
    is_root = fields.Boolean(string=u'根部门?', default=False)

    def create_ding_department(self):
        for res in self:
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            if res.ding_id:
                raise UserError("部门:(%s)已存在了钉钉ID，不能再进行上传。" % res.name)
            data = {'name': res.name}
            # 获取父部门ding_id
            if res.is_root:
                data.update({'parentid': 1})
            else:
                if res.parent_id:
                    data.update({'parentid': res.parent_id.ding_id if res.parent_id.ding_id else ''})
                else:
                    raise UserError("请选择上级部门或则根部门。")
            try:
                result = client.department.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"上传钉钉成功。", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def update_ding_department(self):
        for res in self:
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            data = {
                'id': res.ding_id,  # id
                'name': res.name,  # 部门名称
                'parentid': res.parent_id.ding_id,  # 父部门id
            }
            if res.is_root:
                data.update({'parentid': 1})
            try:
                result = client.department.update(data)
                _logger.info(result)
                res.message_post(body=u"更新钉钉部门成功", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_department(self):
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_department_by_id(res.ding_id, self.company_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除部门。", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def unlink(self):
        for res in self:
            if res.ding_id and dt.get_config_is_delete(self, res.company_id):
                self._delete_dingtalk_department_by_id(res.ding_id, res.company_id)
        return super(HrDepartment, self).unlink()

    def _delete_dingtalk_department_by_id(self, ding_id, company):
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.department.delete(ding_id)
            _logger.info("已在钉钉上删除Id:{}的部门".format(result))
        except Exception as e:
            raise UserError(e)
        return
