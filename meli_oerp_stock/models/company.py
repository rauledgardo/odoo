# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, osv, models, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

import pdb

#from .meli_oerp_config import *
#from .warning import warning

import requests
#from ..melisdk.meli import Meli

class ResCompany(models.Model):

    _inherit = "res.company"

    mercadolibre_stock_warehouse = fields.Many2one("stock.warehouse", string="Stock Warehouse Default", help="Almacen predeterminado")
    mercadolibre_stock_location_to_post = fields.Many2one("stock.location", string="Stock Location To Post", help="Ubicación desde dónde publicar el stock")
    mercadolibre_stock_location_to_post_many = fields.Many2many("stock.location", string="Stock Location To Post", help="Ubicaciones desde dónde publicar el stock")

    mercadolibre_stock_warehouse_full = fields.Many2one("stock.warehouse", string="Stock Warehouse Default for FULL", help="Almacen predeterminado para modo fulfillment")
    mercadolibre_stock_location_to_post_full = fields.Many2one("stock.location", string="Stock Location To Post for Full", help="Ubicación desde dónde publicar el stock en modo Full")

    mercadolibre_order_confirmation_delivery = fields.Selection([ ("manual", "No entregar"),
                                                ("paid_confirm_deliver", "Pagado > Entregar"),
                                                ("paid_confirm_shipped_deliver", "Pagado > Entregado > Entregar")],
                                                string='Acción al confirmar un pedido',
                                                help='Acción al confirmar una orden o pedido de venta')

    mercadolibre_order_confirmation_delivery_full = fields.Selection([ ("manual", "No entregar"),
                                                ("paid_confirm_deliver", "Pagado > Entregar"),
                                                ("paid_confirm_shipped_deliver", "Pagado > Entregado > Entregar")],
                                                string='(FULL) Acción al confirmar un pedido',
                                                help='(FULL) Acción al confirmar una orden o pedido de venta')

    #TODO: process
    mercadolibre_stock_filter_order_datetime = fields.Datetime("Order Closed Date (For shipping)")
    mercadolibre_stock_filter_order_datetime_to = fields.Datetime("Order Closed Date To (For shipping)")

    #TODO: activate
    mercadolibre_stock_virtual_available = fields.Selection([("virtual","Virtual (quantity-reserved)"),("theoretical","En mano (quantity)")],default='virtual')

    #TODO: activate
    #mercadolibre_stock_sku_regex = fields.Char(string="Sku Regex")

    #TODO: activate
    mercadolibre_stock_sku_mapping = fields.Many2many("meli_oerp.sku.rule",string="Sku Rules")

    #TODO:
    #si shipped que haga automaticamente ejecute la entrega
    #mercadolibre_shipped = fields.Boolean()
    #mercadolibre_stock_filter_order_datetime = fields.Datetime("Order Closed Date (For shipping)")
    #mercadolibre_stock_filter_order_datetime_to = fields.Datetime("Order Closed Date To (For shipping)")

    #procesar cuando es "Comprar"
    #mercadolibre_stock_sale_route_process = fields.Boolean(string="Routing Sale")
    #producir
    mercadolibre_stock_mrp_production_process = fields.Boolean(string="Process Manufacturing Productions",default=False,index=True)
