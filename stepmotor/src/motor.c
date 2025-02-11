#include <bcm2835.h>
#include <stdio.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdlib.h>
#include <getopt.h>

// 定義步進馬達的 GPIO 腳位
#define IN1 RPI_BPLUS_GPIO_J8_31 // BCM GPIO 6
#define IN2 RPI_BPLUS_GPIO_J8_33 // BCM GPIO 13
#define IN3 RPI_BPLUS_GPIO_J8_35 // BCM GPIO 19
#define IN4 RPI_BPLUS_GPIO_J8_37 // BCM GPIO 26

// 定義步進馬達的步進順序 (二相激磁)
int stepSequence[4][4] = {
    {1, 1, 0, 0}, // IN1, IN2, IN3, IN4
    {0, 1, 1, 0},
    {0, 0, 1, 1},
    {1, 0, 0, 1}
};

// 初始化 GPIO 腳位
void setup() {
    if (!bcm2835_init()) {
        printf("BCM2835 初始化失敗！\n");
        exit(1);
    }

    // 設置 GPIO 腳位為輸出模式
    bcm2835_gpio_fsel(IN1, BCM2835_GPIO_FSEL_OUTP);
    bcm2835_gpio_fsel(IN2, BCM2835_GPIO_FSEL_OUTP);
    bcm2835_gpio_fsel(IN3, BCM2835_GPIO_FSEL_OUTP);
    bcm2835_gpio_fsel(IN4, BCM2835_GPIO_FSEL_OUTP);

    // 將所有腳位初始化為低電位
    bcm2835_gpio_write(IN1, LOW);
    bcm2835_gpio_write(IN2, LOW);
    bcm2835_gpio_write(IN3, LOW);
    bcm2835_gpio_write(IN4, LOW);
}

// 執行步進馬達的單一步進
void stepMotor(int step) {
    bcm2835_gpio_write(IN1, stepSequence[step][0]);
    bcm2835_gpio_write(IN2, stepSequence[step][1]);
    bcm2835_gpio_write(IN3, stepSequence[step][2]);
    bcm2835_gpio_write(IN4, stepSequence[step][3]);
}

// 控制馬達旋轉
void rotateMotor(bool direction, int steps, int pps) {
    int delay = 1000000 / pps;  // 計算延遲，單位為微秒

    if (direction) {
        for (int i = 0; i < steps; i++) {
            for (int step = 0; step < 4; step++) {
                stepMotor(step);
                bcm2835_delayMicroseconds(delay);
            }
        }
    } else {
        for (int i = 0; i < steps; i++) {
            for (int step = 3; step >= 0; step--) {
                stepMotor(step);
                bcm2835_delayMicroseconds(delay);
            }
        }
    }
}

// 主函式
int main(int argc, char *argv[]) {
    // 預設值
    bool direction = true; // 順時針：1，逆時針：0
    int steps = 512;       // 預設步數
    int pps = 100;         // 每秒步數 (pulse per second)

    // 命令列參數解析
    int opt;
    while ((opt = getopt(argc, argv, "d:s:p:")) != -1) {
        switch (opt) {
            case 'd': // 方向
                direction = atoi(optarg);
                break;
            case 's': // 步數
                steps = atoi(optarg);
                break;
            case 'p': // 每秒步數
                pps = atoi(optarg);
                break;
            default: // 不明參數
                fprintf(stderr, "Usage: %s -d [0|1] -s steps -p pps\n", argv[0]);
                return 1;
        }
    }

    // 確認參數輸入
    printf("步進馬達控制開始！\n");
    printf("方向：%s\n", direction ? "順時針" : "逆時針");
    printf("步數：%d\n", steps);
    printf("速度：%d PPS\n", pps);

    setup();

    // 旋轉馬達
    rotateMotor(direction, steps, pps);

    // 停止後清除腳位
    printf("旋轉結束！\n");
    bcm2835_gpio_write(IN1, LOW);
    bcm2835_gpio_write(IN2, LOW);
    bcm2835_gpio_write(IN3, LOW);
    bcm2835_gpio_write(IN4, LOW);

    bcm2835_close();
    return 0;
}
