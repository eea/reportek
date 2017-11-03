"""
Utility script for dumping data from the Reporting Obligations Database to YAML
"""
import xmlrpc.client as xmlrpclib
import yaml


endpoints = {
    'countries': 'getCountries',
    'activities': 'getActivities',
    'deadlines': 'getRODeadlines',
    'summary': 'getROSummary',
    'complete': 'getROComplete'
}


def dump_data(server, method):
    with open(f'{endpoint}.yml', 'w') as yaml_file:
        data = getattr(server.WebRODService, method)()
        dump = yaml.dump(data, default_flow_style=False, allow_unicode=True, encoding=None)
        yaml_file.write(dump)


if __name__ == '__main__':
    server = xmlrpclib.Server('http://rod.eionet.europa.eu/rpcrouter')
    for endpoint, method_name in endpoints.items():
        dump_data(server, method_name)
