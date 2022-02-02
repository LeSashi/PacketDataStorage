import json
import cv2 as cv
import math
import numpy as np
import os


def getVideoLocation(videoName):
    return "Videos/" + videoName

def rescaleFrame(frame, scale):

    width = int(frame.shape[1]* scale)
    height = int(frame.shape[0] * scale)

    return cv.resize(frame, (width,height), interpolation = cv.INTER_AREA)


def encode(filmName,videoName,resolutionMulti,fpsMulti,packetSize):

    videoLocation = getVideoLocation(videoName)

    videoCapture = cv.VideoCapture(videoLocation)

    if not videoCapture.isOpened():
        print("Error opening video")
        return False

    fpsMultiReciprocal = math.ceil(1/fpsMulti)

    realWidth  = videoCapture.get(cv.CAP_PROP_FRAME_WIDTH)
    scaledWidth = math.floor(realWidth*resolutionMulti)

    realHeight = videoCapture.get(cv.CAP_PROP_FRAME_HEIGHT)
    scaledHeight = math.floor(realHeight*resolutionMulti)

    realFPS = round(videoCapture.get(cv.CAP_PROP_FPS),3)
    scaledFPS = round(realFPS*fpsMulti,3)

    totalFrames = int(videoCapture.get(cv.CAP_PROP_FRAME_COUNT))
    scaledFrames = math.ceil(totalFrames / fpsMultiReciprocal)

    print(f"""
    Total Frames: {str(totalFrames)}
    Scaled Frames: {str(scaledFrames)}

    Real Width: {str(realWidth)}
    Scaled Width: {str(scaledWidth)}

    Real Height: {str(realHeight)}
    Scaled Height: {str(scaledHeight)}

    Real FPS: {str(realFPS)}
    Scaled FPS: {str(scaledFPS)}
    """)

    prevPercentageCompleted = 0

    totalFrameIterations = 0
    scaledFrameIterations = 0

    packetIndex = 0
    packetData = ""

    storageFolder = "PacketData/" + filmName

    if os.path.exists(storageFolder):
        print("Please Delete Old Storage Folder")
        return


    os.makedirs(storageFolder)

    
    while True:

        success, frame = videoCapture.read()

        if not success:
            print("Frame",str(totalFrameIterations),"failed to read")
            continue

        if (totalFrameIterations) % fpsMultiReciprocal == 0:

            frame = rescaleFrame(frame,resolutionMulti)

            row,col,_ = frame.shape

            colTable = []

            for colI in range(col):

                rowTable = []

                for rowI in range(row):
                    
                    colorData = frame[rowI][colI]
                    colorData = list(colorData)
          
                    for i,colorValue in enumerate(colorData): colorData[i] = np.int(colorValue)# allows json to sterilise

                    rowTable.append([colorData[2],colorData[1],colorData[0]] ) 

                colTable.append(rowTable)

            
            
            
            jsonPixelData = json.dumps(colTable)

            lastPacket = (scaledFrameIterations + 1) >= scaledFrames

            if ((scaledFrameIterations + 1) % packetSize == 0) or lastPacket:
                
                packetData += jsonPixelData

                packetIndex += 1

                packetData = "[" + packetData + "]" # close table

                storageLocation = storageFolder + "/" + str(packetIndex) + ".json"
            
            
                with open(storageLocation, 'w') as file: 
                    file.write(packetData)

                packetData = ""

            else:
                packetData += jsonPixelData + ", "

            scaledFrameIterations += 1


        percentageCompleted = round((totalFrameIterations/totalFrames)*100)

        if percentageCompleted > prevPercentageCompleted:

            print("Progress:",str(percentageCompleted) + "%")
            prevPercentageCompleted = percentageCompleted

        totalFrameIterations += 1

        if totalFrameIterations >= totalFrames:
            break
        
    

    videoCapture.release()
    cv.destroyAllWindows()

    if scaledFrames != scaledFrameIterations:
        print(f"Frame Estimation Error. Predited:{str(scaledFrames)}, Actual:{str(scaledFrameIterations)}")

    configData = {

        "packets": packetIndex,
        "packetSize": packetSize,

        "width": scaledWidth,
        "height": scaledHeight,

        "totalFrames": scaledFrameIterations,

        "fps": scaledFPS,

    }

    with open(storageFolder + "/config.json", 'w') as file:
        file.write(json.dumps(configData))

    print("Encoding Packets Completed")
    print(f"{str(packetIndex)} Packets Created")
