"""
Raspberry Pi Pico (MicroPython) exercise:
work with SIM868 GSM/GPRS/GNSS Module
"""
import machine
import os
import utime
import binascii

from machine import UART, Pin

class GNSSNavInformation(object):
    def __init__(self, data: str) -> None:
        self.rawData: str = data
        self.gnssRunStatus: int = 0
        self.fixStatus: int = 0
        self.dateTime: list = [] # [Year, Month, Day, Hour, Minute, Second]
        self.latitude: float = 0.0
        self.longitude: float = 0.0
        self.mslaltitude: float = 0.0
        self.speedOverGround: float = 0.0
        self.courseOverGround: float = 0.0
        self.fixMode: int = 0
        self.hdop: float = 0
        self.pdop: float = 0
        self.vdop: float = 0
        self.gpsSatellitesInView: int = 0
        self.gnssSatellitesUsed: int = 0
        self.glonassSatellitesInView: int = 0
        self.cn0max: float = 0
        self.hpa: float = 0
        self.vpa: float = 0
        
    @property
    def GNSSRunStatus(self) -> int:
        return self.gnssRunStatus
        
    @property
    def FixStatus(self) -> int:
        return self.fixStatus
    
    @property
    def DateTime(self) -> list:
        return self.dateTime
    
    @property
    def Latitude(self) -> float:
        return self.latitude
    
    @property
    def Longitude(self) -> float:
        return self.longitude
    
    @property
    def MSLAltitude(self) -> float:
        return self.mslaltitude
    
    @property
    def SpeedOverGround(self) -> float:
        return self.speedOverGround
    
    @property
    def CourseOverGround(self) -> float:
        return self.courseOverGround
    
    @property
    def HDOP(self) -> float:
        return self.hdop
    
    @property
    def PDOP(self) -> float:
        return self.pdop
    
    @property
    def VDOP(self) -> float:
        return self.vdop
    
    @property
    def GPSSatellitesInView(self) -> int:
        return self.gpsSatellitesInView
    
    @property
    def GNSSSatellitesUsed(self) -> int:
        return self.gnssSatellitesUsed
    
    @property
    def GLONASSSatellitesInView(self) -> int:
        return self.glonassSatellitesInView
    
    @property
    def CN0max(self) -> float:
        return self.cn0max
    
    @property
    def HPA(self) -> float:
        return self.hpa
    
    @property
    def VPA(self) -> float:
        return self.vpa
    
    @property
    def FixMode(self) -> int:
        return self.fixMode

    @property
    def DataToList(self) -> list:
        return [navInfo.GNSSRunStatus, navInfo.FixStatus, navInfo.DateTime, navInfo.Latitude, navInfo.Longitude, navInfo.MSLAltitude,
                navInfo.SpeedOverGround, navInfo.CourseOverGround, navInfo.FixMode, navInfo.HDOP, navInfo.PDOP, navInfo.VDOP,
                navInfo.GPSSatellitesInView, navInfo.GNSSSatellitesUsed, navInfo.GLONASSSatellitesInView, navInfo.CN0max,
                navInfo.HPA, navInfo.VPA]
    
    def ParseFloat(self, rawData: str) -> float:
        if rawData == "": return 0.0
        return float(rawData)
    
    def ParseInt(self, rawData: str) -> int:
        if rawData == "": return 0
        return int(rawData)
        
    def Parse(self, data: str = "") -> None:
        source: str = self.rawData if data == "" else data
        if source.find("AT+CGNSINF\r\r\n+CGNSINF: ") != -1:
            source = source = source.replace("AT+CGNSINF\r\r\n+CGNSINF: ", "") 
        elif source.find("AT+CGNSINF") != -1:
            source = source.replace("AT+CGNSINF\r\r\n", "")
        elif source.find("AT+CGNSINF: ") != -1:
            source = source.replace("AT+CGNSINF: ", "")
            
        # Trzeba sprawdzić czy ostatni nie jest połaczony z ok
        if source.find("\r\n\r\nOK\r\n"):
            source = source.replace("\r\n\r\nOK\r\n", "")
            
        srcSplit: list = source.split(",")

        # Valid size for date
        if len(srcSplit) != 21: return
        
        self.gnssRunStatus = self.ParseInt(srcSplit[0])
        self.fixStatus = self.ParseInt(srcSplit[1])

        year: str = srcSplit[2][0:4]
        month: str = srcSplit[2][4:6]
        day: str = srcSplit[2][6:8]
        hour: str = srcSplit[2][8:10]
        minute: str = srcSplit[2][10:12]
        second: str = srcSplit[2][12:14]
        
        self.dateTime = [year, month, day, hour, minute, second]
        self.latitude = self.ParseFloat(srcSplit[3])
        self.longitude = self.ParseFloat(srcSplit[4])
        self.mslaltitude = self.ParseFloat(srcSplit[5])
        self.speedOverGround = self.ParseFloat(srcSplit[6])        
        self.courseOverGround = self.ParseFloat(srcSplit[7])
        self.fixMode = self.ParseInt(srcSplit[8])
        self.hdop = self.ParseFloat(srcSplit[10])
        self.pdop = self.ParseFloat(srcSplit[11])
        self.vdop = self.ParseFloat(srcSplit[12])
        self.gpsSatellitesInView = self.ParseInt(srcSplit[14])
        self.gnssSatellitesUsed = self.ParseInt(srcSplit[15])
        self.glonassSatellitesInView = self.ParseInt(srcSplit[16])
        self.cn0max = self.ParseFloat(srcSplit[18])
        self.hpa = self.ParseFloat(srcSplit[19])
        self.vpa = self.ParseFloat(srcSplit[20])

class ATCommandSender(object):
    def __init__(self, uart: UART) -> None:
        self.uart: UART = uart
        
    def SendCommand(self, command: str, watchdog: int = 100) -> str:
        result: str = ""
        didRecieve: bool = False
        recievedBuffer: bytes = b''
        encodedCommand: bytes = (command+'\r\n').encode() 
        
        self.uart.write(encodedCommand)
        
        time = utime.ticks_ms()
        while (utime.ticks_ms() - time) < watchdog:
            if self.uart.any():
                recievedBuffer = b"".join([recievedBuffer, self.uart.read(1)])
                didRecieve = True
        
        if recievedBuffer != '':
            result = recievedBuffer.decode()
        elif didRecieve == False:
            result = "TIMEOUT"
        return result    
    
    def SendCommandWH(self, command: str, expectedResponse: str = "OK", watchdog: int = 100) -> list:
        isResponseCorrect: bool = False
        moduleResponse: str = self.SendCommand(command, watchdog)
        
        if expectedResponse in moduleResponse:
            isResponseCorrect = True
        return [isResponseCorrect, moduleResponse]

class SIM868(ATCommandSender):
    def __init__(self, uart: UART, powerPin: int = 14) -> None:
        super().__init__(uart)
        self.powerPin: Pin = Pin(powerPin, Pin.OUT)
        
    def PowerReset(self) -> None:
        self.powerPin.value(1)
        utime.sleep(1)
        self.powerPin.value(0)
        
    def StartModule(self, watchDog: int = 6000) -> bool:
        response: str = ""
        didStartCorrectly: bool = False
        
        time = utime.ticks_ms()
        while (utime.ticks_ms() - time) < watchDog:
            response = self.SendCommand("ATE1")
            response = self.SendCommand("AT")
            if 'OK' in response:
                return True
            else:
                self.PowerReset()
                utime.sleep(100)
                
        return didStartCorrectly

    def EnableGPS(self) -> bool:
        return self.SendCommandWH("AT+CGNSPWR=1")[0]
               
    def DisableGPS(self) -> bool:
        return self.SendCommandWH("AT+CGNSPWR=0")[0]
    
    def GetGNSSNavInfo(self) -> GNSSNavInformation:
        moduleResponse: str = self.SendCommand("AT+CGNSINF")
        gnssni: GNSSNavInformation = GNSSNavInformation(moduleResponse)        
        gnssni.Parse()
        #gnssni.Parse("+CGNSINF: 1,1,20241201111755.000,50.282724,18.680043,270.862,0.59,189.6,1,,2.5,2.6,0.9,,9,6,5,,43,,")
        return gnssni
        
pwr_en = 14  # pin to control the power of the module
uart_port = 0
uart_baute = 115200

uart = machine.UART(uart_port, uart_baute)

def hexstr_to_str(hex_str):
    hex_data = hex_str.encode('utf-8')
    str_bin = binascii.unhexlify(hex_data)
    return str_bin.decode('utf-8')


def str_to_hexstr(string):
    str_bin = string.encode('utf-8')
    return binascii.hexlify(str_bin).decode('utf-8')


def wait_resp_info(timeout=2000):
    prvmills = utime.ticks_ms()
    info = b""
    while (utime.ticks_ms()-prvmills) < timeout:
        if uart.any():
            info = b"".join([info, uart.read(1)])
    print(info.decode())
    return info


# Send AT command
def send_at(cmd, back, timeout=2000):
    rec_buff = b''
    uart.write((cmd+'\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms()-prvmills) < timeout:
        if uart.any():
            rec_buff = b"".join([rec_buff, uart.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(cmd + ' no responce')


# Check the network status
def check_network():
    for i in range(1, 3):
        if send_at("AT+CGREG?", "0,1") == 1:
            print('SIM868 is online\r\n')
            break
        else:
            print('SIM868 is offline, please wait...\r\n')
            utime.sleep(5)
            continue
    send_at("AT+CPIN?", "OK")
    send_at("AT+CSQ", "OK")
    send_at("AT+COPS?", "OK")
    send_at("AT+CGATT?", "OK")
    send_at("AT+CGDCONT?", "OK")
    send_at("AT+CSTT?", "OK")
    #send_at("AT+CSTT=\""+APN+"\"", "OK")
    send_at("AT+CIICR", "OK")
    send_at("AT+CIFSR", "OK")


# Get the gps info
def get_gps_info():
    count = 0
    print('Start GPS session...')
    send_at('AT+CGNSPWR=1', 'OK')
    utime.sleep(2)
    for i in range(1, 10):
        uart.write(bytearray(b'AT+CGNSINF\r\n'))
        rec_buff = wait_resp_info()
        if ',,,,' in rec_buff.decode():
            print('GPS is not ready')
#            print(rec_buff.decode())
            if i >= 9:
                print('GPS positioning failed, please check the GPS antenna!\r\n')
                send_at('AT+CGNSPWR=0', 'OK')
            else:
                utime.sleep(2)
                continue
        else:
            if count <= 3:
                count += 1
                print('GPS info:')
                print(rec_buff.decode())
            else:
                send_at('AT+CGNSPWR=0', 'OK')
                break


sim: SIM868 = SIM868(uart)
started = sim.StartModule()
print(f"Did module start? {started}")
print(f"Enable GPS {sim.EnableGPS()}")
print(f"Disable GPS {sim.DisableGPS()}")
navInfo: GNSSNavInformation = sim.GetGNSSNavInfo()
print(navInfo.DataToList)

# ATE1
# OK
# AT
# OK

# SIM868 is ready
# ATE1
# OK
# AT
# OK

# Start GPS session...
# AT+CGNSPWR=1
# OK

# +CGNSPWR: 1

# AT+CGNSINF
# +CG



# AT+CGNSINF
# +CGNSINF: 1,0,20241201111750.000,,,,1.07,189.6,0,,,,,,8,0,4,,42,,

# OK

# GPS is not ready
# AT+CGNSINF
# +CGNSINF: 1,1,20241201111755.000,50.282724,18.680043,270.862,0.59,189.6,1,,2.5,2.6,0.9,,9,6,5,,43,,

# OK

# GPS info:
# AT+CGNSINF
# +CGNSINF: 
# 1,
# 1,
# 20241201111755.000,
# 50.282724,18.680043,
# 270.862,
# 0.59,
# 189.6,
# 1,
# ,
# 2.5,
# 2.6,
# 0.9,
# ,
# 9,
# 6,
# 5,
# ,
# 43
# ,
# ,

# OK
