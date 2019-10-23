from so import *
if __name__ == '__main__':
    ptList = []
    mem = MemoryManager(64, 4)
    ptList.append(PageTable(0, mem.allocFrames(4)))
    ptList.append(PageTable(1, mem.allocFrames(4)))
    mem.putPageTable(94, ptList)

    pt2 = mem.removePageTable(94)
    print()
