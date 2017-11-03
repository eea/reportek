#!/usr/bin/env python3

"""
Load (i.e. scrape) the list of clients and save it as a fixture.
"""

import re
import requests
import yaml
from collections import OrderedDict
from xml.etree import ElementTree


URL = "http://rod.eionet.europa.eu/clients"
MODELNAME = "core.client"


def load_data():
    resp = requests.get(URL)

    root = ElementTree.fromstring(resp.content)
    table = root.find('.//xhtml:table[@id="listItem"]/xhtml:tbody',
                      namespaces={"xhtml":"http://www.w3.org/1999/xhtml"})

    id_re = re.compile('^.*\/clients\/([0-9]+$)')
    clients = []
    for row in table:
        td1, td2 = row
        a = td1[0]
        id = int(id_re.fullmatch(a.get('href'))[1])
        name = a.text
        abbr = td2.text
        if abbr is None:
            abbr = ""

        clients.append({
            "id": id,
            "name": name,
            "abbr": abbr,
        })

    return clients

def mk_fixture(clients):
    out = [
        OrderedDict((
            ("model", MODELNAME),
            ("pk", c['id']),
            ("fields", OrderedDict((
                ("name", c['name']),
                ("acronym", c['abbr']),
            )))
        ))
        for c in clients
    ]
    
    return yaml.dump(out, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    yaml.add_representer(OrderedDict, dict_representer)
    
    clients = load_data()
    print(mk_fixture(clients))
