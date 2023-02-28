# -*- coding: utf-8 -*-
from odoo import models, fields, api,_ 

 
class gss_sale_crmlead(models.Model):
    _inherit = 'crm.lead'
    
    vendor_ids = fields.One2many(
        'product.supplierinfo.gss', 'opportunity_id', string='Selection des Fournisseurs')
    
    
    def action_new_quotation(self):
        order_lines = self.env['sale.order.line']
        SalerOrder = self.env['sale.order']
        sale_id = SalerOrder.create({
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'origin': self.name,
            'source_id': self.source_id.id,
            'company_id': self.company_id.id or self.env.company.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)]
        })
       
        for line in self.vendor_ids:
            data = {'name': line.name.id,
                    'product_tmpl_id': line.product_tmpl_id.id,
                    'price': line.price,
                    'min_qty': line.min_qty,
                    'delay': line.delay} 
        
            self.env['product.supplierinfo']._check_vendors(data)  
            if line.vendor_select:
                product = self.env['product.product'].search(
                    [('product_tmpl_id','=',line.product_tmpl_id.id)],
                    limit=1)
                vendor = self.env['product.supplierinfo'].search(
                    [('name','=',line.name.id),('product_tmpl_id','=',line.product_tmpl_id.id),
                     ('price','=',line.price),('min_qty','=',line.min_qty),('delay','=', line.delay)],limit=1)
                  
                price = line.price
                discount = 0
                vals = {
                    'display_type': False,
                    'name': product.name,
                    'state': 'draft',
                    'price_usd': line.price_usd,
                    'price_unit': price,
                    'discount': discount,
                    'product_uom_qty': line.min_qty,
                    'product_id': product.id,
                    'product_uom': line.product_uom.id,
                    'order_id': sale_id.id,
                    'vendor_id': vendor.id,
                }
              
                order_lines.create(vals)
                order_lines._compute_tax_id()
                
        return self.action_view_sale_quotation()
        