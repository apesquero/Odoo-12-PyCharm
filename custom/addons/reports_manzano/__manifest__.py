# -*- coding: utf-8 -*-
{
    'name': 'Reports Manzanodecora',
    'description': 'Módulo Personalización Informes Manzanodecora',
    'version': '12.0.1.0.0',
    'author': 'Amaro Pesquero',
    'depends': ['web', 'account', 'sale', 'payment_signal', 'custom_partner', ],
    'data': [
        'data/paper_formats.xml',
        'views/report_templates.xml',
        'views/report_layout.xml',
        'views/report_saleorder.xml',
        'report/sale_report_templates.xml',
    ],
    'category': 'Sales',
    'installable': True,
    'application': False,
}
