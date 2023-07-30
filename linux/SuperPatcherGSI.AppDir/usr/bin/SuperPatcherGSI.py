python
import argparse
import os
import shutil
import pathlib

TempDIR = os.getcwd() + "/" + "tmp"
HERE = os.path.realpath(os.path.dirname(__file__))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-i' , '--input' , type=argparse.FileType('r') , help='''input the super.img that is going to be modifed, if super.img is sparse its going to temporarily be unsparsed''')
parser.add_argument('-o' , '--output', help="Directs the output to a name of your choice")
parser.add_argument('-s' , '--SLOT' , type=int , help="number of slots on the device can only be 1 (A) or 2 (A/B)")
args = parser.parse_args()

# err check
def check():
    err = ""
    try:
        if args.SLOT == 1 or args.SLOT == 2:
            pass
        else:
            print("Invalid Slot number ({slot})".format(slot=args.SLOT))
            err += " &SLOT"
        if args.input.name.endswith(".img"):
            pass
        else:
            print("Invalid Format at INPUT please use .img file")
            err += " &InvalidFormatINPUT"
        if args.output.endswith(".img"):
            pass
        else:
            print("Invalid Format at INPUT please use .img file")
            err += " &InvalidFormatOUTPUT"
        if err == "":
            err = "OK"
    except ValueError:
        err = "Flag ValueError"
    except AttributeError:
        err = "Flag AttributeError"
    return err

# unpack / replacing

def lpunpack():
    os.system("python3 {dir}/lpunpack.py {superimg} {tempdir}".format(superimg=args.input.name, tempdir=TempDIR , dir=HERE))

def IMGchoose(): # choose an img file to be replaced
    TempImgList = os.listdir(TempDIR)
    i = 0
    for img in TempImgList:
        if img.endswith(".img"):
            print("option number " + str(i) + " " + TempImgList[i] + " size of (" + str(os.path.getsize(TempDIR + "/" + img)) + ") bytes")
        i += 1
    while (True):
        try:
            imgnum = input("Please Choose: ")
            if int(imgnum) <= i - 1:
                while (True):
                    try:
                        replacmentpath = input("Please Input Path To Replacment Partition:\n")
                        replacmentpath = str(pathlib.Path(replacmentpath).absolute())
                        if replacmentpath.endswith(".img"):
                            brk = input("Are you sure this is the path to file (Y/n): ")
                            if brk == "Y" or brk == "y" or brk == "yes" or brk == "Yes" or brk == "": # just making sure
                                break
                        elif replacmentpath.endswith(" "):  # sometimes people tap space it ruins it and it can and will get confusing
                            print("Path Ends With Space!!")
                        else:
                            print("Please Input a Valid Path to a IMG File!")
                    except ValueError:
                        print("Please Input a Valid Path!")
                    except AttributeError:
                        print("How did you even manage to get AttributeError, this is here just incase !?")
                shutil.copy(replacmentpath , TempDIR + "/" + TempImgList[int(imgnum)])
                redo = input("Img replaced!\nreplace another (Y/n): ")
                if redo == "Y" or redo == "y" or redo == "yes" or redo == "Yes": # just making sure
                    IMGchoose()
                break
            else:
                print("Please Put a Valid Number!")
        except ValueError:
            print("Please Put a Number In!")

def IMGsizeCALC(): # calculate size
    totalsize = 512000000 # extra overhead of 0.5G
    TempImgList = os.listdir(TempDIR)
    i = 0
    for img in TempImgList:
        if img.endswith(".img"):
            totalsize += os.path.getsize(TempDIR + "/" + img)
        i += 1
    reminder = totalsize % 512 # making devision by 512
    totalsize += reminder
    return totalsize

# lpmake
def lpmake(devicesize , metadatasize):
    lpmake_args = " --device-size={devicesize}".format(devicesize=devicesize) + " --metadata-slots={slot}".format(slot=args.SLOT) + " --output {output}".format(output=args.output) + " --metadata-size {metadatasize}".format(metadatasize=metadatasize)
    sparse = input("make sparse (flashable with fastboot) ? (Y/n): ")
    if sparse == "Y" or sparse == "y" or sparse == "yes" or sparse == "Yes" or sparse == "": # just making sure
        lpmake_args += " --sparse"
    
    lpmake_args = lpmake_add_args(lpmake_args)
    print("============================")
    print("    using these flags:")
    print("============================")
    print(lpmake_args)
    print("============================")
    
    return os.system("{dir}/bin/lpmake {lpargs}".format(lpargs=lpmake_args , dir=HERE))

def lpmake_add_args(lpmake_args):
    TempImgList = os.listdir(TempDIR)
    for img in TempImgList:
        if img.endswith(".img"):
            lpmake_args += " --partition={name}:none:{size}".format(name=os.path.splitext(img)[0] , size=os.path.getsize(TempDIR + "/" + img))
            if os.path.getsize(TempDIR + "/" + img) != 0:
                lpmake_args += " --image={name}={filedir}".format(name=os.path.splitext(img)[0] , filedir=(TempDIR + "/" + img))
    return lpmake_args

def testdvi512(num):
    if num % 512 == 0:
        return True
    else:
        return False

def main():
    err = check()

    if err != "OK":
        print("error code ({error}) exiting...!".format(error=err))
        return err
    else:
        print("flags successfully verified and appear to be correct, error code ({error})".format(error=err))
    
    print("============================")
    print("        unpacking...")
    print("============================")
    lpunpack()
    print("============================")
    print("  choose img to replace ")
    print("============================")
    
    
    IMGchoose() # replaces selcted partition with GSI
    #let user choose size
    metadatasize = 512000
    devicesize = IMGsizeCALC()
    print("============================")
    try:
        dvsize = input("device size (super.img size) in bytes must be evenly divisible by 512, defualt ({devicesize}) bytes: ".format(devicesize=devicesize))
        if dvsize != "" and testdvi512(int(dvsize)):
            devicesize = int(dvsize)
    except ValueError:
        print("Invalid Number skipping ..!")
    
    try:
        mdsize = input("metadata size in bytes must be evenly divisible by 512 defualt=~0.5KiB: ")
        if mdsize != "" and testdvi512(int(dvsize)):
            metadatasize = int(mdsize)
    except ValueError:
        print("Invalid Number skipping ..!")
    
    #repack
    lperr = lpmake(devicesize , metadatasize)
    err = lperr if lperr != 0 else err # give lpmake error as external code if there was an error
    print("============================")
    print("        cleaning...")
    print("============================")
    shutil.rmtree(TempDIR) # clean tmp dir
    return err # return err code to external

err = main()
exit(err)
