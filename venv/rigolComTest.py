import serial
import time


if __name__ == '__main__':
    print("Hi")


    try:
        comPort = serial.Serial('COM5', 9600, timeout=0.5, parity=serial.PARITY_NONE, write_timeout=0.5)

    except serial.SerialException as error:
        #print(comPort.port)
        #comPort.close()
        print(f"*het happend: {error}")
        exit(-1)


    try:
        while True:
            #str = bytes(input(),'ascii')

            str = input(">> ")

            print(str)

            comPort.write(bytes(str + '\r\n', 'ascii'))#'\r\n'
            # time.sleep(1)
            # out=b''
            # while comPort.inWaiting() > 0:
            #     out=out+comPort.read(1)
            #
            # if out != b'':
            #     print(out)


            comPort.flush()
            #comPort.
            print(comPort.readline())

    finally:
        comPort.close()

