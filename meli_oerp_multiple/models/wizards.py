# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo import api, models, fields
import logging
from odoo.exceptions import UserError
from .warning import warning

_logger = logging.getLogger(__name__)


class product_template_update(models.TransientModel):
    _inherit = "mercadolibre.product.template.update"

    connection_account = fields.Many2one("mercadolibre.account",string="MercadoLibre Account")

    def product_template_update(self, context=None):
        context = context or self.env.context
        _logger.info("meli_oerp_multiple >> wizard product_template_update "+str(context))
        company = self.env.user.company_id
        product_ids = []
        if ('active_ids' in context):
            product_ids = context['active_ids']
        product_obj = self.env['product.template']

        warningobj = self.env['warning']

        account = self.connection_account
        company = (account and account.company_id) or company

        if account:
            meli = self.env['meli.util'].get_new_instance( company, account )
            if meli.need_login():
                return meli.redirect_login()
        else:
            meli = None

        meli_id = False
        if self.meli_id:
            meli_id = self.meli_id
        res = {}
        for product_id in product_ids:
            product = product_obj.browse(product_id)
            if (product):
                if self.force_meli_pub:
                    product.meli_pub = True
                    for variant in product.product_variant_ids:
                        variant.meli_pub = True
                if (product.meli_pub):
                    res = product.product_template_update( meli_id=meli_id, meli=meli, account=account )

            if 'name' in res:
                return res

        return res

class ProductTemplateBindToMercadoLibre(models.TransientModel):

    _name = "mercadolibre.binder.wiz"
    _description = "Wizard de Product Template MercadoLibre Binder"
    _inherit = "ocapi.binder.wiz"

    connectors = fields.Many2many("mercadolibre.account", string='MercadoLibre Accounts',help="Cuenta de mercadolibre origen de la publicación")
    meli_id = fields.Char( string="MercadoLibre Products Ids",help="Ingresar uno o varios separados por coma: (MLXYYYYYYY: MLA123456789, MLA458..., ML...., ... )")
    bind_only = fields.Boolean( string="Bind only using SKU", help="Solo asociar producto y variantes usando SKU (No modifica el producto de Odoo)" )
    use_barcode = fields.Boolean( string="Use Barcode" )

    def product_template_add_to_connector(self, context=None):

        context = context or self.env.context

        _logger.info("product_template_add_to_connector (MercadoLibre)")

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.template']

        res = {}
        for product_id in product_ids:

            product = product_obj.browse(product_id)

            for mercadolibre in self.connectors:
                meli_id = False
                bind_only = False
                _logger.info(_("Check %s in %s") % (product.display_name, mercadolibre.name))
                #Binding to
                if self.meli_id:
                    meli_id = self.meli_id.split(",")
                else:
                    meli_id = [False]
                if self.bind_only:
                    bind_only = self.bind_only
                for mid in meli_id:
                    product.mercadolibre_bind_to( mercadolibre, meli_id=mid, bind_variants=True, bind_only=bind_only )


    def product_template_remove_from_connector(self, context=None):

        context = context or self.env.context

        _logger.info("product_template_remove_from_connector (MercadoLibre)")

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.template']

        res = {}
        for product_id in product_ids:

            product = product_obj.browse(product_id)

            for mercadolibre in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, mercadolibre.name))
                #Binding to
                meli_id = False
                if self.meli_id:
                    meli_id = self.meli_id.split(",")
                else:
                    meli_id = [False]
                for mid in meli_id:
                    product.mercadolibre_unbind_from( account=mercadolibre, meli_id=mid )

class ProductTemplateBindUpdate(models.TransientModel):

    _name = "mercadolibre.binder.update.wiz"
    _description = "Wizard de Product Template MercadoLibre Binder Update"

    update_odoo_product = fields.Boolean(string="Update Odoo Products")
    update_odoo_product_variants = fields.Boolean(string="Update Odoo Product Variants")
    update_images = fields.Boolean(string="Update images")
    update_stock = fields.Boolean(string="Only update stock")
    update_price = fields.Boolean(string="Only update price")

    def binding_product_template_update(self, context=None):

        context = context or self.env.context

        _logger.info("binding_product_template_update (MercadoLibre)")

        company = self.env.user.company_id
        bind_ids = ('active_ids' in context and context['active_ids']) or []
        bindobj = self.env['mercadolibre.product_template']

        res = {}

        for bind_id in bind_ids:

            bindT = bindobj.browse(bind_id)
            if bindT:
                bindT.product_template_update()


class ProductVariantBindUpdate(models.TransientModel):

    _name = "mercadolibre.binder.variant.update.wiz"
    _description = "Wizard de Product Variant MercadoLibre Binder Update"

    update_odoo_product = fields.Boolean(string="Update Full Odoo Product")
    #update_odoo_product_variants = fields.Boolean(string="Update Odoo Product Variants")
    #update_images = fields.Boolean(string="Update images")
    update_stock = fields.Boolean(string="Only update stock")
    update_price = fields.Boolean(string="Only update price")

    def binding_product_variant_update(self, context=None):

        context = context or self.env.context

        _logger.info("binding_product_variant_update (MercadoLibre)")

        warningobj = self.env['warning']
        company = self.env.user.company_id
        bind_ids = ('active_ids' in context and context['active_ids']) or []
        bindobj = self.env['mercadolibre.product']

        rest = []
        correct = []

        for bind_id in bind_ids:

            bind = bindobj.browse(bind_id)
            if bind:
                if self.update_odoo_product:
                    res = bind.product_update()
                    if res and 'error' in res:
                        rest.append(res)
                    correct.append("Id: "+str(bind.conn_id)+" Product:"+str(bind.product_id.default_code))

                if self.update_price:
                    res = bind.product_post_price(context=context)
                    if res and 'error' in res:
                        rest.append(res)
                    correct.append("Id: "+str(bind.conn_id)+" Product:"+str(bind.product_id.default_code)+" Price:"+str(bind.price))

                if self.update_stock:
                    res = bind.product_post_stock(context=context)
                    if res and 'error' in res:
                        rest.append(res)
                    correct.append("Id: "+str(bind.conn_id)+" Product:"+str(bind.product_id.default_code)+" Stock:"+str(bind.stock))

        if len(rest):
            return warningobj.info( title='STOCK POST WARNING', message="Revisar publicaciones", message_html="<h3>Correct</h3>"+str(correct)+"<br/>"+"<h2>Errores</h2>"+str(rest))

        return rest

class ProductVariantBindToMercadoLibre(models.TransientModel):

    _name = "mercadolibre.variant.binder.wiz"
    _description = "Wizard de Product Variant MercadoLibre Binder"
    _inherit = "ocapi.binder.wiz"

    connectors = fields.Many2many("mercadolibre.account", string='MercadoLibre Accounts')
    meli_id = fields.Char(string="MercadoLibre Product Id (MLXYYYYYYY: MLA123456789 )")
    meli_id_variation = fields.Char(string="MercadoLibre Product Variation Id ( ZZZZZZZZZ: 123456789 )")
    bind_only = fields.Boolean( string="Bind only using SKU", help="Solo asociar producto y variantes usando SKU (No modifica el producto de Odoo)" )

    def product_product_add_to_connector(self, context=None):

        context = context or self.env.context

        _logger.info("product_product_add_to_connector (MercadoLibre)")

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.product']

        res = {}
        for product_id in product_ids:

            product = product_obj.browse(product_id)

            for mercadolibre in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, mercadolibre.name))
                meli_id = False
                meli_id_variation = False
                #Binding to
                if self.meli_id:
                    meli_id = self.meli_id

                if self.meli_id_variation:
                    meli_id_variation = self.meli_id_variation

                product.mercadolibre_bind_to( mercadolibre, meli_id=meli_id, meli_id_variation=meli_id_variation  )


    def product_product_remove_from_connector(self, context=None):

        context = context or self.env.context

        _logger.info("product_product_remove_from_connector (MercadoLibre)")

        company = self.env.user.company_id
        product_ids = context['active_ids']
        product_obj = self.env['product.product']

        res = {}
        for product_id in product_ids:

            product = product_obj.browse(product_id)

            for mercadolibre in self.connectors:
                _logger.info(_("Check %s in %s") % (product.display_name, mercadolibre.name))
                #Binding to
                meli_id = False
                meli_id_variation = False
                if self.meli_id:
                    meli_id = self.meli_id
                if self.meli_id_variation:
                    meli_id_variation = self.meli_id_variation
                product.mercadolibre_unbind_from( account=mercadolibre, meli_id=meli_id, meli_id_variation=meli_id_variation )

class ProductTemplatePostExtended(models.TransientModel):

    _inherit = "mercadolibre.product.template.post"

    force_meli_new_pub = fields.Boolean(string="Crear una nueva publicación")
    connectors = fields.Many2one("mercadolibre.account",string="MercadoLibre Account")

    def product_template_post(self, context=None):

        context = context or self.env.context
        company = self.env.user.company_id
        _logger.info("multiple product_template_post: context: " + str(context))

        product_ids = []
        if ('active_ids' in context):
            product_ids = context['active_ids']
        product_obj = self.env['product.template']
        warningobj = self.env['warning']

        res = {}
        
        _logger.info("context in product_template_post:")
        _logger.info(self.env.context)
        custom_context = {
            'connectors': self.connectors,
            'force_meli_new_pub': self.force_meli_new_pub,
            
            'force_meli_pub': self.force_meli_pub,
            'force_meli_active': self.force_meli_active,
            'post_stock': self.post_stock,
            'post_price': self.post_price
        }
        posted_products = 0
        for product_id in product_ids:
            
            productT = product_obj.browse(product_id)

            for account in self.connectors:
                comp = account.company_id or company
                meli = self.env['meli.util'].get_new_instance( comp, account )
                if meli:
                    if meli.need_login():
                        return meli.redirect_login()
                    #res = productT.with_context(custom_context).product_template_post( context=None, account=account, meli=meli )
                    
                    if (self.force_meli_pub and not productT.meli_pub):
                        productT.meli_pub = True
                    if (productT.meli_pub):
    
                        if self.post_stock:
                            res = productT.with_context(custom_context).product_template_post_stock(meli=meli,account=account)
                        if self.post_price:
                            res = productT.with_context(custom_context).product_template_post_price(meli=meli,account=account)
                        if not self.post_stock and not self.post_price:
                            res = productT.with_context(custom_context).product_template_post(context=None, account=account, meli=meli)

                    if res and 'name' in res:
                        return res
                    posted_products+=1
                    
        if (posted_products==0 and not 'name' in res):
            res = warningobj.info( title='MELI WARNING', message="Se intentaron publicar 0 productos. Debe forzar las publicaciones o marcar el producto con el campo Meli Publication, debajo del titulo.", message_html="" )

        return res

class SaleOrderGlobalInvoice(models.TransientModel):

    _name = "sale.order.global.invoice.meli.wiz"
    _description = "Wizard de Factura Global"


    connection_account = fields.Many2one( "mercadolibre.account", string='MercadoLibre Account',help="Cuenta de mercadolibre origen de la publicación")
    journal_id = fields.Many2one( "account.journal", string='Diario', help="Diario contable" )
    partner_id = fields.Many2one( "res.partner", string="Cliente", help="Debe seleccionar un cliente", required=True )
    account_id = fields.Many2one( "account.account", string='Cuenta', help="Cuenta" )
    invoice = fields.Many2one( "account.move", string='Existing draft invoice',help='si quiere seguir agregando lineas a una factura global existente')
    total = fields.Selection( [('amount_total','Total Odoo'),('meli_total_amount','Total Amount'),('meli_paid_amount','Paid Amount')], string="Total Amount",  ) 
    update_order = fields.Boolean( string="Actualizar orden", default=False )
    fix = fields.Boolean( string="Reprocesar", default=False )

    def create_sale_order_global_invoice( self, context=None ):

        context = context or self.env.context

        _logger.info("sale_order_global_invoice (MercadoLibre)")
        orders_ids = ('active_ids' in context and context['active_ids']) or []
        orders_obj = self.env['sale.order']

        #self._cr.autocommit(False)
        try:
            
            if not self.connection_account:
                raise UserError('Connection Account not defined!')
                
            config = self.connection_account.configuration
            
            company = self.connection_account.company_id or self.env.user.company_id
            
            partner_id = self.partner_id
            account_id = self.account_id
            
            #journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
            
            if not config:
                raise UserError('Connection Account Config not defined!')
            
            product_vml = self.env['product.product'].search( [ ( 'default_code', '=', 'VENTAML' ) ], limit=1 )
            
            if not product_vml:
                product_vml = self.env['product.product'].create({ "default_code": 'VENTAML', "name": 'Venta ML' })
                
            if product_vml:
                product_vml = product_vml[0]
                
            if not partner_id:
                raise UserError('Must select a client!')
                
            if not product_vml:
                raise UserError("Product with default_code (Referencia) 'VENTAML' not founded or cannot be created.")
            
            invoice  = self.invoice

            inv_fields = { 
                "name": (invoice and invoice.name) or "Factura Global",
                
                "journal_id": (invoice and invoice.journal_id.id) or (self.journal_id and self.journal_id.id) or (config.mercadolibre_invoice_journal_id and config.mercadolibre_invoice_journal_id.id),
                "partner_id": (invoice and invoice.partner_id.id) or partner_id.id,
                "company_id": ( company and company.id ),
                "move_type": "out_invoice",
                "invoice_line_ids": []                    
            }            

            if not invoice:
                _logger.info("Create global invoice:"+str(inv_fields))
                invoice = self.env["account.move"].create(inv_fields)
                
            if not invoice:
                raise UserError('Error, invoice couldnt be created or found.')

            orders_ids_fix = []
            if self.fix and invoice and invoice.invoice_line_ids:
                for iline in invoice.invoice_line_ids:
                    order = orders_obj.search([('name','=',iline.name)], limit=1)
                    if order:
                        orders_ids_fix.append(order.id)
                        orders_ids.append(order.id)

            for order_id in orders_ids:

                _logger.info("Adding order to invoice: %s " % (order_id) )

                order = orders_obj.browse(order_id)
                
                if order:
                    #check meli_status_brief to update
                    #mstatus = order.meli_status_brief
                    self.update_order and order.meli_orders and order.meli_orders[0].orders_update_order()
                    
                    total_amount = order.meli_total_amount or order.amount_total
                    if self.total == 'amount_total':
                        total_amount = order.amount_total or total_amount
                    if self.total == 'meli_total_amount':
                        total_amount = order.meli_total_amount or total_amount
                    if self.total == 'meli_paid_amount':
                        total_amount = order.meli_paid_amount or total_amount
                        
                    #search order id or name
                    ifields = {
                        'account_id': (account_id and account_id.id) or invoice.journal_id.default_account_id.id,
                        'move_id': invoice and invoice.id,
                        'product_id': product_vml and product_vml.id,
                        'product_uom_id': product_vml.uom_id.id,
                        'quantity': 1,
                        'discount': 0,
                        'name': ''+str(order.name),
                        'meli_sale_name': ''+str(order.name),
                        'meli_sale_id': order.id,
                        'price_unit': total_amount,
                        'tax_ids': [(6, 0, product_vml.taxes_id.ids)],
                        #'credit': order.meli_total_amount,
                        #'debit': order.meli_total_amount,
                        #'amount_currency': order.meli_total_amount
                    }
                    ifields2 = {
                        'account_id': invoice.journal_id.default_account_id.id,
                        'move_id': invoice and invoice.id,
                        #'product_id': product_vml and product_vml.id,
                        'quantity': 1,
                        
                        'name': ''+str(order.name),
                        'price_unit': order.meli_total_amount,
                        #'amount_currency': order.meli_total_amount,
                        #'debit': order.meli_total_amount,
                        #'amount_currency': order.meli_total_amount
                    }
                    
                    _logger.info("Adding order to invoice: %s " % (str(ifields)) )
                    
                    #in
                    inline = self.env["account.move.line"].search([
                                                            ( 'product_id', '=', product_vml.id ),
                                                            ( 'move_id', '=', invoice.id ),
                                                            ( 'name', '=', ifields['name'] )
                                                            ], limit=1)
                    if not inline:
                        #inline = self.env["account.move.line"].create( ifields )
                        inv_fields["invoice_line_ids"].append( (0,0, ifields ) )
                        for oli in order.order_line:
                            oli.qty_invoiced = oli.qty_to_invoice
                            oli.invoice_status = "invoiced"
                        order.invoice_status = "invoiced"
                    else:
                        #inv_fields["invoice_line_ids"].append( (0,0, ifields ) )
                        pass
                        
                    
                    #invoice.invoice_line_ids = 
            if len(inv_fields["invoice_line_ids"]):
                _logger.info("fields:"+str(fields))
                invoice.write(inv_fields)
                
                for iline in invoice.invoice_line_ids:
                    order = iline.meli_sale_id
                    if order:
                        for oli in order.order_line:
                            oli.qty_invoiced = oli.qty_to_invoice
                            oli.invoice_status = "invoiced"
                        order.invoice_status = "invoiced"

        except Exception as e:
            _logger.info("order_update > Error creando factura global")
            _logger.error(e, exc_info=True)
            #self._cr.rollback()
            raise e

        return {}

class NotificationsProcessWiz(models.TransientModel):
    _name = "mercadolibre.notification.wiz"
    _description = "MercadoLibre Notifications Wiz"

    connection_account = fields.Many2one( "mercadolibre.account", string='MercadoLibre Account',help="Cuenta de mercadolibre origen de la publicación")
    
    def process_notifications( self, context=None ):

        context = context or self.env.context

        _logger.info("process_notifications (MercadoLibre)")
        noti_ids = ('active_ids' in context and context['active_ids']) or []
        noti_obj = self.env['mercadolibre.notification']
        
        try:
            meli = None
            if self.connection_account:
                meli = self.env['meli.util'].get_new_instance( self.connection_account.company_id, self.connection_account )
                if meli.need_login():
                    return meli.redirect_login()
            
            ##if not self.connection_account:
            #    raise UserError('Connection Account not defined!')
            for noti_id in noti_ids:

                _logger.info("Processing notification: %s " % (noti_id) )

                noti = noti_obj.browse(noti_id)
                ret = []
                if noti:
                    reti = None
                    if self.connection_account and noti.connection_account and noti.connection_account.id==self.connection_account.id:
                        reti = noti.process_notification(meli=meli)
                    else:
                        reti = noti.process_notification()
                    if reti:
                        ret.append(str(reti))
                    
        except Exception as e:
            _logger.info("process_notifications > Error procesando notificacion")
            _logger.error(e, exc_info=True)
            _logger.error(str(ret))
            #self._cr.rollback()
            raise e
            
        _logger.info("Processing notification result: %s " % (str(ret)) )
            
            
