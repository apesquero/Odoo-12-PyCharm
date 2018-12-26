# -*- coding: utf-8 -*-from openerp import models, fields
from odoo import api, fields, models, exceptions, _
import odoo.addons.decimal_precision as dp

class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    type = fields.Selection(selection_add=[('image', 'Image'),
                                           ('range', 'Range')])

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    image = fields.Binary(string='Image')
    attr_type = fields.Selection(string='Type',
                                 related='attribute_id.type')
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
            if value.type != 'range':
                continue
            if value.min_range > value.max_range:
                raise exceptions.Warning(
                    _('The min range should be less than the max range.'))
        return True

class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    image = fields.Binary(string='Image', related="product_attribute_value_id.image")
    numeric_value = fields.Float('Numeric Value',
                                 digits=dp.get_precision('Product Attribute'))

