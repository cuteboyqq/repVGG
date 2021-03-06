#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 13:49:09 2022

@author: ali
reference code at below link:
    https://docs.microsoft.com/zh-cn/windows/ai/windows-ml/tutorials/pytorch-convert-model

"""

import torch.onnx
import os
os.environ["KMP_DUPLICATE_LIB_OK"]  =  "TRUE"
import torch
import torch.nn as nn
import torch.nn.functional as F

c1,c2,c3,c4 = 8,16,32,64
NUM_CLASS = 8

#定义残差块ResBlock
class ResBlock(nn.Module):
    def __init__(self, inchannel, outchannel, stride=1):
        super(ResBlock, self).__init__()
        #这里定义了残差块内连续的2个卷积层
        self.left = nn.Sequential(
            nn.Conv2d(inchannel, outchannel, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(outchannel),
            nn.ReLU(inplace=True),
            nn.Conv2d(outchannel, outchannel, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(outchannel)
        )
        self.shortcut = nn.Sequential()
        if stride != 1 or inchannel != outchannel:
            #shortcut，这里为了跟2个卷积层的结果结构一致，要做处理
            self.shortcut = nn.Sequential(
                nn.Conv2d(inchannel, outchannel, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(outchannel)
            )
            
    def forward(self, x):
        out = self.left(x)
        #将2个卷积层的输出跟处理过的x相加，实现ResNet的基本结构
        out = out + self.shortcut(x)
        out = F.relu(out)
        
        return out
 
class ResNet(nn.Module):
    def __init__(self, ResBlock, num_classes=NUM_CLASS):
        super(ResNet, self).__init__()
        self.inchannel = 64
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU()
        )
        self.layer1 = self.make_layer(ResBlock, c1, 2, stride=1)#16
        self.layer2 = self.make_layer(ResBlock, c2, 2, stride=2)#32
        self.layer3 = self.make_layer(ResBlock, c3, 2, stride=2)#64        
        self.layer4 = self.make_layer(ResBlock, c4, 2, stride=2)#128        
        self.fc = nn.Linear(c4, num_classes)#512 for 64*64,128 for 32*32
    #这个函数主要是用来，重复同一个残差块    
    def make_layer(self, block, channels, num_blocks, stride):
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for stride in strides:
            layers.append(block(self.inchannel, channels, stride))
            self.inchannel = channels
        return nn.Sequential(*layers)
    
    def forward(self, x):
        #在这里，整个ResNet18的结构就很清晰了
        out = self.conv1(x)
        #print(out.shape)
        out = self.layer1(out)
        #print(out.shape)
        out = self.layer2(out)
        #print(out.shape)
        out = self.layer3(out)
        #print(out.shape)
        out = self.layer4(out)
        #print(out.shape)
        out = F.avg_pool2d(out, 4)
        #print(out.shape)
        out = out.view(out.size(0), -1)
        #print(out.shape)
        out = self.fc(out)
        #print(out.shape)
        return out

#Function to Convert to ONNX 
def Convert_ONNX(model,input_size): 

    # set the model to inference mode 
    model.eval() 

    # Let's create a dummy input tensor
    
    dummy_input = torch.randn(1, 3, input_size, input_size, device = 'cpu')  
    #dummy_input = torch.randn(1, 3, input_size, input_size)  

    # Export the model   
    torch.onnx.export(model,         # model being run 
         dummy_input,       # model input (or a tuple for multiple inputs) 
         "2022-07-03-resnet-Size32-16-32-48-64-b2-2-3-2.onnx",       # where to save the model  
         export_params=True,  # store the trained parameter weights inside the model file 
         opset_version=9,    # the ONNX version to export the model to 
         verbose=True,
         #do_constant_folding=True,  # whether to execute constant folding for optimization 
         input_names = ['data'],   # the model's input names 
         output_names = ['resnet18'], # the model's output names 
         #dynamic_axes={'modelInput' : {0 : 'batch_size'},    # variable length axes 
                                #'modelOutput' : {0 : 'batch_size'}}
                    ) 
    print(" ") 
    print('Model has been converted to ONNX') 


def get_args():
    import argparse
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-weights','--weights',help='model path',default="/home/ali/repVGG/model/2022-07-03/resnet-Size32-16-32-48-64-b2-2-3-2.pt")
    parser.add_argument('-img-size','--img-size',type=int,default=32)
   
    
    return parser.parse_args()    
    
if __name__ == "__main__": 

    # Let's build our model 
    #train(5) 
    #print('Finished Training') 

    # Test which classes performed well 
    #testAccuracy() 
    ''' get parameters from console'''
    args = get_args()
    ''' assign parameter'''
    path = args.weights
    input_size = args.img_size
    
    # Let's load the model we just created and test the accuracy per label 
    
    #model = ResNet(ResBlock)
    #if torch.cuda.is_available():
        #model.cuda()
        #print("use GPU cuda")
    #else:
        #print("No GPU available, use cpu")
    #print(model)
    #print("===========================================================================================")
    #params = list(model.parameters())
    #print(len(params))
    
    #for name, parameters in model.named_parameters():
        #print(f'{name}: {parameters.size()}')
    #model = Network() 
    #path = "/home/ali/TLR/model/TLR_ResNet18-20220621-8cls-Finetune-Add-Argos-ver2-Size32-8-16-32-64.pt" 
    model = torch.load(path,map_location=torch.device('cpu')) 
    #model = torch.load(path) 

    # Test with batch of images 
    #testBatch() 
    # Test how the classes performed 
    #testClassess() 
 
    # Conversion to ONNX 
    Convert_ONNX(model,input_size) 