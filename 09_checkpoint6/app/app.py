import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json
from openai import OpenAI


# import joblib
import logging
import pandas as pd

from flask import Flask, request, render_template, json


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL", "")
QUESTION_CONTEXT = "Напиши два ответа на основании предложенного текста. Первый ответ - название компании, о которой идет речь в тексте. Второй ответ - направление цены, напиши \"up\" или \"down\". Ответ должен выглядить так: \"Название тикета компании на биржи. Число\""
AUTHORS = os.getenv("AUTHORS", "")
AUTHORS = os.getenv("AUTHORS").split(',')
USER_AGENT = os.getenv("USER_AGENT")
DS_API_KEY = os.getenv("DS_API_KEY", "")


class Article:
    month_dict = {
    'января': '01',
    'февраля': '02',
    'марта': '03',
    'апреля': '04',
    'мая': '05',
    'июня': '06',
    'июля': '07',
    'августа': '08',
    'сентября': '09',
    'октября': '10',
    'ноября': '11',
    'декабря': '12'
    }
    
    def __init__(self, date, text, parsed=False):#, likes):
        if not parsed:
            self.date = date
            self.text = text
        else:            
            self.date = self.fix_dates(date)
            self.text = self.clean_text(text)
            self.ticker, self.prediction = 0, 0

    def clean_text(self, text):
        emoji_pattern = re.compile("["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F700-\U0001F77F"  # alchemical symbols
                                u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                                u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                                u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                                u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                                u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                                u"\U00002702-\U000027B0"  # Dingbats
                                u"\U000024C2-\U0001F251" 
                                "]+", flags=re.UNICODE)
        clean_text = emoji_pattern.sub(r'', text)
        return clean_text
    
    def fix_dates(self, date_string):
        if 'Сегодня' in date_string:
            result = datetime.combine(datetime.now().date(), 
                                    #   (datetime.combine(datetime.today(), datetime.strptime(date_string.split(" ")[-1], '%H:%M').time()) - timedelta(hours=3)).time()).strftime("%Y-%m-%d %H:%M")
                                      (datetime.combine(datetime.today(), datetime.strptime(date_string.split(" ")[-1], '%H:%M').time()) + timedelta(hours=3)).time()).strftime("%Y-%m-%d %H:%M")

        elif 'Вчера' in date_string:
            result = datetime.combine(datetime.now().date() - timedelta(days=1), 
                                    #   (datetime.combine(datetime.today(), datetime.strptime(date_string.split(" ")[-1], '%H:%M').time()) - timedelta(hours=3)).time()).strftime("%Y-%m-%d %H:%M")
                                      (datetime.combine(datetime.today(), datetime.strptime(date_string.split(" ")[-1], '%H:%M').time()) + timedelta(hours=3)).time()).strftime("%Y-%m-%d %H:%M")

        else:
            result_list = date_string.split(" ")
            result_list[1] = self.month_dict[result_list[1]]
            result_list.pop(3)

            result_list[-1]=str((int(result_list[-1].split(':')[0])+21)%24) + ":" + result_list[-1].split(':')[1]
            date_str = ' '.join(result_list)
            date_format = '%d %m %Y %H:%M'
            result = datetime.strptime(date_str, date_format).strftime("%Y-%m-%d %H:%M")

        return result
    
    def predict(self):       
        # question_context = get_question_context()
        question_context = QUESTION_CONTEXT

        client = OpenAI(api_key=DS_API_KEY, base_url="https://api.deepseek.com/v1")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": question_context},
                {"role": "user", "content": self.text},
                {"role": "user", "content": 'Напиши краткий ответ в одну строчку. Только название одной компании и направлении цены, больше ничего, два слова через пробел без пояснений'}
                ]
            )
        answer = response.choices[0].message.content
        answer = answer.strip().upper()
        prediction = 0
        ticker = 0
        if "DOWN" in answer:
            prediction = -1
            answer = answer.replace("DOWN", "")
        elif "UP" in answer:
            prediction = 1
            answer = answer.replace("UP", "")
        else:
            return 0, 0
        if len(answer) < 20:
            ticker = re.sub(r'[+\-=:/]', '', answer)   
        else:     
            return 0, 0     
        self.ticker, self.prediction =  ticker, prediction

class Authors:
    def __init__(self, authors_list=[]):
        self.authors_list = authors_list

    def add_author(self, author):
        self.authors_list.append(author)

    def save_to_json(self, filename):
        author_data_list = []
        for author in self.authors_list:
            author_data = {
                "name": author.name,
                "base_url": author.base_url,
                "subscribers": int(author.subscribers),
                "size": author.size,
                "month_activity": int(author.month_activity),
                "profitability": author.profitability,
                "articles": [{"date": article.date, "text": article.text} for article in author.articles],
            }
            author_data_list.append(author_data)

        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(author_data_list, json_file, ensure_ascii=False, indent=4)

class Author:
    def __init__(self, name: str, subscribers, size, month_activity, profitability, articles):
        self.name = name
        self.base_url = self.get_base_url(name)
        self.subscribers = subscribers 
        self.size = size
        self.month_activity = month_activity
        self.profitability = profitability
        self.articles  = articles

    def get_base_url(self, name, start= BASE_URL):
        return start+name



app = Flask(__name__)


# функция обновляет файл и отпраляет новые данны
@app.route('/update_data', methods=['Get', 'POST'])
def update_data():
    try:
        new_articles = {}
        articles_to_send = {}
        #открываем имеющиеся данные
        with open('/app/data/data_posts.json', 'r', encoding='utf-8') as file:
            json_content = file.read()
            data = json.loads(json_content)

        for author in AUTHORS:
            new_articles[author] = []
            # парсинг страницы
            url = BASE_URL + author
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(markup = response.text, features="html.parser")
            posts = soup.find_all('div', {'data-qa-tag':'PulsePost'})

            for post in posts:
                text = post.find_all('div', {'class':'pulse-profilepage__fGGBmY'})[0].get_text()
                date = post.find_all('div', {'pulse-profilepage__cSULlZ'})[0].get_text()
                article = Article(date, text, parsed=True)
                dates = [item['date'] for item in data[author]['articles']]
                # если нашли новый пост, добавляем его в словарь
                if not (article.date in dates):         
                    article.predict()

                    post_data =  {
                            'date': article.date,
                            'text': article.text,
                            'ticker': article.ticker,
                            'prediction': article.prediction
                            }
                    new_articles[author].append(post_data)
                else:
                    break

            if len(new_articles[author])>0: # если у автора есть новые публикации, добавляем их в словарь
                logger.info(f"{author}: у автора есть новые посты")

                articles_to_send[author] = {
                    "base_url":data[author]['base_url'],
                    "subscribers":data[author]['subscribers'],
                    "size":data[author]['size'],
                    "month_activity":data[author]['month_activity'],
                    "profitability":data[author]['profitability'],
                    "articles":new_articles[author]
                }
                data[author]['articles'] = new_articles[author] + data[author]['articles']
            else:
                logger.info(f"{author}: у автора нет новых постов") 

        if articles_to_send:
            logger.info("Есть новые посты")
            with open('/app/data/data_posts.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return articles_to_send

        else:
            logger.info("Нет новых постов")
            return {}
    except Exception as e:
        logger.info(json.dumps(f"Error: {e}"))
        return json.dumps(f"Error: {e}")

# функция обновляет файл и отпраляет все данные
@app.route('/send_data', methods=['Get', 'POST'])
def send_data():
    try:
        #открываем имеющиеся данные
        with open('/app/data/data_posts.json', 'r', encoding='utf-8') as file:
            json_content = file.read()
            data = json.loads(json_content)
        new_articles = {}

        for author in AUTHORS:
            new_articles[author] = []

            # парсинг страницы
            url = BASE_URL + author
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(markup = response.text, features="html.parser")
            posts = soup.find_all('div', {'data-qa-tag':'PulsePost'})

            for post in posts:
                text = post.find_all('div', {'class':'pulse-profilepage__fGGBmY'})[0].get_text()
                date = post.find_all('div', {'pulse-profilepage__cSULlZ'})[0].get_text()
                article = Article(date, text, parsed=True)
                dates = [item['date'] for item in data[author]['articles']]
                # если нашли новый пост, добавляем его в словарь
                if not (article.date in dates):         
                    article.predict()

                    post_data =  {
                            'date': article.date,
                            'text': article.text,
                            'ticker': article.ticker,
                            'prediction': article.prediction
                            }
                    new_articles[author].append(post_data)
                else:
                    if len(new_articles[author])>0:
                        logger.info(f"{author}: у автора есть новые посты")
                    else:
                        logger.info(f"{author}: у автора нет новых постов") 
                    break
            data[author]['articles'] = new_articles[author] + data[author]['articles']

        # сохраняем обновленный словарь в файл
        with open('/app/data/data_posts.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        # возвращаем все данные
        return data
    except Exception as e:
        logger.info(json.dumps(f"Error: {e}"))
        return json.dumps(f"Error: {e}")
    

if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)