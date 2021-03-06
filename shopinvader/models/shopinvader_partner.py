# -*- coding: utf-8 -*-
# Copyright 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class ShopinvaderPartner(models.Model):
    _name = 'shopinvader.partner'
    _description = 'Shopinvader Partner'
    _inherit = 'shopinvader.binding'
    _inherits = {'res.partner': 'record_id'}

    record_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade')
    partner_email = fields.Char(
        related='record_id.email',
        readonly=True,
        required=True,
        store=True)

    _sql_constraints = [
        ('record_uniq', 'unique(backend_id, record_id, partner_email)',
         'A partner can only have one binding by backend.'),
        ('email_uniq', 'unique(backend_id, partner_email)',
         'An email must be uniq per backend.'),
    ]

    @api.model
    def create(self, vals):
        vals = self._prepare_create_params(vals)
        return super(ShopinvaderPartner, self).create(vals)

    @api.model
    def _prepare_create_params(self, vals):
        # As we want to have a SQL contraint on customer email
        # we have to set it manually to avoid to raise the constraint
        # at the creation of the element
        if not vals.get('partner_email'):
            vals['partner_email'] = vals.get('email')
        if not vals.get('partner_email') and vals.get('record_id'):
            vals['partner_email'] = self.env['res.partner'].browse(
                vals['record_id']).email
        if not vals.get('record_id'):
            vals['record_id'] = self._get_or_create_partner(vals).id
        return vals

    @api.model
    def _get_or_create_partner(self, vals):
        config = self.env['shopinvader.config.settings']
        partner = self.env['res.partner'].browse()
        if not config.is_partner_duplication_allowed():
            domain = self._get_unique_partner_domain(vals)
            partner = partner.search(domain)
        if partner:
            # here we check if one of the given value is different than those
            # on partner. If true, we create a child partner to keep the
            # given informations
            partner = partner[0]
            if not self._is_same_partner_value(partner, vals):
                self._create_child_partner(partner, vals)
            return partner
        return partner.create(vals.copy())

    @api.model
    def _get_unique_partner_domain(self, vals):
        """ """
        email = vals['email']
        return [('email', '=', email)]

    @api.model
    def _is_same_partner_value(self, partner, vals):
        """ we check if one of the given value is different than values
            of the given partner
        """
        data = partner._convert_to_write(partner._cache)
        for key in data:
            if key not in vals:
                continue
            if data[key] != vals[key]:
                return False
        return True

    @api.model
    def _create_child_partner(self, parent, vals):
        vals = self._prepare_create_child_params(parent, vals)
        return self.env['res.partner'].create(vals)

    @api.model
    def _prepare_create_child_params(self, parent, vals):
        v = vals.copy()
        v['parent_id'] = parent.id
        if not v.get('type'):
            v['type'] = 'other'
        v.pop('email')
        return v
