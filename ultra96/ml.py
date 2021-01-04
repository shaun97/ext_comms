import numpy as np
import torch
import brevitas.nn as qnn
from brevitas.core.quant import QuantType
from sklearn.preprocessing import Normalizer
import brevitas.onnx
import os
import joblib

moves_dict = {
    0: "zigzag",
    1: "hair",
    2: "rocket",
    3: "shouldershrug",
    4: "pushback",
    5: "windowwipe",
    6: "scarecrow",
    7: "elbowlock",
    8: "logout"
}


def eval_model(model, criterion, optimizer, dataloader, start=0, end=0):
    model.eval()
    criterion = torch.nn.CrossEntropyLoss()
    preds = []
    truths = []
    if start == end:
        start = 0
        end = len(dataloader)
    with torch.no_grad():
        for i, (data, label) in enumerate(dataloader):
            if i >= start and i < end:
                out = model(data)
                loss = criterion(out, torch.max(label, 1)[1])
                preds.append(np.argmax(out))
                truths.append(np.argmax(label))
    return confusion_matrix(truths, preds), accuracy_score(truths, preds), f1_score(truths, preds, average='weighted')


class MultiHead4MLP(torch.nn.Module):
    def __init__(self, input_size, output_size):
        super(MultiHead4MLP, self).__init__()
        self.input_size = int(input_size/4)
        self.relu = qnn.QuantReLU(bit_width=2, max_val=4)
        self.fc1a = qnn.QuantLinear(
            self.input_size, 128, bias=True, weight_bit_width=2)
        self.fc1b = qnn.QuantLinear(
            self.input_size, 128, bias=True, weight_bit_width=2)
        self.fc1c = qnn.QuantLinear(
            self.input_size, 128, bias=True, weight_bit_width=2)
        self.fc1d = qnn.QuantLinear(
            self.input_size, 128, bias=True, weight_bit_width=2)
        self.fc2 = qnn.QuantLinear(512, 128, bias=True, weight_bit_width=2)
        self.fc3 = qnn.QuantLinear(128, 64, bias=True, weight_bit_width=2)
        self.fc_out = qnn.QuantLinear(
            64, output_size, bias=False, weight_bit_width=2)

    def forward(self, x):
        a, b, c, d = torch.split(x, self.input_size, -1)
        a = self.fc1a(a)
        a = self.relu(a)

        b = self.fc1b(b)
        b = self.relu(b)

        c = self.fc1a(c)
        c = self.relu(c)

        d = self.fc1b(d)
        d = self.relu(d)

        x = torch.cat((a, b, c, d), -1)

        x = self.fc2(x)
        x = self.relu(x)

        x = self.fc3(x)
        x = self.relu(x)

        out = self.fc_out(x)

        return out


model = MultiHead4MLP(168, 9)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
# model_path = '/home/xilinx/ML/checkpoints/mlp_2910_com/epoch_110_95_95.pth'
model_path = '/home/xilinx/ML/checkpoints/mlp_2910_com/epoch_160_95_95.pth'
checkpoint = torch.load(model_path)
criterion = checkpoint['criterion']
model.load_state_dict(checkpoint['model_state_dict'])
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
transformer = joblib.load("/home/xilinx/ML/transformers/2910_com_Norm.tfr")

m = torch.nn.Softmax(dim=0)


def infer_data(samples):
    window = []
    for i, l in enumerate(samples):
        x = np.array(l)
        x = np.nan_to_num(x)
        x = x.reshape(1, -1)
        x = transformer[i].transform(x)
        for value in x[0]:
            window.append(value)
    window = torch.tensor(window, dtype=torch.float32)
    with torch.no_grad():
        out = model(window)
        out = m(out)
    # print(f"Confidence: {out}")
    maxConfidence = out[np.argmax(out).item()]
    if(maxConfidence > 0.85):
        return [moves_dict[np.argmax(out).item()], maxConfidence]
    else:
        return ["NoMatch", maxConfidence]
