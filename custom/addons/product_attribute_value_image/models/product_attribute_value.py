# -*- coding: utf-8 -*-from openerp import models, fields
from odoo import api, fields, models

class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    type = fields.Selection(selection_add=[('image', 'Image')])

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    image = fields.Binary(string='Image')

class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    image = fields.Binary(string='Image', related="product_attribute_value_id.image")
