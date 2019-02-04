# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    price_extra_type = fields.Selection([('standard', 'Standard'),
                                         ('percentage', 'Percentage')],
                                        string='Price Extra Type',
                                        required=True,
                                        default='standard')

    percentage = fields.Integer(string='Percent Extra Price',
                                default=0)

    @api.onchange('price_extra_type')
    def _compute_price_extra(self):
        for product in self:
            if product.price_extra_type == 'percentage':
                # list_price = self.env['product.template'].search([]).list_price
                list_price = 100
                price_percent = (product.percentage * list_price) / 100
                product.update({'price_extra': product.price_extra + price_percent})
