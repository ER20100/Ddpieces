# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
import json

class gss_sale_order(models.Model):
    _inherit= 'sale.order'
    
    transport_usd = fields.Monetary(
        string="Transport USD"
    )
    transport_cad = fields.Monetary(
        string="Transport CAD"
    )
    package = fields.Monetary(
        string="Emballage"
    )
    
    convert  = fields.Float(
        string="Conversion",
        required=True,
        default=1.33
    )
    convert_cad  = fields.Float(
        string="Conversion CAD",
        compute = "_compute_convert_cad",
        store=True,
    )
    price_douane = fields.Monetary(
        string="Douane"
    )
    percent_port =  fields.Float(
        string="Frais Port 6%",
        compute = "_compute_total_cost",
        store=True,
    )
    
    cart_credit =  fields.Integer(
        string="Carte Credit",
        default= 1
    )
    
    cost_total =  fields.Monetary(
        string="Cout total",
        compute = "_compute_total_cost",
        store=True,
    )
    
    
    # price_ccr_total =  fields.Monetary(
    #     string="Prix de vente CC",
    #     compute = "_compute_total_cost",
    #     store=True,
    # )
    
    price_profit_total =  fields.Monetary(
        string="Profit Total",
        compute = "_compute_price_total",
        store=True,
    )
    
    total_transport =  fields.Monetary(
        string="transport",
        compute = "_compute_total_cost",
        store=True,
    )
    
    
    @api.depends("convert",'transport_usd','transport_cad','package')
    def _compute_convert_cad(self):
        for record in self:
            record.convert_cad =  ((record.convert * record.transport_usd) + record.transport_cad + record.package) * 1.2
    
    @api.depends('order_line.price_subtotal')
    def _compute_total_cost(self):
        for order in self:
            amount_US = amount_transp = cost_total = 0.0
            for line in order.order_line:
                amount_US += line.price_usd * line.product_uom_qty 
                amount_transp += line.price_before_trans
                cost_total += line.price_before_trans + line.price_transport_douane
           
            order.update({
                'cost_total':cost_total,
                'total_transport':amount_transp,
                'percent_port':(amount_transp* 6.0)/100.0 if amount_US > 0.0 else 0.0 ,
            })
    
    @api.depends('cost_total','amount_untaxed')
    def _compute_price_total(self):  
        for rec in self:
            rec.price_profit_total = rec.amount_untaxed - rec.cost_total
            
            
    @api.depends('order_line.tax_id', 'order_line.price_unit_cad', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            price = order_line.price_unit_cad * (1 - (order_line.discount or 0.0) / 100.0)
            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)
           

class gss_sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    reference  = fields.Char(related="product_id.default_code", string="No PIECE")
    price_usd = fields.Float(
        string="Prix USD",
    )
    conversion_line = fields.Float(
        string="Conversion en CAD",
        compute = "_compute_conversion",
        store= True
    )
    price_unit = fields.Float('Prix CAD', required=True, digits='Product Price', default=0.0)

    price_before_trans =  fields.Monetary(
        string="Total avant Transport",
        compute = "_compute_price_before_transport",
        store= True
    )
    
    percentage = fields.Float(
        string="%",
        compute = "_compute_percentage_value",
        store= True
    )
    
    price_transport_douane = fields.Monetary(
        string="Transports et douanes Canadiens",
        compute = "_compute_price_transport_douane",
        store= True
    )
    
    costline_transport_douane = fields.Monetary(
        string="Cout unitaire Incl Transport",
        compute = "_compute_cost_transport_douane",
        store= True
    )
    
    profit  = fields.Float(
        string="Profit %",
        default=155.0
    )
    
    price_unit_cad = fields.Float(
        'Prix Vendant Unitaire',
        readonly=True,
        digits='Product Price', 
        compute = "_compute_price_unit",
        default=0.0)
    
    vendor_id = fields.Many2one(
        'product.supplierinfo',
        string='Fournisseur')
    
    @api.depends("order_id.convert",'price_usd')
    def _compute_conversion(self):
        for record in self:
            record.conversion_line =  record.order_id.convert * record.price_usd
    
    
    @api.depends("product_uom_qty",'price_unit', 'conversion_line')
    def _compute_price_before_transport(self):
        for record in self:
            record.price_before_trans =  record.product_uom_qty * (record.price_unit + record.conversion_line)
    
    @api.depends('price_before_trans','order_id.total_transport')
    def _compute_percentage_value(self):
        for record in self:
            if record.order_id.total_transport != 0.0:
                record.percentage =  (record.price_before_trans * 100.0)/ record.order_id.total_transport 
    
    
    @api.depends("percentage",'order_id.convert_cad','order_id.price_douane','order_id.percent_port')
    def _compute_price_transport_douane(self):
        for record in self:
            record.price_transport_douane = (record.percentage/100.0) * (record.order_id.convert_cad + record.order_id.price_douane + record.order_id.percent_port)
    
    @api.depends("product_uom_qty",'profit','price_transport_douane','price_before_trans','order_id.cart_credit')
    def _compute_price_unit(self):
        for record in self:
            if record.order_id.cart_credit == 1 :
            #     record.price_unit_cad = (((record.price_before_trans * (record.profit/100.0)) + record.price_transport_douane )/ record.product_uom_qty) * 1.03 if record.product_uom_qty > 0  else 0
            # else:
                record.price_unit_cad = ((record.price_before_trans * (record.profit/100.0)) + record.price_transport_douane )/ record.product_uom_qty  if record.product_uom_qty > 0  else 0
    
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','price_unit_cad')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit_cad * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': line.price_unit_cad * line.product_uom_qty,
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    
    
    @api.depends("price_before_trans",'price_transport_douane', 'product_uom_qty')
    def _compute_cost_transport_douane(self):
        for record in self:
            record.costline_transport_douane =   (record.price_transport_douane + record.price_before_trans) / record.product_uom_qty  if record.product_uom_qty>0.0 else 0.0
    
    
    
    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        values = super(gss_sale_order_line, self)._prepare_procurement_values(group_id)
        values['vendor_id'] = self.vendor_id.id
        return values

    
    
   
  