import cv2
import PySpin
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time

class Camera(object):
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        if self.cam_list.GetSize() == 0:
            print("未找到相機。")
            self.system.ReleaseInstance()
            self.cam = None
            exit()
            return
        self.cam = self.cam_list[0]  # 使用第一台相機
        try:
            self.cam.Init()
        except PySpin.SpinnakerException as ex:
            print(f"初始化相機錯誤: {ex}")
            self.cam = None

        self.number_of_images = 1

    def set_polarized8_format(self):
        if self.cam is None:
            return
        try:
            node_pixel_format = PySpin.CEnumerationPtr(self.cam.GetNodeMap().GetNode("PixelFormat"))
            if not PySpin.IsAvailable(node_pixel_format) or not PySpin.IsWritable(node_pixel_format):
                print("PixelFormat 節點不可用或不可寫入。")
                return
            polarized8_entry = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName("Polarized8"))
            if not PySpin.IsAvailable(polarized8_entry) or not PySpin.IsReadable(polarized8_entry):
                print("Polarized8 格式不可讀取。")
                return
            node_pixel_format.SetIntValue(polarized8_entry.GetValue())
            print("像素格式已設置為 Polarized8。")
        except PySpin.SpinnakerException as ex:
            print(f"設定像素格式錯誤: {ex}")
    def open_camera(self):
        if self.cam is None:
            return
        try:
            self.cam.BeginAcquisition()
            print("開始擷取畫面。")
        except PySpin.SpinnakerException as ex:
            print(f"開始 Acquisition 錯誤: {ex}")

    def close_camera(self):
        if self.cam is None:
            return
        try:
            self.cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
            print(f"結束 Acquisition 錯誤: {ex}")
        try:
            self.cam.DeInit()
        except PySpin.SpinnakerException as ex:
            print(f"DeInit 錯誤: {ex}")
        print("關閉相機。")
        del self.cam
        self.cam_list.Clear()
        del self.cam_list
        try:
            self.system.ReleaseInstance()
        except PySpin.SpinnakerException as ex:
            print(f"釋放系統實例錯誤: {ex}")

    def preview(self, image_result):
        r"""
        使用 PySpin 提取四個偏振角度的影像，拼接並縮放後返回。
        """
        choice = 0  # 0: Single, 1: Quadrant
        previewI0   = PySpin.ImageUtilityPolarization.ExtractPolarQuadrant(image_result, PySpin.SPINNAKER_POLARIZATION_QUADRANT_I0)
        self.i0 = previewI0.GetNDArray()
        if choice == 1:
            
            previewI45  = PySpin.ImageUtilityPolarization.ExtractPolarQuadrant(image_result, PySpin.SPINNAKER_POLARIZATION_QUADRANT_I45)
            previewI90  = PySpin.ImageUtilityPolarization.ExtractPolarQuadrant(image_result, PySpin.SPINNAKER_POLARIZATION_QUADRANT_I90)
            previewI135 = PySpin.ImageUtilityPolarization.ExtractPolarQuadrant(image_result, PySpin.SPINNAKER_POLARIZATION_QUADRANT_I135)
            
            self.i45 = previewI45.GetNDArray()
            self.i90 = previewI90.GetNDArray()
            self.i135 = previewI135.GetNDArray()
            row1 = np.hstack((self.i0, self.i90))
            row2 = np.hstack((self.i45, self.i135))
            combined = np.vstack((row1, row2))
            resized = cv2.resize(combined, (612, 512))
        elif choice ==  0:
            resized = cv2.resize(self.i0, (612, 512))
        
        return resized

    def stocks_preview(self,image_result):
        previewS0 = PySpin.ImageUtilityPolarization_CreateStokesS0(image_result)
        previewS1 = PySpin.ImageUtilityPolarization_CreateStokesS1(image_result)
        previewS2 = PySpin.ImageUtilityPolarization_CreateStokesS2(image_result)
        width = previewS0.GetWidth()
        height = previewS0.GetHeight()
        self.s0 = np.frombuffer(previewS0.GetData(), dtype=np.int16).reshape((height,width))
        self.s1 = np.frombuffer(previewS1.GetData(), dtype=np.int16).reshape((height,width))
        self.s2 = np.frombuffer(previewS2.GetData(), dtype=np.int16).reshape((height,width))
        self.normalized_s0 = cv2.normalize(self.s0, None, 0, 255, cv2.NORM_MINMAX).astype(np.float16)
        self.normalized_s1 = cv2.normalize(self.s1, None, -1, 1, cv2.NORM_MINMAX).astype(np.float16)
        self.normalized_s2 = cv2.normalize(self.s2, None, -1, 1, cv2.NORM_MINMAX).astype(np.float16)
        stokes = np.hstack((self.s0, self.s1, self.s2))
        stokes_resized = cv2.resize(stokes, (918 , 256))
        normalized = cv2.normalize(stokes_resized, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        # 套用 JET colormap
        jet_colormap = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        return jet_colormap


    def http_frames(self):
        if self.cam is None:
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera not initialized\r\n'
            return
        print("Image streaming started")
        while True:
            try:
                image_result = self.cam.GetNextImage(1000)
            except PySpin.SpinnakerException as ex:
                if hasattr(ex, 'errorCode') and ex.errorCode == -1014:
                    print(f"Error: {ex}, attempting to restart Acquisition")
                    try:
                        self.cam.EndAcquisition()
                    except Exception as e:
                        print("EndAcquisition failed:", e)
                    try:
                        self.cam.BeginAcquisition()
                        print("Restarting Acquisition successful")
                    except Exception as e:
                        print("Restarting Acquisition failed:", e)
                        time.sleep(0.5)
                    continue
                else:
                    print(f"Other error: {ex}")
                    time.sleep(0.1)
                    continue

            if image_result.IsIncomplete():
                print("Image capture incomplete")
                image_result.Release()
                continue

            frame = self.preview(image_result)
            image_result.Release()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("JPEG conversion failed")
                continue
            jpg_frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg_frame + b'\r\n')

    def save(self, colorfilter):
        # 實作儲存影像的邏輯
        print("儲存影像功能被呼叫。")
        self.raw.Save(f"./Picture/{colorfilter}_raw_image_{self.number_of_images}.tiff")  # 儲存原始 Polarized8 影像
        self.number_of_images += 1
        """
        cv2.imwrite(f"./Picture/{colorfilter}_i0_image.png", self.i0)  # 存成 PNG
        
        cv2.imwrite(f"./Picture/{colorfilter}_i90_image.png", self.i90)  # 存成 PNG
        cv2.imwrite(f"./Picture/{colorfilter}_i45_image.png", self.i45)  # 存成 PNG
        cv2.imwrite(f"./Picture/{colorfilter}_i135_image.png", self.i135)  # 存成 PNG
        np.save(f"./Picture/{colorfilter}S0.npy", self.normalized_s0)
        np.save(f"./Picture/{colorfilter}S1.npy", self.normalized_s1)
        np.save(f"./Picture/{colorfilter}S2.npy", self.normalized_s2)
        """
        


# 若在測試環境（有螢幕的電腦）可使用下面程式來測試相機
if __name__ == '__main__':

    cam = Camera()

    cam.set_polarized8_format()
    cam.open_camera()
    while True:
        try:
            image_result = cam.cam.GetNextImage(1000)
        except PySpin.SpinnakerException as ex:
            print("取得影像錯誤:", ex)
            continue
        if image_result.IsIncomplete():
            image_result.Release()
            continue
        frame = cam.preview(image_result)
        stock = cam.stocks_preview(image_result)
        image_result.Release()


        cv2.imshow("Camera Preview", frame)
        cv2.imshow("Stokes Preview", stock)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('s'):
            cam.save(f"{input('請輸入檔名：')}")

    cam.close_camera()
    cv2.destroyAllWindows()
