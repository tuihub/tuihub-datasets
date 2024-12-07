import json

from module.SteamService import SteamService

if __name__ == '__main__':
    steam_service = SteamService('C4C6CD52896D408FED14EA3564D0E59E')
    app_list = steam_service.get_app_list()
    with open('app_list.json', 'w', encoding='utf8') as f:
        f.writelines(json.dumps(app_list, ensure_ascii=False, indent=2))
