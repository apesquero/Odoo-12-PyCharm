# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    # @api.multi
    # def unlink(self):
    #     product_ids = self.env['product.supplierinfo'].with_context(
    #         active_test=False).search([
    #         ('attribute_value_ids', 'in', self.ids)])
    #     if product_ids:
    #         raise UserError(_('The operation cannot be completed:\n \
    #             You are trying to delete an attribute value with a \
    #             reference on a product supplier variant.'))
    #     return super(ProductAttributeValue, self).unlink()

    price_extra_type = fields.Selection([('standard', 'Standard'),
                                         ('percentage', 'Percentage')],
                                        string='Price Extra Type',
                                        required=True,
                                        default='standard')

    # supplier_ids = fields.Many2many('product.supplierinfo',
    #                                 id1='att_id',
    #                                 id2='prod_id',
    #                                 string='Variants',
    #                                 readonly=True)


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    # attribute_id = fields.Many2one(
    #     comodel_name='product.attribute', related='value_id.attribute_id')
    price_extra_type = fields.Selection(
        related='product_attribute_value_id.price_extra_type')
    # supplier_ids = fields.Many2many(related='value_id.supplier_ids')
