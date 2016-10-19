# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division

from datetime import datetime
import re
from urllib2 import URLError

from bs4 import BeautifulSoup
import mechanize


class ParivahanTimeOutException(Exception):

    def __int__(self, message):
        super(ParivahanTimeOutException, self).__init__(message)


class ParivahanException(Exception):

    def __int__(self, message):
        super(ParivahanException, self).__init__(message)


def get_parivahan_data(registration_no, request_timeout=10):

    clean = lambda x: x.strip('\n\t\r: ')
    join_with_underscore = lambda x: "_".join(clean(x).split())

    reg_match = re.match(r"([A-Za-z]{2}[0-9]{1,2}[A-Za-z]{1,3})([0-9]{1,4})", registration_no)
    if not reg_match:
        raise ParivahanException('Registration number is not valid')

    br = mechanize.Browser()
    br.set_handle_refresh(False)
    try:
        br.open('https://parivahan.gov.in/rcdlstatus/vahan/rcstatus.xhtml',
                timeout=request_timeout)
    except URLError as e:
        raise ParivahanTimeOutException(e.message)

    br.select_form('convVeh_Form')
    br.form['convVeh_Form:tf_reg_no1'] = reg_match.group(1).upper()
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
                    key = join_with_underscore(table_columns[i].text).lower()
                    val = clean(table_columns[i+1].text)

                    if key == 'registration_date':
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


def is_vehicle_stolen(registration_no, request_timeout=10):

    # is_valid() checks if vehicle_type is a substring of vehicle types found on samanvay website
    # vehicle_class() gets a list of html select option and filters them who are `is_valid`
    # sorry for making it too cryptic. Didn't want to add one more function
    is_valid = lambda x: x.text.strip() in vehicle_type
    vehicle_class = lambda xx: (filter(is_valid, xx) or [None])[0]

    registration_details = get_parivahan_data(registration_no)
    owner = registration_details.get('owner_name')
    chassis_no = registration_details.get('chasi_no')
    engine_no = registration_details.get('engine_no')
    vehicle_type = registration_details.get('vehicle_class')

    if None in (chassis_no, engine_no, vehicle_type, owner):
        raise Exception('Could not fetch required registration details from parivahan.')

    br = mechanize.Browser()
    try:
        res = br.open('http://164.100.44.112/vahansamanvay/Internetquery.aspx',
                      timeout=request_timeout)
    except URLError as e:
        raise ParivahanTimeOutException(e.message)

    try:
        #filter vehicle class
        vehicle_type = vehicle_class(BeautifulSoup(res.get_data(),
                                                   'lxml').find('select',
                                                                id='ddVehTypeName').find_all('option'))
        if vehicle_type is None:
            raise Exception('No match.')

        vehicle_type = vehicle_type.get('value')
    except Exception as e:
        print "Couldn't determine vehicle type from the registration data. Error: {}".format(e.message)

    br.select_form(nr=0)
    br.form['txtAppName'] = owner
    br.form['ddVehTypeName'] = [vehicle_type]
    br.form['txtRegistration'] = registration_no
    br.form['txtChasis'] = chassis_no
    br.form['txtEngine'] = engine_no

    br.submit()

    # mechanize will take care of sending session cookies.
    res = br.open('http://164.100.44.112/vahansamanvay/InternetQueryOutput.aspx')
    soup = BeautifulSoup(res.get_data(), 'lxml')
    panel = soup.find('div', id='Panel1')
    tables = soup.find_all('table')
    if not tables or len(tables) < 2:
        raise Exception('Unexpected page structure.')

    table = tables[1]
    tr = (table.find_all('tr') or [None])[-1]
    if tr is None:
        raise Exception('Unexpected page structure.')

    text = tr.find('td').text
    if text and 'has not been reported as stolen by police' in text:
        return False, re.sub(r"[\r\n\t ]+", " ", str(panel))
    else:
        # don't know what comes in the text for stolen vehicle
        return True, re.sub(r"[\r\n\t ]+", " ", str(panel))


if __name__ == '__main__':
    print get_parivahan_data('KA05JH6941')