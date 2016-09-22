# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division

from bs4 import BeautifulSoup
from datetime import datetime
import re
import mechanize


def get_parivahan_data(registration_no):

    clean = lambda x: "_".join(map(str, x.strip('\n\t\r: ').split()))

    reg_match = re.match(r"([A-Za-z0-9]{6})([0-9]{1,4})", registration_no)
    if not reg_match:
        raise Exception('Registration number is not valid')

    br = mechanize.Browser()
    br.open('https://parivahan.gov.in/rcdlstatus/vahan/rcstatus.xhtml')

    br.select_form('convVeh_Form')
    br.form['convVeh_Form:tf_reg_no1'] = reg_match.group(1)
    br.form['convVeh_Form:tf_reg_no2'] = reg_match.group(2)

    res = br.submit()
    soup = BeautifulSoup(res.get_data(), 'lxml')
    table_rows = soup.table.find_all('tr')

    data = {}
    for row in table_rows:
        table_columns = row.find_all('td')
        for i in xrange(0, len(table_columns), 2):
            try:
                if table_columns[i] and table_columns[i+1]:
                    key = clean(table_columns[i].text)
                    val = clean(table_columns[i+1].text)

                    if key == 'Registration_Date':
                        try:
                            val = datetime.strptime(val, '%d-%b-%Y')
                        except Exception as e:
                            print "Exception {} while parsing registration date: {}".format(e.message, val)
                            val = None

                    data[key] = val
            except Exception as e:
                print e.message
                continue

    return data


if __name__ == '__main__':
    print get_parivahan_data('KA05JH6941')