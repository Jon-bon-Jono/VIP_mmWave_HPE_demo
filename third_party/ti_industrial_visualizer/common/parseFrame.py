import json
import struct
import logging
import sys
import time
import numpy as np
import math
import os
import datetime

# Local File Imports
from parseTLVs import *
from gui_common import *
from tlv_defines import *

log = logging.getLogger(__name__)

parserFunctions = {
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS:                     parsePointCloudTLV,
    MMWDEMO_OUTPUT_MSG_RANGE_PROFILE:                       parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MAJOR:             parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MINOR:             parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MINOR:             parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_AZIMUT_HEAT_MAP_MAJOR:     parseRangeAzimuthMajorTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_AZIMUT_HEAT_MAP_MINOR:     parseRangeAzimuthMinorTLV,  
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP:              parseRangeDopplerHeatmapTLV,
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO:           parseSideInfoTLV,
    MMWDEMO_OUTPUT_MSG_SPHERICAL_POINTS:                    parseSphericalPointCloudTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_3D_TARGET_LIST:          parseTrackTLV,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST:                     parseTrackTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_HEIGHT:           parseTrackHeightTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_INDEX:            parseTargetIndexTLV,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_INDEX:                    parseTargetIndexTLV,
    MMWDEMO_OUTPUT_MSG_COMPRESSED_POINTS:                   parseCompressedSphericalPointCloudTLV,
    MMWDEMO_OUTPUT_MSG_OCCUPANCY_STATE_MACHINE:             parseOccStateMachTLV,
    MMWDEMO_OUTPUT_MSG_VITALSIGNS:                          parseVitalSignsTLV,
    MMWDEMO_OUTPUT_EXT_MSG_DETECTED_POINTS:                 parsePointCloudExtTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6843:               parseGestureFeaturesTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_OUTPUT_PROB_6843:            parseGestureProbTLV6843,
    MMWDEMO_OUTPUT_MSG_GESTURE_CLASSIFIER_6432:             parseGestureClassifierTLV6432,
    MMWDEMO_OUTPUT_EXT_MSG_ENHANCED_PRESENCE_INDICATION:    parseEnhancedPresenceInfoTLV,
    MMWDEMO_OUTPUT_EXT_MSG_CLASSIFIER_INFO:                 parseClassifierTLV,
    MMWDEMO_OUTPUT_MSG_SURFACE_CLASSIFICATION:              parseSurfaceClassificationTLV,
    MMWDEMO_OUTPUT_EXT_MSG_VELOCITY:                        parseVelocityTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RX_CHAN_COMPENSATION_INFO:       parseRXChanCompTLV,
    MMWDEMO_OUTPUT_MSG_EXT_STATS:                           parseExtStatsTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6432:               parseGestureFeaturesTLV6432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_x432:               parseGesturePresenceTLV6432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_THRESH_x432:        parsePresenceThreshold,
    MMWDEMO_OUTPUT_EXT_MSG_STATS_BSD:                       parseExtStatsTLVBSD,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST_2D_BSD:              parseTrackTLV2D,
    MMWDEMO_OUTPUT_EXT_MSG_CAM_TRIGGERS:                    parseCamTLV,
    MMWDEMO_OUTPUT_EXT_MSG_POINT_CLOUD_ANTENNA_SYMBOLS:     parseAntSymbols,
    MMWDEMO_OUTPUT_EXT_MSG_ADC_SAMPLES:                     parseADCSamples,
    MMWDEMO_OUTPUT_EXT_MSG_MODE_SWITCH_INFO:                parseModeSwitchTLV,
    MMWDEMO_OUTPUT_EXT_POINT_CLOUD_MINOR:                   parseGestureMinorMotionPointCloudExtTLV,
    MMWDEMO_OUTPUT_EXT_MSG_CAMERA_ON_IND:                   parseCameraOnTLV,
    MMWDEMO_OUTPUT_EXT_MSG_CLUSTER_LOCATIONS:               parseClusterLocs,
    MMWDEMO_OUTPUT_MSG_INTRUSION_DET_3D_SNR :               parse3DSNR,
    MMWDEMO_OUTPUT_MSG_INTRUSION_DET_3D_DET_MAT:            parse3DSNR_ID,
    MMWDEMO_OUTPUT_MSG_INTRUSION_DET_INFO:                  parseIDInfo    
}

unusedTLVs = [
    MMWDEMO_OUTPUT_MSG_NOISE_PROFILE,
    MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_STATS,
    MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS,
    MMWDEMO_OUTPUT_MSG_PRESCENCE_INDICATION,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_x432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_THRESH_x432,
    MMWDEMO_OUTPUT_EXT_MSG_MICRO_DOPPLER_RAW_DATA,
    MMWDEMO_OUTPUT_EXT_MSG_MICRO_DOPPLER_FEATURES,
    MMWDEMO_OUTPUT_EXT_MSG_QUICK_EVAL_INFO,
    MMWDEMO_OUTPUT_EXT_RANGE_DOPPLER_MAP,
    MMWDEMO_OUTPUT_EXT_POINT_CLOUD_CARTESIAN,
    MMWDEMO_OUTPUT_EXT_POINT_CLOUD_SPHERICAL,
    MMWDEMO_OUTPUT_EXT_CLASSIFIER_VARS
]

def parseCapon3DFrame(frameData):
    """
    Legacy / older 3D People Counting Capon3D UART frame parser.

    Header:
        Q9I2H = 48 bytes

    TLVs observed in the old parser:
        6 = compressed spherical point cloud
        7 = 3D target list
        8 = target index / point-to-track association
        9 = side info / unused here
    """

    headerStruct = '<Q9I2H'
    headerLen = struct.calcsize(headerStruct)
    tlvHeaderLen = 8
    magicExpected = 0x0708050603040102

    outputDict = {}
    outputDict['error'] = 0

    try:
        (
            magic,
            version,
            packetLength,
            platform,
            frameNum,
            subFrameNum,
            chirpMargin,
            frameMargin,
            uartSentTime,
            trackProcessTime,
            numTLVs,
            checksum,
        ) = struct.unpack(headerStruct, frameData[:headerLen])
    except Exception as e:
        log.warning(f'Capon3D header parsing failed: {e}')
        outputDict['error'] = 1
        return outputDict

    if magic != magicExpected:
        log.warning('Capon3D parser called on frame without expected magic word')
        outputDict['error'] = 1
        return outputDict

    outputDict['frameNum'] = frameNum
    outputDict['numDetectedPoints'] = 0
    outputDict['numDetectedTracks'] = 0
    outputDict['pointCloud'] = np.zeros((0, 7), np.float64)

    frameData = frameData[headerLen:]

    for _ in range(numTLVs):
        if len(frameData) < tlvHeaderLen:
            outputDict['error'] = 2
            return outputDict

        try:
            tlvType, tlvLength = struct.unpack('<2I', frameData[:tlvHeaderLen])
        except Exception as e:
            log.warning(f'Capon3D TLV header parsing failed: {e}')
            outputDict['error'] = 2
            return outputDict

        # In this legacy format, tlvLength includes the 8-byte TLV header.
        payloadLen = tlvLength - tlvHeaderLen
        payload = frameData[tlvHeaderLen:tlvHeaderLen + payloadLen]

        if tlvType == 6:
            _parseCapon3DCompressedPointCloud(payload, payloadLen, outputDict)
        elif tlvType == 7:
            _parseCapon3DTargetList(payload, payloadLen, outputDict)
        elif tlvType == 8:
            _parseCapon3DTargetIndexes(payload, payloadLen, outputDict)
        elif tlvType == 9:
            # Side info / extra data. Ignore for now.
            pass
        else:
            log.info(f'Capon3D: unhandled TLV type {tlvType}, length {tlvLength}')

        frameData = frameData[tlvLength:]

    return outputDict


def _parseCapon3DCompressedPointCloud(tlvData, tlvLength, outputDict):
    pUnitStruct = '<5f'      # elev, azim, doppler, range, snr units
    pointStruct = '<2bh2H'   # elevation, azimuth, doppler, range, snr

    pUnitSize = struct.calcsize(pUnitStruct)
    pointSize = struct.calcsize(pointStruct)

    if tlvLength < pUnitSize:
        outputDict['numDetectedPoints'] = 0
        outputDict['pointCloud'] = np.zeros((0, 7), np.float64)
        return

    try:
        pUnit = struct.unpack(pUnitStruct, tlvData[:pUnitSize])
    except Exception as e:
        log.error(f'Capon3D point unit parsing failed: {e}')
        outputDict['numDetectedPoints'] = 0
        outputDict['pointCloud'] = np.zeros((0, 7), np.float64)
        return

    tlvData = tlvData[pUnitSize:]
    numPoints = int((tlvLength - pUnitSize) / pointSize)

    pointCloud = np.zeros((numPoints, 7), np.float64)
    pointCloud[:, 6] = 255

    for i in range(numPoints):
        try:
            elevation, azimuth, doppler, rng, snr = struct.unpack(pointStruct, tlvData[:pointSize])
        except Exception as e:
            log.error(f'Capon3D point parsing failed at point {i}: {e}')
            numPoints = i
            pointCloud = pointCloud[:numPoints, :]
            break

        tlvData = tlvData[pointSize:]

        # First fill as spherical: range, azimuth, elevation.
        pointCloud[i, 0] = rng * pUnit[3]
        pointCloud[i, 1] = azimuth * pUnit[1]
        pointCloud[i, 2] = elevation * pUnit[0]
        pointCloud[i, 3] = doppler * pUnit[2]
        pointCloud[i, 4] = snr * pUnit[4]

    # Convert first three columns from spherical to Cartesian.
    if numPoints > 0:
        pointCloud[:, 0:3] = sphericalToCartesianPointCloud(pointCloud[:, 0:3])

    outputDict['numDetectedPoints'] = numPoints
    outputDict['pointCloud'] = pointCloud


def _parseCapon3DTargetList(tlvData, tlvLength, outputDict):
    # Legacy parser's parseDetectedTracksSDK3x used I9f:
    # tid, posX, posY, velX, velY, accX, accY, posZ, velZ, accZ
    targetStruct = '<I9f'
    targetSize = struct.calcsize(targetStruct)

    numTargets = int(tlvLength / targetSize)
    targets = np.zeros((numTargets, 16), np.float64)

    for i in range(numTargets):
        try:
            t = struct.unpack(targetStruct, tlvData[:targetSize])
        except Exception as e:
            log.error(f'Capon3D target parsing failed at target {i}: {e}')
            numTargets = i
            targets = targets[:numTargets, :]
            break

        tlvData = tlvData[targetSize:]

        targets[i, 0] = t[0]   # TID
        targets[i, 1] = t[1]   # posX
        targets[i, 2] = t[2]   # posY
        targets[i, 3] = t[7]   # posZ
        targets[i, 4] = t[3]   # velX
        targets[i, 5] = t[4]   # velY
        targets[i, 6] = t[8]   # velZ
        targets[i, 7] = t[5]   # accX
        targets[i, 8] = t[6]   # accY
        targets[i, 9] = t[9]   # accZ

    outputDict['numDetectedTracks'] = numTargets
    outputDict['trackData'] = targets


def _parseCapon3DTargetIndexes(tlvData, tlvLength, outputDict):
    indexes = np.frombuffer(tlvData[:tlvLength], dtype=np.uint8).astype(np.float64)
    outputDict['trackIndexes'] = indexes

    if 'pointCloud' in outputDict:
        n = min(len(indexes), outputDict['pointCloud'].shape[0])
        if n > 0:
            outputDict['pointCloud'][:n, 6] = indexes[:n]

def parseStandardFrame(frameData):
    # Constants for parsing frame header
    headerStruct = 'Q8I'
    frameHeaderLen = struct.calcsize(headerStruct)
    tlvHeaderLength = 8

    # Define the function's output structure and initialize error field to no error
    outputDict = {}
    outputDict['error'] = 0

    # A sum to track the frame packet length for verification for transmission integrity 
    totalLenCheck = 0   

    # Read in frame Header
    try:
        magic, version, totalPacketLen, platform, frameNum, timeCPUCycles, numDetectedObj, numTLVs, subFrameNum = struct.unpack(headerStruct, frameData[:frameHeaderLen])
    except:
        log.error('Error: Could not read frame header')
        outputDict['error'] = 1

    # Move frameData ptr to start of 1st TLV   
    frameData = frameData[frameHeaderLen:]
    totalLenCheck += frameHeaderLen

    # Save frame number to output
    outputDict['frameNum'] = frameNum

    # Initialize the point cloud struct since it is modified by multiple TLV's
    # Each point has the following: X, Y, Z, Doppler, SNR, Noise, Track index
    outputDict['pointCloud'] = np.zeros((numDetectedObj, 7), np.float64)
    # Initialize the track indexes to a value which indicates no track
    outputDict['pointCloud'][:, 6] = 255
    # Find and parse all TLV's
    for i in range(numTLVs):
        try:
            tlvType, tlvLength = tlvHeaderDecode(frameData[:tlvHeaderLength])
            frameData = frameData[tlvHeaderLength:]
            totalLenCheck += tlvHeaderLength
        except:
            log.warning('TLV Header Parsing Failure: Ignored frame due to parsing error')
            outputDict['error'] = 2
            return {}

        # print(tlvType)

        if (tlvType in parserFunctions):
            parserFunctions[tlvType](frameData[:tlvLength], tlvLength, outputDict)
        elif (tlvType in unusedTLVs):
            log.debug("No function to parse TLV type: %d" % (tlvType))
        else:
            log.info("Invalid TLV type: %d" % (tlvType))

        # Move to next TLV
        frameData = frameData[tlvLength:]
        totalLenCheck += tlvLength
    
    # Pad totalLenCheck to the next largest multiple of 32
    # since the device does this to the totalPacketLen for transmission uniformity
    totalLenCheck = 32 * math.ceil(totalLenCheck / 32)

    # Verify the total packet length to detect transmission error that will cause subsequent frames to dropped
    if (totalLenCheck != totalPacketLen):
        log.warning('Frame packet length read is not equal to totalPacketLen in frame header. Subsequent frames may be dropped.')
        outputDict['error'] = 3

    return outputDict

# Decode TLV Header
def tlvHeaderDecode(data):
    tlvType, tlvLength = struct.unpack('2I', data)
    return tlvType, tlvLength
