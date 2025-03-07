import argparse
import pandas as pd
import numpy as np

class class_label:
    def func(self, x, unit):
        new_label = np.arange(0, 2, 2 / unit)
        for i in range(0, unit - 1):
            if (x >= new_label[i]) & (x < new_label[i + 1]):
                return new_label[i]
            if (x >= new_label[unit - 2]):
                return new_label[unit - 2]

    """
    def generate_class(self, dataset, label_column, unit):
        '''
        dataset: dataset name (brave / weather)
        label_column: column name of original label
        unit: 10cm / 20cm (range of each class)
    
        return df: whole label file with new class label (column: 'class_label')
        '''
        label_path = '../preprocessing/' + dataset + '_data_label.csv'
        df = pd.read_csv(label_path)
        df['class_label'] = df[label_column].apply(lambda x: self.func(x, unit))
        return df
    """

    def generate_class(self, df, label_column, unit):
        '''
        df : label dataframe
        label_column: column name of original label
        unit: 10cm / 20cm (range of each class)

        return df: whole label file with new class label (column: 'class_label')
        '''
        df[f'class_label_{unit}'] = df[label_column].apply(lambda x: self.func(x, unit))
        return df
