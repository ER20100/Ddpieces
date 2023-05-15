# -*- coding: utf-8 -*-
from odoo import models, fields, api,_ 
from odoo.exceptions import ValidationError

class gss_sale_product(models.Model):
    _inherit = 'product.product'
    _rec_name='default_code'
    
    @api.model
    def create(self, values):
        pm_id = self.env.ref('stock.route_warehouse0_mto').id 
        values['route_ids'] = [(4,pm_id)]
        result = super(gss_sale_product,self).create(values)
        return result
    
class gss_sale_productemplate(models.Model):
    _inherit = 'product.template'
   
      
    # @api.constrains('default_code')
    # def _check_unique_ref(self):
    #    return self._onchange_default_code()
       
    
    @api.onchange('default_code')
    def _onchange_default_code(self):
        if not self.default_code:
            return

        domain = [('default_code', '=', self.default_code)]
        if self.id.origin:
            domain.append(('id', '!=', self.id.origin))

        if self.env['product.template'].search(domain, limit=1):
            raise ValidationError('La reference interne doit etre unique!')
           