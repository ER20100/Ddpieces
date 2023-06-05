# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _



class StockRuleOrderOps(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        _fields = super(StockRuleOrderOps, self)._get_custom_move_fields()
        _fields += ['vendor_id']
        _fields += ['note_dachat']
        return _fields
    
    # def _prepare_purchase_order(self, company_id, origins, values):
    #     print(">>>>>>>>>>>>>>>>>")
    #     print(values)
    #     res = super(StockRuleOrderOps, self)._prepare_purchase_order(company_id, origins, values)
    #     return res