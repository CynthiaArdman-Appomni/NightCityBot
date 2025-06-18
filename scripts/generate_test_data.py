import json
from pathlib import Path

FILES = [
    'attendance_log.json',
    'business_open_log.json',
    'cyberware_log.json',
    'system_status.json',
    'thread_map.json',
]

def main() -> None:
    for name in FILES:
        path = Path(name)
        if not path.exists():
            if name == 'system_status.json':
                data = {
                    'cyberware': True,
                    'attend': True,
                    'open_shop': True,
                    'loa': True,
                    'housing_rent': True,
                    'business_rent': True,
                    'trauma_team': True,
                    'dm': True,
                }
            else:
                data = {}
            path.write_text(json.dumps(data, indent=2))
            print(f'Created {name}')
        else:
            print(f'{name} already exists')

if __name__ == '__main__':
    main()
