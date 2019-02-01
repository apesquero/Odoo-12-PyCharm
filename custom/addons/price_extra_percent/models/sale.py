# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    value_id = fields.Many2many('product.template.attribute.value',
                                'Product Template Attribute Value',
                                ondelete='cascade',
                                required=True)

    price_extra_type = fields.Selection(related='value_id.price_extra_type')


