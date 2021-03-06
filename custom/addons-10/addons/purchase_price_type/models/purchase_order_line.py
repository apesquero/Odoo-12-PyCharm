# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID, exceptions
from odoo.exceptions import ValidationError
from math import ceil


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    origin_width = fields.Float(string="Width",
                                required=True,
                                default=0.0)
    origin_height = fields.Float(string="Height",
                                 required=True,
                                 default=0.0)

    width_uom = fields.Many2one('product.uom',
                                string='Width UOM',
                                related='product_id.width_uom',
                                readonly=True)
    height_uom = fields.Many2one('product.uom',
                                 string='Width UOM',
                                 related='product_id.width_uom',
                                 readonly=True)

    purchase_price_type = fields.Selection([('standard', 'Standard'),
                                            ('fabric', 'Fabric'),
                                            ('table_1d', '1D Table'),
                                            ('table_2d', '2D Table'),
                                            ('area', 'Area')],
                                           string='Sale Price Type',
                                           related='product_id.product_price_type')

    rapport = fields.Float(related='product_id.rapport')
    rapport_uom = fields.Many2one('product.uom',
                                  string='Rapport UOM',
                                  related='product_id.rapport_uom',
                                  readonly=True)

    @api.constrains('origin_width', 'origin_height')
    def _check_origin_dimensions_constrains(self):
        for record in self:
            product = self.product_id.with_context(
                width=self.origin_width,
                height=self.origin_height
            )
            seller = product._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=self.order_id.date_order and self.order_id.date_order[:10],
                uom_id=self.product_uom)

            if seller:
                seller = seller.with_context(
                    width=self.origin_width,
                    height=self.origin_height
                )
                if not seller.origin_check_purchase_dim_values(
                        record.origin_width, record.origin_height):
                    raise ValidationError(_("Invalid dimension in:\n%s!")
                                          % self.product_id.name_get()[0][1])


    @api.onchange('product_id',
                  'origin_width',
                  'origin_height',
                  'product_attribute_ids')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.product_tmpl_id:
            return result

        if self.can_create_product:
            try:
                with self.env.cr.savepoint():
                    self.product_id = self.create_variant_if_needed()
            except exceptions.ValidationError as e:
                return {'warning': {
                    'title': _('Product not created!'),
                    'message': e.name,
                }}

        product = self.product_id.with_context(width=self.origin_width,
                                               height=self.origin_height)

        if product.product_price_type in ['table_2d', 'area'] \
                and self.origin_height != 0 and self.origin_width != 0 \
                and not self.product_id.origin_check_sale_dim_values(self.origin_width,
                                                                     self.origin_height):
            raise ValidationError(_("Invalid Dimensions!"))
        elif product.product_price_type == 'table_1d' and self.origin_width != 0 \
                and not self.product_id.origin_check_sale_dim_values(self.origin_width, 0):
            raise ValidationError(_("Invalid Dimensions!"))

        if self.product_tmpl_id.product_price_type not in ['fabric', 'table_1d', 'table_2d', 'area']:
            self.origin_height = self.origin_width = 0

        # rapport calculation
        if self.product_tmpl_id.product_price_type in ['fabric']:
            rapport = (self.width_uom.factor * self.rapport) / self.rapport_uom.factor
            width_uom = self.width_uom.name
            if rapport > 0:

                result_width = (int(ceil(round((self.origin_width / rapport), 2)))) * rapport
                remainder = result_width - self.origin_width
                if remainder > 0:
                    self.origin_width = result_width
                    product = product.with_context(width=self.origin_width)

                    message = _("The measure is less than the necessary rapport:\n"
                                "The measure has been increased %.2f %s!") % (remainder, width_uom)
                    mess = {'title': _("Warning measure"),
                            'message': message}
                    result = {'warning': mess}

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = product.uom_po_id or product.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}

        product_lang = product.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
            'width': self.origin_width,
            'height': self.origin_height
        })
        name = product_lang.display_name
        if product.product_price_type in ['fabric']:
            width_uom = product.width_uom.name
            name += _(' [Length:%.2f %s]') % (self.origin_width,
                                              width_uom)
        elif product.product_price_type in ['table_1d']:
            width_uom = product.width_uom.name
            name += _(' [ Width:%.2f %s]') % (self.origin_width,
                                              width_uom)
        elif product.product_price_type in ['table_2d', 'area']:
            height_uom = product.height_uom.name
            width_uom = product.width_uom.name
            name += _(' [Width:%.2f %s x Height:%.2f %s]') % (self.origin_width,
                                                              width_uom,
                                                              self.origin_height,
                                                              height_uom)
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        self.name = name

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(product.supplier_taxes_id.filtered(
                lambda r: r.company_id.id == company_id)
            )
        else:
            self.taxes_id = fpos.map_tax(product.supplier_taxes_id)

        self._suggest_quantity()
        self._onchange_quantity()

        return result

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return

        product = self.product_id.with_context(
            width=self.origin_width,
            height=self.origin_height
        )

        seller = product._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        seller = seller.with_context(
            width=self.origin_width,
            height=self.origin_height,
            product_id=product
        )

        price_unit = self.env['account.tax']._fix_tax_included_price(
            seller.get_supplier_price(),
            product.supplier_taxes_id,
            self.taxes_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id \
                != self.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)
        if seller and self.product_uom and seller.product_uom \
                != self.product_uom:
            price_unit = self.env['product.uom']._compute_price(seller.product_uom.id,
                                                                price_unit,
                                                                to_uom_id=self.product_uom.id)
        self.price_unit = price_unit

        # @api.multi
        # def _create_stock_moves(self, picking):
        #     moves = super(PurchaseOrderLine, self)._create_stock_moves(picking)
        #     for move in moves:
        #         width = 0
        #         height = 0
        #         if move.purchase_line_id.origin_width:
        #             width = move.purchase_line_id.origin_width
        #         if move.purchase_line_id.origin_height:
        #             height = move.purchase_line_id.origin_height
        #         move.update({
        #             'origin_width': width,
        #             'origin_height': height
        #         })
        #     return moves
