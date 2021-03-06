# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                        Alexandre Díaz <alex@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from .consts import PRICE_TYPES


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    price_area_min_width = fields.Float(string="Min. Width",
                                        default=0.0,
                                        digits=dp.get_precision('Product Price'))
    price_area_max_width = fields.Float(string="Max. Width",
                                        default=0.0,
                                        digits=dp.get_precision('Product Price'))
    price_area_min_height = fields.Float(string="Min. Height",
                                         default=0.0,
                                         digits=dp.get_precision('Product Price'))
    price_area_max_height = fields.Float(string="Max. Height",
                                         default=0.0,
                                         digits=dp.get_precision('Product Price'))
    min_price_area = fields.Monetary('Min. Price')

    price_type = fields.Selection(
            PRICE_TYPES,
            string='Supplier Price Type',
            required=True,
            default='standard',
        )
    prices_table = fields.One2many('product.prices_table',
                                   'supplier_product_id',
                                   string="Supplier Prices Table")

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

    def origin_check_dim_values(self, width, height):
        if self.price_type in ['table_1d', 'table_2d']:
            product_prices_table_obj = self.env['product.prices_table']
            norm_width = self.origin_normalize_width_value(width)
            if self.price_type == 'table_2d':
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
        elif self.price_type == 'area':
            return width >= self.price_area_min_width and \
                width <= self.price_area_max_width and \
                height >= self.price_area_min_height and \
                height <= self.price_area_max_height
        return True

    def origin_normalize_width_value(self, width):
        headers = self.get_price_table_headers()
        norm_val = width
        for index in range(len(headers['x'])-1):
            if width > headers['x'][index] and width <= headers['x'][index+1]:
                norm_val = headers['x'][index+1]
        return norm_val

    def origin_normalize_height_value(self, height):
        headers = self.get_price_table_headers()
        norm_val = height
        for index in range(len(headers['y'])-1):
            if height > headers['y'][index] and height <= headers['y'][index+1]:
                norm_val = headers['y'][index+1]
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
            if self.price_type == 'table_2d':
                origin_height = self.origin_normalize_height_value(origin_height)
                res = product_prices_table_obj.search([
                    ('supplier_product_id', '=', self.id),
                    ('pos_x', '=', origin_width),
                    ('pos_y', '=', origin_height)
                ], limit=1)
                result = res and res.value or False
            elif self.price_type == 'table_1d':
                res = product_prices_table_obj.search([
                    ('supplier_product_id', '=', self.id),
                    ('pos_x', '=', origin_width)
                ], limit=1)
                result = res and res.value or False
            elif self.price_type == 'area':
                result = self.price * origin_width * origin_height
                result = max(self.min_price_area, result)
        if not result:
            result = self.price
        return result
