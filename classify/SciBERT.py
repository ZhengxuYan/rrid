# -*- coding: utf-8 -*-
"""COVIDScholar_multilabel_SciBERT_benchmark

# Fine Tuning SciBERT for COVID-19 Document MultiLabel Text Classification
"""

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
import logging
logging.basicConfig(level=logging.ERROR)

# Setting up the device for GPU usage

from torch import cuda
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score, precision_score, recall_score

device = 'cuda' if cuda.is_available() else 'cpu'
print("Using Device:", device)

MAX_LEN = 512
TRAIN_BATCH_SIZE = 4
VALID_BATCH_SIZE = 4
EPOCHS = 6
LEARNING_RATE = 1e-05
tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased', truncation=True, do_lower_case=True)

def hamming_score(y_true, y_pred, normalize=True, sample_weight=None):
    acc_list = []
    for i in range(y_true.shape[0]):
        set_true = set( np.where(y_true[i])[0] )
        set_pred = set( np.where(y_pred[i])[0] )
        tmp_a = None
        if len(set_true) == 0 and len(set_pred) == 0:
            tmp_a = 1
        else:
            tmp_a = len(set_true.intersection(set_pred))/\
                    float( len(set_true.union(set_pred)) )
        acc_list.append(tmp_a)
    return np.mean(acc_list)


with open("top_level_RR_reviews.json", "r") as file:
    data = json.load(file)

category_labels = ['Biological and Chemical Sciences',
 'Public Health',
 'Physical Sciences & Engineering',
 'Humanities/Social Sciences',
 'Medical Sciences',
 'General']

def cats_to_vector(cats):
    """Converts a cats dictionary to a list of labels"""
    output = []
    for category in category_labels:
        output.append(cats[category])
    return output

new_df = pd.DataFrame()
new_df['text'] = [e['text'] for e in data]
new_df['labels'] = [[1 if c in e['categories'] else 0 for c in category_labels] for e in data]

class MultiLabelDataset(Dataset):

    def __init__(self, dataframe, tokenizer, max_len):
        self.tokenizer = tokenizer
        self.data = dataframe
        self.text = dataframe.text
        self.targets = self.data.labels
        self.max_len = max_len

    def __len__(self):
        return len(self.text)

    def __getitem__(self, index):
        text = str(self.text[index])
        text = " ".join(text.split())

        inputs = self.tokenizer.encode_plus(
            text,
            None,
            add_special_tokens=True,
            max_length=self.max_len,
            pad_to_max_length=True,
            return_token_type_ids=True
        )
        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        token_type_ids = inputs["token_type_ids"]


        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'targets': torch.tensor(self.targets[index], dtype=torch.float)
        }

def loss_fn(outputs, targets):
    return torch.nn.BCEWithLogitsLoss()(outputs, targets)

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


def get_datasets(df, kf):
    for train_index, test_index in kf.split(df):
        train_data = df.iloc[train_index].reset_index(drop=True)
        test_data = df.iloc[test_index].reset_index(drop=True)
        training_set = MultiLabelDataset(train_data, tokenizer, MAX_LEN)
        testing_set = MultiLabelDataset(test_data, tokenizer, MAX_LEN)
        yield training_set, testing_set

results = []
kf = KFold(n_splits=10, shuffle=True, random_state=42)
for training_set, testing_set in get_datasets(new_df, kf):
    train_params = {'batch_size': TRAIN_BATCH_SIZE,
                'shuffle': True,
                'num_workers': 0
                }

    test_params = {'batch_size': VALID_BATCH_SIZE,
                'shuffle': True,
                'num_workers': 0
                }
                
    training_loader = DataLoader(training_set, **train_params)
    testing_loader = DataLoader(testing_set, **test_params)

    model = SciBERTModel()
    model.to(device)

    optimizer = torch.optim.Adam(params =  model.parameters(), lr=LEARNING_RATE)

    for epoch in range(EPOCHS):
        model.train()
        for i, data in tqdm(enumerate(training_loader, 0)):
            ids = data['ids'].to(device, dtype = torch.long)
            mask = data['mask'].to(device, dtype = torch.long)
            token_type_ids = data['token_type_ids'].to(device, dtype = torch.long)
            targets = data['targets'].to(device, dtype = torch.float)

            outputs = model(ids, mask, token_type_ids)

            optimizer.zero_grad()
            loss = loss_fn(outputs, targets)
            item = loss.item()
            loss.backward()
            optimizer.step()
        print(f"Epoch: {epoch}, Loss:  {item}")

    model.eval()
    fin_targets=[]
    fin_outputs=[]
    with torch.no_grad():
        for _, data in tqdm(enumerate(testing_loader, 0)):
            ids = data['ids'].to(device, dtype = torch.long)
            mask = data['mask'].to(device, dtype = torch.long)
            token_type_ids = data['token_type_ids'].to(device, dtype = torch.long)
            targets = data['targets'].to(device, dtype = torch.float)
            outputs = model(ids, mask, token_type_ids)
            fin_targets.extend(targets.cpu().detach().numpy().tolist())
            fin_outputs.extend(torch.sigmoid(outputs).cpu().detach().numpy().tolist())
    outputs = np.array(fin_outputs) >= 0.5
    targets = np.array(fin_targets)
    val_hamming_loss = metrics.hamming_loss(targets, outputs)
    val_hamming_score = hamming_score(np.array(targets), np.array(outputs))
    print(epoch, val_hamming_loss, val_hamming_score)
    precision_recall_f1s = []
    for i in range(6):
        precision = precision_score(np.array(targets)[:, i], np.array(outputs)[:, i])
        recall = recall_score(np.array(targets)[:, i], np.array(outputs)[:, i])
        f1 = f1_score(np.array(targets)[:, i], np.array(outputs)[:, i])
        precision_recall_f1s.append({'label': category_labels[i], 'precision': precision, 'recall': recall, 'f1': f1})
        

    results.append((precision_recall_f1s, fin_targets, fin_outputs))

# Save the model's state dictionary
model_save_path = "models/scibert.pth"
torch.save(model.state_dict(), model_save_path)

# Save the tokenizer
tokenizer_save_path = "models/scibert_tokenizer"
tokenizer.save_pretrained(tokenizer_save_path)

#compute average scores for all folds
avg_precision_recall_f1s = []
for i in range(6):
    avg_precision = np.zeros(6)
    avg_recall = np.zeros(6)
    avg_f1 = np.zeros(6)
    for result in results:
        result = result[0]
        avg_precision[i] += result[i]['precision']
        avg_recall[i] += result[i]['recall']
        avg_f1[i] += result[i]['f1']
    avg_precision[i] /= len(results)
    avg_recall[i] /= len(results)
    avg_f1[i] /= len(results)
    avg_precision_recall_f1s.append({'label': category_labels[i], 'precision': avg_precision[i], 'recall': avg_recall[i], 'f1': avg_f1[i]})

all_targets = [entry[1] for entry in results]
all_outputs = [entry[2] for entry in results]

output = {'average_f1_precison_recall': avg_precision_recall_f1s, 'all_f1_precison_recall': results, 'targets': all_targets, 'outputs': all_outputs}
with open('SciBERT_benchmark_results.json', 'w') as f:
    json.dump(output, f)