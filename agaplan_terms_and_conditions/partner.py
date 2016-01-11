from openerp import models, fields, api
from openerp.tools.translate import _

class res_partner(models.Model):
    _inherit = 'res.partner'

    date_terms_signed = fields.Datetime('Date Terms Signed', help='Date on witch the sales conditions/terms are signed')
    print_terms = fields.Boolean('Print Terms', help='If true the sales conditions/terms will be printed on the documents')

    _defaults = {
        'print_terms' : True,
    }

# vim:sts=4:et
