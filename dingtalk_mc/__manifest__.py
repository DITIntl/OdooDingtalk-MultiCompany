# -*- coding: utf-8 -*-
{
    'name': "Odoo集成钉钉-多公司版本",
    'summary': """支持多个钉钉企业对应Odoo多公司体系""",
    'description': """支持多个钉钉企业对应Odoo多公司体系""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '12.1.0',
    'depends': ['base', 'hr', 'mail'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # 'data/ir_cron.xml',
        'wizard/synchronous.xml',

        'views/assets.xml',
        'views/dingtalk_config.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_partner.xml',
    ],
}
