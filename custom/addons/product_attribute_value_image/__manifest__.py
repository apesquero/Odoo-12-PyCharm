# -*- encoding: utf-8 -*-
{
    'name': 'Product Attribute Value Image',
    'version': "12.0.1.0.0",
    'author': 'Amaro Pesquero Rodríguez',
    'category': 'Sales Management',
    'depends': ['product',
                'sale',
                ],
    'data': ['views/product_attribute_value_view.xml',
             'views/sale_product_configurator_templates.xml',
             ],
    'installable': True,
    'application': False,
}
