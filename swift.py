"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import datetime
import logging
import re
import time

import dateutil.parser
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

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

    def __init__(self, webdriver: WebDriver, url: str, max_count_documents: int = None, last_document: SPP_document = None, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self.driver = webdriver
        self._max_count_documents = max_count_documents
        self._last_document = last_document
        if url:
            self.URL = url
        else:
            raise ValueError('url must be a link to the swift topic main page')

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
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
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

        self.driver.set_page_load_timeout(40)

        links = []
        for page in self._encounter_pages():
            # Получение URL новой страницы
            for link in self._collect_doc_links(page):
                # Запуск страницы и ее парсинг
                self._parse_news_page(link)

        for link in links:
            self._parse_news_page(link)
        # ---
        # ========================================

    def _encounter_pages(self) -> str:
        _base = self.URL
        _params = '?page='
        page = 1
        while True:
            url = _base + _params + str(page)
            page += 1
            yield url

    def _collect_doc_links(self, url: str) -> list:
        links = []

        try:
            self._initial_access_source(url)
        except Exception as e:
            raise NoSuchElementException() from e

        cards = self.driver.find_elements(By.CLASS_NAME, 'card')  # Карточки со страницы
        for card in cards:
            try:
                link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                links.append(link)
                self.logger.debug(f'Prepare link {link}')
            except Exception as e:
                self.logger.debug(f'Card cannot read in {self.driver.current_url}. Error: {e}')
        return links

    def _parse_news_page(self, url: str):
        self.logger.debug(f'Start parse document by url: {url}')

        try:
            # Важные данные
            self._initial_access_source(url, 3)
            intro = self.driver.find_element(By.CLASS_NAME, 'page-banner-news__intro')
            _title = intro.find_element(By.TAG_NAME, 'h1').text

            _subtitle = intro.find_element(By.CLASS_NAME, 'subtitle')
            date = intro.find_element(By.CLASS_NAME, 'subtitle').text
            d1 = date.split('\n')[1]
            d2 = re.match(r'([\d \w]*) |.*', d1).groups()[0]
            _published = dateutil.parser.parse(d2)
        except Exception as e:
            raise NoSuchElementException(
                'Страница не открывается или ошибка получения обязательных полей') from e
        else:
            document = SPP_document(
                None,
                _title,
                None,
                None,
                url,
                None,
                None,
                _published,
                datetime.datetime.now()
            )
            try:
                _category = _subtitle.find_element(By.XPATH, 'div[1]').text
                if _category:
                    document.other_data = {'category': _category.replace(',', '')}
            except:
                self.logger.debug('There aren\'t a category in the page')

            _text = self.driver.find_element(By.CLASS_NAME, 'news-content__left').text
            document.text = _text
            self.find_document(document)

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

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self._last_document and self._last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self._last_document})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))

        if self._max_count_documents and len(self._content_document) >= self._max_count_documents:
            raise Exception(f"Max count articles reached ({self._max_count_documents})")
