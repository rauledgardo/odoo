# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo import api, models, fields
import logging

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

        for product_id in product_ids:
            
            productT = product_obj.browse(product_id)
                        
            for mercadolibre in self.connectors:
                comp = mercadolibre.company_id or company
                meli = self.env['meli.util'].get_new_instance( comp, mercadolibre )
                if meli:
                    if meli.need_login():
                        return meli.redirect_login()
                    res = productT.with_context(
                                                {
                                                    'connectors': self.connectors,
                                                    'force_meli_new_pub': self.force_meli_new_pub,
                                                    'force_meli_pub': self.force_meli_pub, 
                                                    'force_meli_active': self.force_meli_active
                                                }
                                                ).product_template_post( context=None, account=mercadolibre, meli=meli )
                    if res and 'name' in res:
                        return res
        
        return res        
                                     
