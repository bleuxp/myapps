# -*- coding: utf-8 -*-

from barcode.writer import ImageWriter
from barcode import EAN8
import base64
import io
from PIL import Image, ImageFile
import qrcode
import math
import re
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductAutoBarcode(models.Model):
    _inherit = 'product.product'


class ProductTemplateAutoBarcode(models.Model):
    _inherit = 'product.template'

    barcode_image = fields.Binary()

    @api.model
    def create(self, vals_list):
        templates = super(ProductTemplateAutoBarcode, self)
        barcode_id = templates.id
        barcode_search = False
        while not barcode_search:
            ean = generate_ean('29' + str(barcode_id))
            if self.env['product.product'].search([('barcode', '=', ean)]):
                barcode_search = False
            else:
                barcode_search = True
        if "barcode" not in vals_list or not barcode_search:
            vals_list["barcode"] = ean
        im_barcode = EAN8(vals_list["barcode"], writer=ImageWriter())
        img_byte_arr = io.BytesIO()
        png_barcode = im_barcode.save("barcode_product", options={"write_text": False})
        img = Image.open(png_barcode, mode='r')
        thresh = 200
        fn = lambda x: 255 if x > thresh else 0
        im = img.convert('L').point(fn, mode='1')
        im.save(img_byte_arr, format='BMP')
        img_byte_arr = img_byte_arr.getvalue()
        encoded = base64.b64encode(img_byte_arr)
        vals_list["barcode_image"] = encoded
        #img_qr = io.BytesIO()
        #qrcode.make(vals_list["barcode"]).save(img_qr)
        #vals_list["barcode_image"] = base64.b64encode(img_qr.getvalue())
        templates = super(ProductTemplateAutoBarcode, self).create(vals_list)
        return templates

    def generate_new_barcode(self):
        for prod_id in self:
            ean = generate_ean('29' + str(prod_id.id))
            prod_id.barcode = ean

    def new_barcode_image(self):
        if self.barcode:
            my_barcode = EAN8(self.barcode, writer=ImageWriter())
            #img_qr = io.BytesIO()
            #qrcode.make(my_barcode).save(img_qr)
            #self.barcode_image = base64.b64encode(img_qr.getvalue())
            img_byte_arr = io.BytesIO()
            png_barcode = my_barcode.save("barcode_product", options={"write_text": False})
            img = Image.open(png_barcode, mode='r')
            thresh = 200
            fn = lambda x: 255 if x > thresh else 0
            im = img.convert('L').point(fn, mode='1')
            im.save(img_byte_arr, format='BMP')
            img_byte_arr = img_byte_arr.getvalue()
            encoded = base64.b64encode(img_byte_arr)
            self.barcode_image = encoded
        else:
            raise UserError(_('Warning! Please insert or create New Barcode'))


def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 8:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum
    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 8:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "00000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:8]
    if len(ean) < 8:
        ean = ean + '0' * (8 - len(ean))
    return ean[:-1] + str(ean_checksum(ean))
