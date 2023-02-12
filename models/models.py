# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosCategory(models.Model):
    _inherit = "pos.category"

    price_by_weight = fields.Float ('Prix Categ /g', default=0.0)
    total_by_weight = fields.Float ('Prix Total /g', readonly=True, default=0.0)

    @api.onchange('price_by_weight','parent_id')
    def _onchange_price_by_weight(self):
        products = self.env['product.template'].search([('pos_categ_id', 'in', self.ids)])
        self.total_by_weight = self.price_by_weight
        if self.parent_id :
            self.total_by_weight = self.parent_id.total_by_weight + self.price_by_weight
            categs = self.env['pos.category'].search([('parent_id', 'in', self.ids)])
            for categ in categs :
                categ.total_by_weight = self.total_by_weight + categ.total_by_weight
        for pro in products :
            if not pro.uniq_price:
                pro.list_price = self.total_by_weight * pro.weight


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    categ_price = fields.Float ('Prix Vente /g', related='pos_categ_id.price_by_weight',)
    uniq_price = fields.Boolean ('Prix Unique')

    purchase_price_by_gramme = fields.Float ('Prix Achat /g')

    @api.onchange('categ_price', 'list_price', 'weight')
    def _onchange_price_by_weight(self):
        if not self.uniq_price and self.categ_price and self.weight:
            self.list_price = self.categ_price * self.weight

    @api.onchange('standard_price', 'purchase_price_by_gramme', 'weight')
    def _onchange_cost_price_by_weight(self):
        if self.standard_price and self.weight:
            self.purchase_price_by_gramme = self.standard_price / self.weight
        if self.purchase_price_by_gramme and self.weight:
            self.standard_price = self.purchase_price_by_gramme * self.weight


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    gramme_price = fields.Float('Prix /g', related='product_id.purchase_price_by_gramme', readonly=False)
    weight = fields.Float('Poid', related='product_id.weight', readonly=False)

    @api.onchange('gramme_price', 'weight')
    def _onchange_price_by_weight(self):
        if self.gramme_price and self.weight:
            self.product_id.standard_price = self.price_unit = self.gramme_price * self.weight

    @api.onchange('pos_categorie', 'weight')
    def _onchange_pos_categorie(self):
        if self.pos_categorie.price_by_weight > 0 and self.weight:
            self.sale_price = self.pos_categorie.price_by_weight * self.weight
            self.product_id.categ_price = self.pos_categorie.price_by_weight