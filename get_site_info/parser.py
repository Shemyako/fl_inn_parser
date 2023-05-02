import logging, time
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_comp_info(i, driver, wait):
    """
    На открытой вкладке через поисковую строку ищем ИНН нужный нам. Переходим по ссылке на ифнормацю о компании
    Далее получаем искомые данные
    i - ИНН
    driver - WebDriver
    wait - WebDriverWait
    """
    # Перечень информации, которую ищем
    answer = {
        "is_actual": "",
        "director" : "",
        "site" : "",
        "mail" : "",
        "phone" : "",
        "type_of_work" : "",
        "name" : ""
    }

    # Если вдруг ИНН нет
    if i == "" or i == None:
        return list(answer.values())
    
    # Если появилась капча
    if driver.find_elements(By.XPATH, '//*[@id="challenge-form"]'):
        raise BaseException("Нужно пройти проверку")
    
    # Ищем инн той компании, которая сейчас открыта
    old_inn = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[7]/div[1]/div[1]/div[2]/p[2]/span[1]') 
    if old_inn == []:
        old_inn = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[8]/div[1]/p[8]/a') 
        if old_inn == []:
            old_inn = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[6]/div[1]/div[1]/div[2]/p[2]/span[1]') 
            if old_inn == []:
                old_inn = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[8]/div[1]/div[1]/div[2]/p[2]/span[1]') 
    
    # Если инн не такой же, что мы сейчас ищем, будем его искать (через поисковую строку)
    if old_inn and old_inn[0].text != i:
        
        # Поиск в поисковой строке
        search_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="autocomplete-0-input"]')))
        search_input.send_keys(i)
        time.sleep(2)
        
        # Ждём появления компании с требуемым ИНН
        confirm_bttn = wait.until(lambda d: d.find_element(By.XPATH, f"//span[text()='{i}']"))
        confirm_bttn = driver.find_elements(By.XPATH, f"//div[span[text()='{i}']]")
        # Ищем действующую компанию. Нужно для ИП. Там бывает много закрытых и одна действующая
        for j in confirm_bttn:
            if i in j.text and "Действующее" in j.text:
                confirm_bttn = j
                break
        # Если не нашли действующую, то возьмём просто последнюю
        if isinstance(confirm_bttn, list):
            confirm_bttn = confirm_bttn[-1]
        # Нажимаем по этой компании
        confirm_bttn.click()

        # Ждём появления названия компании (=прогрузки страницы)
        # ип ли
        if "/ip/" in driver.current_url:
            comp_name = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="nameCompCard"]')))
        else:
            comp_name = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="main-total-card"]/div/div[1]/div[1]/h2')))
        answer["name"] = comp_name.text
    # else:
    #     driver.refresh()


    ###
    # Требуемая компания загружена. Начинам искать данные

    # Номер телефона
    # Если уже видим номер телефона
    phone = driver.find_elements(By.XPATH, '//*[@id="body-content-block"]/div[1]/div/div/div/div/div[2]/div[2]/p/text()')
    if phone != []:
        answer["phone"] = phone[0].text
        
    else:
        ### Ищем кнопку Показать контакты
        get_info_bttn = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[1]/p[2]/a[1]/span')
        if get_info_bttn == []:
            # Почта
            get_info_bttn = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[2]/p[2]/a[1]/span')
            if get_info_bttn == []:
                # Сайт
                get_info_bttn = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[3]/p[2]/a/span')
                if get_info_bttn == []:
                    get_info_bttn = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[1]/p[2]/a/span')

        # Если нашли кнопку (контакты существуют)
        if get_info_bttn != []:
            # Нажимаем, чтобы появились данные
            get_info_bttn[0].click()
            time.sleep(2)
            
            # Если превысили лимит
            if driver.find_elements(By.XPATH,"//p[text()='Вы запрашиваете информацию слишком часто. Попробуйте позже.']"):
                logging.warning(f"{i} - блокировка. Ожидаем минуту")
                time.sleep(60)
                logging.warning(f"{i} - повтор после блокировки")
                return get_comp_info(i, driver, wait)


            phone = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[1]/p[2]')
            answer["phone"] = "" if phone == [] else phone[0].text
            
            # Нажимаем на кнопку Показать ещё (там обычно мусорные номера)
            confirm_bttn = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[1]/a')
            if confirm_bttn:
                confirm_bttn[-1].click()
                phone = driver.find_elements(By.XPATH, '//*[@id="contacts-phone-collapse"]')
                answer["phone"] += "" if phone == [] else ("\n" + phone[0].text)
            
            mail = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[2]/p[2]')
            answer["mail"] = mail[0].text if mail != [] else ''
            
            site = driver.find_elements(By.XPATH, '//*[@id="contacts_main_total"]/div[1]/div[3]/p[2]')
            answer["site"] = site[0].text if site != [] else ''

    # Ищем директора
    director = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[7]/div[1]/div[4]/p[3]/a[1]')
    if director == []:
        director = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[6]/div[1]/div[4]/p[3]/a[1]')
        if director == []:
            director = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[7]/div[1]/div[5]/p[3]/a[1]')
            if not director:
                director = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[8]/div[1]/div[4]/p[3]/a[1]')
        
    # Ищем основной вид деятельности
    type_of_work = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[8]/div[1]/div[2]/p[2]')
    if type_of_work == []:
        type_of_work = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[8]/div[2]/div/p[2]')
        if type_of_work == []:
            type_of_work = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[7]/div[1]/div[2]/p[2]')
            if type_of_work == []:
                type_of_work = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[6]/div[1]/div[2]/p[2]')

        
    # Смотрим, действующая ли компания
    is_actual = driver.find_elements(By.XPATH, '//*[@id="main-total-card"]/div/div[1]/div[1]/p/b')

    answer["is_actual"] = is_actual[0].text
    answer["director"] = director[0].text if director != [] else ''
    answer["type_of_work"] = type_of_work[0].text if type_of_work != [] else ''

    time.sleep(10)

    return list(answer.values())