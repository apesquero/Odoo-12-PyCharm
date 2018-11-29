# -*- coding: utf-8 -*-
from odoo import api, models

class SaleOrderReportManzano(models.AbstractModel):
    _name = 'report.sale.report_salemanzano'
    _description = 'Manzanodecora Report'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_sale('sale.report_salemanzano')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.sale,
            'docs': self,
        }
        return report_obj.render('sale.report_salemanzano', docargs)
