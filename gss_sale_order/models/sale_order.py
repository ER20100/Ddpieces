# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
import json
from odoo.tools.misc import get_lang

class gss_sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    reference  = fields.Char(related="product_id.default_code", string="No PIECE")
    price_usd = fields.Float(
        string="Prix USD",
    )
    conversion_line = fields.Float(
        string="Conversion en CAD",
        compute = "compute_all",
        store= True
    )
    price_unit_cad = fields.Float('Prix CAD', required=True, digits='Product Price', default=0.0)

    price_before_trans =  fields.Monetary(
        string="Total avant Transport",
        compute = "compute_all",
        store= True
    )
    
    percentage = fields.Float(
        string="%",
       
    )
    
    price_transport_douane = fields.Monetary(
        string="Transports et douanes Canadiens",
        compute = "compute_all",
        store= True
    )
    
    costline_transport_douane = fields.Monetary(
        string="Cout unitaire Incl Transport",
        compute = "compute_all",
        store= True
    )
    
    profit  = fields.Float(
        string="Profit %",
        default=155.0,
        store=True,
    )
    transport_mode = fields.Selection([
        ("road","Transport routier"),
        ("sea","Transport maritime"),
        ("train","Transport ferroviaire"),
        ("fly","Transport aérien")], string='Mode de Transport')
  
    vendor_id = fields.Many2one(
        'product.supplierinfo',
        string='Fournisseur')
    
    # @api.depends('price_usd')
    # def _compute_conversion(self):
    #     convert = self.env['ir.config_parameter'].sudo(). \
    #         get_param("gss_sale_order.convert", default=1.33)
    #     for record in self:
    #         record.conversion_line =  float(convert) * record.price_usd
    
    
    # @api.depends("product_uom_qty",'price_unit_cad', 'conversion_line')
    # def _compute_price_before_transport(self):
    #     for record in self:
    #         record.price_before_trans =  record.product_uom_qty * (record.price_unit_cad + record.conversion_line)
    
    # def _compute_percentage(self):
    #         return self.order_id.order_percentage()
          
                
    # @api.onchange('percentage')     
    # def _inverse_percentage(self):
    #     for record in self:
    #         record.price_before_trans = (record.percentage/100.0) * record.order_id.total_transport
    
    # @api.onchange('profit')
    # def _onchange_profit(self):
    #     for record in self:
    #         record.price_unit = (((record.price_before_trans * (record.profit/100.0)) + record.price_transport_douane) / record.product_uom_qty) * 1.03 
            
    # @api.depends('percentage','order_id.convert_cad','order_id.price_douane','order_id.percent_port')
    # def _compute_price_transport_douane(self):
    #     for record in self:
    #         record.price_transport_douane = (record.percentage/100.0) * (record.order_id.convert_cad + record.order_id.price_douane + record.order_id.percent_port)

    # def _inverse_percentage(self):
    #    pass
    
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': line.price_unit * line.product_uom_qty,
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    
    
    # @api.depends("price_before_trans",'price_transport_douane', 'product_uom_qty')
    # def _compute_cost_transport_douane(self):
    #     for record in self:
    #         record.costline_transport_douane =   (record.price_transport_douane + record.price_before_trans) / record.product_uom_qty  if record.product_uom_qty>0.0 else 0.0
    
    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        values = super(gss_sale_order_line, self)._prepare_procurement_values(group_id)
        values['vendor_id'] = self.vendor_id.id
        values['note_dachat'] = self.order_id.note_dachat
        return values

 
    @api.depends('product_uom_qty','percentage',
                 'order_id.price_douane','order_id.percent_port',
                 'price_unit_cad','price_usd','profit',
                 'order_id.total_transport','order_id.transport_usd','order_id.transport_cad','order_id.package')
    def compute_all(self):
        convert = self.env['ir.config_parameter'].sudo(). \
            get_param("gss_sale_order.convert", default=1.33)
        for record in self:
            conversionline = tprice_before_trans = tpercentage = tprice_transport_douane = tcostline_transport_douane = tprice = convertcad = 0.0
            conversionline =  float(convert) * record.price_usd
            convertcad = ((float(convert) * record.order_id.transport_usd) + record.order_id.transport_cad + record.order_id.package) * 1.2
            tprice_before_trans = record.product_uom_qty * (record.price_unit_cad + conversionline)
            tpercentage = (tprice_before_trans / record.order_id.total_transport) * 100.0 if not record.percentage else record.percentage
            tprice_transport_douane = (tpercentage/100.0) * (convertcad + record.order_id.price_douane + record.order_id.percent_port)
            tcostline_transport_douane =   (tprice_transport_douane + tprice_before_trans) / record.product_uom_qty  if record.product_uom_qty>0.0 else 0.0
            tprice = (((tprice_before_trans * (record.profit/100.0)) + tprice_transport_douane) / record.product_uom_qty) * 1.03
            record.update({
                'conversion_line':conversionline,
                'price_before_trans':tprice_before_trans,
                'price_transport_douane':tprice_transport_douane,
                'costline_transport_douane':tcostline_transport_douane,
                'price_unit':tprice,
                'percentage':tpercentage,
            })
   
            
class gss_sale_order(models.Model):
    _inherit= 'sale.order'
    
    transport_usd = fields.Monetary(
        string="Transport USD"
    )
    transport_cad = fields.Monetary(
        string="Transport CAD"
    )
    package = fields.Monetary(
        string="Emballage",
        default = 4.5
    )
    note_dachat = fields.Char()
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
    )
    
    cart_credit =  fields.Integer(
        string="Carte Credit",
        default= 1
    )
    
    cost_total =  fields.Monetary(
        string="Cout total",
        store=True,
        compute = "_compute_total_cost",
    )
    
    
    # price_ccr_total =  fields.Monetary(
    #     string="Prix de vente CC",
    #     compute = "_compute_total_cost",
    #     store=True,
    # )
    
    price_profit_total =  fields.Monetary(
        string="Profit Total",
        store=True,
        compute = "_compute_price_total",
    )
    
    total_transport =  fields.Float(
        string="transport", 
        compute='order_percentage',
        store=True  
    )
     
    @api.depends('order_line')
    def order_percentage(self):
        for record in self:
            record.total_transport = sum(l.product_uom_qty * (l.price_unit_cad + l.conversion_line) for l in record.order_line)
                
    @api.depends('transport_usd','transport_cad','package')
    def _compute_convert_cad(self):
        convert = self.env['ir.config_parameter'].sudo(). \
            get_param("gss_sale_order.convert", default=1.33)
        for record in self:
            record.convert_cad =  ((float(convert) * record.transport_usd) + record.transport_cad + record.package) * 1.2
    
    def _inverse_percent_port(self):
        for order in self:
            tamount_US = tamount_transp  = 0.0
            for line in order.order_line:
               
                tamount_US += line.price_usd * line.product_uom_qty 
                tamount_transp += line.price_before_trans   
            order.update({
                'percent_port':(tamount_transp * 6.0)/100.0 if tamount_US > 0.0 else 0.0 ,
            })
    
    @api.onchange('percent_port')
    def onchange_percent_port(self):
        for rec in self.order_line:
            rec.price_unit_cad = (self.percent_port / 0.06)/rec.product_uom_qty - rec.conversion_line
      
                
    @api.depends('order_line.price_before_trans','order_line.percentage')
    def _compute_total_cost(self):
        for order in self:
            amount_US = amount_transp = cost_total = cost_total1 = 0.0
            for line in order.order_line:
               
                amount_US += line.price_usd * line.product_uom_qty 
                amount_transp += line.price_before_trans
                cost_total1 += line.price_transport_douane
                cost_total += line.price_before_trans 
                
            order.update({
                'cost_total':cost_total + cost_total1,
            })
           
            
    
    @api.depends('cost_total','amount_untaxed')
    def _compute_price_total(self):  
        for rec in self:
            rec.price_profit_total = (rec.amount_untaxed/1.03) - rec.cost_total
            
            
    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

   
  