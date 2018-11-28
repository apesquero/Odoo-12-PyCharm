# -*- coding: utf-8 -*-

{
    'name': 'Account Variant Configurator',
    'description': 'Module that expands the way of calculating the price according to the dimensions, for the products of sale',
    'version': '10.0.1.0',
    'author': 'Amaro Pesquero',
    'data': [
            'views/account_invoice_view.xml',
            ],
    'category': 'Accounting',
    'depends': ['account',
                'product_variant_configurator',
                ],
    'application': True,
    'installable': True,
    'post_init_hook': 'assign_product_template',
}
