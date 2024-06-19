import torch
from datasets import load_dataset
from transformers import BertTokenizer, BertForSequenceClassification
from preprocess import Preprocessor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import sys
import argparse



def main():


    # Загрузка данных и разделение на тренировочную и валидационную выборки
    parser = argparse.ArgumentParser(description='Please enter model name')

    # Добавление аргументов
    parser.add_argument('--modelname', type=str, help='Model name', required=True)
    args = parser.parse_args()
    path = f"../models/{args.modelname}"

    print("Loading dataset")
    sys.stdout.flush()

    dataset = load_dataset("cornell-movie-review-data/rotten_tomatoes")

    test_data = dataset['test']
    # Токенизация
    print("Text tokenization")
    sys.stdout.flush()
    tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
    preprocessor = Preprocessor(tokenizer, max_length=64)
    test_data = test_data.map(preprocessor, batched=True)

    print("Model uploading")
    sys.stdout.flush()
    model = BertForSequenceClassification.from_pretrained(path)


    input_ids_test = torch.tensor(test_data['input_ids'])
    attention_mask_test = torch.tensor(test_data['attention_mask'])
    labels_test = torch.tensor(test_data['label'])
    print("Predicting")
    sys.stdout.flush()
    outputs = model(input_ids=input_ids_test, attention_mask=attention_mask_test, labels=labels_test)
    print("Results:")
    sys.stdout.flush()
    preds = torch.argmax(outputs.logits.detach(), dim=1)
    accuracy = accuracy_score(labels_test, preds)
    precision = precision_score(labels_test, preds)
    recall = recall_score(labels_test, preds)
    f1 = f1_score(labels_test, preds)
    print(f"\tAccuracy: {accuracy}")
    print(f"\tPrecision: {precision}")
    print(f"\tRecall: {recall}")
    print(f"\tf1 score: {f1}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()