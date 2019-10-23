#!/usr/bin/env python

from hardware import *
import log
from entities.enums.ProcessStates import *


## emulates a compiled program
class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            # print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)


## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info(" Program Finished ")
        # pbc_Finished = no es necesario crear un variable para finish
        self.kernel.pcbTable.changeStateRunningPcb(ProcessStates.TERMINATED)  # le cambia el estado  al proceso  como
        self.kernel.dispatcher.save(self.kernel.pcbTable.runningPcb)  # el proceso running se quita de cpu y se guarda
        self.kernel.pcbTable.setOffPcbRunning()  # se quita el proceso que se mato del running pcbTable

        if self.kernel.readyQueue.queue:  # hay pcb en ready?
            nextPcb = self.kernel.readyQueue.getProgramByFifo()  # busco siguiente programa por FIFO
            self.kernel.dispatcher.load(nextPcb)  # carga el pcb en mmu y setea el pc en cpu
            self.kernel.pcbTable.setOnPcbRunning(nextPcb)  #


class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        newPCB = Pcb(irq.parameters.name,
                     ProcessStates.NEW,
                     self.kernel.pcbTable.getNewPid(),
                     self.kernel.loader.load(irq.parameters))  # se crea un nuevo process control block (PCB)

        self.kernel.pcbTable.add(newPCB)  # se agrega PCB a la tabla

        if self.kernel.pcbTable.runningPcb:  # pregunta si hay algún pcb ejecutandose
            newPCB.changeState(ProcessStates.READY)  # cambio proceso a estado ready
            self.kernel.readyQueue.addQueue(newPCB)  # agrego pcb a la cola reaedy
        else:
            self.kernel.pcbTable.setOnPcbRunning(newPCB)  # actualiza estado a running
            self.kernel.dispatcher.load(newPCB)  # carga el programa en mmu y setea el pc


class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcb = self.kernel.pcbTable.runningPcb
        self.kernel.pcbTable.changeStateRunningPcb(ProcessStates.WAITING)
        self.kernel.dispatcher.save(self.kernel.pcbTable.runningPcb)  # lo manda al save del dispatcher. Cpu idle
        self.kernel.pcbTable.setOffPcbRunning()
        self.kernel.ioDeviceController.runOperation(pcb, operation)
        log.logger.info(self.kernel.ioDeviceController)

        if self.kernel.readyQueue.queue:
            nextPcb = self.kernel.readyQueue.getProgramByFifo()  # busco siguiente programa por FIFO
            self.kernel.dispatcher.load(nextPcb)  # carga el pcb en mmu y setea el pc en cpu
            self.kernel.pcbTable.setOnPcbRunning(nextPcb)


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        log.logger.info(self.kernel.ioDeviceController)

        if self.kernel.pcbTable.runningPcb:
            self.kernel.pcbTable.changeStateRunningPcb(ProcessStates.READY)  # cambio estado de pcb running
            self.kernel.dispatcher.save(self.kernel.pcbTable.runningPcb)  # actualiza pc, actualiza en pcbTable y  idle
            self.kernel.readyQueue.addQueue(self.kernel.pcbTable.runningPcb)  # corro el pcb running a queue ready
            self.kernel.pcbTable.setOffPcbRunning()  # quito el pcb running de ejecucion

        self.kernel.pcbTable.setOnPcbRunning(pcb)
        self.kernel.dispatcher.load(pcb)  # dispatcher carga programa y se sigue ejecutando de donde quedo,
        # cuando se llamo el evento de interruption handler IO IN


# Pcb
class Pcb:

    def __init__(self, path, state, pid, basedir):
        self._path = path
        self._state = state
        self._pid = pid
        self._baseDir = basedir
        self._pc = 0

    @property
    def state(self):
        return self._state

    @property
    def pc(self):
        return self._pc

    @property
    def pid(self):
        return self._pid

    @property
    def path(self):
        return self._path

    @property
    def baseDir(self):
        return self._baseDir

    def changeState(self, state):
        self._state = state

    def updatePC(self, pc):
        self._pc = pc


# Pcb Table
class PcbTable:

    def __init__(self):
        self._pcbs = []
        self._runningPcb = None

    @property
    def pcbs(self):
        return self._pcbs

    @property
    def runningPcb(self):
        return self._runningPcb

    def add(self, pcb):
        self._pcbs.append(pcb)

    def getNewPid(self):
        return self.maxPid() + 1

    def maxPid(self):
        return max(pcb.pid for pcb in self.pcbs) if self.pcbs else 0

    def setOffPcbRunning(self):
        self._runningPcb = None

    def setOnPcbRunning(self, pcb):
        pcb.changeState(ProcessStates.RUNNING)
        self._runningPcb = pcb

    def changeStateRunningPcb(self, state):
        self.runningPcb._state = state

    def updatePcb(self, pcbtoupdate):
        for idx, item in enumerate(self.pcbs):
            if pcbtoupdate.pid == item.pid:
                self._pcbs[idx] = pcbtoupdate
                break


class Loader:

    def __init__(self):
        self._dirNextInstruction = 0

    @property
    def dirNextInstruction(self):
        return self._dirNextInstruction

    def load(self, program):
        baseDir: int = self.dirNextInstruction
        # loads the program in main memory
        for inst in program.instructions:
            HARDWARE.memory.put(self.dirNextInstruction, inst)
            self._dirNextInstruction += 1

        return baseDir


class Dispatcher:

    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return _kernel

    @staticmethod
    def load(pcb):
        HARDWARE.mmu._baseDir = pcb.baseDir
        HARDWARE.cpu._pc = pcb.pc

    def save(self, pcb):
        pcb.updatePC(HARDWARE.cpu.pc)
        self._kernel.pcbTable.updatePcb(pcb)
        HARDWARE.cpu._pc = -1


class ReadyQueue:
    def __init__(self, kernel):
        self._kernel = kernel
        self._queue = []

    @property
    def kernel(self):
        return _kernel

    @property
    def queue(self):
        return self._queue

    def addQueue(self, pcb):
        pcb.changeState(ProcessStates.READY)
        self._queue.append(pcb)

    def getProgramByFifo(self):
        return self.queue.pop(0)


class Kernel():

    def __init__(self):
        # setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        # controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

        # controls for load program in memory
        self._loader = Loader()
        self._readyQueue = ReadyQueue(self)
        self._pcbTable = PcbTable()
        self._dispatcher = Dispatcher(self)

    @property
    def readyQueue(self):
        return self._readyQueue

    @property
    def pcbTable(self):
        return self._pcbTable

    @property
    def loader(self):
        return self._loader

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    # emulates a "system call" for programs execution
    @staticmethod
    def run(program):
        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, program)
        HARDWARE.interruptVector.handle(newIRQ)

    def __repr__(self):
        return "Kernel "
