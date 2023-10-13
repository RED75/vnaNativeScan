import math
import threading

import serial
import time
import traceback

import matplotlib.pyplot as plt
import seaborn as sns

import VNARequestBuilder
sns.set()

# TODO: write interface for listener, and implement listener for data visualising

#     public static final int MODENUM_UNKNOWN = -1;
#     public static final int MODENUM_TRANSMISSION = 1;
#     public static final int MODENUM_REFLECTION = 2;
#     public static final int MODENUM_RSS1 = 3;
#     public static final int MODENUM_RSS2 = 4;
#     public static final int MODENUM_RSS3 = 5;
#     public static final int MODENUM_COMBI = 10;
#     public static final int MODENUM_TEST = 99;


class VNA():
    com_port_adr: str = ""
    __START_GEN_PREFIX: int = 2
    __START_ATTENUATION_SETTING: int = 3
    __DDS_TICKS_PER_MHZ: int = 8_259_595 #for pro2 8259595 # for pro 8_259_552
    __SCAN_MODES: dict[str, int] = {"TRAN": 1, "REFL": 2}

    __ADC_RESOLUTION_BITS: int = 8

    def __init__(self, com: str ):
        self.com_port_adr = com

    def __enter__(self):
        self.__init_comPort(self.com_port_adr)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.comPort.close()

    def __init_comPort(self, com: str ):
        try:
            self.comPort = serial.Serial(com, 115200, timeout=1, parity=serial.PARITY_NONE,
                                         write_timeout=1)  # , stopbits=serial.STOPBITS_ONE
        except serial.SerialException as ex:
            print("Something wrong with com port")
            traceback.print_exc()
            exit(-1)

    def _F_to_dds_ticks(self, F: int) -> int:
        return int(F / 1_000_000.0 * self.__DDS_TICKS_PER_MHZ)

    def _culc_attenuation(self, attenuation: int) -> int:
        # Math.pow(10.0, (60.2 - (double)att / 100.0) / 20.0)
        return math.pow(10, (60.2 - attenuation / 100.0) / 20.0)

    def _culc_phase(self, phase: float):
        return (phase / 100.0 / 180.0 * 8192.0)

    def start_generator(self, F1: int, F2: int, attenuation1: int = 1, attenuation2=1, phase: float = 0):
        # ddsF1:int = F1 / 1_000_000 * __DDS_TICKS_PER_MHZ
        # ddsF2: int = F2 / 1_000_000 * __DDS_TICKS_PER_MHZ
        self.comPort.reset_input_buffer()
        self.comPort.reset_output_buffer()
        self.comPort.write(bytes(f"{self.__START_GEN_PREFIX:.0f}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self._F_to_dds_ticks(F1)}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self._F_to_dds_ticks(F2)}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self._culc_attenuation(phase)}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self.__START_ATTENUATION_SETTING}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self._culc_attenuation(attenuation1):.0f}\r", "us-ascii"))
        self.comPort.write(bytes(f"{self._culc_attenuation(attenuation2):.0f}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{1022}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{1022}\r", "us-ascii"))
        # time.sleep(0.1)
        self.comPort.flush()

    def stop_generator(self):
        self.start_generator(0, 0, 0, 0, 0)

    def _get_records(self, F_start: int, F_stop: int, n_steps: int, timeout: float) -> list[float]:

        """
        read n_records records
        :param timeout: timeout for input steam afrer witch getting data will be finished
        :return:
        """

        start_function_time = time.time()
        F_step = (F_stop - F_start)/n_steps
        resultLosses = []

        for i in range(n_steps):
            start_time = time.time();
            while (time.time()-start_time)*1000<timeout:
                if (self.comPort.in_waiting >= 8):
                    buffer = self.comPort.read(8)
                    # p1 = (buffer[0] & 255) + (buffer[1] & 255) * 256
                    # p2 = (buffer[4] & 255) + (buffer[5] & 255) * 256
                    p1 = (buffer[0] ) + (buffer[1] ) * 256
                    p2 = (buffer[4] ) + (buffer[5] ) * 256
                    resultLosses.append((p2-p1)/2)
                    print(f"step #{i} F = {F_start+i*F_step:.1f} R={resultLosses[-1]:.1f}")
                    print(f"step #{i} F = {F_start + i * F_step:.1f} Buffer = {buffer.hex()}")
                    break
                else:
                    time.sleep(timeout/10.0/1000.0)
                    continue
            else:
                break
        print(f"reading InputStream finished. {len(resultLosses)} records recieved. It took {time.time() - start_function_time} seconds")
        #sns.scatterplot(resultLosses)

        plt.plot(resultLosses)
        plt.show()

    def _get_records_vna1300_native(self, F_start: int, F_stop: int, n_steps: int, timeout: float) -> list[float]:

        """
        read n_records records
        :param timeout: timeout for input steam afrer witch getting data will be finished
        :return:
        """
        start_function_time = time.time()
        F_step = (F_stop - F_start)/n_steps
        resultLosses = []

        for i in range(n_steps):
            start_time = time.time()
            while (time.time()-start_time)*1000<timeout:
                if (self.comPort.in_waiting >= 8*3):
                    buffer = self.comPort.read(8*3)
                    p1 = (buffer[0] & 255) + (buffer[1] & 255) * 256
                    p2 = (buffer[4] & 255) + (buffer[5] & 255) * 256

                    resultLosses.append((p2-p1)/2)
                    print(f"step #{i} F = {F_start+i*F_step:.1f} R={resultLosses[-1]:.1f}")
                    print(f"step #{i} F = {F_start+i*F_step:.1f} Buffer = {buffer.hex()}")
                    break
                else:
                    time.sleep(timeout/10.0/1000.0)
                    continue
            else:
                break
        print(f"reading InputStream finished. {len(resultLosses)} records recieved. It took {time.time() - start_function_time} seconds")
        #sns.scatterplot(resultLosses)

        plt.plot(resultLosses)
        plt.show()




    def scan(self, F_start: int, F_stop: int, n_steps: int, scan_mode: int, unknown: int):
        # print("scan_mode = {0}".format(scan_mode))

        step_dds: int = int(max(self._F_to_dds_ticks(F_stop - F_start) / n_steps, 1))
        print(f"step_dds={step_dds}")
        self.comPort.reset_input_buffer()
        self.comPort.reset_output_buffer()
        self.comPort.write(bytes(f"{scan_mode:d}\r", "us-ascii"))  # if (dib.isFixed6dBOnThru()) 20 else 0
        self.comPort.write(bytes(f"{self._F_to_dds_ticks(F_start)}\r", "us-ascii")) # send start frequency in dds ticks
        self.comPort.write(bytes(f"{unknown:d}\r", "us-ascii"))  # dont have a guess what is it needed for
        self.comPort.write(bytes(f"{n_steps:d}\r", "us-ascii"))  # n of steps
        self.comPort.write(bytes(f"{step_dds:d}\r", "us-ascii"))  # nomber of dds ticks per step
        self.comPort.flush()

        records = self._get_records(F_start, F_stop, n_steps, timeout=10000)

        #protocol of vna1300
        #40 06 (E8 03)->(n steps) 03 (01)->(n averages) 10 (00 80 96 98)->(f_start) 00 00 (00 00 00 01)->(step in hz) 00 00 00 00 00 00 00
        #10000000 1000 0 10001000


        # self.comPort.write(bytes(f"{self._F_to_dds_ticks(step):.0f}\r", "us-ascii"))#frequency step

        # self.comPort.write(bytes(f"{self._F_to_dds_ticks()}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{self._culc_attenuation(phase)}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{self.__START_ATTENUATION_SETTING}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{self._culc_attenuation(attenuation1):.0f}\r", "us-ascii"))
        # self.comPort.write(bytes(f"{self._culc_attenuation(attenuation2):.0f}\r", "us-ascii"))

        #     public static final int MODENUM_UNKNOWN = -1;
        #     public static final int MODENUM_TRANSMISSION = 1;
        #     public static final int MODENUM_REFLECTION = 2;
        #     public static final int MODENUM_RSS1 = 3;
        #     public static final int MODENUM_RSS2 = 4;
        #     public static final int MODENUM_RSS3 = 5;
        #     public static final int MODENUM_COMBI = 10;
        #     public static final int MODENUM_TEST = 99;

    def scanPro2(self, F_start: int, F_stop: int, n_steps: int, scan_mode: int, unknown: int):
        # print("scan_mode = {0}".format(scan_mode))

        step_dds: int = int(max(self._F_to_dds_ticks(F_stop - F_start) / n_steps, 1))
        print(f"step_dds={step_dds}")
        self.comPort.reset_input_buffer()
        self.comPort.reset_output_buffer()
        self.comPort.write(bytes(f"{scan_mode:d}\r", "us-ascii"))  # if (dib.isFixed6dBOnThru()) 20 else 0
        self.comPort.write(bytes(f"{self._F_to_dds_ticks(F_start)}\r", "us-ascii")) # send start frequency in dds ticks
        self.comPort.write(bytes(f"{unknown:d}\r", "us-ascii")) #SampleRate # dont have a guess what is it needed for
        self.comPort.write(bytes(f"{n_steps:d}\r", "us-ascii"))  # n of steps
        self.comPort.write(bytes(f"{step_dds:d}\r", "us-ascii"))  # nomber of dds ticks per step
        self.comPort.flush()

        records = self._get_records(F_start, F_stop, n_steps, timeout=10000)

    def scanPro2Native(self, F_start: int = 10_000_000, F_stop: int = 10_001_000, n_steps: int = 1000, averages: int = 15):
        """
        scan mini vna pro 1300 using native byte protocol for setting scaning parametres
        :return:
        """
        self.comPort.reset_input_buffer()
        self.comPort.reset_output_buffer()

        # base_template1 = bytearray.fromhex("40 06 e8 03 03 0f 10 00 80 96 98 00 00 00 00 00 01 00 00 00 00 00 00 00")
        # self.comPort.write(base_template1)

        vna_request_builder = VNARequestBuilder.VNARequestBuilder(F_start, F_stop, n_steps, averages)
        print(vna_request_builder.get_codes())
        self.comPort.write(vna_request_builder.get_codes())


        self.comPort.flush()
        records = self._get_records_vna1300_native(F_start, F_stop, n_steps, timeout=1000)
        #records = self._get_records(F_start, F_stop, n_steps*3, timeout=1000)



if __name__ == '__main__':
    with VNA(com="COM3") as vna:
        vna.scanPro2Native(F_start= 9_999_500, F_stop = 10_001_500, n_steps = 1000, averages = 16)
        #vna.scan(F_start=9_999_500, F_stop=10_000_500, n_steps=500, scan_mode=0, unknown=-10)# working 0,20, 1 but with timeout=10000
        #vna.scan(F_start=9_999_500, F_stop=10_000_500, n_steps=1000, scan_mode=20, unknown=0)  # working 0,100

        # vna.start_generator(10_000_000,10_000_000)
        # time.sleep(2)
        # vna.stop_generator()

if __name__ != '__main__':
    print("Hi")

    try:
        comPort = serial.Serial('COM3', 115200, timeout=1, parity=serial.PARITY_NONE,
                                write_timeout=1)  # , stopbits=serial.STOPBITS_ONE

    except serial.SerialException as error:
        # print(comPort.port)
        # comPort.close()
        print(f"*het happend: {error}")
        exit(-1)

    try:
        while True:
            if str == "": comPort.flush()

            # print(str)
            for i in range(10_000_000, 10_100_000, 100):
                value = i / 1_000_000.0 * 8259552
                print(i, f"{value:.0f}\r")
                comPort.write(bytes(f"{2:.0f}\r", "us-ascii"))
                comPort.write(bytes(f"{value:.0f}\r", "us-ascii"))
                comPort.write(bytes(f"{value:.0f}\r", "us-ascii"))
                comPort.write(bytes(f"{0}\r", "us-ascii"))
                comPort.write(bytes(f"{3}\r", "us-ascii"))
                comPort.write(bytes(f"{1022}\r", "us-ascii"))
                comPort.write(bytes(f"{1022}\r", "us-ascii"))

                time.sleep(1)
                comPort.flush()
    finally:
        comPort.close()
