###########################################################################
# (C) 2017 Helmholtz-Zentrum Potsdam - Deutsches GeoForschungsZentrum GFZ #
#                                                                         #
# License: LGPLv3 (https://www.gnu.org/copyleft/lesser.html)              #
###########################################################################

import uuid
import datetime
import dateutil.parser
import seiscomp.db.generic.inventory
from xml.etree import cElementTree as ET

ns = "{http://www.fdsn.org/xml/station/1}"


class Error(Exception):
    pass


class Inventory(seiscomp.db.generic.inventory.Inventory):
    def __init__(self):
        super(Inventory, self).__init__()


    def __poles_zeros(self, tree):
        uu = str(uuid.uuid1())
        resp = self.insert_responsePAZ(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        lowFreq = None
        highFreq = None
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

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.numberOfPoles = len(poles)
        resp.numberOfZeros = len(zeros)
        resp.poles = " ".join(poles)
        resp.zeros = " ".join(zeros)
        return resp, inUnit, outUnit, lowFreq, highFreq


    def __coefficients(self, tree):
        uu = str(uuid.uuid1())
        resp = self.insert_responseFIR(name=uu, publicID=uu, symmetry='A')
        inUnit = None
        outUnit = None
        lowFreq = None
        highFreq = None
        coeff = []

        for e in tree:
            if e.tag == ns + "CfTransferFunctionType":
                if e.text != "DIGITAL":
                    raise Error("unsupported CfTransferFunctionType")

            elif e.tag == ns + "Numerator":
                coeff.append(e.text)

            elif e.tag == ns + "Denominator":
                raise Error("IIR filters not supported")

            elif e.tag == ns + "InputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        inUnit = e1.text

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, lowFreq, highFreq


    def __fir(self, tree):
        uu = str(uuid.uuid1())
        resp = self.insert_responseFIR(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        lowFreq = None
        highFreq = None
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

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, lowFreq, highFreq


    def __polynomial(self, tree):
        uu = str(uuid.uuid1())
        resp = self.insert_responsePolynomial(name=uu, publicID=uu)
        inUnit = None
        outUnit = None
        lowFreq = None
        highFreq = None
        coeff = []

        for e in tree:
            if e.tag == ns + "ApproximationType":
                if e.text == "MACLAURIN":
                    resp.approximationType = 'M'

            elif e.tag == ns + "FrequencyLowerBound":
                lowFreq = float(e.text)
                unit = e.attrib.get("unit", "HERTZ")

                if unit == "RADIANS/SECOND":
                    resp.frequencyUnit = 'A'

                else:
                    resp.frequencyUnit = 'B'

            elif e.tag == ns + "FrequencyUpperBound":
                highFreq = float(e.text)
                unit = e.attrib.get("unit", "HERTZ")

                if unit == "RADIANS/SECOND":
                    resp.frequencyUnit = 'A'

                else:
                    resp.frequencyUnit = 'B'

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

            elif e.tag == ns + "OutputUnits":
                for e1 in e:
                    if e1.tag == ns + "Name":
                        outUnit = e1.text

        resp.numberOfCoefficients = len(coeff)
        resp.coefficients = " ".join(coeff)
        return resp, inUnit, outUnit, lowFreq, highFreq


    def __stage(self, tree):
        resp = None
        inUnit = None
        outUnit = None
        lowFreq = None
        highFreq = None
        inputSampleRate = 0
        decimationFactor = 1
        delay = 0
        correction = 0
        gain = 1.0
        gainFrequency = 0.0

        for e in tree:
            if e.tag == ns + "PolesZeros":
                resp, inUnit, outUnit, lowFreq, highFreq = self.__poles_zeros(e)

            elif e.tag == ns + "Coefficients":
                resp, inUnit, outUnit, lowFreq, highFreq = self.__coefficients(e)

            elif e.tag == ns + "FIR":
                resp, inUnit, outUnit, lowFreq, highFreq = self.__fir(e)

            elif e.tag == ns + "Polynomial":
                resp, inUnit, outUnit, lowFreq, highFreq = self.__polynomial(e)

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
            if hasattr(resp, "decimationFactor"):
                resp.decimationFactor = decimationFactor
                resp.delay = delay * inputSampleRate
                resp.correction = correction * inputSampleRate

            if hasattr(resp, "gainFrequency"):
                resp.gainFrequency = gainFrequency

            resp.gain = gain

        return resp, inUnit, outUnit, lowFreq, highFreq, gain


    def __process_response(self, tree, cha, sensor, logger):
        stages = {}

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

            elif e.tag == ns + "Stage":
                stages[int(e.attrib['number'])] = self.__stage(e)

        unit = None
        logger.gain = 1.0
        afc = []
        dfc = []

        for i in range(len(stages)):
            resp, inUnit, outUnit, lowFreq, highFreq, gain = stages[i+1]

            if not sensor.response:
                sensor.response = resp.publicID
                sensor.unit = inUnit
                sensor.lowFrequency = lowFreq
                sensor.highFrequency = highFreq

            elif resp is None:
                logger.gain *= gain
                continue

            elif inUnit != unit:
                raise Error("unexpected input unit: %s, expected: %s" % (inUnit, unit))

            elif inUnit == "COUNTS" and outUnit != "COUNTS":
                raise Error("unexpected output unit: %s, expected: COUNTS" % outUnit)

            elif hasattr(resp, "numberOfCoefficients") and resp.numberOfCoefficients == 0:
                logger.gain *= resp.gain
                self.remove_responseFIR(resp.name)

            elif hasattr(resp, "numberOfPoles") and resp.numberOfPoles == 0 and resp.numberOfZeros == 0:
                logger.gain *= resp.gain
                self.remove_responsePAZ(resp.name)

            elif inUnit == "COUNTS":
                dfc.append(resp.publicID)

            else:
                afc.append(resp.publicID)

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
            loc = sta.insert_sensorLocation(locationCode, start, end=end, publicID=uuid.uuid1())
            locs[(locationCode, start)] = loc

        cha = loc.insert_stream(code, start, end=end)
        cha.restricted = (tree.attrib.get("restrictedStatus", "").lower() == "closed")
        cha.shared = True
        cha.format = "steim2"
        cha.flags = ""
        cha.sensor = str(uuid.uuid1())
        cha.sensorChannel = 0
        cha.datalogger = str(uuid.uuid1())
        cha.dataloggerChannel = 0

        sensor = self.insert_sensor(name=cha.sensor, publicID=cha.sensor)
        logger = self.insert_datalogger(name=cha.datalogger, publicID=cha.datalogger)

        for e in tree:
            if e.tag == ns + "Latitude":
                loc.latitude = float(e.text)

            elif e.tag == ns + "Longitude":
                loc.longitude = float(e.text)

            elif e.tag == ns + "Elevation":
                loc.elevation = float(e.text)

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

                else:
                    cha.sampleRateNumerator = 1
                    cha.sampleRateDenominator = int(round(1/sampleRate))

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

                    elif e1.tag == ns + "Model":
                        sensor.model = e1.text

                    elif e1.tag == ns + "Type":
                        sensor.type = e1.text

                    elif e1.tag == ns + "SerialNumber":
                        cha.sensorSerialNumber = e1.text

            elif e.tag == ns + "DataLogger":
                for e1 in e:
                    if e1.tag == ns + "Description":
                        logger.description = e1.text

                    elif e1.tag == ns + "Model":
                        logger.digitizerModel = e1.text
                        logger.recorderModel = e1.text

                    elif e1.tag == ns + "SerialNumber":
                        cha.dataloggerSerialNumber = e1.text

            elif e.tag == ns + "Response":
                self.__process_response(e, cha, sensor, logger)

        if not cha.flags:
            cha.flags = "GC"


    def __process_station(self, tree, net):
        code = tree.attrib['code']
        start = dateutil.parser.parse(tree.attrib['startDate']).replace(tzinfo=None)
        sta = net.insert_station(code, start, publicID=uuid.uuid1())

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
                        sta.description = e1.text

                    elif e1.tag == ns + "Town":
                        sta.place = e1.text

                    elif e1.tag == ns + "Country":
                        sta.country = e1.text

            elif e.tag == ns + "Channel":
                self.__process_channel(e, sta, locs)


    def __process_network(self, tree):
        code = tree.attrib['code']
        start = dateutil.parser.parse(tree.attrib['startDate']).replace(tzinfo=None)
        net = self.insert_network(code, start, publicID=uuid.uuid1())

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
        tree = ET.parse(src).getroot()

        for e in tree:
            if e.tag == ns + "Source":
                self.__archive = e.text

            elif e.tag == ns + "Network":
                self.__process_network(e)

