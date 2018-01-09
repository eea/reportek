import argparse
import yaml


def make_fixture(obligations, fix_fd):
    def valid_date(d):
        # Guard against nonsensical values in ROD
        if d and d != '0000-00-00':
            return d + 'T00:00:00+00:00'
        return None

    def fk_list(fk_str):
        # ROD FK lists have extra commas, e.g: ',102,34,2,36,8,28,'
        return [int(fk) for fk in fk_str.split(',')[1:-1]] if fk_str else []

    _bool_dict = {
        'Y': True,
        'N': False,
    }

    def get_bool(v):
        return _bool_dict[v]

    fixture = [
        {
            'model': 'core.obligation',
            'pk': int(o['PK_RA_ID']),
            'fields': {
                'title': o['TITLE'],
                'description': o['DESCRIPTION'],
                'terminated': get_bool(o['TERMINATE']),
                'created_at': valid_date(o['FIRST_REPORTING']) or '1990-01-01T00:00:00+00:00',
                'active_since': valid_date(o['FIRST_REPORTING']) or '1990-01-01T00:00:00+00:00',
                'client': int(o['FK_CLIENT_ID']) if o['FK_CLIENT_ID'] else None,
                'instrument':
                    # Prevent entries with 'FK_SOURCE_ID' = '0' from causing integrity errors
                    int(o['FK_SOURCE_ID']) \
                    if o['FK_SOURCE_ID'] and o['FK_SOURCE_ID'] != '0' else None,
            }
        }
        for o in obligations
    ]
    yaml.dump(fixture, fix_fd)


def load_obligations(dump_path):
    with open(dump_path) as f:
        return yaml.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create an obligations fixture from obligations YAML (ROD) dump.')
    parser.add_argument('dump_path', help='ROD dump path')
    parser.add_argument('fixture_path', help='Fixture path.')
    args = parser.parse_args()

    obligations_dump = load_obligations(args.dump_path)
    with open(args.fixture_path, 'w') as fix_fd:
        make_fixture(obligations_dump, fix_fd)
