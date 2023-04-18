from core.api import Api

api = Api()

y = api.search('vpn', first=False, all_page=True)
print(y)