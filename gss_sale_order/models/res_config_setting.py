# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class ResConfiqSettingGss(models.TransientModel):
    _inherit = "res.config.settings"
    
    convert = fields.Float(config_parameter='gss_sale_order.convert', required=True, default=1.33, string="Conversion")
    
    
