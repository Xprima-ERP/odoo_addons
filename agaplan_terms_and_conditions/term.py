from openerp import models, fields, api
from openerp.tools.translate import _


class term_term(models.Model):
    _name = "term.term"
    _description = "Terms and conditions"

    name = fields.Char('Name', size=64, required=True )
    pdf = fields.Binary('PDF File', help="The PDF file to attach to the report", required=True)
    mode = fields.Selection([('begin','Before report'),('end','After report'),('duplex','Every other page')], string="Insertion mode", required=True)
    term_rule_ids = fields.One2many('term.rule','term_id','Uses',help='reports where the term is used')


class term_rule(models.Model):
    _name = 'term.rule'
    _description = 'Rules to define where the linked term is to be used.'

    sequence = fields.Integer('Sequence')
    term_id = fields.Many2one('term.term','Term', required=True)
    company_id = fields.Many2one('res.company','Company')
    report_id = fields.Many2one('ir.actions.report.xml', 'Report', required=True)
    report_name = fields.Char('Report Name', size=64, readonly=True, related="report_id.report_name")
    
    condition = fields.Text('Condition', help='condition on when to print the term')

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'term.rule', context=c)
    }


class report_xml(models.Model):
    _inherit = 'ir.actions.report.xml'

    term_rule_ids = fields.One2many('term.rule','report_id',help='List of possible terms to be added.')


class res_company(models.Model):
    _inherit = 'res.company'

    term_rule_ids = fields.One2many('term.rule','company_id',help='List of terms for this company.')


# vim:sts=4:et
