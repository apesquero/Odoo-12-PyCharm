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

    numeric_value = fields.Float('Numeric Value',
                                 digits=dp.get_precision('Product Attribute'))
    min_range = fields.Float('Min',
                             digits=dp.get_precision('Product Attribute'))
    max_range = fields.Float('Max',
                             digits=dp.get_precision('Product Attribute'))


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    image = fields.Binary(string='Image', related="product_attribute_value_id.image")
    numeric_value = fields.Float('Numeric Value',
                                 digits=dp.get_precision('Product Attribute'),
                                 related="product_attribute_value_id.numeric_value")
    min_range = fields.Float('Min',
                             digits=dp.get_precision('Product Attribute'),
                             related="product_attribute_value_id.min_range")
    max_range = fields.Float('Max',
                             digits=dp.get_precision('Product Attribute'),
                             related="product_attribute_value_id.max_range")

