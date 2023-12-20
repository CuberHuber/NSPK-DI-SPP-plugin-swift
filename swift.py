"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import datetime
import itertools
import logging
import os
import re
import time

import dateutil.parser
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common import NoSuchElementException

from src.spp.types import SPP_document


class SWIFT:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'swift'
    _content_document: list[SPP_document]

    HOST = 'https://www.swift.com/news-events/'

    def __init__(self, webdriver: WebDriver, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        self.driver = webdriver

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        self._parse()
        self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -
        release_url = 'https://www.swift.com/news-events/press-releases'
        news_url = 'https://www.swift.com/news-events/news'

        self.driver.set_page_load_timeout(40)

        links = []
        links.extend(self._contain_links_from_url(release_url))
        links.extend(self._contain_links_from_url(news_url))
        print(links)

        for link in links:
            self._parse_news_page(link)


        ...

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(document))

        # ---
        # ========================================

    def _contain_links_from_url(self, url: str) -> list:
        links = []
        last_page = 0

        self._initial_access_source(url, 5)

        try:
            link_to_last_page = self.driver.find_element(By.CLASS_NAME, 'pager__item--last').find_element(By.TAG_NAME, 'a').get_attribute('href')
            last_page = int(re.match(r'.*?page=(\d+)', link_to_last_page).groups()[0])
            self.logger.debug(f'Last page is {last_page}')
        except:
            self.logger.error('Last page not find')
            return links

        # Вернуть назад
        # for page in range(0, last_page+1):
        for page in range(0, 12 if last_page+1 >= 12 else last_page+1):  # для теста
            if page > 0:
                self._initial_access_source(f'{url}?page={page}')

            cards = self.driver.find_elements(By.CLASS_NAME, 'card')                # Карточки со страницы
            for card in cards:
                try:
                    link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    links.append(link)
                    self.logger.debug(f'Prepare link {link}')
                except Exception as e:
                    self.logger.debug(f'Card cannot read in {self.driver.current_url}')

        return links

    def _parse_news_page(self, url: str):
        self._initial_access_source(url, 3)
        self.logger.debug(f'Start parse document by url: {url}')

        document = SPP_document(
            None,
            None,
            None,
            None,
            url,
            None,
            {},
            None,
            datetime.datetime.now()
        )

        try:
            content = self.driver.find_element(By.CLASS_NAME, 'news-content__left')
            text = content.text
            document.text = text
        except Exception as e:
            self.logger.error(e)
            return

        try:
            intro = self.driver.find_element(By.CLASS_NAME, 'page-banner-news__intro')
            title = intro.find_element(By.TAG_NAME, 'h1').text
            document.title = title

            date = intro.find_element(By.CLASS_NAME, 'subtitle').text
            d1 = date.split('\n')[1]
            d2 = re.match(r'([\d \w]*) |.*', d1).groups()[0]
            t = dateutil.parser.parse(d2)
            document.pub_date = t
        except Exception as e:
            self.logger.error(e)
            return

        self.logger.info(self._find_document_text_for_logger(document))
        self._content_document.append(document)

    def _initial_access_source(self, url: str, delay: int = 2):
        self.driver.get(url)
        self.logger.debug('Entered on web page '+url)
        time.sleep(delay)
        self._agree_cookie_pass()

    def _agree_cookie_pass(self):
        """
        Метод прожимает кнопку agree на модальном окне
        """
        cookie_agree_xpath = '//*[@id="onetrust-accept-btn-handler"]'

        try:
            cookie_button = self.driver.find_element(By.XPATH, cookie_agree_xpath)
            if WebDriverWait(self.driver, 5).until(ec.element_to_be_clickable(cookie_button)):
                cookie_button.click()
                self.logger.debug(F"Parser pass cookie modal on page: {self.driver.current_url}")
        except NoSuchElementException as e:
            self.logger.debug(f'modal agree not found on page: {self.driver.current_url}')

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    @staticmethod
    def some_necessary_method():
        """
        Если для парсинга нужен какой-то метод, то его нужно писать в классе.

        Например: конвертация дат и времени, конвертация версий документов и т. д.
        :return:
        :rtype:
        """
        ...

    @staticmethod
    def nasty_download(driver, path: str, url: str) -> str:
        """
        Метод для "противных" источников. Для разных источника он может отличаться.
        Но основной его задачей является:
            доведение driver селениума до файла непосредственно.

            Например: пройти куки, ввод форм и т. п.

        Метод скачивает документ по пути, указанному в driver, и возвращает имя файла, который был сохранен
        :param driver: WebInstallDriver, должен быть с настроенным местом скачивания
        :_type driver: WebInstallDriver
        :param url:
        :_type url:
        :return:
        :rtype:
        """

        with driver:
            driver.set_page_load_timeout(40)
            driver.get(url=url)
            time.sleep(1)

            # ========================================
            # Тут должен находится блок кода, отвечающий за конкретный источник
            # -
            # ---
            # ========================================

            # Ожидание полной загрузки файла
            while not os.path.exists(path + '/' + url.split('/')[-1]):
                time.sleep(1)

            if os.path.isfile(path + '/' + url.split('/')[-1]):
                # filename
                return url.split('/')[-1]
            else:
                return ""
