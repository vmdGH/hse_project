
from transformers import BertForSequenceClassification
import torch
from torch.utils.data import DataLoader
import  torch.nn as nn
from tqdm import tqdm
import torcheval

from IPython.display import clear_output
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Union, List, Tuple, Optional, Any

from mixup import mixup_embeddings

sns.set_style('whitegrid')
plt.rcParams.update({'font.size': 15})
def plot_losses(train_losses: List[float],
                train_metrics: torch.Tensor, val_metrics: torch.Tensor):
    """
    Plot loss and perplexity of train and validation samples
    :param train_losses: list of train losses at each epoch
    :param val_losses: list of validation losses at each epoch
    """
    clear_output()
    fig, axs = plt.subplots(1, 2, figsize=(13, 4))
    axs[0].plot(range(1, len(train_losses) + 1), train_losses, label='train')
    axs[0].set_ylabel('loss')


    axs[1].plot(range(1, len(train_metrics) + 1), train_metrics, label='train')
    axs[1].plot(range(1, len(val_metrics) + 1), val_metrics, label='val')
    axs[1].set_ylabel('metric (accuracy)')

    for ax in axs:
        ax.set_xlabel('epoch')
        ax.legend()

    plt.show()


def training_epoch(model: BertForSequenceClassification, optimizer: torch.optim.Optimizer, criterion: nn.Module,
                   loader: DataLoader, tqdm_desc: str, metric: torcheval.metrics):
    """
    Process one training epoch
    :param model: language model to train
    :param optimizer: optimizer instance
    :param criterion: loss function class
    :param loader: training dataloader
    :param tqdm_desc: progress bar description
    :return: running train loss
    """
    device = next(model.parameters()).device
    train_loss = 0.0
    model.train()
    for batch in tqdm(loader, desc=tqdm_desc):
        optimizer.zero_grad()
        input_ids = torch.stack(batch['input_ids']).transpose(0, 1).to(device)
        attention_mask = torch.stack(batch['attention_mask']).transpose(0, 1).to(device)
        labels = batch['label'].to(device)
        # with torch.no_grad():
        outputs = model.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = outputs.pooler_output
        embeddings, labels = mixup_embeddings(embeddings, labels) # аугментация
        outputs = model.classifier(embeddings)
        outputs = torch.sigmoid(outputs)
        loss = criterion(outputs, labels) # лосс на выборке без аугментации 
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
        metric.update(torch.argmax(outputs.detach(), dim=1), torch.argmax(labels.detach(), dim=1))
    train_loss /= len(loader.dataset)
    return train_loss, metric.compute()


@torch.no_grad()
def validation_epoch(model: BertForSequenceClassification, criterion: nn.Module,
                     loader: DataLoader, tqdm_desc: str, metric: torcheval.metrics):
    """
    Process one validation epoch
    :param model: language model to validate
    :param criterion: loss function class
    :param loader: validation dataloader
    :param tqdm_desc: progress bar description
    :return: validation loss
    """
    device = next(model.parameters()).device
    model.eval()
    for batch in tqdm(loader, desc=tqdm_desc):
        input_ids = torch.stack(batch['input_ids']).transpose(0, 1).to(device)
        attention_mask = torch.stack(batch['attention_mask']).transpose(0, 1).to(device)
        labels = batch['label'].to(device)
        # labels = torch.stack([labels, 1. - labels], dim=1)

        labels = torch.stack([1. - labels, labels], dim=1)

        outputs = model.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = outputs.pooler_output
        outputs = model.classifier(embeddings)
        outputs = torch.sigmoid(outputs)
        loss = criterion(outputs, labels)
        metric.update(torch.argmax(outputs.detach(), dim=1), torch.argmax(labels.detach(), dim=1))

    return metric.compute()

