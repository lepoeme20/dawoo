import argparse
import random

import numpy as np
import torch


def str2bool(v):
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def fix_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)


# define "soft" cross-entropy for wave direction classification
def soft_label_half(li,window_size) :
    
    #li = [0,0,0,0,0,1]
    #window_size =2
    max_v = len(li)-1
    position = torch.argmax(li)
    for i in range(1,window_size+1) :
        
        if (position-i) < 0   :
            li[position+i] = 1/(1+i)
            continue 
        
        elif (position-i)>=0 and (position+i) < max_v :
            
            li[position-i] = 1/(1+i)
            li[position+i] = 1/(1+i)
            
        elif (position+i) > max_v :
            li[position-i] = 1/(1+i)
            
    return li


def make_target_dist(target, window_size,class_num):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    target_dist = torch.FloatTensor(target.shape[0], class_num)
    
    target_dist = target_dist.zero_()
    
    target_dist = target_dist.to(device)
    target = target.to(device)
    target_dist = target_dist.scatter_(1, target.view(-1, 1), 1)
    
    
    target_dist = [soft_label_half(li,window_size).tolist() for li in target_dist]
    target_dist = torch.Tensor(target_dist)

    return target_dist.to(device)



def softXEnt(inputs, target,class_num, window_size):
    # target = labels
    # window_size=2
    # class_num=10
    target_dist = make_target_dist(target, window_size,class_num)
    logprobs = torch.nn.functional.log_softmax(inputs, dim=1)
    return  -(target_dist * logprobs).sum() / inputs.shape[0]


class EarlyStopping:
    """Early stops the training if validation loss doesn't improve after a given patience.
    ref: https://github.com/Bjarten/early-stopping-pytorch
    """

    def __init__(
        self, patience=7, verbose=False, delta=0, path="best_model.pt", trace_func=print
    ):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                            Default: 7
            verbose (bool): If True, prints a message for each validation loss improvement.
                            Default: False
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                            Default: 0
            path (str): Path for the checkpoint to be saved to.
                            Default: 'checkpoint.pt'
            trace_func (function): trace print function.
                            Default: print
        """
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.Inf
        self.delta = delta
        self.path = path
        self.trace_func = trace_func

    def __call__(self, val_loss, model):

        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            self.trace_func(
                f"EarlyStopping counter: {self.counter} out of {self.patience}"
            )
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss, model):
        """Saves model when validation loss decrease."""
        if self.verbose:
            self.trace_func(
                f"Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}).  Saving model ..."
            )
        torch.save(model.state_dict(), self.path)
        self.val_loss_min = val_loss