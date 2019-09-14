###########################################################################
# (C) 2017 Helmholtz-Zentrum Potsdam - Deutsches GeoForschungsZentrum GFZ #
#                                                                         #
# License: LGPLv3 (https://www.gnu.org/copyleft/lesser.html)              #
###########################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import uuid
import json
import math
import datetime
import dateutil.parser
import fdsnwsscripts.seiscomp.db.generic.inventory
from fdsnwsscripts.seiscomp import logs
from xml.etree import cElementTree as ET

try:
    import scipy.signal
    _have_scipy = True

except ImportError:
    _have_scipy = False


ns = "{http://www.fdsn.org/xml/station/1}"


def _uuid():
    return str(uuid.uuid1())


def _cha_id(cha):
    loc = cha.mySensorLocation
    sta = loc.myStation
    net = sta.myNetwork
    return "%s.%s.%s.%s.%s" % (net.code, sta.code, loc.code, cha.code, cha.start.isoformat())


def _is_fir_response(obj):
    return hasattr(obj, "symmetry")


def _is_paz_response(obj):
    return hasattr(obj, "poles")


def _optimize_fir(coeff):
    i = 0

    while i*2 < len(coeff):
        if coeff[i] != coeff[-i-1]:
            break

        i += 1

    if i*2 == len(coeff):
        return 'C', i

    elif i*2 > len(coeff):
        return 'B', i

    else:
        return 'A', len(coeff)


class Error(Exception):
    pass


class Fallback(Exception):
    pass


class Inventory(fdsnwsscripts.seiscomp.db.generic.inventory.Inventory):
    def __init__(self):
        super(Inventory, self).__init__()


    def __poles_zeros(self, tree):
        uu = _uuid()
        resp = self.insert_responsePAZ(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        remark = None
        poles = []
        zeros = []

        for e in tree:
            if e.tag == ns + "PzTransferFunctionType":
                if e.text == "LAPLACE (RADIANS/SECOND)":
                    resp.type = 'A'

                elif e.text == "LAPLACE (HERTZ)":
                    resp.type = 'B'

                elif e.text == "DIGITAL (Z-TRANSFORM)":
                    resp.type = 'D'

            elif e.tag == ns + "NormalizationFactor":
                resp.normalizationFactor = float(e.text)

            elif e.tag == ns + "NormalizationFrequency":
                resp.normalizationFrequency = float(e.text)

            elif e.tag == ns + "Pole":
                real = None
                imaginary = None

                for e1 in e:
                    if e1.tag == ns + "Real":
                        real = e1.text

                    if e1.tag == ns + "Imaginary":
                        imaginary = e1.text

                poles.append("(%s,%s)" % (real, imaginary))

            elif e.tag == ns + "Zero":
                real = None
                imaginary = None

                for e1 in e:
                    if e1.tag == ns + "Real":
                        real = e1.text

                    if e1.tag == ns + "Imaginary":
                        imaginary = e1.text

                zeros.append("(%s,%s)" % (real, imaginary))

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

                    if e1.tag == ns + "Description":
                        remark = json.dumps({"unit": e1.text})

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.numberOfPoles = len(poles)
        resp.numberOfZeros = len(zeros)
        resp.poles = " ".join(poles)
        resp.zeros = " ".join(zeros)
        return resp, inUnit, outUnit, remark


    def __fir_coefficients(self, tree):
        inUnit = None
        outUnit = None
        remark = None
        coeff = []
        denominatorCount = 0

        for e in tree:
            if e.tag == ns + "CfTransferFunctionType":
                if e.text != "DIGITAL":
                    raise Fallback

            elif e.tag == ns + "Numerator":
                coeff.append(e.text)

            elif e.tag == ns + "Denominator":
                denominatorCount += 1

                if denominatorCount > 1 or float(e.text) != 1.0:
                    raise Fallback

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

                    if e1.tag == ns + "Description":
                        remark = json.dumps({"unit": e1.text})

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        symmetry, ncoeff = _optimize_fir(coeff)
        del coeff[ncoeff:]

        uu = _uuid()
        resp = self.insert_responseFIR(name=uu, publicID=uu)
        resp.symmetry = symmetry
        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, remark


    def __iir_coefficients(self, tree):
        if not _have_scipy:
            raise Error("error: scipy not installed")

        uu = _uuid()
        resp = self.insert_responsePAZ(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        remark = None
        numerators = []
        denominators = []

        for e in tree:
            if e.tag == ns + "CfTransferFunctionType":
                if e.text == "ANALOG (RADIANS/SECOND)":
                    resp.type = 'A'

                elif e.text == "ANALOG (HERTZ)":
                    resp.type = 'B'

                elif e.text == "DIGITAL":
                    resp.type = 'D'

            elif e.tag == ns + "Numerator":
                numerators.append(float(e.text))

            elif e.tag == ns + "Denominator":
                denominators.append(float(e.text))

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

                    if e1.tag == ns + "Description":
                        remark = json.dumps({"unit": e1.text})

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        if resp.type != 'D':
            # not supported by evalresp, order of coefficients is not clear
            raise Error("error: unsupported transfer function type")

        # tested with evalresp V4.0.6
        numerators = scipy.trim_zeros(numerators, 'b') if numerators else [1.0]
        denominators = scipy.trim_zeros(denominators, 'b') if denominators else [1.0]

        d = len(numerators) - len(denominators)

        if d > 0:
            denominators += d * [0.0]

        elif d < 0:
            numerators += -d * [0.0]

        try:
            zeros, poles, gain = scipy.signal.tf2zpk(numerators, denominators)

        except Exception as ex:
            raise Error("error: %s" % ex)

        resp.normalizationFactor = gain
        resp.numberOfPoles = len(poles)
        resp.numberOfZeros = len(zeros)
        resp.poles = " ".join("(%s,%s)" % (c.real, c.imag) for c in poles)
        resp.zeros = " ".join("(%s,%s)" % (c.real, c.imag) for c in zeros)
        return resp, inUnit, outUnit, remark


    def __fir(self, tree):
        uu = _uuid()
        resp = self.insert_responseFIR(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        remark = None
        coeff = []

        for e in tree:
            if e.tag == ns + "Symmetry":
                if e.text == "NONE":
                    resp.symmetry = 'A'

                elif e.text == "ODD":
                    resp.symmetry = 'B'

                elif e.text == "EVEN":
                    resp.symmetry = 'C'

            elif e.tag == ns + "NumeratorCoefficient":
                coeff.append(e.text)

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

                    if e1.tag == ns + "Description":
                        remark = json.dumps({"unit": e1.text})

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        if resp.symmetry == 'A':
            symmetry, ncoeff = _optimize_fir(coeff)
            del coeff[ncoeff:]

        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, remark


    def __polynomial(self, tree):
        uu = _uuid()
        resp = self.insert_responsePolynomial(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        remark = None
        lowFreq = None
        highFreq = None
        coeff = []

        for e in tree:
            if e.tag == ns + "ApproximationType":
                if e.text == "MACLAURIN":
                    resp.approximationType = 'M'

            elif e.tag == ns + "FrequencyLowerBound":
                lowFreq = float(e.text)

            elif e.tag == ns + "FrequencyUpperBound":
                highFreq = float(e.text)

            elif e.tag == ns + "ApproximationLowerBound":
                resp.approximationLowerBound = float(e.text or "0")

            elif e.tag == ns + "ApproximationUpperBound":
                resp.approximationUpperBound = float(e.text or "0")

            elif e.tag == ns + "MaximumError":
                resp.approximationError = float(e.text)

            elif e.tag == ns + "Coefficient":
                coeff.append(e.text)

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

                    if e1.tag == ns + "Description":
                        remark = json.dumps({"unit": e1.text})

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.frequencyUnit = 'B'
        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, remark, lowFreq, highFreq


    def __stage(self, tree):
        resp = None
        inUnit = None
        outUnit = None
        remark = None
        lowFreq = None
        highFreq = None
        inputSampleRate = 0.0
        decimationFactor = 1
        delay = 0.0
        correction = 0.0
        gain = None
        gainFrequency = None
        converted = False
        extraDecimation = None

        for e in tree:
            if e.tag == ns + "PolesZeros":
                resp, inUnit, outUnit, remark = self.__poles_zeros(e)

            elif e.tag == ns + "Coefficients":
                try:
                    resp, inUnit, outUnit, remark = self.__fir_coefficients(e)

                except Fallback:
                    resp, inUnit, outUnit, remark = self.__iir_coefficients(e)
                    converted = True

            elif e.tag == ns + "FIR":
                resp, inUnit, outUnit, remark = self.__fir(e)

            elif e.tag == ns + "Polynomial":
                resp, inUnit, outUnit, remark, lowFreq, highFreq = self.__polynomial(e)

            elif e.tag == ns + "Decimation":
                for e1 in e:
                    if e1.tag == ns + "InputSampleRate":
                        inputSampleRate = float(e1.text)

                    elif e1.tag == ns + "Factor":
                        decimationFactor = int(e1.text)

                    elif e1.tag == ns + "Delay":
                        delay = float(e1.text)

                    elif e1.tag == ns + "Correction":
                        correction = float(e1.text)

            elif e.tag == ns + "StageGain":
                for e1 in e:
                    if e1.tag == ns + "Value":
                        gain = float(e1.text)

                    elif e1.tag == ns + "Frequency":
                        gainFrequency = float(e1.text)

        if resp is not None:
            resp.gain = gain

            if hasattr(resp, "gainFrequency"):
                resp.gainFrequency = gainFrequency

            if hasattr(resp, "decimationFactor"):
                resp.decimationFactor = decimationFactor
                resp.delay = delay * inputSampleRate
                resp.correction = correction * inputSampleRate

            elif _is_paz_response(resp) and resp.type == 'D' and decimationFactor != 1:
                # add separate decimation stage
                uu = _uuid()
                fir = self.insert_responseFIR(name=uu, publicID=uu)
                fir.decimationFactor = decimationFactor
                fir.delay = delay * inputSampleRate
                fir.correction = correction * inputSampleRate
                fir.gain = 1.0
                fir.symmetry = 'A'
                fir.numberOfCoefficients = 1
                fir.coefficients = "1.0"
                extraDecimation = fir.publicID

            if converted:
                resp.normalizationFrequency = gainFrequency

        return resp, inUnit, outUnit, remark, lowFreq, highFreq, gain, converted, extraDecimation


    def __process_response(self, tree, cha, sensor, logger):
        stages = {}
        fallback = None

        for e in tree:
            if e.tag == ns + "InstrumentSensitivity":
                for e1 in e:
                    if e1.tag == ns + "Value":
                        cha.gain = float(e1.text)

                    elif e1.tag == ns + "Frequency":
                        cha.gainFrequency = float(e1.text)

                    elif e1.tag == ns + "InputUnits":
                        for e2 in e1:
                            if e2.tag == ns + "Name":
                                cha.gainUnit = e2.text

            elif e.tag == ns + "InstrumentPolynomial":
                resp, inUnit, outUnit, remark, lowFreq, highFreq = self.__polynomial(e)
                resp.gain = 1.0
                resp.gainFrequency = 0.0
                fallback = (resp, inUnit, outUnit, remark, lowFreq, highFreq, 1.0, False, None)
                cha.gainUnit = inUnit

            elif e.tag == ns + "Stage":
                i = int(e.attrib['number'])

                try:
                    stages[i] = self.__stage(e)

                except Error as ex:
                    raise Error("%s stage %d: %s" % (_cha_id(cha), i, ex))

        if not stages and fallback:
            stages[1] = fallback

        logger.gain = 1.0
        unit = None
        afc = []
        dfc = []

        for i in range(1, len(stages)+1):
            try:
                resp, inUnit, outUnit, remark, lowFreq, highFreq, gain, converted, extraDecimation = stages[i]

            except KeyError:
                raise Error("%s: error: missing stage %d" % (_cha_id(cha), i))

            if converted:
                logs.notice("%s stage %d: notice: coefficients converted to PAZ" % (_cha_id(cha), i))

            if i == 1:
                sensor.unit = inUnit
                sensor.remark = remark

                if resp is None:
                    raise Error("%s: error: missing stage 1 response" % _cha_id(cha))

                elif _is_fir_response(resp) or (_is_paz_response(resp) and resp.type == 'D'):
                    # add dummy sensor to digital input
                    uu = _uuid()
                    paz = self.insert_responsePAZ(name=uu, publicID=uu)
                    paz.type = 'A'
                    paz.gain = 1.0
                    paz.gainFrequency = 0.0
                    paz.normalizationFactor = 1.0
                    paz.normalizationFrequency = 0.0
                    paz.numberOfPoles = 0
                    paz.numberOfZeros = 0
                    sensor.response = paz.publicID
                    sensor.lowFrequency = None
                    sensor.highFrequency = None
                    inUnit = "COUNTS"

                else:
                    sensor.response = resp.publicID
                    sensor.lowFrequency = lowFreq
                    sensor.highFrequency = highFreq
                    unit = outUnit
                    continue

            elif resp is None:
                if gain is not None:
                    logger.gain *= gain

                continue

            elif inUnit != unit:
                raise Error("%s stage %d: error: unexpected input unit: %s, expected: %s" % (_cha_id(cha), i, inUnit, unit))

            if _is_fir_response(resp) and (resp.numberOfCoefficients == 0 or (resp.numberOfCoefficients == 1 and float(resp.coefficients) == 1.0 and resp.decimationFactor == 1)):
                logger.gain *= resp.gain
                self.remove_responseFIR(resp.name)

            elif _is_paz_response(resp) and resp.numberOfPoles == 0 and resp.numberOfZeros == 0:
                logger.gain *= resp.gain
                self.remove_responsePAZ(resp.name)

            elif _is_fir_response(resp) or (_is_paz_response(resp) and resp.type == 'D'):
                dfc.append(resp.publicID)

            elif not dfc:
                afc.append(resp.publicID)

            else:
                raise Error("%s stage %d: error: analogue stage after digital" % (_cha_id(cha), i))

            if extraDecimation:
                logs.notice("%s stage %d: notice: adding extra decimation stage" % (_cha_id(cha), i))
                dfc.append(extraDecimation)

            unit = outUnit

        deci = logger.insert_decimation(cha.sampleRateNumerator, cha.sampleRateDenominator)
        deci.analogueFilterChain = " ".join(afc)
        deci.digitalFilterChain = " ".join(dfc)


    def __process_channel(self, tree, sta, locs):
        code = tree.attrib['code']
        locationCode = tree.attrib['locationCode']
        start = dateutil.parser.parse(tree.attrib['startDate']).replace(tzinfo=None)

        try:
            end = dateutil.parser.parse(tree.attrib['endDate']).replace(tzinfo=None)

            if end > datetime.datetime(2100, 1, 1):
                end = None

        except KeyError:
            end = None

        try:
            loc = locs[(locationCode, start)]

            if loc.end is not None and (end is None or end > loc.end):
                loc.end = end

        except KeyError:
            loc = sta.insert_sensorLocation(locationCode, start, end=end, publicID=_uuid())
            locs[(locationCode, start)] = loc

        cha = loc.insert_stream(code, start, end=end)
        cha.restricted = (tree.attrib.get("restrictedStatus", "").lower() == "closed")
        cha.shared = True
        cha.format = "steim2"
        cha.flags = ""
        cha.sensor = _uuid()
        cha.sensorChannel = 0
        cha.datalogger = _uuid()
        cha.dataloggerChannel = 0
        clockDrift = None

        sensor = self.insert_sensor(name=cha.sensor, publicID=cha.sensor)
        logger = self.insert_datalogger(name=cha.datalogger, publicID=cha.datalogger)

        for e in tree:
            if e.tag == ns + "Latitude":
                latitude = float(e.text)

                if loc.latitude is not None and loc.latitude != latitude:
                    logs.warning("%s: warning: conflicting latitude: %s vs. %s" % (_cha_id(cha), loc.latitude, latitude))

                loc.latitude = latitude

            elif e.tag == ns + "Longitude":
                longitude = float(e.text)

                if loc.longitude is not None and loc.longitude != longitude:
                    logs.warning("%s: warning: conflicting longitude: %s vs. %s" % (_cha_id(cha), loc.longitude, longitude))

                loc.longitude = longitude

            elif e.tag == ns + "Elevation":
                elevation = float(e.text)

                if loc.elevation is not None and loc.elevation != elevation:
                    logs.warning("%s: warning: conflicting elevation: %s vs. %s" % (_cha_id(cha), loc.elevation, elevation))

                loc.elevation = elevation

            elif e.tag == ns + "Depth":
                cha.depth = float(e.text)

            elif e.tag == ns + "Azimuth":
                cha.azimuth = float(e.text)

            elif e.tag == ns + "Dip":
                cha.dip = float(e.text)

            elif e.tag == ns + "Type":
                cha.flags += e.text[0]

            elif e.tag == ns + "SampleRate":
                if cha.sampleRateNumerator is not None:
                    continue

                sampleRate = float(e.text)

                if sampleRate > 1:
                    cha.sampleRateNumerator = int(round(sampleRate))
                    cha.sampleRateDenominator = 1

                elif sampleRate > 0:
                    cha.sampleRateNumerator = 1
                    cha.sampleRateDenominator = int(round(1/sampleRate))

                else:
                    cha.sampleRateNumerator = 0
                    cha.sampleRateDenominator = 0

            elif e.tag == ns + "SampleRateRatio":
                for e1 in e:
                    if e1.tag == ns + "NumberSamples":
                        cha.sampleRateNumerator = int(e1.text)

                    if e1.tag == ns + "NumberSeconds":
                        cha.sampleRateDenominator = int(e1.text)

            elif e.tag == ns + "Sensor":
                for e1 in e:
                    if e1.tag == ns + "Description":
                        sensor.description = e1.text

                    elif e1.tag == ns + "Type":
                        sensor.type = e1.text[:10]

                        if not sensor.description:
                            sensor.description = e1.text

                    elif e1.tag == ns + "Model":
                        sensor.model = e1.text

                    elif e1.tag == ns + "Manufacturer":
                        sensor.manufacturer = e1.text

                    elif e1.tag == ns + "SerialNumber":
                        cha.sensorSerialNumber = e1.text

            elif e.tag == ns + "DataLogger":
                for e1 in e:
                    if e1.tag == ns + "Description":
                        logger.description = e1.text

                    elif e1.tag == ns + "Type":
                        if not logger.description:
                            logger.description = e1.text

                    elif e1.tag == ns + "Model":
                        logger.digitizerModel = e1.text
                        logger.recorderModel = e1.text

                    elif e1.tag == ns + "Manufacturer":
                        logger.digitizerManufacturer = e1.text
                        logger.recorderManufacturer = e1.text

                    elif e1.tag == ns + "SerialNumber":
                        cha.dataloggerSerialNumber = e1.text

            elif e.tag == ns + "ClockDrift":
                clockDrift = float(e.text)

            elif e.tag == ns + "StorageFormat":
                cha.format = e.text

            elif e.tag == ns + "Response":
                try:
                    self.__process_response(e, cha, sensor, logger)

                except Error as ex:
                    logs.error(str(ex))

        if cha.sampleRateDenominator and clockDrift is not None:
            logger.maxClockDrift = clockDrift * cha.sampleRateNumerator / cha.sampleRateDenominator

        if not cha.flags:
            cha.flags = "GC"


    def __process_station(self, tree, net):
        code = tree.attrib['code']
        start = dateutil.parser.parse(tree.attrib['startDate']).replace(tzinfo=None)
        sta = net.insert_station(code, start, publicID=_uuid())

        try:
            sta.end = dateutil.parser.parse(tree.attrib['endDate']).replace(tzinfo=None)

            if sta.end > datetime.datetime(2100, 1, 1):
                sta.end = None

        except KeyError:
            sta.end = None

        sta.restricted = (tree.attrib.get("restrictedStatus", "").lower() == "closed")
        sta.shared = True
        sta.archive = self.__archive
        sta.archiveNetworkCode = net.code

        locs = {}

        for e in tree:
            if e.tag == ns + "Latitude":
                sta.latitude = float(e.text)

            elif e.tag == ns + "Longitude":
                sta.longitude = float(e.text)

            elif e.tag == ns + "Elevation":
                sta.elevation = float(e.text)

            elif e.tag == ns + "Site":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        sta.description = e1.text if e1.text else code

                    elif e1.tag == ns + "Town":
                        sta.place = e1.text

                    elif e1.tag == ns + "Country":
                        sta.country = e1.text

            elif e.tag == ns + "Channel":
                self.__process_channel(e, sta, locs)


    def __process_network(self, tree):
        code = tree.attrib['code']
        start = dateutil.parser.parse(tree.attrib['startDate']).replace(tzinfo=None)
        net = self.insert_network(code, start, publicID=_uuid())

        try:
            net.end = dateutil.parser.parse(tree.attrib['endDate']).replace(tzinfo=None)

            if net.end > datetime.datetime(2100, 1, 1):
                net.end = None

        except KeyError:
            net.end = None

        net.restricted = (tree.attrib.get("restrictedStatus", "").lower() == "closed")
        net.shared = True
        net.archive = self.__archive
        net.netClass = 't' if code[0] in "0123456789XYZ" else 'p'

        for e in tree:
            if e.tag == ns + "Description":
                net.description = e.text

            elif e.tag == ns + "Station":
                self.__process_station(e, net)


    def load_fdsnxml(self, src):
        try:
            tree = ET.parse(src).getroot()

        except Exception as ex:
            raise Error(ex)

        for e in tree:
            if e.tag == ns + "Source":
                self.__archive = e.text

            elif e.tag == ns + "Network":
                if 'startDate' not in e.attrib:
                    logs.error("error: network %s is missing startDate" % e.attrib['code'])
                    continue

                self.__process_network(e)

