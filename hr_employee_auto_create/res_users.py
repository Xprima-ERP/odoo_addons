# -*- coding: utf-8 -*-

from osv import osv


class User(osv.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    def create(self, cr, uid, vals, context=None):
        '''
        When a new user is created, also create an hr.employee and link it with
        the new user.
        '''
        user_id = super(User, self).create(cr, uid, vals, context=context)

        empl_model = self.pool.get('hr.employee')
        name = vals.get('name', vals.get('login'))
        empl_vals = {'name': name, 'user_id': user_id}
        empl_model.create(cr, uid, empl_vals, context=context)

        return user_id

User()
