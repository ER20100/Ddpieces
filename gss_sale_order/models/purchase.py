# -*- coding: utf-8 -*-
from odoo import models, fields, api,_ 

 
class gss_purchase_order(models.Model):
    _inherit = 'purchase.order'
    
    note_dachat = fields.Char()