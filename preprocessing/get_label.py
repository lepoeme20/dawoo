import os
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dataset', type=str, help='data name'
    )
    parser.add_argument(
        '--radar-path', type=str, help='radar csv path'
    )
    parser.add_argument(
        '--data-path', type=str, help='original data path'
    )
    parser.add_argument(
        '--num-worker', type=int, default=4, help='# of workers for Pool'
    )
    params, _ = parser.parse_known_args()
    return params

def set_phase(row, trn_idx, dev_idx, tst_idx):
    phase = None
    if row['label_idx'] in trn_idx:
        phase = 'train'
    elif row['label_idx'] in dev_idx:
        phase = 'dev'
    elif row['label_idx'] in tst_idx:
        phase = 'test'
    return phase

def set_date_format(date):
    split_date = date.split('_')
    new_date = f'{split_date[0]}-{split_date[1]}-{split_date[2]} {split_date[3]}:{split_date[4]}'
    return new_date

if __name__=='__main__':
    args = get_args()

    total_img, total_time, total_idx = [], [], []
    total_direction, total_height, total_period = [], [], []

    if args.dataset == 'brave':
        # set radar_path and load WaveParam_2020.csv
        radar_path = './WaveParam_2021.csv'
        # set data_path
        data_path = '/media/lepoeme20/Data/projects/daewoo/hyundai_brave'

        radar_df = pd.read_csv(radar_path, index_col=None)
        radar_df = radar_df.rename(columns={"Date&Time": "Date"})
        radar_df = radar_df[radar_df[' SNR'] != 0.]

        # change date column type to datetime
        radar_df.Date = pd.to_datetime(radar_df.Date, format="%Y/%m/%d %H:%M")

        # set folder (date)
        radar_df.set_index('Date', inplace=True)
        folders = sorted([f for f in os.listdir(data_path) if '-' in f and f > '2020-10-22'])

        # set rm img list
        rm_df = pd.read_csv('./brave_rm.csv').iloc[:, 1:5]
        remove_img_dict = defaultdict(list)

        for k, v1, v2 in zip(rm_df.folder_name.values, rm_df.remove_start_image.values, rm_df.remove_end_image.values):
            tmp = (v1, v2)
            remove_img_dict[k].append(tmp)

        label_idx = 0
        for i, folder in enumerate(folders):
            print(folder)
            # extract specific time and empty rows
            df = radar_df[folder[:10]]

            # get images
            all_imgs = sorted(os.listdir(os.path.join(data_path, folders[i])))
            try:
                all_imgs.extend(sorted(os.listdir(os.path.join(data_path, folders[i+1]))))
            except IndexError:
                pass

            # remove unusable images
            rm_imgs = []
            for (start, end) in remove_img_dict[folders[i]]:
                rm_imgs.extend(list(filter(lambda x: start <= x[:-4] <= end, all_imgs)))
            try:
                for (start, end) in remove_img_dict[folders[i+1]]:
                    rm_imgs.extend(list(filter(lambda x: start <= x[:-4] <= end, all_imgs)))
            except IndexError:
                pass
            all_imgs = list(filter(lambda x: x not in rm_imgs, all_imgs))
            print(len(all_imgs))

            # create empty lists for append
            height_list, direction_list, period_list = [], [], []
            img_list, time_list, idx_list = [], [], []

            for idx in range(df.shape[0]):
                time = df.index[idx]
                height = float(df[' T.Hs'].iloc[idx])
                period = float(df[' T.Dp'].iloc[idx])
                direction = float(df[' T.Tp'].iloc[idx])

                # set time
                # local time = UTC time + 9 hours
                aligned_time = time + timedelta(hours=9)
                start = datetime.strftime((aligned_time - timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                end = datetime.strftime((aligned_time + timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                imgs = list(filter(lambda x: start <= x[:-6] <= end, all_imgs))

                # save images
                file_list = os.listdir(os.path.join(data_path, folder))
                image_path = []
                for img_name in imgs:
                    if img_name in file_list:
                        path = os.path.join(data_path, folders[i], img_name)
                    else:
                        path = os.path.join(data_path, folders[i+1], img_name)
                    image_path.append(path)
                img_list.extend(image_path)

                # save label
                height_list.extend([height]*len(imgs))
                direction_list.extend([direction]*len(imgs))
                period_list.extend([period]*len(imgs))
                # save time
                time_list.extend([time]*len(imgs))
                # save label index for i.i.d. condition sampling
                idx_list.extend([label_idx]*len(imgs))
                label_idx += 1

            # append data
            total_img.extend(img_list)
            total_time.extend(time_list)
            total_height.extend(height_list)
            total_direction.extend(direction_list)
            total_period.extend(period_list)
            total_idx.extend(idx_list)

    elif args.dataset == 'weather_4':
        # radar_path = '/Volumes/lepoeme/daewoo/weather_new/wavex_11.csv'
        # set data_path
        # data_path = '/media/lepoeme20/Data/projects/daewoo/weather/data'

        radar_df = pd.read_csv(args.radar_path, index_col=None)
        # get code name
        columns = radar_df.iloc[9, :].values
        # change first column name to 'Date'
        columns[0] = 'Date'
        # rename columns
        radar_df.columns = columns
        # remove rows except data
        radar_df = radar_df.iloc[13: , :]
        # change date column type to datetime
        radar_df.Date = pd.to_datetime(radar_df.Date, format="%y-%m-%d %H:%M %p")

        # set folder (date)
        folders = sorted(os.listdir(args.data_path))
        radar_df.set_index('Date', inplace=True)

        label_idx = 0
        for folder in folders:
            print(folder)
            df = radar_df[folder[:10]]

            # get images
            all_imgs = sorted(os.listdir(os.path.join(args.data_path, folder)))

            # create empty lists for append
            height_list, direction_list, period_list = [], [], []
            img_list, time_list, idx_list = [], [], []

            for idx in range(radar_df.shape[0]):
                # time = datetime.strftime(radar_df.index[0], "%Y%m%d%H%M%S")
                time = radar_df.index[idx]
                height = float(radar_df['Hm0'].iloc[idx])
                period = float(radar_df['Tm02'].iloc[idx])
                direction = float(radar_df['Dp1-t'].iloc[idx])

                # set time
                # local time = UTC time + 9 hours
                # 기상 1호는 할 필요 없음 
                # aligned_time = time + timedelta(hours=9)
                # start = datetime.strftime((aligned_time - timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                # end = datetime.strftime((aligned_time + timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                start = datetime.strftime((time - timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                end = datetime.strftime((time + timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                imgs = list(filter(lambda x: start <= x[:-6] <= end, all_imgs))

                # save images
                image_path = [os.path.join(args.data_path, folder, impath) for impath in imgs]
                img_list.extend(image_path)
                # save label
                height_list.extend([height]*len(imgs))
                direction_list.extend([direction]*len(imgs))
                period_list.extend([period]*len(imgs))
                # save time
                time_list.extend([time]*len(imgs))
                # save label index for i.i.d. condition sampling
                idx_list.extend([label_idx]*len(imgs))
                label_idx += 1

            # append data
            total_img.extend(img_list)
            total_time.extend(time_list)
            total_height.extend(height_list)
            total_direction.extend(direction_list)
            total_period.extend(period_list)
            total_idx.extend(idx_list)

    elif args.dataset == 'weather_1':
        # radar_path = '/Volumes/lepoeme/daewoo/weather_old/wavex_label_2018.csv'
        # set data_path
        # data_path = '/Volumes/lepoeme/daewoo/weather_new/weather_1'

        radar_df = pd.read_csv(args.radar_path, index_col=None)
        radar_df.DATE = [set_date_format(date) for date in radar_df.DATE.values]
        # change date column type to datetime
        radar_df.Date = pd.to_datetime(radar_df.DATE, format="%Y-%m-%d %H:%M")

        # set folder (date)
        folders = sorted(os.listdir(args.data_path))
        radar_df.set_index('DATE', inplace=True)

        label_idx = 0
        for folder in folders:
            print(folder)
            df = radar_df[folder[:10]]

            # get images
            all_imgs = sorted(os.listdir(os.path.join(args.data_path, folder)))

            # create empty lists for append
            height_list, direction_list, period_list = [], [], []
            img_list, time_list, idx_list = [], [], []

            for idx in range(radar_df.shape[0]):
                # time = datetime.strftime(radar_df.index[0], "%Y%m%d%H%M%S")
                time = radar_df.index[idx]
                height = float(radar_df['SWH'].iloc[idx])
                period = float(radar_df['SWT'].iloc[idx])
                direction = float(radar_df['DIR'].iloc[idx])

                # set time
                # local time = UTC time + 9 hours
                # 기상 1호는 할 필요 없음 
                # aligned_time = time + timedelta(hours=9)
                # start = datetime.strftime((aligned_time - timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                # end = datetime.strftime((aligned_time + timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                start = datetime.strftime((time - timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                end = datetime.strftime((time + timedelta(minutes=2, seconds=30)), "%Y%m%d%H%M%S")
                imgs = list(filter(lambda x: start <= x[:-6] <= end, all_imgs))

                # save images
                image_path = [os.path.join(args.data_path, folder, impath) for impath in imgs]
                img_list.extend(image_path)
                # save label
                height_list.extend([height]*len(imgs))
                direction_list.extend([direction]*len(imgs))
                period_list.extend([period]*len(imgs))
                # save time
                time_list.extend([time]*len(imgs))
                # save label index for i.i.d. condition sampling
                idx_list.extend([label_idx]*len(imgs))
                label_idx += 1

            # append data
            total_img.extend(img_list)
            total_time.extend(time_list)
            total_height.extend(height_list)
            total_direction.extend(direction_list)
            total_period.extend(period_list)
            total_idx.extend(idx_list)


    # create dictionary for build pandas dataframe
    data_dict = {
        'time':total_time,
        'image':total_img,
        'height':total_height,
        'direction': total_direction,
        'period': total_period,
        'label_idx': total_idx
    }
    final_df = pd.DataFrame(data_dict)

    np.random.seed(22)

    # Time Series
    unique_id = np.unique(final_df['label_idx'])
    trn_idx, dev_idx, tst_idx = np.split(
        unique_id, [int(.6*len(unique_id)), int(.8*len(unique_id))]
        )
    final_df['time_phase'] = final_df.apply(
        lambda row: set_phase(row, trn_idx, dev_idx, tst_idx), axis=1)

    # i.i.d condition
    np.random.shuffle(unique_id)
    trn_idx, dev_idx, tst_idx = np.split(
        unique_id, [int(.6*len(unique_id)), int(.8*len(unique_id))]
        )
    final_df['iid_phase'] = final_df.apply(
        lambda row: set_phase(row, trn_idx, dev_idx, tst_idx), axis=1)

    final_df.to_csv(f'./brave_data_label.csv', index=False)
