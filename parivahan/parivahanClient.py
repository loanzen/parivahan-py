# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

import re

import requests
from bs4 import BeautifulSoup


class ParivahanException(Exception):
    def __init__(self, message):
        super(ParivahanException, self).__init__(message)


class ParivahanClient(object):

    ACTION_URL_REGEX = r".*([jJ][sS][eE][sS][sS][iI][oO][nN][iI][dD])=(.*)"
    REG_NO_REGEX = r"([A-Za-z]{2}[0-9]{2}[a-zA-Z]{2})([0-9]{4})"
    SESSION_COOKIE = 'JSESSIONID'
    URL = 'https://parivahan.gov.in/rcdlstatus/vahan/rcstatus.xhtml'

    def __init__(self):

        self.session = None

        self._params = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source':"convVeh_Form:j_idt21",
            'javax.faces.partial.execute': "@all",
            'javax.faces.partial.render': "convVeh_Form:rcPanel",
            'convVeh_Form:j_idt21': "convVeh_Form:j_idt21",
            'convVeh_Form': "convVeh_Form",
            'convVeh_Form:tf_reg_no1': None,
            'convVeh_Form:tf_reg_no2': None,
            'javax.faces.ViewState': None}

    def _prepare(self, registration_no):

        reg_match = re.match(self.REG_NO_REGEX, registration_no)
        if not reg_match:
            raise ParivahanException('Registration number is not valid')

        r = requests.get(self.URL)
        if r.status_code != 200:
            raise ParivahanException('Parivahan URL not working. '
                                     'Error {}'.format(r.status_code))

        soup = BeautifulSoup(r.content, 'lxml')

        form = soup.find('form')
        if not form:
            raise ParivahanException('Form not found in the response.')

        action_url = form.get('action')
        match = re.match(self.ACTION_URL_REGEX, action_url)

        if not match:
            raise ParivahanException('SessionID not found in action url')

        self.session = match.group(2)

        hidden_items = form.find_all('input', type='hidden')

        view_state = None
        for item in hidden_items:
            if item.get('id') and 'ViewState' in item.get('id'):
                view_state = item.get('value')

        if not view_state:
            raise ParivahanException('view state not found in the form data.')

        self._params.update(**{
            'convVeh_Form:tf_reg_no1': reg_match.group(1).upper(),
            'convVeh_Form:tf_reg_no2': reg_match.group(2),
            'javax.faces.ViewState': view_state
        })

    def get_registration_details(self, registration_no):
        self._prepare(registration_no)
        data = {}
        res = requests.post(self.URL, data=self._params, cookies={self.SESSION_COOKIE: self.session})
        #print res.content
        if res.status_code != 200:
            raise ParivahanException('Parivahan URL not working. '
                                     'Error {}'.format(res.status_code))

        soup = BeautifulSoup(res.content, 'lxml')
        table_rows = soup.div.table.find_all('tr')
        for row in table_rows:
            table_columns = row.find_all('td')
            for i in xrange(0, len(table_columns), 2):
                if table_columns[i] and table_columns[i+1]:
                    data[table_columns[i].text] = table_columns[i+1].text

        return data

if __name__ == '__main__':
    parivahan = ParivahanClient()
    print parivahan.get_registration_details('KA05JH6942')