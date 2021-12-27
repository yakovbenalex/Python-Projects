# coding: UTF-8
# Test exercise - download mp4 videos from site Toldot.ru
# Download Трактат ЭРУВИН videos
from threading import Thread
import wget
import os.path

# vars for options
goPCtoSleep = False
answer = ""

fname = "avn_dafYomi_eruvin_{0}{1}_mix_HD.mp4"

url = "https://media.toldot.ru/tv/AGRANOVICH_DAF_YOMI/ERUVIN/" + fname

# folderPath = 'D:\\Уроки\\Трактат Эрувин\\'
folderPath = '.'  # current python script folder (you can specify your path)
fileName = folderPath + fname
file = 'avn_dafYomi_eruvin_{0}{1}_mix_HD.mp4'
# for select which videos need to download
filesFromNum = 2
filesToNum = 3

# check files exist
def isFileExist(i, ab, printFileExist):
    curFileName = fileName.format(i, ab)
    if os.path.isfile(curFileName):
        if printFileExist:
            print("File {0} already exist".format(curFileName))
        return True
    else:
        return False

# check files exist too, but without return bool value
def checkFilesExists(start, end):
    absentFilesCount = 0
    print("Next files is absent: ")
    for i in range(start, end):
        if  absentFilesCount > 10:
            print("And other...")
            return
        else:
            curFileName = fileName.format(i, 'a')
            if not os.path.isfile(curFileName):
                print("File {0} not exist".format(curFileName))
                absentFilesCount = absentFilesCount + 1
            curFileName = fileName.format(i, 'b')
            if not os.path.isfile(curFileName):
                print("File {0} not exist".format(curFileName))
                absentFilesCount = absentFilesCount + 1

# main works to download files by specified range
def prescript(start, end, ab):
    for i in range(start, end):
        if not isFileExist(i, ab, False):
            # wget.download(url.format(i, ab), fileName.format(i, ab))
            try:
                print('downloading %s' % file.format(i, ab))
                wget.download(url.format(i, ab), fileName.format(i, ab))

            except Exception:
                print('Error...')

# print files list in directory
def printFilesList():
    files = os.listdir(folderPath)
    for f in files:
        print(f)

# parallel downloading files
def downloadFiles():
    thread1 = Thread(target=prescript, args=(filesFromNum, filesToNum, 'a'))
    thread2 = Thread(target=prescript, args=(filesFromNum, filesToNum, 'b'))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()


def main():
    while(1):
        print("\n1 - download files \n2 - show files list \n0 - exit\nother - check files exists")
        answer = input("enter answer: ")
        print()
        if answer == "1":
            # check if user select option sleep PC after downloading !!! WORK ONLY ON WINDOWS SYSTEMS
            print("Sleep after downloading?\ny - yes, n and other - no")
            answer = input("enter answer: ")
            goPCtoSleep = True if (answer == "y") else False

            downloadFiles()

            if goPCtoSleep:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                # os.system("Rundll32.exe Powrprof.dll,SetSuspendState Sleep")

        if answer == "2":
            printFilesList()
        if answer == "0":
            return
        else:
            checkFilesExists(filesFromNum, filesToNum)

        # prescript(18, 18, 'a')
        # downloadFiles()

        


if __name__ == '__main__':
    main()
