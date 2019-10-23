from hardware import *
from so import *
import log


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

    ##  create a program
    prg = Program("test.exe", [ASM.CPU(2), ASM.IO(), ASM.CPU(1), ASM.IO(), ASM.CPU(3)])
    prg2 = Program("tiesto.exe", [ASM.CPU(7)])
    prg3 = Program("mozila.exe", [ASM.CPU(3), ASM.IO(), ASM.CPU(2), ASM.IO(), ASM.CPU(2)])
    # execute the program
    kernel.run(prg)
    kernel.run(prg2)
    kernel.run(prg3)



