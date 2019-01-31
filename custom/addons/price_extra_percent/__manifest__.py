# -*- coding: utf-8 -*-

{
    'name': 'Attribute Price Extra Percent',
    'version': '1.0',
    'author': "Amaro Pesquero",
    'website': 'https://www.eiqui.com',
    'category': 'Sales',
    'summary': "Add Percent Option in Sale and Pruchase variant Price",
    'description': "Add Percent Option in Sale and Pruchase variant Price",
    'depends': [
        'sale',
        'purchase',
    ],
    'data': [
        'views/product_attribute_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
