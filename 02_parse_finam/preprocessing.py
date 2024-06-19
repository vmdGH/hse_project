from settings import tickers
from parse_last_day import parse_last_day
import os
import pandas as pd
import numpy as np


def column_name_preprocesing(df):
    df = df.copy()
    df.rename(columns={'<OPEN>': 'open', '<HIGH>': 'high', '<LOW>': 'low', '<CLOSE>': 'close', '<VOL>': 'volume', '<TICKER>':'symbol','<DATE>':'datetime'}, inplace=True)
    columns_to_keep = ['symbol', 'datetime', 'open', 'close', 'high', 'low', 'volume']
    df = df[columns_to_keep]
    df.sort_values(by = ['symbol','datetime'], inplace = True)
    df['change_in_price'] = df['close'].diff()
    return df

def read_files():
    folder_path = './data/to_predict/'
    files = os.listdir(folder_path)
    print(files)
    list_to_concat = []
    for file in files:
        if 'txt' in file:
            list_to_concat.append(pd.read_csv(f'./data/to_predict/{file}', sep=','))

    result = pd.concat(list_to_concat, ignore_index=True)
    result = column_name_preprocesing(result)
    mask = result['symbol'] != result['symbol'].shift(1)
    result['change_in_price'] = np.where(mask == True, np.nan, result['change_in_price'])

    return result


def rsi(df, n = 14):
    df = df.copy()
    up_df, down_df = df[['symbol','change_in_price']].copy(), df[['symbol','change_in_price']].copy()
    up_df.loc['change_in_price'] = up_df.loc[(up_df['change_in_price'] < 0), 'change_in_price'] = 0
    down_df.loc['change_in_price'] = down_df.loc[(down_df['change_in_price'] > 0), 'change_in_price'] = 0
    down_df['change_in_price'] = down_df['change_in_price'].abs()
    ewma_up = up_df.groupby('symbol')['change_in_price'].transform(lambda x: x.ewm(span = n).mean())
    ewma_down = down_df.groupby('symbol')['change_in_price'].transform(lambda x: x.ewm(span = n).mean())
    relative_strength = ewma_up / ewma_down
    relative_strength_index = 100.0 - (100.0 / (1.0 + relative_strength))
    df[f'down_days_{n}'] = down_df['change_in_price']
    df[f'up_days_{n}'] = up_df['change_in_price']
    df[f'RSI_{n}'] = relative_strength_index
    return df

def stochastic_oscillator(df, n = 14):
    df = df.copy()
    low_n, high_n = df[['symbol','low']].copy(), df[['symbol','high']].copy()
    low_n = low_n.groupby('symbol')['low'].transform(lambda x: x.rolling(window = n).min())
    high_n = high_n.groupby('symbol')['high'].transform(lambda x: x.rolling(window = n).max())
    k_percent = 100 * ((df['close'] - low_n) / (high_n - low_n))
    df[f'low_{n}'] = low_n
    df[f'high_{n}'] = high_n
    df[f'k_percent_{n}'] = k_percent
    return df

def williams_percent_r(df, n =14):
    df = df.copy()
    low_n, high_n = df[['symbol','low']].copy(), df[['symbol','high']].copy()
    low_n = low_n.groupby('symbol')['low'].transform(lambda x: x.rolling(window = n).min())
    high_n = high_n.groupby('symbol')['high'].transform(lambda x: x.rolling(window = n).max())
    r_percent = ((high_n - df['close']) / (high_n - low_n)) * - 100
    df[f'r_percent_{n}'] = r_percent
    return df

def macd(df):
    df = df.copy()
    ema_26 = df.groupby('symbol')['close'].transform(lambda x: x.ewm(span = 26).mean())
    ema_12 = df.groupby('symbol')['close'].transform(lambda x: x.ewm(span = 12).mean())
    macd = ema_12 - ema_26
    ema_9_macd = macd.ewm(span = 9).mean()
    df['MACD'] = macd
    df['MACD_EMA'] = ema_9_macd
    return df

def price_rate(df, n = 9):
    df = df.copy()
    df[f'Price_Rate_Of_Change_{n}'] = df.groupby('symbol')['close'].transform(lambda x: x.pct_change(periods = n))
    return df

def obv(df):
    df = df.copy()
    volume = df['volume']
    change = df['close'].diff()
    prev_obv = 0
    obv_values = []
    for i, j in zip(change, volume):
        if i > 0:
            current_obv = prev_obv + j
        elif i < 0:
            current_obv = prev_obv - j
        else:
            current_obv = prev_obv
        prev_obv = current_obv
        obv_values.append(current_obv)
    df['on_balance_volume'] = pd.Series(obv_values, index = df.index)
    return df

def add_indicators(df):
    df = df.copy()
    df = rsi(df)
    df = stochastic_oscillator(df)
    df = williams_percent_r(df)
    df = macd(df)
    df = price_rate(df)
    df = obv(df)
    return df

def add_target(df):
    df = df.copy()
    close_groups = df.groupby('symbol')['close']
    close_groups = close_groups.transform(lambda x : np.sign(x.diff()))
    df['target'] = close_groups
    df['target'] = df['target'].replace(0, -1)
    return df
