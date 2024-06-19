import torch

def mixup_embeddings(embeddings, labels, alpha=0.25):
    """
    Implementation of MixUp augmentation for embeddings
    """
    batch_size = embeddings.size(0)
    lambda_param = torch.distributions.Beta(alpha, alpha).sample().item()
    index = torch.randperm(batch_size)
    mixed_embeddings = lambda_param * embeddings + (1 - lambda_param) * embeddings[index, :]
    mixed_labels = lambda_param * labels + (1 - lambda_param) * labels[index]

    mixed_labels = torch.stack([1 - mixed_labels, mixed_labels], dim=1)
    return mixed_embeddings, mixed_labels
