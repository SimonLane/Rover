# Introduction

This is a Linux port of [Simon Lane's](https://github.com/SimonLane) original "Dr Raman" scripts to linux. Its not much of a port... most of the effort was spent figuring out how to install all the required dependencies. In the end the Mamba distribution and package manager did the trick, having gone down many rabit holes using raw Python and PyEnv...

Using Python 3.10.12:
```
Python 3.10.12 | packaged by conda-forge | (main, Jun 23 2023, 22:28:59) [GCC 12.3.0] on linux
```

# Installing Mamba
Open a terminal windows and type the following, accepting the license and following the on-screen instructions.

```
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-aarch64.sh
chmod +x Mambaforge-Linux-aarch64.sh
./Mambaforge-Linux-aarch64.sh
```

Once the install has completed you can delete the install script like so:

```
rm ./Mambaforge-Linux-aarch64.sh
```


# Setting Up The Mamba Environment

A Mamba environment, is any Python "environment" aims to sandbox your system so that packages you install in one environment do not invalidate/trouble/etc packages installed in another environment.

To create an environment for the Dr Raman script type the following:

```
mamba env create -f ./environment_linux_rock.yml
```

## Patching The `ctypes` Module

In my installation the `ctypes` module was not able to find libusb because of the way it searched for libraries. It ended trying the load a Mamba env directory asif it was a `.so` (library). To fix this you will have to modify `\_findLib\_prefix()` in `${HOME}/mambaforge/envs/drramin/lib/python3.10/ctypes/util.py` so that it not only checks that the DLL path it is detecting exists, but also that it is specifically a file and not a directory.

For the Rock Pi 4 you are looking for the branch `elif os.name == "posix":` and within that branch the final `else` clause where no `sys.platform` has matched.

```
def _findLib_prefix(name):
    if not name:
        return None
    for fullname in (name, "lib%s.so" % (name)):
        path = os.path.join(sys.prefix, 'lib', fullname)
        print("fullname = {}".format(fullname))
        if os.path.exists(path) and os.path.isfile(path):
#                               ^^^^^^^^^^^^^^^^^^^^^^^^^
#                               ADD THIS BIT
            print("Returning {}".format(path))
            return path
    return None
```

## Create UDev Rule To Get Permissions To Read Spectrometer USB
Disconnect the spectrometer if connected.

Create the following udev rule file:

```
sudo echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="24aa", ATTRS{idProduct}=="4000", GROUP="users", MODE="0666"' > /etc/udev/rules.d/wasatch.rules
```

Then reload:

```
sudo udevadm control --reload 
```

Connect the spectrometer


# Running the script
Type

```
mamba activate drramin
```

Then run the script as you would usually.
 
