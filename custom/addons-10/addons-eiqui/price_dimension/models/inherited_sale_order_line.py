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

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _

from .consts import PRICE_TYPES

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    origin_width = fields.Float(string="Width", required=False)
    origin_height = fields.Float(string="Height", required=False)
    product_price_type = fields.Selection(PRICE_TYPES,
        string='Sale Price Type',
        related='product_tmpl_id.sale_price_type')

    @api.constrains('origin_width')
    def _check_origin_width(self):
        for record in self:
            if not record.product_id.origin_check_sale_dim_values(
                    record.origin_width, record.origin_height):
                raise ValidationError("Invalid width!")

    @api.constrains('origin_height')
    def _check_origin_height(self):
        for record in self:
            if not record.product_id.origin_check_sale_dim_values(
                    record.origin_width, record.origin_height):
                raise ValidationError("Invalid height!")


    """Si no cargas el 'product_attribute_ids' no te va a funcionar
        Hay demasiados onchange, se puede separar y optimizar mucho mas"""

    @api.onchange('product_id', 'origin_width', 'origin_height', 'product_attribute_ids')
    def product_id_change(self):
        super(SaleOrderLine, self).product_id_change()
        product_tmp = False
        if not self.product_tmpl_id or (self.product_id and \
                self.product_id.product_tmpl_id.id != \
                self.product_id.product_tmpl_id.id):
            return
        if self.can_create_product:
            try:
                with self.env.cr.savepoint():
                    product_tmp = self.product_id = self.create_variant_if_needed()
            except exceptions.ValidationError as e:
                return {'warning': {
                    'title': _('Product not created!'),
                    'message': e.name,
                }}
        vals = {}
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,

            width=self.origin_width,
            height=self.origin_height
        )

        if product.sale_price_type in ['table_2d', 'area'] and \
                self.origin_height != 0 and self.origin_width != 0 and \
                not self.product_id.origin_check_sale_dim_values(
                self.origin_width, self.origin_height):
            raise ValidationError(_("Invalid Dimensions!"))
        elif product.sale_price_type == 'table_1d' and self.origin_width != 0 and \
                not self.product_id.origin_check_sale_dim_values(self.origin_width, 0):
            raise ValidationError(_("Invalid Dimensions!"))

        if self.product_tmpl_id.sale_price_type not in ['table_1d','table_2d', 'area']:
            self.origin_height = self.origin_width = 0
        name = ''
        if self.product_id:
            name = product.name_get()[0][1]
        if product.sale_price_type in ['table_2d', 'area']:
            height_uom = product.height_uom.name
            width_uom = product.width_uom.name
            name += _(' [Width:%.2f %s x Height:%.2f %s]') % \
                (self.origin_width, width_uom, self.origin_height, height_uom)
        elif product.sale_price_type == 'table_1d':
            width_uom = product.width_uom.name
            name += _(' [ Width:%.2f %s]') % (self.origin_width, width_uom)
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        """Elimina el _get_display_price(product), anulando la propiedad pricelist"""

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(
                product.lst_price, product.taxes_id, self.tax_id)

        #~ if product_tmp:
            #~ self.product_id = False
            #~ product_tmp.unlink()
        self.update(vals)


    """Al eliminar el onchange, esto no se actualiza, lo cual provoca que no se actualice
    el precio, en principio parece que bien, porque el precio no se fastidia, pero rompe 
    la estructura de sale.order.line, es mas, se pierde toda la funcionalidad de Sale Price 
    - Advanced priccing..."""

    def product_uom_change(self):
        super(SaleOrderLine, self).product_uom_change()
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),

                width=self.origin_width,
                height=self.origin_height
            )
            #esto sobra por completo si tienes un buen IDE
            import wdb; wdb.set_trace()

            self.price_unit = self.env['account.tax']._fix_tax_included_price(
                product.price, product.taxes_id, self.tax_id)

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(group_id=group_id)
        vals.update({
            'origin_width': self.origin_width,
            'origin_height': self.origin_height
        })
        return vals

    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order'] #Empty recordset
        for line in self:
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)

            vals = line._prepare_order_line_procurement(
                group_id=line.order_id.procurement_group_id.id)
            vals['product_qty'] = line.product_uom_qty - qty
            new_proc = self.env["procurement.order"].with_context(
                    procurement_autorun_defer=True,
                ).create(vals)
            # Do one by one because need pass specific context values
            new_proc.with_context(
                width=line.origin_width,
                height=line.origin_height).run()
            new_procs += new_proc
        return new_procs
