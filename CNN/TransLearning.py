# -*- coding: UTF-8 -*-

"""
Transfer learning for feature extracting or finetuning. 
"""
from schnablelab.apps.base import OptionParser, ActionDispatcher
from base import EarlyStopping, LeafcountingDataset, image_transforms, initialize_model, train_model_regression 
import sys
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import logging
import pandas as pd

def main():
    actions = (
        ('regression', 'using pretrained model to solve regression problem'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def regression(args):
    """
    %prog regression train_csv, train_dir, valid_csv, valid_dir, model_name_prefix
    Args:
        train_csv: csv file (comma separated without header) containing all training image filenames.
        train_dir: directory where training images are located
        valid_csv: csv file (comma separated without header) containing all validation image filenames.
        valid_dir: directory where validation images are located
        model_name_prefix: the prefix of the output model name 
    """
    p = OptionParser(regression.__doc__)
    p.add_option('--batchsize', default=36, type='int', 
                    help='batch size')
    p.add_option('--epoch', default=200, type='int', 
                    help='number of total epochs')
    p.add_option('--patience', default=20, type='int', 
                    help='patience in early stopping')
    p.add_option('--pretrained_mn', default='vgg16',
                    help='pretrained model name. Available pretrained models: vgg16, googlenet, resnet18, resnet152...')
    p.add_option('--tl_type', default='feature_extract', choices=('feature_extract', 'finetuning'),
                    help='transfer learning type')
    p.add_option('--logfile', default='training.log',
                    help = 'the file saving log')
    p.add_option('--history', default='history_loss.csv',
                    help = 'the file saving training and validation losses.')

    opts, args = p.parse_args(args)
    if len(args) != 5:
        sys.exit(not p.print_help())
    train_csv, train_dir, valid_csv, valid_dir, model_name_prefix = args
    logging.basicConfig(filename=opts.logfile, level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")

    # prepare training and validation data
    train_dataset = LeafcountingDataset(train_csv, train_dir, image_transforms['train'])
    valid_dataset = LeafcountingDataset(valid_csv, valid_dir, image_transforms['valid'])
    train_loader = DataLoader(train_dataset, batch_size=opts.batchsize)
    valid_loader = DataLoader(valid_dataset, batch_size=opts.batchsize)
    dataloaders_dict = {'train': train_loader, 'valid': valid_loader}

    # initialize the pre-trained model
    model, input_size = initialize_model(model_name=opts.pretrained_mn)
    logging.debug(model)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    logging.debug('device: %s'%device)

    feature_extract = True if opts.tl_type == 'feature_extract' else False

    params_to_update = model.parameters()
    logging.debug("Params to learn:")
    if feature_extract:
        params_to_update = []
        for name, param in model.named_parameters():
            if param.requires_grad == True:
                params_to_update.append(param)
                logging.debug("\t",name)
    else:
        for name, param in model.named_parameters():
            if param.requires_grad == True:
                logging.debug("\t",name)
    # optimizer
    sgd_optimizer = optim.SGD(params_to_update, lr=0.001, momentum=0.9)
    # loss
    criterion = nn.MSELoss()
    # train and validation
    inception = True if opts.model_name=='inception' else False
    since = time.time()
    model_ft, train_hist, valid_hist = train_model_regression(model, dataloaders_dict, 
                                                            criterion, sgd_optimizer,
                                                            model_name_prefix, 
                                                            patience=opts.patience, 
                                                            num_epochs=opts.epoch, 
                                                            is_inception=inception)
    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    # save train and validation loss.
    logging.debug('saving loss history...')
    df = pd.DataFrame(dict(zip(['training_loss', 'validation_loss'], [train_hist, valid_hist])))
    df.to_csv(opts.history, index=False)

if __name__ == "__main__":
    main()