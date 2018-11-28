# -*- coding: utf-8 -*-
{
    'name': 'Custom Sale Order Type',
    'description': 'Module that adds the functionality of change of numbering by commercial',
    'version': '12.0.1.0.0',
    'author': 'Amaro Pesquero',
    'depends': ['sale_order_type'],
    'data': [
        'views/inherit_sale_order_view.xml',
        'views/inherit_res_partner_view.xml',
    ],
    'category': 'Sales',
    'installable': True,
    'application': False,
    'auto_install': True,
}