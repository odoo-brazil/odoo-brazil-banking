# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
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

import logging
from openerp import models, fields, api
from datetime import date
from ..boleto.document import Boleto
from ..boleto.document import BoletoException
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_payment_created = fields.Date(
        u'Data da criação do pagamento', readonly=True)
    boleto_own_number = fields.Char(
        u'Nosso Número', readonly=True)
    
    #validate config to generate boletos
    @api.multi
    def validate_boleto_config(self):
        for move_line in self:
            if move_line.payment_mode_id.type_payment != '00':
                raise Warning(u"Payment mode Tipo SPED must be 00 - Duplicata")
            if not move_line.payment_mode_id.internal_sequence_id:
                raise Warning(u"Please set sequence in payment mode")
            if move_line.company_id.own_number_type != '2':
                raise Warning(u"Tipo de nosso número Sequéncial uniquo por modo de pagamento")
            if not move_line.payment_mode_id.boleto_type:
                raise Warning(u'Configure o tipo de boleto no modo de '
                              u'pagamento')
            if not move_line.payment_mode_id.boleto_convenio:
                raise Warning(u"Codigo convênio not set in payment method")
            if not move_line.payment_mode_id.boleto_carteira:
                raise Warning(u"Carteira not set in payment method")
            return True
    
                
    @api.multi
    def send_payment(self):
        boleto_list = []
        self.validate_boleto_config()
        for move_line in self:
            if move_line.payment_mode_id.type_payment == '00':
                number_type = move_line.company_id.own_number_type
                if not move_line.boleto_own_number:
                    if number_type == '0':
                        nosso_numero = self.env['ir.sequence'].next_by_id(
                            move_line.company_id.own_number_sequence.id)
                    elif number_type == '1':
                        nosso_numero = \
                            move_line.transaction_ref.replace('/', '')
                    else:
                        nosso_numero = self.env['ir.sequence'].next_by_id(
                            move_line.payment_mode_id.
                            internal_sequence_id.id)
                else:
                    nosso_numero = move_line.boleto_own_number
                try:
                    int(nosso_numero)
                except:
                    raise Warning(u"Nosso numero must be integer please check prefix and suffix in payment method sequence")
                boleto = Boleto.getBoleto(move_line, nosso_numero)
                if boleto:
                    move_line.date_payment_created = date.today()
                    move_line.transaction_ref = \
                        boleto.boleto.format_nosso_numero()
                    move_line.boleto_own_number = nosso_numero
                

                boleto_list.append(boleto.boleto)
        return boleto_list
