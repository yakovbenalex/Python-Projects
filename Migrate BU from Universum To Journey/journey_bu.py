# Created by Yakov Opalev 06.09.2021
# migrate BU from Universum app to Journey BU format
# Google play app links:
# https://play.google.com/store/apps/details?id=ru.schustovd.diary
# https://play.google.com/store/apps/details?id=com.journey.app
import json
import os
import shutil
import time
from os import path
from exif import Image

# CONSTANTS
JSON_FILE_UNIVERSUM_BU = "data.json"
JSON_FILE_DEFAULT = "json_default.json" # default empty json mark, further it will be filled with data

# ---
OUTPUT_FOLDER = "output"
# ---
# Universum fields to Journey fields
KEY_ID = ["id", "id"]  # mark id
KEY_COMMENT = ["comment", "text"]  # comment text
KEY_DATE = ["date", None]  # created in string format ('%Y-%m-%d')
KEY_TIME = ["time", None]  # created in string format ('%H:%M:%S')
KEY_CREATED = ["created", "date_journal"]  # created in number of milliseconds
KEY_CHANGED = ["changed", "date_modified"]  # changed in number of milliseconds
KEY_TIMEZONE = [None, "timezone"]  # timezone
KEY_PHOTO = ["photo", "photos"]  # photo file name
KEY_GRADE = ["grade", "sentiment"]  # grade of mood (1 to 5, sadness to happiness)
KEY_SHAPE = ["shape", "tags"]  # for adding tag
KEY_GPS_LAT = [None, "lat"]  # gps data latitude
KEY_GPS_LON = [None, "lon"]  # gps data longitude
KEY_PREVIEW_TEXT = [None, "preview_text"]
KEY_FAVOURITE = [None, "favourite"]
KEY_MONEY = ["money", None]

SENTIMENT_DEF_VAL = 0

PROGRESS_MARKS_STEP_PRINT = 100  # for limit line length in printed progress


# universum grade to journey sentiment (1 to 5, sadness to happiness)
def getSentimentByGrade(x):
    return {
        1: 0.25,
        4: 0.75,
        2: 1.00,
        5: 1.25,
        3: 1.75
    }.get(x, SENTIMENT_DEF_VAL)  # 0 is default if x not found


# universum grade to journey sentiment (1 to 5, sadness to happiness)
# You can specify your own tags to shapes
def getTagByShape(x):
    return {
        "TRIANGLE_UP": "взлет",
        "TRIANGLE_DOWN": "падение",
        "TRIANGLE_RIGHT": "",
        "TRIANGLE_LEFT,": "",
        "OCTAGON": "приобритение",
        "PENTAGON": "необычное",
        "RHOMBUS": "важное",
        "SQUARE": "встреча",
        "STAR": "значимое"
    }.get(x, "")  # null is default if x not found


# convert gps format
def dms2dd(gps, direction):  # 'gps' is tuple of degree minutes and seconds
    # deg, minutes, seconds, direction = gps[0], gps[1], gps[2], img.gps_latitude_ref
    return (float(gps[0]) + float(gps[1]) / 60 + float(gps[2]) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)


def getTimeInSeconds(dateTimeStr):
    return int(time.mktime(time.strptime(dateTimeStr, '%Y-%m-%d %H:%M:%S')))


def getTimeInSecondsOnlyDate(dateStr):
    return int(time.mktime(time.strptime(dateStr, '%Y-%m-%d')))


def printProgress(cur, count):
    print(str(cur) + " / " + str(count))


# main work ------------------------------------------------------------
# open default json format from bu journey
with open(JSON_FILE_DEFAULT, encoding='utf-8') as jsonFileDefault:
    jsonDefault = json.load(jsonFileDefault)
    jsonFileDefault.close()

# open json file from bu universum
with open(JSON_FILE_UNIVERSUM_BU, encoding='utf-8') as jsonFileUniversum:
    jsonUniversum = json.load(jsonFileUniversum)
    jsonFileUniversum.close()

# create output folder for new json files if not exists
if not path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# bu transfer work --------------------------------------------------
# get default json bu journey values
json_tmp = jsonDefault.copy()

recordsCount = len(jsonUniversum['marks'])
curMark = 1

# get first timestamp -------
# convert date and time to Unix format
dtStr = jsonUniversum['marks'][0][KEY_DATE[0]] + " " + jsonUniversum['marks'][0][KEY_TIME[0]]
dStr = jsonUniversum['marks'][0][KEY_DATE[0]]
# get timestamp in seconds count
lastTimestamp = getTimeInSeconds(dtStr)
lastTimestampDate = getTimeInSecondsOnlyDate(dStr)

univId = jsonUniversum['marks'][0][KEY_ID[0]]
universumMarkId = str(lastTimestamp * 1000) + "-" + univId[0:8] + univId[9:13] + univId[14:18]
# add id to mark
json_tmp[KEY_ID[1]] = universumMarkId

# vars init
joinMark = True
joinShapeOrGrade = False
photoCountInMark = 0
marksCount = 0
photoMarksCount = 0
commentMarksCount = 0

# pass marks from bu universum from json file -----
for item in jsonUniversum['marks']:
    # convert date and time to Unix format
    dtStr = item[KEY_DATE[0]] + " " + item[KEY_TIME[0]]
    dStr = item[KEY_DATE[0]]
    # get timestamp in seconds count
    uTime = getTimeInSeconds(dtStr)
    uTimeDate = getTimeInSecondsOnlyDate(dStr)

    # check if mark need to join to current BU item 
    if uTime == lastTimestamp and photoCountInMark < 10:
        joinMark = True
        joinShapeOrGrade = False
    else:
        if (KEY_SHAPE[0] in item
            or KEY_GRADE[0] in item
            or (not json_tmp[KEY_PHOTO[1]] and not json_tmp[KEY_COMMENT[1]])) \
                and uTimeDate == lastTimestampDate:
            joinMark = True
            joinShapeOrGrade = False
        else:
            joinMark = False
            lastTimestampDate = uTimeDate
        lastTimestamp = uTime

    if not joinMark:
        # save new json (each mark) to file
        with open(OUTPUT_FOLDER + "\\" + json_tmp[KEY_ID[1]] + ".json", "w", encoding='utf-8') as write_file:
            json.dump(json_tmp, write_file, ensure_ascii=False)

        # statistics
        marksCount += 1
        if json_tmp[KEY_PHOTO[1]]:
            photoMarksCount += 1
        else:
            commentMarksCount += 1

            # CHECK EMPTY MARK
        if (json_tmp[KEY_FAVOURITE[1]] or json_tmp[KEY_SHAPE[1]]) \
                and (not json_tmp[KEY_PHOTO[1]] and json_tmp[KEY_COMMENT[1]] == ""):
            print(item[KEY_DATE[0]], " ", item[KEY_TIME[0]])

        # get default json bu journey values
        json_tmp = jsonDefault.copy()
        json_tmp[KEY_PHOTO[1]] = list()
        json_tmp[KEY_SHAPE[1]] = list()
        json_tmp[KEY_GRADE[1]] = 0

        # get and save new mark id
        univId = item[KEY_ID[0]]
        universumMarkId = str(uTime * 1000) + "-" + univId[0:8] + univId[9:13] + univId[14:18]
        # add id to mark
        json_tmp[KEY_ID[1]] = universumMarkId

        photoCountInMark = 0
        joinMark = False
        joinShapeOrGrade = False

    # if record has grade or shape field, then write this field and get next mark
    if KEY_SHAPE[0] in item or KEY_GRADE[0] in item:
        if KEY_SHAPE[0] in item:
            if item[KEY_SHAPE[0]] == "STAR":
                json_tmp[KEY_FAVOURITE[1]] = True
            else:
                markTag = getTagByShape(item[KEY_SHAPE[0]])
                json_tmp[KEY_SHAPE[1]].append(markTag)
        else:  # if KEY_GRADE[0] in item:
            json_tmp[KEY_GRADE[1]] = getSentimentByGrade(item[KEY_GRADE[0]])

        joinShapeOrGrade = True

        if curMark % PROGRESS_MARKS_STEP_PRINT == 0:
            printProgress(curMark, recordsCount)
        elif curMark == recordsCount:
            printProgress(curMark, recordsCount)
        curMark += 1
        continue

    # this section need to change specific timezone by timestamp in seconds from 1970 (create your own conditions) 
    # change timezone if mark made in engels (2021 summer) (2021 winter) (2020 summer) (2019 summer) (2018 summer)
    # (7/4/2021 to 10/10/2021) or (1/5/2021 to 2/4/2021) or (6/23/2020 to 8/27/2020) or (7/23/2019 to 8/25/2019) or
    # (7/27/2018 to 8/27/2018)
    if (1625401800 < uTime < 1633860000) or (1609849200 < uTime < 1612440000) or (1592928000 < uTime < 1598516400) or \
            (1563898800 < uTime < 1566750000) or (1532694000 < uTime < 1535371200):
        # change timezone
        json_tmp[KEY_TIMEZONE[1]] = "Europe/Samara"
    # fly to the Tyumen GMT +5
    elif 1527750000 < uTime < 1528138800:
        # change timezone
        json_tmp[KEY_TIMEZONE[1]] = "Asia/Yekaterinburg"
        uTime -= 3600
    else:
        # change timezone
        json_tmp[KEY_TIMEZONE[1]] = "Europe/Moscow"
        uTime += 3600


    # save date and time in unix format in milliseconds
    uTime *= 1000
    json_tmp[KEY_CREATED[1]] = uTime
    json_tmp[KEY_CHANGED[1]] = uTime

    # create mark id for save it 
    univId = item[KEY_ID[0]]
    universumMarkId = str(uTime) + "-" + univId[0:8] + univId[9:13] + univId[14:18]
    # add id to mark
    json_tmp[KEY_ID[1]] = universumMarkId

    # add text to mark if it exists
    if KEY_COMMENT[0] in item:
        # add text to mark
        if len(item[KEY_COMMENT[0]]) > 0:
            if uTime == lastTimestamp * 1000:
                # "<p dir=\"auto\">" It needed to use html format to save mark text (journet bu format)
                json_tmp[KEY_COMMENT[1]] = json_tmp[KEY_COMMENT[1]] + "\n" + "<p dir=\"auto\">" \
                                           + item[KEY_COMMENT[0]] + "</p> "
                # cut preview text if it length more than 384
                iCmnt = item[KEY_COMMENT[0]]
                jsPrev = json_tmp[KEY_PREVIEW_TEXT[1]]
                if len(iCmnt) + len(jsPrev) < 383:
                    json_tmp[KEY_PREVIEW_TEXT[1]] = jsPrev + "<p dir=\"auto\">" \
                                                    + iCmnt + "</p>"
                else:
                    json_tmp[KEY_PREVIEW_TEXT[1]] = jsPrev + "<p dir=\"auto\">" \
                                                    + iCmnt[0:382 - len(jsPrev)] + ".." + "</p>"
            else:
                json_tmp[KEY_COMMENT[1]] = "<p dir=\"auto\">" + item[KEY_COMMENT[0]] + "</p>"
                # cut preview text if it length more than 384
                if len(item[KEY_COMMENT[0]]) < 383:
                    json_tmp[KEY_PREVIEW_TEXT[1]] = "<p dir=\"auto\">" + item[KEY_COMMENT[0]] + "</p>"
                else:
                    json_tmp[KEY_PREVIEW_TEXT[1]] = "<p dir=\"auto\">" + item[KEY_COMMENT[0]][0:382] + ".." + "</p>"

    # if record has photo
    if KEY_PHOTO[0] in item:
        iPhoto = item[KEY_PHOTO[0]]

        # new photo name
        phName = universumMarkId + "-"
        phId = iPhoto[6:] if len(iPhoto) - 6 < 16 else iPhoto[6:14] + iPhoto[15:19] + iPhoto[20:24]
        phName += str(phId)
        phName += ".jpg"
        try:
            # # rename image file
            # os.rename(item[KEY_PHOTO[0]], OUTPUT_FOLDER + "\\" + phName)
            # copy file for TEST
            shutil.copy2(item[KEY_PHOTO[0]], OUTPUT_FOLDER + "\\" + phName)
            # json_tmp[KEY_PHOTO[1]] = [phName]
            json_tmp[KEY_PHOTO[1]].append(phName)
            photoCountInMark += 1

            # get gps data
            # get image object
            with open(OUTPUT_FOLDER + "\\" + phName, "rb") as src:
                img = Image(src)

            # for check available gps properties in image
            gpsKeys = ["gps_latitude", "gps_latitude_ref", "gps_longitude", "gps_longitude_ref"]
            hasGpsTag = True
            # check all needed gps properties
            for key in gpsKeys:
                if not (key in img.list_all()):
                    hasGpsTag = False

            # if image file has gps tag:
            if hasGpsTag:
                if json_tmp[KEY_GPS_LAT[1]] == 1.7976931348623157e308 or \
                        json_tmp[KEY_GPS_LON[1]] == 1.7976931348623157e308:
                    gpsDDLat = dms2dd(img.gps_latitude, img.gps_latitude_ref)
                    gpsDDLon = dms2dd(img.gps_longitude, img.gps_longitude_ref)
                    # if gps data not zero
                    if gpsDDLat != 0.0 and gpsDDLon != 0.0:
                        json_tmp[KEY_GPS_LAT[1]] = gpsDDLat
                        json_tmp[KEY_GPS_LON[1]] = gpsDDLon

        except FileNotFoundError:
            print("FileNotFound in " + str(curMark) + " mark")

    # if record has money field
    if KEY_MONEY[0] in item:
        if item[KEY_MONEY[0]] > 0:
            json_tmp[KEY_COMMENT[1]] = json_tmp[KEY_COMMENT[1]] + "\n" + "<p dir=\"auto\">Доход: " + str(
                item[KEY_MONEY[0]]) + "</p>"
            json_tmp[KEY_SHAPE[1]].append("доход")
        else:
            json_tmp[KEY_COMMENT[1]] = json_tmp[KEY_COMMENT[1]] + "\n" + "<p dir=\"auto\">Расход: " + str(
                item[KEY_MONEY[0]]) + "</p>"
            json_tmp[KEY_SHAPE[1]].append("расход")

    if curMark % PROGRESS_MARKS_STEP_PRINT == 0:
        printProgress(curMark, recordsCount)
    elif curMark == recordsCount:
        printProgress(curMark, recordsCount)
    curMark += 1

# save last mark json to file
with open(OUTPUT_FOLDER + "\\" + json_tmp[KEY_ID[1]] + ".json", "w", encoding='utf-8') as write_file:
    json.dump(json_tmp, write_file, ensure_ascii=False)

# statistics for last records
marksCount += 1
if json_tmp[KEY_PHOTO[1]]:
    photoMarksCount += 1
else:
    commentMarksCount += 1

print()
print(str(commentMarksCount) + " comment marks.")
print(str(photoMarksCount) + " photo marks.")
print(str(marksCount) + " marks total.")
print()
print("Work is done!")
