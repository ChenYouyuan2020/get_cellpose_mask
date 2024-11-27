import numpy as np
import h5py
import argparse
import os
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('--path',type=str,default='.\outlines.txt', help="the path of merge.h5")
parser.add_argument('--cellpose_mask_path',type=str,default='.\cellpose_mask.txt', help="the path of cellpose_mask.txt")
parser.add_argument('--save_flod',type=str,default='data',help="the save path of mask")
args = parser.parse_args()

PATH = args.path
PATH_MASK = args.cellpose_mask_path
SAVE_FLOD = args.save_flod

def insert_matrix(fluo, fluo_scale, fluo_ori):
    x = np.round(np.arange(fluo.shape[1]) * (1 / fluo_scale)).astype('int')
    x = x + round((fluo_ori.shape[1] - x[-1]) / 2)

    y = np.round(np.arange(fluo.shape[0]) * (1 / fluo_scale)).astype('int')
    y = y + round((fluo_ori.shape[0] - y[-1]) / 2)

    xy = np.meshgrid(x, y)
    p = np.zeros(fluo_ori.shape[:2])

    p[xy[1], xy[0]] = 1
    return p.astype('bool')

def read_txt(path):
    data = np.loadtxt(path, delimiter=',')
    return data.astype('int')


class Scatter_points():
    def __init__(self, path, cellpose_mask_path):
        self.fluo, self.fluo_ori, self.fluo_scale = self.read_h5(path)
        self.cellpose_mask = read_txt(cellpose_mask_path)
        self.scatter_mask = self.scatter_masks()
        self.incell_mask, self.ingroup_mask = self.gene_cells_mask()

    def read_h5(self,path):
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

    def scatter_masks(self):
        scatter_mask = insert_matrix(self.fluo, self.fluo_scale, self.fluo_ori)
        return scatter_mask

    def gene_cells_mask(self):
        cellpose_mask0 = self.cellpose_mask.copy().astype('float')
        scatter_mask0 = self.scatter_mask.copy().astype('float')
        cellpose_mask0[(scatter_mask0==1)&(cellpose_mask0==0)] = np.inf
        scatter_mask0[scatter_mask0 != 0] = cellpose_mask0[scatter_mask0 != 0]
        ingroup = scatter_mask0[scatter_mask0 != 0].reshape(self.fluo.shape[:2])
        ingroup[ingroup == np.inf] = 0
        incell = ingroup.copy()
        incell[incell != 0] = 1

        return incell.astype('int'), ingroup.astype('int')

ScatterPoints = Scatter_points(PATH, PATH_MASK)
scatter_mask = ScatterPoints.scatter_mask
incell_mask = ScatterPoints.incell_mask
ingroup_mask = ScatterPoints.ingroup_mask

np.savetxt(os.path.join(SAVE_FLOD,"scatter_mask.txt"),scatter_mask,delimiter=',')
np.savetxt(os.path.join(SAVE_FLOD,"incell_mask.txt"),incell_mask,delimiter=',')
np.savetxt(os.path.join(SAVE_FLOD,"ingroup_mask.txt"),ingroup_mask,delimiter=',')
