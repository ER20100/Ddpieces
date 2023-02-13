# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

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
        compute = "_compute_conversion_currency",
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
        default= 0
    )
    
    cost_total =  fields.Monetary(
        string="Cout total",
        compute = "_compute_total_cost",
        store=True,
    )
    
    
    price_ccr_total =  fields.Monetary(
        string="Prix de vente CC",
        compute = "_compute_total_cost",
        store=True,
    )
    
    price_profit_total =  fields.Monetary(
        string="Profit Total",
        compute = "_compute_total_cost",
        store=True,
    )
    
    total_transport =  fields.Monetary(
        string="transport",
        compute = "_compute_total_cost",
        store=True,
    )
    
    def update_currency_rates_manually(self):
        self.ensure_one()
        if not (self.company_id.update_currency_rates()):
            raise UserError(_('Unable to connect to the online exchange rate platform. The web service may be temporary down. Please try again in a moment.'))
    
    @api.depends("convert",'transport_usd','transport_cad','package')
    def _compute_convert_cad(self):
        for record in self:
            record.convert_cad =  ((record.convert * record.transport_usd) + record.transport_cad + record.package) * 1.2
    
    @api.depends("order_line",'cart_credit','amount_total')
    def _compute_total_cost(self):
        for record in self:
            amount = sum(line.price_unit * line.product_uom_qty for line in record.order_line)
            if amount > 0.0:
                record.percent_port = (sum(record.order_line.mapped('price_before_trans')) * 6.0)/100.0
            record.cost_total = sum(line.price_before_trans + line.price_transport_douane for line in record.order_line)
            record.price_ccr_total = record.amount_total / 1.03 if record.cart_credit == 1 else 0
            record.price_profit_total = record.price_ccr_total - record.cost_total if record.cart_credit == 1 else record.amount_total - record.cost_total
            record.total_transport = sum(record.order_line.mapped('price_before_trans'))
            
    def _compute_conversion_currency(self):
        for record in self:
            usd_obj = self.env.ref('base.USD')
            record.convert = self.env['res.currency']._get_conversion_rate(usd_obj, record.currency_id, record.company_id, fields.Date.today())
            
    

class gss_sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    reference  = fields.Char(related="product_id.default_code", string="No PIECE")
    price_usd = fields.Float(
        string="Prix USD",
        compute = "_get_conversion_price_usd",
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
    
    # partner_id = fields.Many2one('res.partner',
    #                               string='Fournisseur' )
    
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
                record.price_unit_cad = (((record.price_before_trans * (record.profit/100.0)) + record.price_transport_douane )/ record.product_uom_qty) * 1.03 if record.product_uom_qty > 0  else 0
            else:
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
    
    @api.depends("price_unit")
    def _get_conversion_price_usd(self):
        for record in self:
            usd_obj = self.env.ref('base.USD')
            record.price_usd = self.env['res.currency']._convert( record.price_unit, usd_obj, record.company_id, fields.Date.today(), round=True)
  