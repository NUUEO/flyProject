cmake_minimum_required(VERSION 3.10)
project(StepperMotorControl C)
set(CMAKE_C_COMPILER /usr/bin/aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER /usr/bin/aarch64-linux-gnu-g++)
set(CMAKE_C_STANDARD 11)

# 設定 include 路徑
include_directories(${CMAKE_SOURCE_DIR}/include)

# 設定靜態庫的目錄位置
set(BCM2835_LIB ${CMAKE_SOURCE_DIR}/lib/libbcm2835.a)

# 設定來源檔案
set(SOURCE_DIR ${CMAKE_SOURCE_DIR}/src)
set(SOURCES ${SOURCE_DIR}/motor.c)

# 設定執行檔案輸出目錄
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

# 建立執行檔並連結函式庫
add_executable(motor ${SOURCES})
target_link_libraries(motor ${BCM2835_LIB})
