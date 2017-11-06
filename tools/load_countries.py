#!/usr/bin/env python3

"""
Load (i.e. scrape) the list of clients and save it as a fixture.
"""

import re
import xmlrpc.client as xmlrpclib
import yaml
from collections import OrderedDict


SERVER_URL = "http://rod.eionet.europa.eu/rpcrouter"
MODELNAME = "core.country"


def load_data():
    server = xmlrpclib.Server('http://rod.eionet.europa.eu/rpcrouter')
    countries = server.WebRODService.getCountries()

    id_re = re.compile('^.*\/spatial\/([0-9]+$)')
    for country in countries:
        uri = country.pop('uri')
        id = int(id_re.fullmatch(uri)[1])
        country['id'] = id

    return countries

def mk_fixture(clients):
    out = [
        OrderedDict((
            ("model", MODELNAME),
            ("pk", c['id']),
            ("fields", OrderedDict((
                ("iso", c['iso']),
                ("name", c['name']),
            )))
        ))
        for c in clients
    ]
    
    return yaml.dump(out, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    yaml.add_representer(OrderedDict, dict_representer)
    
    countries = load_data()
    print(mk_fixture(countries))
