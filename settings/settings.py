def question():
    file_path = QUESTION_PATH

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return file_content



"""constants"""
TIMEOUT_SEC = 3

DEFAULT_FILE_PATH = 'authors.txt'

BASE_URL = 'https://www.tinkoff.ru/invest/social/profile/'

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
)

AUTHORS = [
    "artydevCo",
    "ALL_TIME_TRADING",
    "Gaong",
    "Vladislavzz",
    "CyberMoneyFunnyPunk",
    ]

QUESTION_PATH = 'question.txt'


