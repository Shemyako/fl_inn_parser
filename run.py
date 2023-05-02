from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import json
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from get_site_info.parser import get_comp_info
from google_module.check_table import get_innns, put_info

logging.basicConfig(level=logging.INFO)

with open("inn_bot/config.json", "r", encoding='utf-8') as read_file:
    config = json.load(read_file)

### TODO
# Добавить прокси


def main():
    """
    Основная функция. Получаем из гугл таблицы список с ИНН, после чего получаем по ним информацию.
    Далее вносим получнные данные в таблицу
    """
    # options
    options = webdriver.ChromeOptions()

    # user-agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.111 Safari/537.36")
    options.add_argument("start-maximized") # open Browser in maximized mode
    options.add_argument("disable-infobars") # disabling infobars
    options.add_argument("--disable-extensions") # disabling extensions
    options.add_argument("--disable-gpu") # applicable to windows os only
    options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
    options.add_argument("--no-sandbox") # Bypass OS security model

    # headless mode
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path="inn_bot/chromedriver.exe", options=options)
    wait = WebDriverWait(driver, 10)

    # Загружаем страницу
    driver.get("https://zachestnyibiznes.ru/company/ul/1032901820203_2912003588_MBOU-KONOShEOZERSKAYa-SSh-IM-VA-KORYTOVA")

    # До тех пор, пока не пройдёмся по всем ИНН
    while True:
        # Получаем ИНН из таблицы
        inns = get_innns(config["SHEET"], config["LAST_LINE"], config["STEP"], config["TABLE_URL"])
        count = 0
        result = []

        # Для каждого ИНН
        for i in inns:
            count += 1
            logging.info(f"{i}")
            
            # Если в таблице пустая строка (иногда бывает)
            if i == []:
                result.append(['','','','','',''])
                continue
            
            # Стрипаем ИНН
            i = [i[0].strip()]

            # Пробуем получить информацию о компании
            try:
                result.append(get_comp_info(i[0], driver, wait))
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:               # Что-то не сработало. Обычно когда компания не найдена
                logging.warning(f"{i} - вылет")
                put_info(config["SHEET"], result, start_line=config["LAST_LINE"], config["TABLE_URL"])
                
                config["LAST_LINE"] += count
                with open("inn_bot/config.json", "w", encoding='utf-8') as write_file:
                    json.dump(config, write_file, indent=4, ensure_ascii=False)
                del wait
                driver.quit()
                del driver
                main()

            except BaseException:           # Появилась капча. Через пару минут исчезнет
                logging.warning("Вероятно, капча. Заснём-ка на 5 минут")
                del wait
                driver.quit()
                del driver
                time.sleep(300)
                main()
            
            logging.info(result[-1])

        # Закидываем данные в таблицу
        put_info(config["SHEET"], result, config["LAST_LINE"], config["TABLE_URL"])
        print("puted")
        # Обновляем конфиг
        config["LAST_LINE"] += count
        with open("inn_bot/config.json", "w", encoding='utf-8') as write_file:
            json.dump(config, write_file, indent=4, ensure_ascii=False)


if __name__=="__main__":
    main()