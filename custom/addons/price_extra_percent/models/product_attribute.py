# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    price_extra_type = fields.Selection([('standard', 'Standard'),
                                         ('percentage', 'Percentage')],
                                        string='Price Extra Type',
                                        required=True,
                                        default='standard')

    percentage = fields.Integer(string='Percent Extra Price',
                                default=0)
