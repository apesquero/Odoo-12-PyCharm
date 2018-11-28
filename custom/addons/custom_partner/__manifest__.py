# -*- coding: utf-8 -*-
{
    'name': 'Custom Partner Manzanodecora',
    'description': 'Módulo que añade a los contactos nuevos campos',
    'version': '12.0.1.0.0',
    'author': 'Amaro Pesquero',
    'depends': ['base', 'contacts'],
    'data': [
        'views/inherit_res_partner.xml',
    ],
    'category': 'Contact',
    'installable': True,
    'auto_install': True,
    'application': False,
}