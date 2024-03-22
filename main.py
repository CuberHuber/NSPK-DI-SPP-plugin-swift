import datetime
from logging import config

from selenium import webdriver

from swift import SWIFT
from src.spp.types import SPP_document

config.fileConfig('dev.logger.conf')


def driver():
    """
    Selenium web driver
    """
    options = webdriver.ChromeOptions()

    # Параметр для того, чтобы браузер не открывался.
    options.add_argument('headless')

    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    return webdriver.Chrome(options)

release_url = 'https://www.swift.com/news-events/press-releases'
news_url = 'https://www.swift.com/news-events/news'

doc = SPP_document(id=None, title='Swift appoints Stephen Grainger as Chief Executive for Americas & U.K. Region', abstract=None, text='Grainger brings two decades of global industry experience to the role\nJoins from Mastercard where he was Executive Vice President of Cross-Border Services; other past roles include Global Head of Bank Relations and Market Infrastructure at Goldman Sachs, and senior business development roles at Swift \nSHARE\nBrussels, 3 January 2023 — Swift today announces the appointment of Stephen Grainger as the Chief Executive for Americas & U.K. Region. Grainger was most recently Executive Vice President at Mastercard, leading the development and commercialisation of its global Cross-Border Services business, servicing banks, digital platforms and non-bank financial institutions (NBFIs).\nStarting in his new role at Swift today, Grainger will drive the region’s overarching direction and growth, focusing his efforts on further developing strategic customer relationships, supporting customers as they work to transform the cross-border payment experience for their end clients, and working with securities players to improve the efficiency of post-trade processing.\nGrainger brings two decades of global industry experience in the banking world as well as an insightful perspective into the Swift business having previously served in senior business development roles at the cooperative. A leader in the payments industry, he has also held positions at Goldman Sachs, Bank of America, and Citigroup. \nRosemary Stone, Chief Business Development Officer, Swift, commented: Stephen’s industry experience makes him ideally qualified to lead our Americas and UK businesses into the next stage of growth, as we continue to deliver our strategic objectives to best serve the Swift community.”\nStephen Grainger, Chief Executive for Americas & U.K. region, Swift, added: “I am delighted to be returning to Swift at this particularly exciting stage in the organisation’s development. I greatly look forward to supporting the business as it works to transform cross-border payments and securities processing for the benefit of the financial industry.”\nPress contacts:\nFGS Global\n+32 (0)2655 3377 \nswift@fgsglobal.com', web_link='https://www.swift.com/news-events/press-releases/swift-appoints-stephen-grainger-chief-executive-americas-uk-region', local_link=None, other_data=None, pub_date=datetime.datetime(2023, 1, 3, 0, 0), load_date=datetime.datetime(2024, 3, 22, 18, 12, 57, 393034))

parser = SWIFT(driver(), release_url, 10, doc)
docs = parser.content()


print(*docs, sep='\n\r\n')
