# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# {'Ballot Measure': 'QUESTION 004 : Limited Legalization and Regulation of Certain Natural Psychedelic Substances', 'Measure Status': 'Pending', 'State': 'Massachusetts', 'Total Raised in Support': '$0', 'Total Raised in Opposition': '$0', 'link': 'https://www.opensecrets.org/ballot-measures/MA/2024/60301251/summary'}
class Measure(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    measure_name = scrapy.Field()
    measure_status = scrapy.Field()
    measure_total_funding = scrapy.Field()
    state = scrapy.Field()
    measure_link = scrapy.Field()
    funding_committees = scrapy.Field()
   
   
   
class Committees(scrapy.Item):
    committee_name = scrapy.Field()
    support_or_oppose = scrapy.Field()
    committee_total_funding = scrapy.Field()
    committee_link = scrapy.Field()
    donors = scrapy.Field()
    
class Donors(scrapy.Item):
    donor_name = scrapy.Field()
    donor_total_funding = scrapy.Field()
    donor_link = scrapy.Field()
