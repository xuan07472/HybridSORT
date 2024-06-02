import os
import argparse
import math
import cv2
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

def generate_trajectories(file_path, GroundTrues):
    f = open(file_path, 'r')

    lines = f.read().split('\n')        # list of [n_lines] or [n_objs]
    values = []
    for l in lines:
        split = l.split(',')    # <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>, <active>, <category>, <visible_ratio>
        if len(split) < 2:
            break
        numbers = [float(i) for i in split]     # int to float
        values.append(numbers)

    values = np.array(values, np.float_)

    if GroundTrues:     # filter objects
        # values = values[values[:, 6] == 1, :]  # Remove ignore objects, only active objects
        # values = values[values[:, 7] == 1, :]  # Pedestrian only
        values = values[values[:, 8] > 0.4, :]  # visibility only

    values = np.array(values)
    values[:, 4] += values[:, 2]        # tlwh to tlbr
    values[:, 5] += values[:, 3]

    return values

def make_parser():
    parser = argparse.ArgumentParser("MOTChallenge ReID dataset")

    parser.add_argument("--data_path", default="", help="path to MOT data")
    parser.add_argument("--save_path", default="fast_reid/datasets", help="Path to save the MOT-ReID dataset")
    parser.add_argument("--mot", default=17, help="MOTChallenge dataset number e.g. 17, 20")

    return parser


def main(args):

    # Create folder for outputs
    save_path = os.path.join(args.save_path, 'MOT' + str(args.mot) + '-ReID')
    os.makedirs(save_path, exist_ok=True)
    train_save_path = os.path.join(save_path, 'bounding_box_train')
    os.makedirs(train_save_path, exist_ok=True)
    test_save_path = os.path.join(save_path, 'bounding_box_test')
    os.makedirs(test_save_path, exist_ok=True)
    query_save_path = os.path.join(save_path, 'query')
    os.makedirs(query_save_path, exist_ok=True)
    # gallery_save_path = os.path.join(save_path, 'gallery')
    # os.makedirs(gallery_save_path, exist_ok=True)

    # Get gt data
    data_path = os.path.join(args.data_path, 'MOT' + str(args.mot), 'train')

    if args.mot == '17':
        seqs = [f for f in os.listdir(data_path) if 'FRCNN' in f]
    else:
        seqs = os.listdir(data_path)

    seqs.sort()

    id_offset = 0

    for seq in seqs:        # iteration over seqs
        print("current seq", seq)
        print("current id_offset", id_offset)

        ground_truth_path = os.path.join(data_path, seq, 'gt/gt.txt')
        gt = generate_trajectories(ground_truth_path, GroundTrues=True)  # [do filter] frame, id, x_tl, y_tl, x_br, y_br, active, category, visible_ratio

        images_path = os.path.join(data_path, seq, 'img1')
        img_files = os.listdir(images_path)
        img_files.sort()

        num_frames = len(img_files)
        max_id_per_seq = 0
        for f in tqdm(range(num_frames)):     # iteration over frames
            img = cv2.imread(os.path.join(images_path, img_files[f]))
            if img is None:
                print("ERROR: Receive empty frame")
                continue
            H, W, _ = np.shape(img)
            det = gt[f + 1 == gt[:, 0], 1:].astype(np.int_)     # dets in current frame. [id, x_tl, y_tl, x_br, y_br, active, category, visible_ratio]
            for d in range(np.size(det, 0)):
                id_ = det[d, 0]
                x1 = det[d, 1]
                y1 = det[d, 2]
                x2 = det[d, 3]
                y2 = det[d, 4]
                # clamp
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(x2, W)
                y2 = min(y2, H)

                # patch = cv2.cvtColor(img[y1:y2, x1:x2, :], cv2.COLOR_BGR2RGB)
                patch = img[y1:y2, x1:x2, :]        # crop image

                max_id_per_seq = max(max_id_per_seq, id_)       # update 'max_id_per_seq'

                # plt.figure()
                # plt.imshow(patch)
                # plt.show()

                train_fileName = (str(id_+id_offset)).zfill(4) + '_c1s1_' + '_' + (str(f+1)).zfill(6) + '.jpg'
                test_fileName = (str(id_+id_offset)).zfill(4) + '_c1s1_'  + '_' + (str(f+1)).zfill(6) + '.jpg'
                gallery_fileName = (str(id_+id_offset)).zfill(4) + '_c2s2_' + '_' + (str(f+1)).zfill(6) + '.jpg'
                
                # 每5张
                # if f < num_frames // 2:
                #     if f % 5 == 0:
                #         cv2.imwrite(os.path.join(train_save_path, train_fileName), patch)
                # else:
                #     if f % 5 == 0:
                #         cv2.imwrite(os.path.join(test_save_path, test_fileName), patch)
                #     # cv2.imwrite(os.path.join(gallery_fileName, gallery_fileName), patch)
                    
                if f < num_frames // 2:
                    cv2.imwrite(os.path.join(train_save_path, train_fileName), patch)
                else:
                    cv2.imwrite(os.path.join(test_save_path, test_fileName), patch)
                    # cv2.imwrite(os.path.join(gallery_fileName, gallery_fileName), patch)

        id_offset += max_id_per_seq


if __name__ == "__main__":
    args = make_parser().parse_args()
    main(args)
