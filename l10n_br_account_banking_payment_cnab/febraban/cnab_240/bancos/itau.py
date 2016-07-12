# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
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

from ..cnab_240 import Cnab240
import re
import string


class Itau240(Cnab240):
    """

    """

    def __init__(self):
        """

        :return:
        """
        super(Cnab240, self).__init__()
        from cnab240.bancos import itau
        self.bank = itau

    def _prepare_header(self):
        """

        :param order:
        :return:
        """
        
        vals = super(Itau240, self)._prepare_header()
        vals['cedente_dv_ag_cc'] = int(
            vals['cedente_dv_ag_cc'])
        vals['cedente_agencia_dv'] = int(
            vals['cedente_agencia_dv'])
        return vals

    def _prepare_segmento(self, line):
        """

        :param line:
        :return:
        """
        vals = super(Itau240, self)._prepare_segmento(line)
        ref = line.move_line_id.transaction_ref[4:12]
        carteira, nosso_numero, digito = self.nosso_numero(ref)
        #=======================================================================
        # nº da agência: 1572 
        # nº da conta corrente, sem o DAC: 22211
        # nº da subcarteira: 109 (Neste teste saiu 000, conforme já mencionado acima)
        # nosso número: 00000008
        # You multiply each char of the number composed with the fields above by the sequence of multipliers - 2 1 2 1 2 1 2 positioned from right to left.
        # (agency+account+carteira+nossonumero) (15722221110900000008)
        # 
        #=======================================================================
        reference = str(line.order_id.mode.bank_id.bra_number) + str(line.order_id.mode.bank_id.acc_number) + str(self.order.mode.boleto_carteira) + str(ref)
        vals['carteira_numero'] = int(line.order_id.mode.boleto_carteira)
        vals['nosso_numero'] = int(ref)
        vals['nosso_numero_dv'] = int(self.nosso_numero_dv(reference))
        vals['sacado_cidade'] = line.partner_id.l10n_br_city_id.name[:15]
        vals['sacado_bairro'] = line.partner_id.district[:15]
        return vals

    # Override cnab_240.nosso_numero. Diferentes números de dígitos entre
    # CEF e Itau
    def nosso_numero(self, format):
        #should not return digit from this method
        # ust use nosso_numero_dv top return digit
        digito = format[-1:]
        carteira = format[:3]
        nosso_numero = re.sub(
            '[%s]' % re.escape(string.punctuation), '', format[3:-1] or '')
        return carteira, nosso_numero, digito
    
    def nosso_numero_dv(self, format):
        i = 1
        total = 0
        # multiply all digits by 1 and 2 consicutively starting:
        # eg:  1st x 1 + 2nd x 2 + 3rd x 1 + 4th x 2 + ........
        position = 1
        for digit in format:
            if int(position) % 2 == 0:
                result = int(digit) * 2
            else:
                result = int(digit) * 1
            total = total + sum([int(digit) for digit in str(result)])
            position += 1
        digit = total % 10
        if digit != 0:
            digit = 10 - digit
        return digit
