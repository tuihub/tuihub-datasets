import time

import requests


class SteamService:
    def __init__(self, webapi_key: str, request_interval: int = 10):
        self.webapi_key = webapi_key
        self.request_interval = request_interval

    def get_app_list(self) -> dict[int, list[str]]:
        apps = {}
        self._i_store_service_get_app_list_v1(apps, 'schinese')
        self._i_store_service_get_app_list_v1(apps, 'tchinese')
        self._i_store_service_get_app_list_v1(apps, 'english')
        self._i_store_service_get_app_list_v1(apps, 'japanese')
        return apps

    def _i_store_service_get_app_list_v1(self, apps: dict[int, list[str]]
                                         , language: str) -> None:
        last_appid = 0
        while True:
            try:
                url = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
                params = {
                    'key': self.webapi_key,
                    # 'if_modified_since': 0,
                    'have_description_language': language,
                    'include_games': 'true',
                    'include_dlc': 'true',
                    'include_software': 'true',
                    'include_videos': 'false',
                    'include_hardware': 'false',
                    'last_appid': last_appid,
                    'max_results': 50000
                }
                response = requests.get(url, params=params).json()['response']

                for app in response['apps']:
                    if app['appid'] not in apps:
                        apps[app['appid']] = []
                    if app['name'] not in apps[app['appid']]:
                        apps[app['appid']].append(app['name'])

                if 'have_more_results' not in response or not response['have_more_results']:
                    print(f"IStoreService/GetAppList/v1: l: {language}, last_appid: {last_appid}, "
                          f"no more results, sleep {self.request_interval}s")
                    time.sleep(self.request_interval)
                    break

                last_appid = response['last_appid']
                print(f"IStoreService/GetAppList/v1: l: {language}, last_appid: {last_appid}, "
                      f"sleep {self.request_interval}s")
                time.sleep(self.request_interval)
            except Exception as ex:
                print(f"IStoreService/GetAppList/v1: Error: {repr(ex)}, sleep {self.request_interval}s")
                time.sleep(self.request_interval)
                break
