import torch
from torch.utils.data import DataLoader
from datasets import load_dataset, load_from_disk
from transformers import BertTokenizer, BertForSequenceClassification, AdamW 
from torcheval.metrics import BinaryAccuracy
import argparse
import os

from preprocess import Preprocessor
from utils import training_epoch, validation_epoch, plot_losses

from transformers import logging

logging.set_verbosity_error()

def main():
    # Загрузка данных и разделение на тренировочную и валидационную выборки
    parser = argparse.ArgumentParser(description='Please enter model name to save')

    # Добавление аргументов
    parser.add_argument('--modelname', type=str, help='Model name', required=True)
    args = parser.parse_args()
    path = f"../models/{args.modelname}"

    dataset_path = "../data/rotten_tomatoes"

    # Проверяем, существует ли локальный файл
    if os.path.exists(dataset_path):
        # Если файл существует, загружаем датасет из локального файла
        loaded_dataset = load_from_disk(dataset_path)
        print("Dataset loaded from local disk.")
    else:
        # Если файл не существует, загружаем датасет из интернета и сохраняем его
        dataset = load_dataset("cornell-movie-review-data/rotten_tomatoes")
        dataset.save_to_disk(dataset_path)
        loaded_dataset = dataset
        print("Dataset downloaded and saved to local disk.")

    train_data = loaded_dataset['train']
    val_data = loaded_dataset['validation']
    # Токенизация
    tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
    preprocessor = Preprocessor(tokenizer, max_length=32)
    train_data = train_data.map(preprocessor, batched=True)
    val_data = val_data.map(preprocessor, batched=True)

    # Создание DataLoader
    train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=32)

    # Создание модели
    model = BertForSequenceClassification.from_pretrained('bert-base-cased', num_labels=2)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    # Обучение модели
    optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01, no_deprecation_warning=True)
    criterion = torch.nn.BCELoss()
    metric = BinaryAccuracy()
    is_cuda = next(model.parameters()).is_cuda
    print("model is on cuda" if is_cuda else "model is not in cuda")
    num_epochs = 16
    train_losses, train_metrics, val_metrics = [], [], []
    for epoch in range(1, num_epochs + 1):
        train_loss, train_metric = training_epoch(
            model, optimizer, criterion, train_loader,
            tqdm_desc=f'Training {epoch}/{num_epochs}',
            metric = metric
        )
        val_metric = validation_epoch(
            model, criterion, val_loader,
            tqdm_desc=f'Validating {epoch}/{num_epochs}',
            metric=metric
        )
        train_losses += [train_loss]
        train_metrics += [train_metric.tolist()]
        val_metrics += [val_metric.tolist()]
    model.save_pretrained(path)
    print(f"Model fine-tuned and saved at {path}")
    plot_losses(train_losses, train_metrics, val_metrics) 


if __name__ == "__main__":
    main()