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
    HARDWARE.setup(8)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    prg1 = Program("prg1.exe", [ASM.CPU(3), ASM.SAVE(1), ASM.CPU(4)])
    prg2 = Program("prg2.exe", [ASM.CPU(8)])
    prg3 = Program("prg3.exe", [ASM.CPU(8)])

    kernel.fileSystem.write("c:/prg1.exe", prg1)
    kernel.fileSystem.write("c:/prg2.exe", prg2)
    kernel.fileSystem.write("c:/prg3.exe", prg3)

    # execute all programs "concurrently"
    kernel.run("c:/prg1.exe", 3)
    # sleep(1)
    kernel.run("c:/prg2.exe", 3)
    # sleep(2)
    kernel.run("c:/prg3.exe", 3)
