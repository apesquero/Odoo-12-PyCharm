# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SuppliferInfo(models.Model):
    _inherit = 'product.supplierinfo'

    width_uom = fields.Many2one('product.uom',
                                domain="[('category_id', '=', 4)]",
                                related='product_tmpl_id.width_uom',
                                string='Width UOM')
    height_uom = fields.Many2one('product.uom',
                                 domain="[('category_id', '=', 4)]",
                                 related='product_tmpl_id.height_uom',
                                 string='Height UOM')

    purchase_price_type = fields.Selection([
        ('standard', 'Standard'),
        ('fabric', 'Fabric'),
        ('table_1d', '1D Table'),
        ('table_2d', '2D Table'),
        ('area', 'Area')],
        string='Supplier Price Type',
        required=True,
        default='standard'
    )
    """FABRIC"""
    fabric_uom = fields.Many2one('product.uom',
                                 domain="[('category_id', '=', 4)]",
                                 string='Fabric UOM',
                                 related='product_tmpl_id.fabric_uom')

    """AREA"""
    area_uom = fields.Many2one('product.uom',
                               string='Area UOM',
                               related='purchase_prices_area.area_uom')

    purchase_prices_area = fields.One2many('product.supplier_prices_area',
                                           'purchase_area_suppl_id',
                                           string="Purchase Prices Area")

    min_width_area = fields.Float(related='purchase_prices_area.min_width_area')
    max_width_area = fields.Float(related='purchase_prices_area.max_width_area')
    min_height_area = fields.Float(related='purchase_prices_area.min_height_area')
    max_height_area = fields.Float(related='purchase_prices_area.max_height_area')

    min_price_area = fields.Float(related='purchase_prices_area.min_price_area')



    prices_table = fields.One2many('product.prices_table',
                                   'supplier_product_id',
                                   string="Supplier Prices Table")

    @api.onchange('purchase_price_type')
    def _check_tmpl_area(self):
        if self.purchase_price_type == 'area' and self.product_tmpl_id.product_price_type == 'area':
            self.update({'min_width_area': self.product_tmpl_id.min_width_area,
                         'max_width_area': self.product_tmpl_id.max_width_area,
                         'min_height_area': self.product_tmpl_id.min_height_area,
                         'max_height_area': self.product_tmpl_id.max_height_area,
                         'area_uom': self.product_tmpl_id.area_uom
                         })

    @api.one
    @api.constrains('purchase_price_type')
    def _create_relation(self):
        self.ensure_one()
        if self.purchase_price_type == 'area' and self.product_tmpl_id.product_price_type == 'area':
            column = {'min_width_area': self.product_tmpl_id.min_width_area,
                      'max_width_area': self.product_tmpl_id.max_width_area,
                      'min_height_area': self.product_tmpl_id.min_height_area,
                      'max_height_area': self.product_tmpl_id.max_height_area,
                      'min_price_area': self.min_price_area
                      }
            if not self.purchase_prices_area:
                self.write({'purchase_prices_area': [(0, None, column)]})
            return {}
        if self.purchase_price_type == 'area':
            column = {'min_width_area': self.min_width_area,
                      'max_width_area': self.max_width_area,
                      'min_height_area': self.min_height_area,
                      'max_height_area': self.max_height_area,
                      'min_price_area': self.min_price_area
                      }
            if not self.purchase_prices_area:
                self.write({'purchase_prices_area': [(0, None, column)]})
            return {}
        if self.purchase_price_type != 'area' and self.purchase_prices_area.id is not False:
            self.write({'purchase_prices_area': [(2, self.purchase_prices_area.id, False)]})
            return {}

    @api.constrains('min_width_area',
                    'max_width_area',
                    'min_height_area',
                    'max_height_area',
                    'min_price_area')
    def _check_area_values(self):
        if self.purchase_price_type == 'area':
            if self.min_width_area <= 0 or \
                            self.min_height_area <= 0 or \
                            self.max_width_area <= 0 or \
                            self.max_height_area <= 0 or \
                            self.min_price_area <= 0:
                raise ValidationError(_("Error! The values in supplier %s can`t "
                                        "be negative or cero") % self.name.display_name)
            elif self.min_width_area > self.max_width_area:
                raise ValidationError(_("Error! Min. Width in supplier %s can`t "
                                        "be greater than Max. Width") % self.name.display_name)
            elif self.min_height_area > self.max_height_area:
                raise ValidationError(_("Error! Min. Height in supplier %s can`t "
                                        "be greater than Max. Height") % self.name.display_name)
        return True

    def get_price_table_headers(self):
        result = {'x': [0], 'y': [0]}
        for rec in self.prices_table:
            result['x'].append(rec.pos_x)
            result['y'].append(rec.pos_y)
        result.update({
            'x': sorted(list(set(result['x']))),
            'y': sorted(list(set(result['y'])))
        })
        return result

    def origin_check_purchase_dim_values(self, width, height):
        if self.purchase_price_type in ['table_1d', 'table_2d']:
            product_prices_table_obj = self.env['product.prices_table']
            norm_width = self.origin_normalize_width_value(width)
            if self.purchase_price_type == 'table_2d':
                norm_height = self.origin_normalize_height_value(height)
                return product_prices_table_obj.search_count([
                    ('supplier_product_id', '=', self.id),
                    ('pos_x', '=', norm_width),
                    ('pos_y', '=', norm_height),
                    ('value', '!=', 0)]) > 0
            return product_prices_table_obj.search_count([
                ('supplier_product_id', '=', self.id),
                ('pos_x', '=', norm_width),
                ('value', '!=', 0)]) > 0
        elif self.purchase_price_type == 'area':
            return width >= self.min_width_area and \
                width <= self.max_width_area and \
                height >= self.min_height_area and \
                height <= self.max_height_area
        return True

    @api.model
    def origin_normalize_width_value(self, width):
        headers = self.get_price_table_headers()
        norm_val = width
        for index in range(len(headers['x'])-1):
            if headers['x'][0] == 0 and index == 0:
                if width >= headers['x'][index + 1] and \
                                width <= headers['x'][index + 1]:
                    norm_val = headers['x'][index + 2]
            else:
                if width > headers['x'][index] and \
                                width <= headers['x'][index + 1]:
                    norm_val = headers['x'][index + 1]
        return norm_val

    @api.model
    def origin_normalize_height_value(self, height):
        headers = self.get_price_table_headers()
        norm_val = height
        for index in range(len(headers['y']) - 1):
            if headers['y'][0] == 0 and index == 0:
                if height >= headers['y'][index + 1] and \
                                height <= headers['y'][index + 1]:
                    norm_val = headers['y'][index + 2]
            else:
                if height > headers['y'][index] and \
                            height <= headers['y'][index + 1]:
                    norm_val = headers['y'][index + 1]
        return norm_val

    @api.depends('price')
    def get_supplier_price(self):
        origin_width = self.env.context and \
            self.env.context.get('width') or False
        origin_height = self.env.context and \
            self.env.context.get('height') or False
        product_id = self.env.context and \
            self.env.context.get('product_id') or False

        result = False
        if origin_width:
            product_prices_table_obj = self.env['product.prices_table']
            origin_width = self.origin_normalize_width_value(origin_width)
            if self.purchase_price_type == 'table_2d':
                origin_height = self.origin_normalize_height_value(origin_height)
                res = product_prices_table_obj.search([
                    ('supplier_product_id', '=', self.id),
                    ('pos_x', '=', origin_width),
                    ('pos_y', '=', origin_height)
                ], limit=1)
                result = res and res.value or False
            elif self.purchase_price_type == 'table_1d':
                res = product_prices_table_obj.search([
                    ('supplier_product_id', '=', self.id),
                    ('pos_x', '=', origin_width)
                ], limit=1)
                result = res and res.value or False
            elif self.purchase_price_type == 'area':
                # Unit conversion created
                origin_width = (self.area_uom.factor * origin_width) / self.width_uom.factor
                origin_height = (self.area_uom.factor * origin_height) / self.height_uom.factor

                result = self.price * origin_width * origin_height
                result = max(self.min_price_area, result)
            elif self.purchase_price_type == 'fabric':
                # Unit conversion created
                origin_width = (self.fabric_uom.factor * origin_width) / self.width_uom.factor

                result = self.price * origin_width
        if not result:
            result = self.price
        return result
