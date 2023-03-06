# -*- coding: utf-8 -*-
from odoo import models, fields, api,_ 
from odoo.exceptions import ValidationError
 
class gss_productsupllierinfo(models.Model):
    _name = 'product.supplierinfo.gss'
    _description = 'CRM ORDER'
    
    
    name = fields.Many2one(
        'res.partner', 'Fournisseur',
        ondelete='cascade', required=True,
        help="Vendor of this product", check_company=True)
    product_uom = fields.Many2one(
        'uom.uom', 'Unite de Mesure',
        related='product_tmpl_id.uom_id',
        help="This comes from the product form.")
    opportunity_id = fields.Many2one(
        'crm.lead',
        string='Opportunite',
        )
    min_qty = fields.Float(
        'Quantite', default=0.0, required=True, digits="Product Unit Of Measure",
        help="The quantity to purchase from this vendor to benefit from the price, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    price = fields.Float(
        
        'PU CAD', default=0.0, digits='Product Price',
        required=True, help="The price to purchase a product")
    price_usd = fields.Float(
        'PU USD', default=0.0, digits='Product Price USD',
        required=True, help="The price to purchase a product")
    company_id = fields.Many2one(
        'res.company', 'Entreprise',
        default=lambda self: self.env.company.id, index=1)
    product_tmpl_id = fields.Many2one(
        'product.template', 'Produit', check_company=True,
        index=True, ondelete='cascade')
    vendor_select = fields.Boolean(string="selectionner le fournisseur a commander")
    
    product_id = fields.Many2one(
        'product.product', 'Article', check_company=True,
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If not set, the vendor price will apply to all variants of this product.")
    
    delay = fields.Integer(
        'Delai de livraison', default=1, required=True,
        help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")
    reference = fields.Char(string='Reference interne', related='product_tmpl_id.default_code')
    
class productsupllierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    def _check_vendors(self,data):
        vendors = self.search([
        ('name','=',data['name']),
        ('product_tmpl_id','=',data['product_tmpl_id']),
        ('price','=',data['price']),
        ('min_qty','=',data['min_qty']),
        ('delay','=',data['delay']),
        ], limit=1)
        if vendors:
            return vendors.id
        else:
            return self.create({
                'name':data['name'],
                'product_tmpl_id': data['product_tmpl_id'],
                'price': data['price'],
                'min_qty': data['min_qty'],
                'delay':data['delay']   
            }).id
        