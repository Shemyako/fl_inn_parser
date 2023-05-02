# Подключаем библиотеки
import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials	

CREDENTIALS_FILE = 'inn_bot/google_module/token.json'  # Имя файла с закрытым ключом

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

# Запрос к таблице
def get(spreadsheetId:str, range_g):
    """
    Запрашиваем данные из таблицы
    spreadsheetId - url таблицы
    range_g - лист + диапозон, с которого нужно данные подгружать
    """
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 

    resp = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=range_g).execute() # Запрашиваем данные
    return resp


def get_innns(sheet, start_line=2, step=100, url=""):
    """
    Получаем ИНН из таблицы
    sheet - лист в таблице
    start_line - линия, с которой нужно подгружать данные
    step - шаг, с которым запрашивать данные
    url - часть ссылки на гугл таблицу
    Возвращаем список списков с строками ИНН
    """
    answer = []

    # try:
    resp = get(url, f"'{sheet}'!C{start_line}:C{start_line + step}")
    # except BaseException   as e:
    #     print(e)
    #     raise BaseException

    if "values" not in resp:
        raise Exception(f"{start_line} - no values")

    if resp["values"] != []:
        answer = resp["values"]

    return answer


def put_info(sheet, values, start_line=2, url=""):
    """
    Помещаем данные в таблицу
    sheet - лист в таблице
    values - список списков, в котором данные для каждой строки
    start_line - линия, с которой нужно подгружать данные
    url - часть ссылки на гугл таблицу    
    """
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 
    body = {
        "values" : values
    }

    # Вносим данные в таблицу
    resp = service.spreadsheets().values().update(
        spreadsheetId=url,
        range=f"'{sheet}'!O{start_line}",
        valueInputOption="RAW",
        body=body).execute()
