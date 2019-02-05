# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    price_extra_type = fields.Selection([('standard', 'Standard'),
                                         ('percentage', 'Percentage')],
                                        string='Price Extra Type',
                                        required=True,
                                        default='standard')

    percentage = fields.Integer(string='Percent Extra Price',
                                default=0)

    price_extra2 = fields.Float(
        string='Attribute Price Extra',
        default=0.0,
        compute='_compute_price_extra',
        compute_sudo=False,
        digits=dp.get_precision('Product Price'),
        help="""Price Extra: Extra price for the variant with
            this attribute value on sale price. eg. 200 price extra, 1000 + 200 = 1200.""")

    @api.depends('percentage')
    @api.onchange('price_extra_type')
    def _compute_price_extra(self):
        for product in self:
            if product.price_extra_type == 'percentage':
                active_id = product.product_tmpl_id._context['active_id']
                list_price = self.env['product.template'].search(
                    [('id', '=', active_id)]).list_price
                price_percent = (product.percentage * list_price) / 100
                product.update(
                    {'price_extra': price_percent,
                     'price_extra2': price_percent
                     })
