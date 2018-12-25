# -*- encoding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    type = fields.Selection(selection_add=[('numeric', 'Numeric')])


class ProductAttributeLine(models.Model):
    _inherit = "product.attribute.line"

    required = fields.Boolean('Required')
    default = fields.Many2one('product.attribute.value', 'Default')
    attr_type = fields.Selection(string='Type', store=False,
                                 related='attribute_id.attr_type')


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    attr_type = fields.Selection(string='Type',
                                 related='attribute_id.attr_type')
    numeric_value = fields.Float('Numeric Value',
                                 digits=dp.get_precision('Product Attribute'))
    min_range = fields.Float('Min',
                             digits=dp.get_precision('Product Attribute'))
    max_range = fields.Float('Max',
                             digits=dp.get_precision('Product Attribute'))

    @api.constrains('min_range', 'max_range')
    def _check_min_max_range(self):
        for value in self:
            # we check only values of range type attributes.
            if value.attr_type != 'range':
                continue
            if value.min_range > value.max_range:
                raise exceptions.Warning(
                    _('The min range should be less than the max range.'))
        return True
