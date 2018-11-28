# -*- coding: utf-8 -*-
{
    'name': 'Sale Report Manzanodecora',
    'description': 'Módulo Personalización Informes Manzanodecora',
    'version': '12.0.1.0.0',
    'author': 'Amaro Pesquero',
    'depends': ['account', 'sale', 'payment_signal', 'custom_partner', ],
    'data': [
        'views/ins_external_layout_footer.xml',
        'views/ins_external_layout_header.xml',
        'views/ins_external_layout.xml',
        'views/ins_report_invoice_document.xml',
        'views/ins_report_invoice.xml',
        'views/ins_report_saleorder_document.xml',
        'views/ins_report_saleorder.xml',
        'data/paper_formats.xml', ],
    'category': 'Sales',
    'installable': True,
    'application': False,
}
