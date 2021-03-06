# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from math import ceil


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # sale_stock_variant_configurator
    # Redefine again the product template field as a regular one
    product_tmpl_id = fields.Many2one(
        string='Product Template',
        comodel_name='product.template',
        store=True,
        related=False,
        auto_join=True,
    )

    origin_width = fields.Float(string="Width",
                                required=True,
                                default=0.0)
    origin_height = fields.Float(string="Height",
                                 required=True,
                                 default=0.0)

    width_uom = fields.Many2one('product.uom',
                                string='Width UOM',
                                related='product_tmpl_id.width_uom',
                                readonly=True)
    height_uom = fields.Many2one('product.uom',
                                 string='Height UOM',
                                 related='product_tmpl_id.height_uom',
                                 readonly=True)

    sale_price_type = fields.Selection([('standard', 'Standard'),
                                        ('fabric', 'Fabric'),
                                        ('table_1d', '1D Table'),
                                        ('table_2d', '2D Table'),
                                        ('area', 'Area')],
                                       string='Sale Price Type',
                                       related='product_tmpl_id.product_price_type')

    rapport = fields.Float(related='product_tmpl_id.rapport')
    rapport_uom = fields.Many2one('product.uom',
                                  string='Rapport UOM',
                                  related='product_tmpl_id.rapport_uom',
                                  readonly=True)

    @api.constrains('origin_width', 'origin_height')
    def _check_origin_dimensions_constrains(self):
        for record in self:
            if not record.product_id.origin_check_sale_dim_values(
                    record.origin_width, record.origin_height):
                raise ValidationError(_("Invalid dimension in:\n%s!")
                                      % self.product_id.name_get()[0][1])

    @api.onchange('product_id',
                  'origin_width',
                  'origin_height',
                  'product_attribute_ids')
    def product_id_change(self):
        if not self.product_tmpl_id \
                or (self.product_id
                    and self.product_id.product_tmpl_id.id
                        != self.product_id.product_tmpl_id.id):
            return {'domain': {'product_uom': []}}

        # Create a product if it doesn't exist
        if self.can_create_product:
            try:
                with self.env.cr.savepoint():
                    self.product_id = self.create_variant_if_needed()
            except ValidationError as e:
                return {'warning': {
                    'title': _('Product not created!'),
                    'message': e.name,
                }}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)],
                  'width_uom': [('category_id', '=', self.product_id.width_uom.category_id.id)],
                  'height_uom': [('category_id', '=', self.product_id.height_uom.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

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

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        # Avoid the message if you have not completed the attributes and have not defined the product
        if product.id is not False:
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result

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

        name = ''
        if self.product_id:
            name = product.name_get()[0][1]
        if product.product_price_type in ['fabric']:
            width_uom = product.width_uom.name
            name += _(' [Length:%.2f %s]') % (self.origin_width, width_uom)
        elif product.product_price_type in ['table_1d']:
            width_uom = product.width_uom.name
            name += _(' [Width:%.2f %s]') % (self.origin_width, width_uom)
        elif product.product_price_type in ['table_2d', 'area']:
            height_uom = product.height_uom.name
            width_uom = product.width_uom.name
            name += _(' [Width:%.2f %s x Height:%.2f %s]') % \
                    (self.origin_width, width_uom, self.origin_height, height_uom)
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']. \
                _fix_tax_included_price_company(self._get_display_price(product),
                                                product.taxes_id,
                                                self.tax_id,
                                                self.company_id)
        self.update(vals)

        return result

    @api.onchange('origin_width',
                  'origin_height')
    def _check_origin_dimensions(self):

        width_uom = self.product_id.width_uom.name
        height_uom = self.product_id.height_uom.name

        if self.product_id and self.product_id.product_price_type in ['table_1d', 'table_2d']:
            max_width = self.product_id.get_sale_price_table_headers()['x'][-1]
            if self.product_id.get_sale_price_table_headers()['x'][0] == 0:
                min_width = self.product_id.get_sale_price_table_headers()['x'][1]
            else:
                min_width = self.product_id.get_sale_price_table_headers()['x'][0]

        if self.product_id and self.product_id.product_price_type in ['table_2d']:
            max_height = self.product_id.get_sale_price_table_headers()['y'][-1]
            if self.product_id.get_sale_price_table_headers()['y'][0] == 0:
                min_height = self.product_id.get_sale_price_table_headers()['y'][1]
            else:
                min_height = self.product_id.get_sale_price_table_headers()['y'][0]

        if self.product_id and self.product_id.product_price_type in ['area']:
            max_width = self.product_id.max_width_area
            min_width = self.product_id.min_width_area
            max_height = self.product_id.max_height_area
            min_height = self.product_id.min_height_area

        if self.product_id.product_price_type in ['table_2d', 'area'] and \
                        self.origin_height != 0 and self.origin_width != 0 and \
                not self.product_id.origin_check_sale_dim_values(
                    self.origin_width, self.origin_height):
            if self.origin_width > max_width:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "max width = %.0f %s") % (max_width, width_uom))
            if self.origin_width < min_width:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "min width = %.0f %s") % (min_width, width_uom))
            if self.origin_height > max_height:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "max height = %.0f %s") % (max_height, height_uom))
            if self.origin_height < min_height:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "min height = %.0f %s") % (min_height, height_uom))
            else:
                raise ValidationError(_("Invalid Combination of Dimensions\n "
                                        "See the table dimensions"))


        elif self.product_id.product_price_type == 'table_1d' and self.origin_width != 0 and \
                not self.product_id.origin_check_sale_dim_values(self.origin_width, 0):
            if self.origin_width > max_width:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "max width = %.0f %s") % (max_width, width_uom))
            if self.origin_width < min_width:
                raise ValidationError(_("Invalid Dimensions Product! "
                                        "min width = %.0f %s") % (min_width, width_uom))
            else:
                raise ValidationError(_("Invalid Combination of Dimensions\n "
                                        "See the table dimensions"))

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()

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

        if self.order_id.pricelist_id and self.order_id.partner_id:
            self.price_unit = self.env['account.tax']. \
                _fix_tax_included_price_company(self._get_display_price(product),
                                                product.taxes_id,
                                                self.tax_id,
                                                self.company_id)
        return res

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount' \
                or product._name != 'product.product' or self.product_id.id is False:
            return product.with_context(pricelist=self.order_id.pricelist_id.id).price

        final_price, rule_id = self.order_id.pricelist_id. \
            get_product_price_rule(product,
                                   self.product_uom_qty or 1.0,
                                   self.order_id.partner_id)

        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id,
                               date=self.order_id.date_order)

        base_price, currency_id = self.with_context(context_partner). \
            _get_real_price_currency(product, rule_id,
                                     self.product_uom_qty,
                                     self.product_uom,
                                     self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id). \
                with_context(context_partner).compute(base_price,
                                                      self.order_id.pricelist_id.currency_id)

        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

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
        new_procs = self.env['procurement.order']  # Empty recordset
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

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Add measures in sale.py - SaleOrderLine
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({
            'origin_width': self.origin_width,
            'origin_height': self.origin_height,
        })
        return res
