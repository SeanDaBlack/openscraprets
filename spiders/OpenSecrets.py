from pathlib import Path
import re
import urllib.parse
import scrapy
from scrapy.linkextractors import LinkExtractor
from selenium import webdriver
import csv
from ..items import Measure, Committees, Donors
import re

# from schools import *


allowed_domains = ["opensecrets.org/ballot-measures"]

disallowed_domains = ["https://www.opensecrets.org/ballot-measures#donate"]
start_urls = [
    "https://www.opensecrets.org/ballot-measures",
]


ballot_measures = {}
amends = []
class OpenSecretsSpider(scrapy.Spider):

    name = "ballotinitiative"

    disallowed_domains = disallowed_domains
    link_ext = LinkExtractor(allow=allowed_domains, deny=disallowed_domains)
    def start_requests(self):
        urls = start_urls
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={
                "Host": "www.opensecrets.org",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Connection": "keep-alive",
                # "Cookie": "_opensecrets_session=GcfEMoHFHTvBMcUqetAqNigKHtahOpyq8t%2BOFBr3LMHJiZEKZM0PLbvgM1xWRcCHA10JabEWdoGDX%2FUMWHdkhQ5aZ4WB03f8hVrVLTsuPFlyNgV2YHKNQ%2FcfZo%2FxW1ER%2B1MlsGQd4buHrR%2FOW6au0b%2BRdIr7XLDxpxw8BC6%2Fo0u9GmQqt%2BfndZFWkLaU9u3YuJQELl1OTTiVgpHb4InzfolFMCYqIyhENMG12A5UnDwBjBZw8TGwd6NUtHuVTFM7dvmINYvA%2FiQuHHyhNccMnsHrWZ3hBOroUwjGew%3D%3D--nT5LCf2Q2p3mp24z--DBYan4dm8TaDodcr581y7Q%3D%3D; modal-scrim-ask-id-80=true",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Priority": "u=0, i",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            })
        
        # yield ballot_measures

    def parse(self, response):
        # Seperate all the amendments from open secrets
        amendments = response.xpath("//tr")

        # For each amendment, first determine the type of amendment by link and then parse the data
        for amendment in amendments:
            
            if "https://www.opensecrets.org/ballot-measures" == response.url:
                print("ballot_measures")
                # print(parse_measures(self, response, amendment))
                mes = parse_measures(self, response, amendment)
                ballot_measures[mes["measure_link"]] = mes
            elif re.match(r"https://www\.opensecrets\.org/ballot-measures/\w{2}/2024/\w+/summary", response.url):
                committee = parse_committees(self, response, amendment)
                if "funding_committees" in ballot_measures[response.url]:
                    ballot_measures[response.url]["funding_committees"][committee["committee_link"]] = committee  
                    # print(ballot_measures[response.url])
                else:
                    ballot_measures[response.url]["funding_committees"] = {committee.get("committee_link"): committee}
                    
                print("summary")
                pass
            elif "committees" in response.url:
                referer_url = response.request.headers.get("Referer").decode("utf-8")
                donors = parse_donors(self, response, amendment)
                if "donors" in ballot_measures[referer_url]["funding_committees"][donors["donor_link"]]:
                    ballot_measures[referer_url]["funding_committees"][response.url]["donors"][donors["donor_name"]] = donors
                    print("committees")
                else:
                    ballot_measures[referer_url]["funding_committees"][response.url]["donors"] = {donors.get("donor_name"): donors}
                    
                    for key, value in ballot_measures.items():
                        print(key, value)
                    
                    
                    
                pass
            else:
                print(response.url)
                pass
                
            
            
            
        
        for link in self.link_ext.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(OpenSecretsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=scrapy.signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        # This is the function that will run after the spider is finished
        print("Spider has finished. Running post-spider function.")
        
        # csv_headers = ["Measure Name", "Measure Status", "State", "Total Raised in Support", "Total Raised in Opposition", "Link", "Funding Committee Name", "Support or Oppose", "Total Funding", "Donor", "Link", "Donor Name", "Total Funding", "Link"]
        
        csv_headers = ["measure_name", "state", "measure_link", "committee_name", "support_or_oppose", "committee_total_funding", "committee_link", "donor_name", "donor_total_funding", "donor_link"]
        
        # for measure in ballot_measures: I want to write to a csv using yeild
        writer = csv.DictWriter(open("output1.csv", "w", encoding='utf-8'), fieldnames=csv_headers, extrasaction='ignore')
        writer.writeheader()
        
        for measure in ballot_measures:
            # yield measure
            measure_data = ballot_measures[measure]
            
            
            if measure_data.get("funding_committees"):
                for committee in measure_data["funding_committees"]:
                    committee_data = measure_data["funding_committees"][committee]
                    if committee_data.get("donors"):
                        for donor in committee_data["donors"]:
                            donor_data = dict(committee_data["donors"][donor])
                            
                            new_row = {**measure_data, **committee_data, **donor_data}
                            writer.writerow(new_row)
                            # yield donor_data
            #         yield committee_data
            # yield measure_data
            
        
        
        
        
        
        
        self.run_post_spider_function()

    def run_post_spider_function(self):
        # The function to run after the spider closes
        print(ballot_measures)
        yield ballot_measures
        print("This function runs after the spider closes.")
        
        
def parse_measures(self, response, amendment):
    new_amendment = Measure()
    
    th_tags = response.xpath('//th').getall()  # get all the <th> tags in the response

    tags = ["measure_name", "measure_status","measure_total_funding", "state", "measure_link", "funding_committee"] # Initialize an empty list to store the headers

    td_tags = amendment.xpath('./td')

        
    for i, td in enumerate(td_tags):
        key = tags[i]  # Assign the header value as the key
        value = td.xpath('normalize-space(.)').get()
        new_amendment[key] = value

    if amendment.xpath('./td/a/@href').get():
        new_amendment["measure_link"] = "https://www.opensecrets.org" + amendment.xpath('./td/a/@href').get()
    else:
        new_amendment["measure_link"] = response.url
    
    # new_amendment["link"] = data_dict["link"]

    return new_amendment
        
        
       
def parse_committees(self, response, amendment):
    new_amendment = Committees()
    
    th_tags = response.xpath('//th').getall()  # get all the <th> tags in the response

    tags = ["committee_name", "support_or_oppose", "committee_total_funding", "committee_link", "donors"] # Initialize an empty list to store the headers

    td_tags = amendment.xpath('./td')
     
    for i, td in enumerate(td_tags):
        key = tags[i]  # Assign the header value as the key
        value = td.xpath('normalize-space(.)').get()
        new_amendment[key] = value

    if amendment.xpath('./td/a/@href').get():
        new_amendment["committee_link"] = "https://www.opensecrets.org" + amendment.xpath('./td/a/@href').get()
    else:
        new_amendment["committee_link"] = response.url
    

    return new_amendment        
        
        
def parse_donors(self, response, amendment):
    
    new_amendment = Donors()
    
    th_tags = response.xpath('//th').getall()  # get all the <th> tags in the response

    tags = ["donor_name", "donor_total_funding", "donor_link"] # Initialize an empty list to store the headers

    td_tags = amendment.xpath('./td')
     
    for i, td in enumerate(td_tags):
        key = tags[i]  # Assign the header value as the key
        value = td.xpath('normalize-space(.)').get()
        new_amendment[key] = value

    if amendment.xpath('./td/a/@href').get():
        new_amendment["donor_link"] = "https://www.opensecrets.org" + amendment.xpath('./td/a/@href').get()
    else:
        new_amendment["donor_link"] = response.url
    

    return new_amendment
        
        
        
      
        