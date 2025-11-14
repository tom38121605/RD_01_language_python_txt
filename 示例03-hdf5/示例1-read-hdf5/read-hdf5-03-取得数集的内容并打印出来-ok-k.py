from os.path import expanduser
import h5py
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import os.path
import math


# def main():
#
#     file_name = "data0.hdf5"
#     data_file = h5py.File(expanduser(file_name), 'r')
#     print("文件中的对象：", list(data_file.keys()))
#
#     dataset = data_file['/Device_3528137102_0/Theta']      #取得数集的dataset
#     data = dataset[:]  #取得数集的所有内容  # 推荐用 [:]，兼容所有 HDF5 版本
#
#     print("数据集内容：", data)               # 输出该数集的所有内容
#     print("数据集形状：", dataset.shape)      # 输出该数集的行列数和维度， (17704, 1)
#     print("数据集数据类型：", dataset.dtype)   # 输出该数集的内容，uint16
#
#     data_file.close()

# def main():
    # file_name = "C:\\workspace\\ommo_eval_sdk_v0.20.3\\ommo_app\\data\\data0.hdf5"
    # txt_file_name = (file_name[:file_name.rindex('\\')] + "\\" + 'console_log_'
    #                  + file_name[ file_name.rindex('\\') + 1:-5] + '.txt')

    # file_name = r"C:\workspace\ommo_eval_sdk_v0.20.3\ommo_app\data\data0.hdf5"
    # file_path = os.path.dirname(file_name)
    # basename = os.path.basename(file_name)
    # file_base = os.path.splitext(basename)[0]
    # txt_file_name = os.path.join(file_path, f"console_log_{file_base}.txt")
    #
    # print(file_name)
    # print(txt_file_name)

def main():

    file_path = r"data0.hdf5"
    with h5py.File(file_path, 'r') as f:

        last_dataset = None
        data=[]

        def get_dataset_name(name, obj):
            nonlocal last_dataset
            nonlocal data

            if isinstance(obj,h5py.Group):
                print(f"Group路径：----- {name} -----")
            elif isinstance(obj, h5py.Dataset): # and name.endswith("Theta"):
                # print(f"数据集名称：{name.split('/')[-1]}")
                print(f"数据集名称：{os.path.basename(name)}")
                last_dataset = os.path.basename(name)
                data = obj[:]

        f.visititems(get_dataset_name)

        if last_dataset:
           print("数据集名称2：", last_dataset)
           print("数据集内容：", data)



if __name__ == "__main__":
    main()