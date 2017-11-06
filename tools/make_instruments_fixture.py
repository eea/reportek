import argparse
import yaml


def dump_instruments(activities, instruments_fd):
    instruments = [
        {
            'model': 'core.instrument',
            'pk': int(act['PK_SOURCE_ID']),
            'fields': {
                'title': act['SOURCE_TITLE']
            }
        }
        for act in activities
    ]
    yaml.dump(instruments, instruments_fd)


def load_activities(act_path):
    with open(act_path) as f:
        return yaml.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create an instruments fixture from activities YAML dump.')
    parser.add_argument('activities', help='Activities path')
    parser.add_argument('instruments', help='Instruments fixture path.')
    args = parser.parse_args()

    activities = load_activities(args.activities)
    with open(args.instruments, 'w') as instr_fd:
        dump_instruments(activities, instr_fd)
