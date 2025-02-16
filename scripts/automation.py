#!/usr/local/bin/python -u

# Script (written in Python 2.7.15) to automate the configurations to show the screenshot on your
# default web browser.
# To get started, simply run : 'python ./automation.py'

import subprocess
import webbrowser
import argparse

from threading import Timer

adb = ['adb']

parser = argparse.ArgumentParser(
    description='Automation script to activate capturing screenshot of Android device')
parser.add_argument('-s', '--serial', dest='device_serial',
                    help='Device serial number (adb -s option)')
parser.add_argument('-p', '--port', dest='port', nargs='?', const=53516, type=int, default=53516,
                    help='Port number to be connected, by default it\'s 53516')
args_in = parser.parse_args()


def run_adb(args, pipeOutput=True):
    if(args_in.device_serial):
        args = adb + ['-s', args_in.device_serial] + args
    else:
        args = adb + args

    # print('exec cmd : %s' % args)
    out = None
    if (pipeOutput):
        out = subprocess.PIPE

    p = subprocess.Popen([str(arg)
                          for arg in args], stdout=out)
    stdout, stderr = p.communicate()
    return (p.returncode, stdout, stderr)


def locateApkPath():
    (rc, out, _) = run_adb(["shell", "pm",
                            "path",
                            "com.rayworks.droidcast"])
    if (rc):
        raise RuntimeError("Locating apk failure")

    prefix = "package:"
    postfix = ".apk"
    beg = out.index(prefix, 0)
    end = out.rfind(postfix)

    return "CLASSPATH=" + out[beg + len(prefix):(end + len(postfix))].strip()


def openBrowser():
    url = 'http://localhost:%d/screenshot' % args_in.port
    webbrowser.open_new(url)


def identifyDevice():

    (rc, out, _) = run_adb(["devices"])
    if(rc):
        raise RuntimeError("Fail to find devices")
    else:
        # Output as following:
        # List of devices attached
        # 6466eb0c	device
        print out
        device_serial_no = args_in.device_serial

        devicesInfo = str(out)
        deviceCnt = devicesInfo.count('device') - 1
        if(deviceCnt > 1 and (not device_serial_no)):
            raise RuntimeError(
                "Please specify the serial number of target device you want to use ('-s serial_number').")


def automate():
    try:
        identifyDevice()

        class_path = locateApkPath()

        (code, _, err) = run_adb(
            ["forward", "tcp:%d" % args_in.port, "tcp:%d" % args_in.port])
        print(">>> adb forward tcp:%d " % args_in.port, code)

        args = ["shell",
                class_path,
                "app_process",
                "/",  # unused
                "com.rayworks.droidcast.Main",
                "--port=%d" % args_in.port]

        # delay opening the web page
        t = Timer(2, openBrowser)
        t.start()

        # event loop starts
        run_adb(args, pipeOutput=False)

        (code, out, err) = run_adb(
            ["forward", "--remove", "tcp:%d" % args_in.port])
        print(">>> adb unforward tcp:%d " % args_in.port, code)

    except (Exception), e:
        print e


if __name__ == "__main__":
    automate()
