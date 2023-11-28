#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/util/source_generator.py


from app.model.model import Component, Model


def get_network_source(model: Model):
    def class_init_source(c: Component):
        source = f"        "
        if c.code:
            pass
        elif c.is_container():
            pass
        else:
            return source + f"self.{c.name} = nn.{c.type}({c.params})"

    def class_forward_source(c: Component):
        def replace(str: str):
            return str.replace("{OUTPUT}", "input")

        source = f"        input = "
        if c.code:
            return (
                source
                + f"{replace(c.code)}({replace(c.params) if c.params else 'input'})"
            )

        else:
            return source + f"self.{c.name}(input)"

    source = "##################\n"
    source += "# Network Source #\n"
    source += "##################\n\n"

    source += "import torch\n"
    source += "import torch.nn as nn\n"
    source += "\n"

    source += f"class {model.get_source_classname()}(nn.Module):\n"
    source += "    def __init__(self):\n"
    source += "        super(Network, self).__init__()\n\n"
    source += (
        "\n".join(filter(None, [class_init_source(c) for c in model.layers])) + "\n\n"
    )

    source += f"    def forward(self, input):\n"
    source += "\n".join(class_forward_source(c) for c in model.layers) + "\n"
    source += "\n        return input\n"

    return source


def get_train_source(model: Model, num_epochs: int, mini_batches: int):
    model_name = model.get_source_name()
    model_classname = model.get_source_classname()
    optim = model.optimizer
    loss_fn = model.loss_fn

    source = "################\n"
    source += "# Train Source #\n"
    source += "################\n\n"

    source += "import torch\n"
    source += f"from torch.optim import {model.optimizer.type}\n"
    source += "from torch.autograd import Variable\n"
    source += "from torch.utils.data import DataLoader\n\n"

    source += "_ROOT_PATH: str\n"
    source += "try:\n"
    source += "    _ROOT_PATH\n"
    source += "except NameError:\n"
    source += "    _ROOT_PATH = './'\n\n"

    source += "def testAccuracy(model, test_loader):\n"
    source += "    model.eval()\n"
    source += "    accuracy = 0.0\n"
    source += "    total = 0.0\n"
    source += "    \n"
    source += "    with torch.no_grad():\n"
    source += "        for data in test_loader:\n"
    source += "            images, labels = data\n"
    source += "            outputs = model(images)\n"
    source += "            _, predicted = torch.max(outputs.data, 1)\n"
    source += "            total += labels.size(0)\n"
    source += "            accuracy += (predicted == labels).sum().item()\n"
    source += "        \n"
    source += "    accuracy = 100 * accuracy / total\n"
    source += "    return accuracy\n"
    source += "\n"
    source += "def train(model, train_loader, test_loader, loss_fn, optimizer, num_epochs, mini_batches, model_output_path):\n"
    source += "    best_accuracy = 0.0\n"
    source += "    \n"
    source += (
        "    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')\n"
    )
    source += "    print(f'The model will be running on {device}')\n"
    source += "    model.to(device)\n"
    source += "    \n"
    source += "    for epoch in range(num_epochs):\n"
    source += "        running_loss = 0.0\n"
    source += "        \n"
    source += "        for i, (datas, labels) in enumerate(train_loader, 0):\n"
    source += "            inputs = Variable(datas.to(device))\n"
    source += "            labels = Variable(labels.to(device))\n"
    source += "            \n"
    source += "            optimizer.zero_grad()\n"
    source += "            outputs = model(inputs)\n"
    source += "            loss = loss_fn(outputs, labels)\n"
    source += "            loss.backward()\n"
    source += "            optimizer.step()\n"
    source += "            \n"
    source += "            running_loss += loss.item()\n"
    source += "            if i % mini_batches == (mini_batches-1):\n"
    source += "                print('[%d, %5d] loss: %.3f' %\n"
    source += "                      (epoch + 1, i + 1, running_loss / 1000))\n"
    source += "                running_loss = 0.0\n"
    source += "                \n"
    source += "        accuracy = testAccuracy(model, test_loader)\n"
    source += "        print('For epoch', epoch+1,'the test accuracy over the whole test set is %d %%' % (accuracy))\n"
    source += "        \n"
    source += "        if accuracy > best_accuracy:\n"
    source += "            model_scripted = torch.jit.script(model)\n"
    source += "            model_scripted.save(model_output_path)\n"
    source += "            best_accuracy = accuracy\n\n"

    source += f"{model_classname}: torch.nn.Module\n"
    source += "train_loader: DataLoader\n"
    source += "test_loader: DataLoader\n\n"

    source += f"{model_name} = {model_classname}()\n"
    source += f"{loss_fn.name} = torch.nn.{loss_fn.type}({loss_fn.params})\n"
    source += (
        f"{optim.name} = {optim.type}({optim.params.replace('{MODEL}', model_name)})\n"
    )
    source += "\n"

    source += f"train({model_name}, train_loader, test_loader, {loss_fn.name}, {optim.name}, {num_epochs}, {mini_batches}, f'{{_ROOT_PATH}}/{model.id}_{model_name}.pt')\n\n"

    source += (
        f"_SERVER: object\n"
        f"try:\n"
        f"    _SERVER.send_file(f'{{_ROOT_PATH}}/{model.id}_{model_name}.pt', '{model.id}_{model_name}.pt')\n"
        f"except Exception:\n"
        f"    pass\n"
    )

    return source
