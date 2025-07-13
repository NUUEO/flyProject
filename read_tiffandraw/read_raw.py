import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import inspect
import os
import shutil


def get_var_name(var):
    frame = inspect.currentframe().f_back
    return [key for key, value in frame.f_locals.items() if value is var]

def read_and_show_raw(filename, width, height, dtype=np.uint8):
    with open(filename, "rb") as f:
        data = np.frombuffer(f.read(), dtype=dtype)

    # 重新塑形為 2D 影像
    image = data.reshape((height, width))
    return image
def read_tiff(filename, width, height, dtype=np.uint8):
    img = Image.open(filename)
    image = np.array(img, dtype=dtype)
    return np.array(image, dtype=dtype)
def find_raw_files(directory='./'):
    """
    遍歷目錄並找到所有 .raw 檔案（僅限當前目錄）

    參數:
    - directory: 要搜尋的根目錄路徑

    回傳:
    - raw_files: 包含所有找到的 .raw 檔案完整路徑的清單
    """
    raw_files = []
    for file in os.listdir(directory):
        if file.endswith('.raw'):
            file_name = file[:-4]  # 去除 .raw 副檔名
            raw_files.append(os.path.join(directory, file_name))
    return raw_files

def find_tiff_files(directory='./'):
    """
    遍歷目錄並找到所有 .tiff 檔案（僅限當前目錄）

    參數:
    - directory: 要搜尋的根目錄路徑

    回傳:
    - tiff_files: 包含所有找到的 .tiff 檔案完整路徑的清單
    """
    tiff_files = []
    for file in os.listdir(directory):
        if file.endswith('.tiff'):
            file_name = file[:-5]  # 去除 .tiff 副檔名
            tiff_files.append(os.path.join(directory, file_name))
    return tiff_files
def polarization(image):
    # 將影像切換為偏振影像
    # ================
    # 偏振排列模式
    # 90  45
    # 135 0
    # ================
    p90 = np.zeros([1024,1224])
    p45 = np.zeros([1024,1224])
    p135 = np.zeros([1024,1224])
    p0 = np.zeros([1024,1224])
    h,w = np.shape(image)
    for i in range(int(w/2)):
        for j in range(int(h/2)):
            p0[j,i]  = image[j*2,i*2]
            p135[j,i]  = image[j*2,i*2+1]
            p45[j,i] = image[j*2+1,i*2]
            p90[j,i]   = image[j*2+1,i*2+1]
    return p90, p45, p135, p0
    
def stokes(p90, p45, p135, p0):    
    s0 = (p0+p90+p45+p135)/4
    s0 = s0/np.max(s0)
    s1 = (p0-p90)/(255)
    s2 = (p45-p135)/(255)

    return s0, s1, s2

def dolp(s0, s1, s2):
    # 計算偏振度
    # DOLP = sqrt(S1^2 + S2^2) / S0
    Dolp = np.sqrt(s1**2 + s2**2) / s0
    return Dolp
def aop(s1, s2):
    # 計算偏振角度
    # AOP = 0.5 * arctan(S2/S1)
    Aop = 0.5 * np.arctan2(s2, s1)
    Aop = np.degrees(Aop)+180  # 將弧度轉換為度
    return Aop
def image_show(name,folder='./'):
    # 顯示影像
    fig, ax = plt.subplots(2,2,figsize=(10,10),dpi=100)

    ax[0,0].imshow(p0,cmap='jet')
    ax[0,0].axis('off')
    ax[0,0].set_title('P0')
    ax[0,1].imshow(p90,cmap='jet')
    ax[0,1].axis('off')
    ax[0,1].set_title('P90')
    ax[1,0].imshow(p45,cmap='jet')
    ax[1,0].axis('off')
    ax[1,0].set_title('P45')
    ax[1,1].imshow(p135,cmap='jet')
    ax[1,1].axis('off')
    ax[1,1].set_title('P135')
    
    polarization_name = os.path.join(folder, f"{name}_polarization.png")
    fig.savefig(polarization_name)
    fig1, ax1 = plt.subplots(1, 3, figsize=(12, 4),dpi=100)

    # 第一張圖
    im0 = ax1[0].imshow(s0, cmap='gray', vmin=0, vmax=1)
    ax1[0].set_title('S0')
    ax1[0].axis('off')
    divider0 = make_axes_locatable(ax1[0])
    cax0 = divider0.append_axes("right", size="5%", pad=0.05)
    fig1.colorbar(im0, cax=cax0)

    # 第二張圖
    im1 = ax1[1].imshow(s1, cmap='jet', vmin=-1, vmax=1)
    ax1[1].set_title('S1')
    ax1[1].axis('off')
    divider1 = make_axes_locatable(ax1[1])
    cax1 = divider1.append_axes("right", size="5%", pad=0.05)
    fig1.colorbar(im1, cax=cax1)

    # 第三張圖
    im2 = ax1[2].imshow(s2, cmap='jet', vmin=-1, vmax=1)
    ax1[2].set_title('S2')
    ax1[2].axis('off')
    divider2 = make_axes_locatable(ax1[2])
    cax2 = divider2.append_axes("right", size="5%", pad=0.05)
    fig1.colorbar(im2, cax=cax2)
    stokes_name = os.path.join(folder, f"{name}_Stokes.png")
    fig1.savefig(stokes_name)
    plt.tight_layout()
    #plt.show()
def image_save(image,name='new_image',cmap='gray',folder='./',vmin=0,vmax=255):
    filename = os.path.join(folder, f"{name}.png")
    fig = plt.figure(figsize=(5,4),dpi=300)
    ax = fig.add_subplot(111)  # 添加子圖
    im = ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.axis('off')  # 隱藏座標軸
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    fig.colorbar(im, cax=cax)
    plt.savefig(filename, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)  # 關閉圖表以節省資源



if __name__ == "__main__":
    #file = input("請輸入檔名:")
    #file_list = find_tiff_files()
    file_list = find_raw_files()
    numer = len(file_list)
    #print("讀取資料夾內所有的*.tiff檔案")
    for file in file_list:
        os.mkdir(file)
        image = read_and_show_raw(f"{file}.raw", width=2448, height=2048)
        #image = read_tiff(f"{file}.tiff", width=1224, height=1024)
        p90, p45, p135, p0 = polarization(image)
        s0, s1, s2 =stokes(p90, p45, p135, p0)
        Dolp = dolp(s0, s1, s2)
        Aop = aop(s1, s2)
        print(f"儲存影像{file_list.index(file)+1}中.....")

        image_save(s0,'S0',cmap='gray',folder=file,vmin=0, vmax=1)
        image_save(s1,'S1_jet',cmap='jet' ,folder=file,vmin=-1.0, vmax=1.0)
        image_save(s1,'S1_gray',cmap='gray' ,folder=file,vmin=-1.0, vmax=1.0)
        image_save(s2,'S2_jet',cmap='jet' ,folder=file,vmin=-1.0, vmax=1.0)
        image_save(s2,'S2_gray',cmap='gray' ,folder=file,vmin=-1.0, vmax=1.0)
        image_save(p0,'P0',cmap='jet' ,folder=file,vmin=0, vmax=255)
        image_save(p90,'P90',cmap='jet' ,folder=file,vmin=0, vmax=255)
        image_save(p45,'P45',cmap='jet' ,folder=file,vmin=0, vmax=255)
        image_save(p135,'P135',cmap='jet' ,folder=file,vmin=0, vmax=255)
        image_save(Dolp,'DOLP',cmap='jet' ,folder=file,vmin=0, vmax=1)
        image_save(Aop,'AOP',cmap='jet' ,folder=file,vmin=0, vmax=180)

        #image_show(file,folder=file)
        
        # 移動檔案或目錄
        shutil.move(f'{file}.raw', f'./{file}')
        print(f"影像{file_list.index(file)+1}處理完成，目前進度{file_list.index(file)+1}/{numer}")
    print("影像處理完成")