from datetime import datetime
from app.libraries.configuration.cloudflare_config import list_access_rule, delete_access_rule

if __name__ == '__main__':
    result = list_access_rule()
    current_date = datetime.now().strftime('%Y/%m/%d')
    print(current_date)
    for item in result['result']:
        print(item['configuration'])
        if 'Sync from BWAF' in item['notes'] and current_date not in item['notes']:
            print(item['notes'], "Delete")
            result = delete_access_rule(identifier=item['id'])
            print(result)
