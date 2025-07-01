import json
from pathlib import Path
import config

FILES = [
    config.ATTEND_LOG_FILE,
    config.OPEN_LOG_FILE,
    config.CYBERWARE_LOG_FILE,
    config.CYBERWARE_WEEKLY_FILE,
    config.SYSTEM_STATUS_FILE,
    config.THREAD_MAP_FILE,
]

def main() -> None:
    for path in FILES:
        path = Path(path)
        if not path.exists():
            if path.name == 'system_status.json':
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
            print(f'Created {path.name}')
        else:
            print(f'{path.name} already exists')

if __name__ == '__main__':
    main()
