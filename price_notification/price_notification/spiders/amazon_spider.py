import scrapy
import cloudscraper
from scrapy.crawler import CrawlerProcess
import csv
import smtplib
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
import ssl
import datetime

class AmazonSpider(scrapy.Spider):
    name = "amazon"

    mail_info = {
        "mail_use_flag" : True,
        "mail_server" : 'smtp.sendgrid.net',
        "mail_port" : 587,
        "mail_use_ssl" : True,
        "mail_debug" : 1,
        "mail_username" : 'apikey',
        "mail_password" : 'SG.yJU-dIiGQPGmLQFIsgbxT',#TODO
        "mail_default_sender" : 'cndone@gmail.com',#TODO
        "mail_to" : 'cndone@gmail.com',#TODO
    }

    custom_settings = {#CSV出力
        'FEEDS': { 'data/amazon_items.csv': { 'format': 'csv', 'overwrite': False}}
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }

    allowed_domains = ["www.amazon.co.jp"]
    #cloudflare 403対応
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows', 'desktop': True, 'mobile': False})

    def start_requests(self):
        urls = {
            'BALMUDA The Toaster Pro K11A-SE-WH' : 
            {
                'url' : "https://www.amazon.co.jp/s?k=BALMUDA+The+Toaster+Pro+K11A-SE-WH&i=kitchen&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&ref=nb_sb_noss",
                'target_price' : 38000
            }
        }
        for product_name, target in urls.items():
            yield scrapy.Request(url=target['url'], header=self.headers, callback=self.parse, cb_kwargs={'target_product_name': product_name, 'target_price' : target['target_price']})

    def parse(self, response, target_product_name, target_price):
        items =  response.css("div.a-section.a-spacing-small.a-spacing-top-small")
        for item  in items:
            product_name = item.css("div.a-section.a-spacing-none.puis-padding-right-small.s-title-instructions-style > h2 > a > span::text").get()
            price = item.css("span.a-price-whole::text").get()
            url = item.css("div.a-section.a-spacing-none.puis-padding-right-small.s-title-instructions-style > h2 > a::attr(href)").get()
            if product_name is not None and target_product_name in product_name and price is not None:
                price = int(price.replace(',', ''))
                url = "https://www.amazon.co.jp" + url
                # 出力
                yield {
                    "name": product_name,
                    "price": price,
                    "update_date": datetime.datetime.now(),
                    "url" : url,
                }
                if price <= target_price:
                    content = f'''
                商品：{product_name}が￥{price}に値下げました。
                {url}

'''
                    self.send_mail('価格変動通知', content=content)

    def send_mail(self, subject, content):
        '''
        メール送信
        '''
        msg = MIMEText(content, 'html')
        msg['Subject'] = subject
        msg['To'] = self.mail_info['mail_to']
        msg['From'] = self.mail_info['mail_default_sender']
        if self.mail_info['mail_use_ssl']:
            context = ssl.create_default_context()
            server = SMTP_SSL(self.mail_info['mail_server'], 465, context=context)
        else:
            server = smtplib.SMTP(self.mail_info['mail_server'], 465)
            server.starttls()

        server.login(self.mail_info['mail_username'], self.mail_info['mail_password'])
        server.send_message(msg)
        server.quit()

if __name__ == "__main__":
    # with open('data/amazon_items.csv', encoding='UTF-8') as f:
    #     reader = csv.reader(f)
    #     itmes = [row for row in reader]

    process = CrawlerProcess()
    process.crawl(AmazonSpider)
    process.start()

    #参考資料
    #https://www.bizzcode.net/%E3%80%90%E3%82%89%E3%81%8F%E3%82%89%E3%81%8F%E6%83%85%E5%A0%B1%E5%8F%8E%E9%9B%86%E3%80%91python%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E3%82%B9%E3%82%AF%E3%83%AC%E3%82%A4%E3%83%94%E3%83%B3%E3%82%B0/

    

    