# -*- coding: utf-8 -*-
"""
Created on Sat Jun 25 23:46:07 2022

@author: User
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"]  =  "TRUE"
import torch
import torchvision
from torchvision import transforms, utils
#import tkinter
#from tkinter import *
#import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import torch.nn as nn
from network.repVGG import *
from network.resnet import *
from utils.val import *
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

import os
import random
import shutil
import time
import json
import warnings
import torch.nn.functional as F



def train(DO_TRAIN,
          net,
          nums_epoch,
          IMAGE_SIZE,
          BATCH_SIZE,
          SAVE_MODEL_PATH,
          TRAIN_DATA_DIR,
          VAL_DATA_DIR,
          ENABLE_VALIDATION,
          class_names,
          CM_FILENAME,
          c1,c2,c3,c4,
          date):
    
    
    '''
    ============================================================================================
    Enable train or not

    TRAIN : enable/disable train
    TRAIN_EPOCH : enable/disable train model for epoch times
    DRAW_TRAIN_LOSS_EPOCH_GRAPH : enable/disable draw train loss at each epoch
    ENABLE_VALIDATION : enable/disable validation at each epoch

    ============================================================================================
    '''
    if DO_TRAIN:
        TRAIN = True
        TRAIN_EPOCH = True
        DRAW_TRAIN_LOSS_EPOCH_GRAPH = True
        ENABLE_VALIDATION = True
    else:
        TRAIN = False
        TRAIN_EPOCH = False
        DRAW_TRAIN_LOSS_EPOCH_GRAPH = False
        ENABLE_VALIDATION = False
    
    
    
    if TRAIN:
        size = (IMAGE_SIZE,IMAGE_SIZE)
        img_data = torchvision.datasets.ImageFolder(TRAIN_DATA_DIR,
                                                    transform=transforms.Compose([
                                                        transforms.Resize(size),
                                                        #transforms.RandomHorizontalFlip(),
                                                        #transforms.Scale(64),
                                                        transforms.CenterCrop(size),
                                                     
                                                        transforms.ToTensor()
                                                        ])
                                                    )
        
        data_loader = torch.utils.data.DataLoader(img_data, batch_size=BATCH_SIZE,shuffle=True,drop_last=False)
        print(len(data_loader))
        
        '''============================================================================================================================================'''  
        classes = ('GreenLeft', 'GreenRight', 'GreenStraight','RedLeft','RedRight','YellowLeft','YellowRight','others')
        #classes = ('Green', 'GreenLeft', 'GreenRight', 'GreenStraight', 'Off', 'others', 'Red', 'RedLeft', 'RedRight', 'Yellow', 'YellowLeft','YellowRight')
        # 显示一张图片
        def imshow(img):
            img = img / 2 + 0.5   # 逆归一化
            npimg = img.numpy()
            plt.imshow(np.transpose(npimg, (1, 2, 0)))
            plt.show()
        
        # 任意地拿到一些图片
        dataiter = iter(data_loader)
        images, labels = dataiter.next()
        
        # 显示图片
        imshow(torchvision.utils.make_grid(images))
        # 显示类标
        print(' '.join('%5s' % classes[labels[j]] for j in range(4)))
        
        def show_batch(imgs):
            grid = utils.make_grid(imgs,nrow=5)
            plt.imshow(grid.numpy().transpose((1, 2, 0)))
            plt.title('Batch from dataloader')
        
        for i, (batch_x, batch_y) in enumerate(data_loader):
            if(i<6):
                print(i, batch_x.size(), batch_y.size())
        
                show_batch(batch_x)
                plt.axis('off')
                plt.show()
                
        for i, data in enumerate(data_loader):
          img,label=data
          print(i," : ",label)
          
        '''
        =======================================================
        train : Parameter settings : criterion, optimizer, device
        =======================================================
        '''
        import torch.optim as optim
        '''loss function'''
        criterion = nn.CrossEntropyLoss()
        ''' optimizer method '''
        optimizer = optim.SGD(net.parameters(), lr=1e-3, momentum=0.9)
            
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        #device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        _lowest_loss = 1000.0
        
        '''
        =======================================================
        train : Create list for save plot images
        =======================================================
        '''
        loss_history = []
        epochs = []
        avg_precision_list = []
        avg_recall_list = []
        val_loss_list = []
        avg_acc_list = []
        ch = str(c1)+'-'+ str(c2) +'-'+ str(c3) +'-'+ str(c4) #set~~~~~~~~~
        PLOT_TRAIN_LOSS_NAME = ' _Loss_Epoch' + date + 'Size' + str(IMAGE_SIZE) +'-' + ch + ".png"
        sm_pre = 0.0
        sm_recall = 0.0
        sm_acc = 0.0
        save_model = 1
        '''
        =======================================================
        train : Start Train model at each epoch 
        =======================================================
        '''
        if TRAIN_EPOCH:
            for epoch in range(nums_epoch):
                total_loss = 0.0
                tot_loss = 0.0 
                _loss = 0.0
                train_preds = []
                train_trues = []
                y_pred = []   #保存預測label
                y_true = []   #保存實際label
                
                for i, (inputs, labels) in enumerate(data_loader, 0):
                    '''get batch images and corresponding labels'''
                    inputs, labels = inputs.to(device), labels.to(device)
                    '''initial optimizer to zeros'''
                    optimizer.zero_grad()
                    ''' put batch images to convolution neural network '''
                    outputs = net(inputs)
                    """calculate loss by loss function"""
                    loss = criterion(outputs, labels)
                    '''after calculate loss, do back propogation'''
                    loss.backward()
                    '''optimize weight and bais'''
                    optimizer.step()
                      
                    _loss += loss.item()
                    tot_loss += loss.data
                    total_loss += loss.item()
                    train_outputs = outputs.argmax(dim=1)
                    
                    train_preds.extend(train_outputs.detach().cpu().numpy())
                    train_trues.extend(labels.detach().cpu().numpy())
                    '''
                    =======================================================
                    
                    train : After some epochs , Save the model which loss is lowest 
                    (Noted, not save model currently, just to show loss info.)
                    
                    =======================================================
                    '''
                    if i % 6 == 0 and i > 0:  # 每3步打印一次损失值
                        print('[%d, %5d] loss: %.3f' %(epoch + 1, i + 1, _loss / 1))
                        #if epoch > 0:
                        '''    
                        if _loss < _lowest_loss:
                            _lowest_loss = _loss
                            print('Start save model !')
                            torch.save(net, PATH)
                            print('save model complete with loss : %.3f' %(_loss))
                        '''
                        _loss = 0.0
                '''
                ==========================================================
                train : Save model if loss is the smallest at each epoch
                ==========================================================
                '''
                if tot_loss < _lowest_loss:
                    save_model = epoch+1
                    _lowest_loss = tot_loss
                    print('Start save model !')
                    torch.save(net, SAVE_MODEL_PATH)
                    print('save model complete with loss : %.3f' %(tot_loss))
                epochs.extend([epoch+1])
                
                
                '''
                ==========================================================
                train : plot train loss at each epochs
                ==========================================================
                '''
                if DRAW_TRAIN_LOSS_EPOCH_GRAPH:
                    loss_history.extend([int(total_loss)])
                    #epochs.extend([epoch+1])
                    print(epochs)
                    print(loss_history)
                    plt.figure(figsize = (17,9))
                    for a,b in zip(epochs, loss_history): 
                        plt.text(a, b, str(b))
                    plt.plot(epochs,loss_history)
                    plt.xlabel('epochs')
                    plt.ylabel('loss_history')
                    plt.title("loss at each epoch")
                    save_path = os.path.join(train_loss_dir,PLOT_TRAIN_LOSS_NAME)
                    plt.savefig(save_path)
                    plt.show()
                           
                
                
                '''
                =======================================================
                train : Start do validation at each epoch
                =======================================================
                '''
                avg_precision_list, avg_recall_list, val_loss_list, avg_acc_list, sm_pre, sm_recall, sm_ValLoss, sm_acc = Do_Validation_At_Each_Epoch(SAVE_MODEL_PATH,
                                                            VAL_DATA_DIR,
                                                            IMAGE_SIZE,
                                                            ENABLE_VALIDATION,
                                                            y_pred,
                                                            y_true,
                                                            epoch,
                                                            CM_FILENAME,
                                                            BATCH_SIZE,
                                                            class_names,
                                                            avg_precision_list,
                                                            avg_recall_list,
                                                            val_loss_list,
                                                            avg_acc_list,
                                                            epochs,
                                                            save_model,
                                                            c1,c2,c3,c4,
                                                            date)
                
                
    return sm_pre, sm_recall, sm_ValLoss, sm_acc
        
        
if __name__=="__main__":
    
    DO_TRAIN = True
    TRAIN_DATA_DIR = r"/home/ali/TLR/datasets/8/2022-06-17-datasets/roi"
    VAL_DATA_DIR = r"/home/ali/TLR/datasets/8/2022-06-17-datasets/roi-test"
    IMAGE_SIZE = 32
    BATCH_SIZE = 300
    nums_epoch = 50
    ENABLE_VALIDATION = True
    #CM_FILENAME = "repVGG_32_8cls_CM.png"
    class_names = ['GreenLeft', 'GreenRight', 'GreenStraight','RedLeft','RedRight','YellowLeft','YellowRight','others']
    #c1,c2,c3,c4 = 8,16,32,64
    date = '-20220628-8cls-repVGG-'
    #net = RepVGG(num_blocks=[2, 2, 2, 2], num_classes=8,
    #              width_multiplier=[0.25, 0.25, 0.25, 0.25], override_groups_map=None, deploy=False)
    
    ''' 
    =============================================================================
    Start Training Settings :
        prune channel setting list
    ============================================================================
    '''
    channel_list = [
     "0.75-0.75-0.75-2.5",
     "1-1-1-2.5",
     "1.5-1.5-1.5-2.75"
    ]
    num_of_ch = 4
    
    def parsing_channel(channel_line, num_of_ch):
        
        ch_value = [0]*num_of_ch
        for i in range(num_of_ch):
            ch_value[i] = channel_line.split("-")[i]

        return ch_value
    
    
    sm_pre, sm_recall, sm_acc, sm_ValLoss = 0.0, 0.0, 0.0, 0.0
    save_model_record = []
    
    for i in range(len(channel_list)):
        channel_line = channel_list[i]
        ch_value = parsing_channel(channel_line,num_of_ch)
        
        c1 = float(ch_value[0])
        c2 = float(ch_value[1])
        c3 = float(ch_value[2])
        c4 = float(ch_value[3])
        print(c1,c2,c3,c4)
        ch = str(c1) + '-' + str(c2) + '-' + str(c3) + '-' + str(c4)  
        SAVE_MODEL_PATH = '/home/ali/repVGG/model/' + 'repVGG-Size32-' + ch + '.pt'
        CM_FILENAME = 'repVGG_32_8cls_CM_20220628' + ch + '.png' 
        #net = ResNet(ResBlock,c1,c2,c3,c4)
        
        net = RepVGG(num_blocks=[2, 4, 14, 1], num_classes=8,
                      width_multiplier=[c1, c2, c3, c4], override_groups_map=None, deploy=False)
        if torch.cuda.is_available():
            net.cuda() 
            
        sm_pre, sm_recall, sm_ValLoss, sm_acc = train(DO_TRAIN,
                                                      net,
                                                      nums_epoch,
                                                      IMAGE_SIZE,
                                                      BATCH_SIZE,
                                                      SAVE_MODEL_PATH,
                                                      TRAIN_DATA_DIR,
                                                      VAL_DATA_DIR,
                                                      ENABLE_VALIDATION,
                                                      class_names,
                                                      CM_FILENAME,
                                                      c1,c2,c3,c4,
                                                      date)
        save_model_record.append([c1,c2,c3,c4,sm_pre,sm_recall,sm_acc,sm_ValLoss])
    '''=========================================================================================='''    
    fields = ['ch1', 'ch2', 'ch3', 'ch4', 'val_pre', 'val_rec', 'val_acc', 'val_loss']
    
    
    result_dir = "/home/ali/repVGG/result/"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_path = "/home/ali/repVGG/result/repVGG_Train_Result-20220528.csv"
    import csv
    with open(result_path, 'w') as f:
        # using csv.writer method from CSV package
        write = csv.writer(f)
        write.writerow(fields)
        write.writerows(save_model_record)
    
    print("All Training with difference channel is done !!")
                 