import numpy as np
import h5py
from cellpose import models
import argparse
import os
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, default=r'D:\self_file\Large Image 2-st-11-24-3-14-2notd_RGB_DiI.tif', help='Merge file with fluo and scale')
parser.add_argument('--divide_y', type=int, default=8, help='Merge file with fluo and scale')
parser.add_argument('--divide_x', type=int, default=8, help='Merge file with fluo and scale')
parser.add_argument('--save_flod',type=str, default=r'data',help='path for save.')

args = parser.parse_args()
PATH = args.path
D_Y = args.divide_y
D_X = args.divide_x
SAVE_FLOD = args.save_flod

class Get_cellpose_mask():
    def __init__(self,img,cut_y,cut_x):
        self.img = img
        self.cut_y = cut_y
        self.cut_x = cut_x
        self.cut_list_points = self.cut_picture()
        self.masks = self.cellpose_merge()

    def cut_picture(self):
        points_y = [i*(self.img.shape[0]//self.cut_y) for i in range(self.cut_y)]
        points_y.append(self.img.shape[0])
        points_x = [i*(self.img.shape[1]//self.cut_x) for i in range(self.cut_x)]
        points_x.append(self.img.shape[1])
        abst = np.meshgrid(points_x,points_y)
        cut_list_points = []
        for i in range(len(points_y)-1):
            for j in range(len(points_x)-1):
                cut_list_points.append([abst[1][i,j],abst[0][i,j],abst[1][i+1,j+1],abst[0][i+1,j+1]])
        return cut_list_points

    def cellpose_cut(self, img_part):
        model = models.Cellpose(gpu=True, model_type='cyto')
        masks, flows, styles, diams = model.eval(img_part, diameter=None, channels=[0, 1, 2])
        return masks

    def cellpose_merge(self):
        masks_new = np.zeros((self.img.shape[:2]))
        num = 0
        for line in self.cut_list_points:
            [a, b, c, d] = line
            img_part = self.img[a:c, b:d]
            masks = self.cellpose_cut(img_part)
            # merge_mask(patch1, patch2)
            masks[masks != 0] = masks[masks != 0] + num
            num = np.max(masks)
            masks_new[a:c, b:d] = masks
            print("patch from y:(%d，%d), x:(%d,%d) is OK with %d cells "%(a, c, b, d, num))
        print("all patch is OK")
        return masks_new
    #目前mask之间的合并，被patch分割部分细胞并没有merge,需要优化
    def merge_mask(self, mask1, mask2):
        return 0

def read_h5(path):
    file = h5py.File(path, 'r')
    print(file.keys())
    fluo = np.array(file['fluo'])
    fluo_ori = np.array(file['fluo-ori'])
    fluo_scale = np.array(file['fluo_scale'])
    print(fluo.shape, fluo_scale)
    return fluo, fluo_ori, fluo_scale

def read_picture(path):
    fluo_ori = cv2.imread(path,cv2.IMREAD_UNCHANGED)
    return fluo_ori

if __name__ == '__main__':
    if PATH.endswith('.h5'):
        fluo,fluo_ori,fluo_scale = read_h5(PATH)
    else:
        fluo_ori = read_picture(PATH)
    CELL_MASK = Get_cellpose_mask(fluo_ori,D_Y,D_X)
    cell_masks = CELL_MASK.masks
    
    save_path = os.path.join(SAVE_FLOD,"cellpose_masks.txt")
    np.savetxt(save_path, cell_masks, delimiter=',')
