from hardware import *
from so import *
import log
from time import sleep

##
##  MAIN 
##
if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(30)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    prg1 = Program("prg1.exe", [ASM.CPU(3), ASM.IO(), ASM.CPU(3)])
    prg2 = Program("prg2.exe", [ASM.CPU(8)])
    prg3 = Program("prg3.exe", [ASM.CPU(10)])

    # execute all programs "concurrently"1
    kernel.run(prg1, 3)
    sleep(1)
    kernel.run(prg2, 3)
    sleep(2)
    kernel.run(prg3, 3)



