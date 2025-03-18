import numpy as np 
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

s0 = np.load("Picture/closeS0.npy")
s1 = np.load("Picture/closeS1.npy")
s2 = np.load("Picture/closeS2.npy")
fig, ax = plt.subplots(1,3,figsize=(8,4))
imageS0 = ax[0].imshow(s0,cmap='gray')
imageS1 = ax[1].imshow(s1,cmap='jet')
imageS2 = ax[2].imshow(s2,cmap='jet')

ax[0].set_title('S0')
ax[1].set_title('S1')
ax[2].set_title('S2')

divider = make_axes_locatable(ax[0])
cax = divider.append_axes("right", size="5%", pad=0.05)  # 設定 colorbar 大小與間距
cb = plt.colorbar(imageS0, cax=cax)  # 加入 colorbar

divider = make_axes_locatable(ax[1])
cax = divider.append_axes("right", size="5%", pad=0.05)  # 設定 colorbar 大小與間距
cb = plt.colorbar(imageS1, cax=cax)  # 加入 colorbar

divider = make_axes_locatable(ax[2])
cax = divider.append_axes("right", size="5%", pad=0.05)  # 設定 colorbar 大小與間距
cb = plt.colorbar(imageS2, cax=cax)  # 加入 colorbar


plt.show()