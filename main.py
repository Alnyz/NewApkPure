from core.api import Api

api = Api()

y = api.search('vpn', first=False)
api.download(y, count=3)