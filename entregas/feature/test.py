from so import *
if __name__ == '__main__':
    # ptList = []
    # mem = MemoryManager(64, 4)
    # ptList.append(PageTable(0, mem.allocFrames(4)))
    # ptList.append(PageTable(1, mem.allocFrames(4)))
    # mem.putPageTable(94, ptList)
    #
    # pt2 = mem.removePageTable(94)
    list = [0, 1, 2, 3]
    match = next((x for x in list if x == 4), list.pop(0))
    print(match)
