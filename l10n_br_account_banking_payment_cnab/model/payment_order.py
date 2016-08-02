# -*- coding: utf-8 -*-
# #############################################################################
#
#
#    Copyright (C) 2012 KMEE (http://www.kmee.com.br)
#    @author Fernando Marcato Rodrigues
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

from openerp import models, fields, api
from openerp.exceptions import Warning

# TODO: funcao a ser chamada por ação automatizada para resetar o sufixo
#     diariamente


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    file_number = fields.Integer(u'Número sequencial do arquivo')
    # TODO adicionar domain para permitir o modo de pagamento correspondente
    # ao mode
    serie_id = fields.Many2one(
        'l10n_br_cnab.sequence', u'Sequencia interna')
    sufixo_arquivo = fields.Integer(u'Sufixo do arquivo')
    serie_sufixo_arquivo = fields.Many2one(
        'l10n_br_cnab_file_sufix.sequence', u'Série do Sufixo do arquivo')
    
    # we will validate here user inputs required to export
    # a wrong input shouldn't raise error but should show helpful
    # warning message
    @api.multi
    def validate_order(self):
        if not len(self.line_ids):
            raise Warning("Please select lines to export")
        # code must belong to one of allowed code
        if self.mode_type.code not in ['240', '400', '500']:
            raise Warning("Payment Type Code must be 240, 400 or 500, found %s" % self.mode_type.code)
        # legal name max length is accepted 30 chars
        if len(self.company_id.legal_name) > 30:
            raise Warning("Company's Rezão Social should not be longer than 30 chars")
        if not self.mode.boleto_protesto:
            raise Warning(u"Códigos de Protesto in payment mode not defined")
        if not self.mode.boleto_protesto_prazo:
            raise Warning(u"Prazo protesto in payment mode not defined")
        else:
            try:
                int(self.mode.boleto_protesto_prazo)
            except:
                raise Warning("Prazo protesto in payment mode must be integer")
        if not self.mode.bank_id.bra_number_dig:
            raise Warning("Dígito Agência not defined")
        else:
            try:
                int(self.mode.bank_id.bra_number_dig)
            except:
                raise Warning("Dígito Agência must be integer")

            
        # move lines must have transaction refernce
        for line in self.line_ids:
            if not line.partner_id:
                raise Warning("Partner not defined for %s" %line.name)
            if not line.partner_id.legal_name:
                raise Warning("Rezão Social not defined for %s" %line.partner_id.name)
            if len(line.partner_id.legal_name) > 30:
                raise Warning("Partner's Rezão Social should not be longer than 30 chars")
            if not line.partner_id.state_id:
                raise Warning("Partner's state not defined")
            if not line.partner_id.state_id.code:
                raise Warning("Partner's state code not defined")
            # max 15 chars
            if not line.partner_id.district:
                raise Warning("Partner's bairro not defined")
            if not line.partner_id.zip:
                raise Warning("Partner's CEP not defined")
            if not line.partner_id.l10n_br_city_id:
                raise Warning("Partner's city not defined")
            if not line.partner_id.street:
                raise Warning("Partner's street not defined")
            if not line.move_line_id.transaction_ref:
                raise Warning("No transaction reference set for move %s" % line.move_line_id.name)
            # Itau code : 341 supposed not to be larger than 8 digits
            if self.mode.bank_id.bank.bic == '341':
                try:
                    int(line.move_line_id.transaction_ref[4:12])
                except:
                    raise Warning("Transaction reference for move line must be integer")
            if not line.move_line_id.invoice.number:
                raise Warning("Null value in 'numero_documento' number not defined for invoice %s" % line.move_line_id.invoice.number)
            if len(line.move_line_id.invoice.number) > 10:
                raise Warning("numero_documento can not be more than 10 digits long found %s" %line.move_line_id.invoice.number)
        
    
    def get_next_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for ord in self.browse(cr, uid, ids):
            sequence = self.pool.get('ir.sequence')
            # sequence_read = sequence.read(
            #     cr, uid, ord.serie_id.internal_sequence_id.id,
            #     ['number_next'])
            seq_no = sequence.get_id(cr, uid,
                                     ord.serie_id.internal_sequence_id.id,
                                     context=context)
            self.write(cr, uid, ord.id, {'file_number': seq_no})
        return seq_no

    def get_next_sufixo(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for ord in self.browse(cr, uid, ids):
            sequence = self.pool.get('ir.sequence')
            # sequence_read = sequence.read(
            #     cr, uid, ord.serie_id.internal_sequence_id.id,
            #     ['number_next'])
            seq_no = sequence.get_id(
                cr, uid,
                ord.serie_sufixo_arquivo.internal_sequence_id.id,
                context=context)
            self.write(cr, uid, ord.id, {'sufixo_arquivo': seq_no})
        return seq_no

    # @api.multi
    # def set_to_draft(self, *args):
    #     super(PaymentOrder, self).set_to_draft(*args)
    #
    #     for order in self:
    #         for line in order.line_ids:
    #             self.write_added_state_to_move_line(line.move_line_id)
    #     return True

    # @api.multi
    # def write_added_state_to_move_line(self, mov_line):
    #     mov_line.state_cnab = 'added'
