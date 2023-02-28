# -*- coding: utf-8 -*-
# from odoo import http


# class GssSaleOrder(http.Controller):
#     @http.route('/gss_sale_order/gss_sale_order', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gss_sale_order/gss_sale_order/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('gss_sale_order.listing', {
#             'root': '/gss_sale_order/gss_sale_order',
#             'objects': http.request.env['gss_sale_order.gss_sale_order'].search([]),
#         })

#     @http.route('/gss_sale_order/gss_sale_order/objects/<model("gss_sale_order.gss_sale_order"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gss_sale_order.object', {
#             'object': obj
#         })
