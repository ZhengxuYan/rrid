from hashlib import new
import warnings
warnings.simplefilter('ignore')
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn import metrics
import transformers
import torch
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler
from transformers import AutoTokenizer, AutoModel
from torch import cuda
import logging
logging.basicConfig(level=logging.ERROR)

class SciBERTModel(torch.nn.Module):
    def __init__(self):
        super(SciBERTModel, self).__init__()
        self.l1 = AutoModel.from_pretrained("allenai/scibert_scivocab_uncased")
        self.pre_classifier = torch.nn.Linear(768, 768)
        self.dropout = torch.nn.Dropout(0.1)
        self.classifier = torch.nn.Linear(768, 6)

    def forward(self, input_ids, attention_mask, token_type_ids):
        output_1 = self.l1(input_ids=input_ids, attention_mask=attention_mask)
        hidden_state = output_1[0]
        pooler = hidden_state[:, 0]
        pooler = self.pre_classifier(pooler)
        pooler = torch.nn.Tanh()(pooler)
        pooler = self.dropout(pooler)
        output = self.classifier(pooler)
        return output

MAX_LEN = 512
TRAIN_BATCH_SIZE = 4
VALID_BATCH_SIZE = 4
EPOCHS = 6
LEARNING_RATE = 1e-05

device = 'cuda' if cuda.is_available() else 'cpu'
print("Using Device:", device)

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("models/scibert_tokenizer")

# Initialize the model architecture
model = SciBERTModel()

# Load the saved state dictionary into the model
model.load_state_dict(torch.load("models/scibert.pth"))

# Ensure the model is in evaluation mode
model.eval()

# Move the model to the appropriate device
model.to(device)

def predict(text, model, tokenizer):
    # Preprocess the text
    inputs = tokenizer.encode_plus(
        text,
        None,
        add_special_tokens=True,
        max_length=MAX_LEN,
        pad_to_max_length=True,
        return_attention_mask=True,
        return_token_type_ids=True,
        truncation=True
    )
    ids = inputs['input_ids']
    mask = inputs['attention_mask']
    token_type_ids = inputs["token_type_ids"]

    # Convert to tensors
    ids = torch.tensor(ids, dtype=torch.long).unsqueeze(0)  # Add batch dimension
    mask = torch.tensor(mask, dtype=torch.long).unsqueeze(0)
    token_type_ids = torch.tensor(token_type_ids, dtype=torch.long).unsqueeze(0)

    # Move tensors to the appropriate device
    ids = ids.to(device)
    mask = mask.to(device)
    token_type_ids = token_type_ids.to(device)

    # Make predictions
    with torch.no_grad():
        outputs = model(ids, mask, token_type_ids)
        outputs = torch.sigmoid(outputs).cpu().detach().numpy().flatten()

    
    # Map probabilities to category labels
    categories = ['Biological and Chemical Sciences',
                  'Public Health',
                  'Physical Sciences & Engineering',
                  'Humanities/Social Sciences',
                  'Medical Sciences',
                  'General']
    prediction = dict(zip(categories, outputs))

    return prediction


text = "Your new text to classify."
predictions = predict(text, model, tokenizer)
print(predictions)
