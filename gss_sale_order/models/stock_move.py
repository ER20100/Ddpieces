# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveOrderOps(models.Model):
    _inherit = 'stock.move'

    vendor_id = fields.Many2one(
        'product.supplierinfo',
        string='Vendor',
        )
  

    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        values = super(StockMoveOrderOps, self)._prepare_procurement_values()
        values['supplierinfo_id'] = self.vendor_id
        return values
    