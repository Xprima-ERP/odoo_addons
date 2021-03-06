# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api
from openerp.osv import fields as osv_fields
from openerp.tools.translate import _
from openerp.tools import ustr
from openerp.exceptions import AccessError, except_orm


class mail_message(models.Model):
    _inherit = 'mail.message'

    def compute_partner(
        self,
        active_model='res.partner', model='mail.message', res_id=1,
    ):
        """
        Finds all 'active_model' references in 'model/res_id' instance
        """

        context = self.env.context
        if context is None:
            context = {}

        target_ids = set()

        # Check references directly in message table (many2one and one2one).

        current_obj = self.env[model]
        cr = self.env.cr

        cr.execute((
            "SELECT name FROM ir_model_fields WHERE relation='{active_model}' "
            "and model = '{model}' and ttype not in ('many2many', 'one2many');"
        ).format(active_model=active_model, model=model))

        current_data = current_obj.browse([res_id])[0]

        for name in cr.fetchall():
            name = str(name[0])

            var = current_data[name]

            if var:
                target_ids.add(var[0].id)

        # Check references in 'active_model' m2m relation
        # tables pointing to model/res_id

        current_obj = self.env[active_model]

        cr.execute((
            "select name from ir_model_fields where relation='{model}' "
            " and ttype in ('many2many') and model='{active_model}';"
        ).format(active_model=active_model, model=model))

        for field in cr.fetchall():

            field = str(field[0])

            if not current_obj:
                continue

            column = current_obj._columns.get(field)

            if not column or not (
                isinstance(column, fields.Many2many)
                or isinstance(column, osv_fields.many2many)
                or isinstance(column, osv_fields.function)
                    and column.store
            ):
                continue

            field_data = current_obj._columns[field]

            if not field_data:
                continue

            # Read from the m2m relation table

            model_m2m, rel1, rel2 = field_data._sql_names(current_obj)
            requete = (
                "SELECT {rel1} FROM {model_m2m} WHERE {rel2}={res_id};"
            ).format(
                rel1=rel1,
                model_m2m=model_m2m,
                rel2=rel2,
                res_id=res_id)

            cr.execute(requete)
            sec_target_ids = cr.fetchall()
            for sec_target_id in sec_target_ids:
                target_ids.add(sec_target_id[0])

        return list(target_ids)

    @api.depends('model')
    def _get_object_name(self):

        model_obj = self.env['ir.model']

        for message in self:

            model_ids = model_obj.search(
                [('model', '=', message.model)], limit=1)

            if not model_ids:
                continue

            message.object_name = model_ids[0].name

    @api.depends('res_id')
    def _get_body_txt(self):

        for message in self:
            if not message.res_id:
                continue

            record_data = self.env[message.model].browse(message.res_id)
            if message.model in ['crm.meeting', 'crm.lead']:
                message.body_txt = record_data.description
            elif message.model in ['calendar.attendee']:
                message.body_txt = record_data.display_name
            else:
                message.body_txt = record_data.name

    # Fields

    partner_ids = fields.Many2many(
        'res.partner',
        'message_partner_rel', 'message_id', 'partner_id',
        'Partners')

    object_name = fields.Char(
        string='Object Name', size=64, store=True, compute=_get_object_name)

    body_txt = fields.Text(
        string='Content', store=True, compute=_get_body_txt)

    _order = 'date desc'

    @api.model
    def create(self, vals):
        if not vals.get('partner_ids'):
            target_ids = []
            if vals.get('res_id') and vals.get('model'):
                target_ids = self.compute_partner(
                    active_model='res.partner',
                    model=vals.get('model'), res_id=vals.get('res_id'),)

            vals.update({'partner_ids': [(6, 0, target_ids)], })

        return super(mail_message, self.with_context({'default_status': 'outgoing'})).create(vals)

    # Xprima Patch. 'See own leads' users are restricted to messages from their team.
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        """ If user doesn't have access to all messages, reduce list of ids """

        try:
            self.check_access_rule(cr, uid, ids, 'read', context=context)
        except except_orm:
            # Do not have access to sale.order ids
            # This happens for users with see own leads
            # For now, fail silently.
            # TODO: Filter out the ids that cause the failure.

            ids = []

        return super(mail_message, self).read(
            cr, uid, ids, fields=fields, context=context, load=load)


class res_partner(models.Model):
    _inherit = 'res.partner'

    # Fields

    history_ids = fields.Many2many(
        'mail.message',
        'message_partner_rel', 'partner_id', 'message_id',
        'Related Messages'
    )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
