import os
import cv2
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool
from collections import defaultdict
from functools import partial
import argparse
from tqdm import tqdm

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dataset', type=str, help='data name'
    )
    parser.add_argument(
        '--data-path', type=str, help='original data path'
    )
    # parser.add_argument(
    #     '--save-path', type=str, help='data save path'
    # )
    parser.add_argument(
        '--num-worker', type=int, default=4, help='# of workers for Pool'
    )
    params, _ = parser.parse_known_args()
    params.save_path = os.path.join(params.data_path, "crop_data")
    return params


def preprocessing(img_name, data_path, folder, save_path):
    try:
        os.makedirs(os.path.join(save_path, folder), exist_ok=True)
        img = cv2.imread(os.path.join(data_path, folder, img_name), cv2.IMREAD_GRAYSCALE)
        img_gray = img.astype(np.float32)

        # ROI cropping (1344 448)
        if 'weather_old' in data_path:
            img = img_gray[246:694, 149:1493]
        else:
            # 1920 * 1080
            y_total, x_total = img_gray.shape
            w = 1344
            h = 448
            x = int(x_total/2 - w/2)
            y = int(y_total/2 - h/2)
            img = img_gray[y:y+h, x:x+w]

        # Resizing
        # img = cv2.resize(img, dsize=(224, 224))

        # cv2.rectangle(img,(x, y),(x+w, y+h), (0,255,0), 2)
        cv2.imwrite(os.path.join(save_path, folder, img_name), img)
    except AttributeError:
        pass

def save_data(data_folders, start, end):
    progress = tqdm(total=len(data_folders), desc="Progress", position=0, leave=False)

    for folder in data_folders:
        if start <= folder and folder <= end:
            daytime_imgs = []
            files = sorted(os.listdir(os.path.join(args.data_path, folder)))
            for img in files:
                time = img.split('_')
                if time[0][8:10] > '06' and time[0][8:10] < '17':
                    daytime_imgs.append(img)

            save_img=partial(preprocessing, data_path=args.data_path, folder=folder, save_path=args.save_path)

            with Pool(args.num_worker) as p:
                p.map(save_img, daytime_imgs)
        progress.update(1)

if __name__=='__main__':
    args = get_args()

    if args.dataset == 'brave':
        df = pd.read_csv('./brave.csv').iloc[:, 1:5]
        remove_img_dict = defaultdict(list)

        for k, v1, v2 in zip(df.folder_name.values, df.remove_start_image.values, df.remove_end_image.values):
            tmp = (v1, v2)
            remove_img_dict[k].append(tmp)

        # set data_path
        # d_path = '/media/lepoeme20/Data/projects/daewoo/brave/data'
        # s_path = '/media/lepoeme20/Data/projects/daewoo/brave/crop'
        folders = sorted(os.listdir(args.data_path))

        for i, folder in enumerate(folders):
            # create save path
            os.makedirs(os.path.join(args.save_path, folder), exist_ok=True)

            # get images
            all_imgs = sorted(os.listdir(os.path.join(args.data_path, folder)))
            imgs = list(filter(lambda x: 7 <= int(x[8:10]) < 17, all_imgs))

            rm_imgs = []
            for (start, end) in remove_img_dict[folder]:
                start = start if len(start) == 17 else start.replace('.jpg', '')
                end = end if len(end) == 17 else end.replace('.jpg', '')
                if start != '-' and end != '-':
                    rm_imgs.extend(list(filter(lambda x: start <= x[:-4] <= end, imgs)))
            imgs = list(filter(lambda x: x not in rm_imgs, imgs))

            save_img=partial(preprocessing, data_path=args.data_path, folder=folder, save_path=args.save_path)

            with Pool(args.num_worker) as p:
                p.map(save_img, imgs)

            print("{}/{} \t Folder: {} | Total Image: {:,} | RM Image: {:,} | Usable Image: {:,}".format(
                i, len(folders), folder, len(imgs)+len(rm_imgs), len(rm_imgs), len(imgs)))

    elif args.dataset == 'weather_new':
        data_folders = sorted(os.listdir(args.data_path))
        save_data(data_folders, '2020-11-05', '2020-11-07')
        save_data(data_folders, '2020-11-08', '2020-11-11')
        save_data(data_folders, '2020-11-17', '2020-11-17')

    elif args.dataset == 'weather_old':
        data_folders = sorted(os.listdir(args.data_path))
        save_data(data_folders, '2018-11-06', '2018-11-13')

    elif args.dataset == 'kmou':
        for camera in ("PORT", "STBD"):
            args.data_path = os.path.join(args.data_path, camera)
            data_folders = sorted(os.listdir(args.data_path))
            args.save_path = os.path.join(args.data_path, "crop_data")
            os.makedirs(args.save_path, exist_ok=True)
            save_data(data_folders, '2020-11-18-1', '2020-11-19-0')
            save_data(data_folders, '2020-11-23-0', '2020-11-24-0')