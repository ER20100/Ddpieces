# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _



class StockRuleOrderOps(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        _fields = super(StockRuleOrderOps, self)._get_custom_move_fields()
        _fields += ['vendor_id']
        return _fields