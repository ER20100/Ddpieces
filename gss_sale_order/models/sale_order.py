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
        compute = "_compute_conversion",
        store= True
    )
    price_unit_cad = fields.Float('Prix CAD', required=True, digits='Product Price', default=0.0)

    price_before_trans =  fields.Monetary(
        string="Total avant Transport",
        compute = "_compute_price_before_transport",
        store= True
    )
    
    percentage = fields.Float(
        string="%",
        default=100.0
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
    
    @api.depends('price_usd')
    def _compute_conversion(self):
        convert = self.env['ir.config_parameter'].sudo(). \
            get_param("gss_sale_order.convert", default=1.33)
        for record in self:
            record.conversion_line =  float(convert) * record.price_usd
    
    
    @api.depends("product_uom_qty",'price_unit_cad', 'conversion_line')
    def _compute_price_before_transport(self):
        for record in self:
            record.price_before_trans =  record.product_uom_qty * (record.price_unit_cad + record.conversion_line)
    
    def _compute_percentage(self):
        for record in self:
            alltransp = sum(l.product_uom_qty * (l.price_unit_cad + l.conversion_line) for l in self.search([('order_id','=', record.order_id.id)]))
            if alltransp:
                record.percentage =  (record.price_before_trans * 100.0)/ alltransp
            else:
                record.percentage = 100.0
            # record.price_transport_douane = (record.price_before_trans / alltransp) * (record.order_id.convert_cad + record.order_id.price_douane + record.order_id.percent_port)
            record.price_unit = (((record.price_before_trans * (record.profit/100.0)) + record.price_transport_douane) / record.product_uom_qty) * 1.03 
    
    @api.onchange('percentage')
    def _onchange_percentage(self):
        for record in self:
            record.price_unit_cad = (record.percentage/(100.0*record.product_uom_qty)) -  record.conversion_line
    
   
    @api.depends('percentage','order_id.convert_cad','order_id.price_douane','order_id.percent_port')
    def _compute_price_transport_douane(self):
        for record in self:
            record.price_transport_douane = (record.percentage/100.0) * (record.order_id.convert_cad + record.order_id.price_douane + record.order_id.percent_port)

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

    
    
    @api.depends("price_before_trans",'price_transport_douane', 'product_uom_qty')
    def _compute_cost_transport_douane(self):
        for record in self:
            record.costline_transport_douane =   (record.price_transport_douane + record.price_before_trans) / record.product_uom_qty  if record.product_uom_qty>0.0 else 0.0
    
    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        values = super(gss_sale_order_line, self)._prepare_procurement_values(group_id)
        values['vendor_id'] = self.vendor_id.id
        values['note_dachat'] = self.order_id.note_dachat
        return values

    # @api.onchange('product_id')
    # def product_id_change(self):
    #     if not self.product_id:
    #         return
    #     valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
    #     # remove the is_custom values that don't belong to this template
    #     for pacv in self.product_custom_attribute_value_ids:
    #         if pacv.custom_product_template_attribute_value_id not in valid_values:
    #             self.product_custom_attribute_value_ids -= pacv

    #     # remove the no_variant attributes that don't belong to this template
    #     for ptav in self.product_no_variant_attribute_value_ids:
    #         if ptav._origin not in valid_values:
    #             self.product_no_variant_attribute_value_ids -= ptav

    #     vals = {}
    #     if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
    #         vals['product_uom'] = self.product_id.uom_id
    #         vals['product_uom_qty'] = self.product_uom_qty or 1.0

    #     product = self.product_id.with_context(
    #         lang=get_lang(self.env, self.order_id.partner_id.lang).code,
    #         partner=self.order_id.partner_id,
    #         quantity=vals.get('product_uom_qty') or self.product_uom_qty,
    #         date=self.order_id.date_order,
    #         pricelist=self.order_id.pricelist_id.id,
    #         uom=self.product_uom.id
    #     )

    #     vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

    #     self._compute_tax_id()

    #     if self.order_id.pricelist_id and self.order_id.partner_id:
           
    #         # vals['price_unit'] =  (((self.price_before_trans * (self.profit/100.0)) + self.price_transport_douane) / self.product_uom_qty) * 1.03 or 0.0
    #         vals['price_unit'] = self.price_before_trans
    #     self.update(vals)

    #     if product.sale_line_warn != 'no-message':
    #         if product.sale_line_warn == 'block':
    #             self.product_id = False

    #         return {
    #             'warning': {
    #                 'title': _("Warning for %s", product.name),
    #                 'message': product.sale_line_warn_msg,
    #             }
    #         }

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
    
    total_transport =  fields.Monetary(
        string="transport",
        
    )
     
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
                'total_transport':amount_transp,
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

    @api.model
    def create(self, values):
        result = super().create(values)
        result.order_line._compute_percentage()
        result._inverse_percent_port()
        return result
  
    def write(self, values):
        res = super().write(values)
        self.order_line._compute_percentage()
        return res
   
  