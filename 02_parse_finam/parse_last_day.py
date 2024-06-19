from urllib.parse import urlencode
from urllib.request import urlopen
from datetime import datetime
import itertools
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime, timedelta

def dateToStr(date):
    l = date.split('.')
    l[2]=l[2][2:]
    return ''.join(l)

def getFileName(ticker,period,startDate,endDate):
    return f'./data/to_predict/{ticker}_{period}_{dateToStr(startDate)}_{dateToStr(endDate)}.txt'

def getData(url, fileName):
    # print("Стучимся на Финам по ссылке: "+url)
    txt=urlopen(url).readlines()
    local_file = open(fileName, "w") 
    for line in txt:
        local_file.write(line.strip().decode( "windows-1251" )+'\n')	
    local_file.close()
    txt_to_csv(fileName, fileName[:-3] + 'csv')
    print(f"Готово. Проверьте файл {fileName}")

def txt_to_csv(input_file, output_file):
    with open(input_file, 'r') as txt_file:
        lines = txt_file.readlines()

    with open(output_file, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for line in lines:
            values = line.strip().split(' ')
            csv_writer.writerow(values)




def parse_last_day(tickers):
    periods = {'daily': 8,}
    period = 'daily'

    current_date = datetime.now()
    
    startDate = current_date - timedelta(days=100)
    endDate = current_date - timedelta(days=1)

    startDate = startDate.strftime("%d.%m.%Y")
    endDate = endDate.strftime("%d.%m.%Y")


    market = 0
    start_date = datetime.strptime(startDate, "%d.%m.%Y").date()
    start_date_rev=datetime.strptime(startDate, '%d.%m.%Y').strftime('%Y%m%d')
    end_date = datetime.strptime(endDate, "%d.%m.%Y").date()
    end_date_rev=datetime.strptime(endDate, '%d.%m.%Y').strftime('%Y%m%d')

    for ticker in tickers:
        fileName = getFileName(ticker,period,startDate,endDate)
        params = urlencode([
                            ('market', market), #на каком рынке торгуется бумага
                            ('em', tickers[ticker]), #вытягиваем цифровой символ, который соответствует бумаге.
                            ('code', ticker), #тикер нашей акции
                            ('apply',0), #не нашёл что это значит. 
                            ('df', start_date.day), #Начальная дата, номер дня (1-31)
                            ('mf', start_date.month - 1), #Начальная дата, номер месяца (0-11)
                            ('yf', start_date.year), #Начальная дата, год
                            ('from', start_date), #Начальная дата полностью
                            ('dt', end_date.day), #Конечная дата, номер дня	
                            ('mt', end_date.month - 1), #Конечная дата, номер месяца
                            ('yt', end_date.year), #Конечная дата, год
                            ('to', end_date), #Конечная дата
                            ('p', periods[period]), #Таймфрейм
                            ('f', ticker+"_" + start_date_rev + "_" + end_date_rev), #Имя сформированного файла
                            ('e', ".csv"), #Расширение сформированного файла
                            ('cn', ticker), #ещё раз тикер акции	
                            ('dtf', 1), #В каком формате брать даты. Выбор из 5 возможных. См. страницу https://www.finam.ru/profile/moex-akcii/sberbank/export/
                            ('tmf', 1), #В каком формате брать время. Выбор из 4 возможных.
                            ('MSOR', 0), #Время свечи (0 - open; 1 - close)	
                            ('mstime', "on"), #Московское время	
                            ('mstimever', 1), #Коррекция часового пояса	
                            ('sep', 1), #Разделитель полей	(1 - запятая, 2 - точка, 3 - точка с запятой, 4 - табуляция, 5 - пробел)
                            ('sep2', 1), #Разделитель разрядов
                            ('datf', 1), #Формат записи в файл. Выбор из 6 возможных.
                            ('at', 1)]) #Нужны ли заголовки столбцов
        FINAM_URL = "http://export.finam.ru/"
        url = FINAM_URL + ticker+"_" + start_date_rev + "_" + end_date_rev + ".csv?" + params
        getData(url, fileName)