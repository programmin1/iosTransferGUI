# iosTransferGUI
Simple GTK GUI program to transfer books to iPad, share files to/from compatible apps, and screenshot iDevices. Tested on Ubuntu with libimobiledevice 1.2.

This simple application builds upon the work of [Book2Pad](https://github.com/rk700/book2pad), [Ifuse](https://github.com/libimobiledevice/ifuse) and [Libimobiledevice](http://www.libimobiledevice.org/) and their Python bindings (Thanks Zhou Hao for the [examples](https://github.com/upbit/python-imobiledevice_demo)).

# Setup
* Libimobiledevice >= 1.2 is required to connect with recent versions of iOS.
* [Ifuse](https://github.com/libimobiledevice/ifuse) >= 1.1.3 is required for app itunes-file-sharing support with --documents.
* Python-plist and Python-imobiledevice packages should be installed.

# Features
* Drag and drop books to iBooks
* Mount itunes-file-sharing-compatible apps to transfer files to/from device.
* Screenshot and save tif image file.
* View device details.

# Usage
* Download with the "Download Zip" link, or git checkout the repository.
* Run TransferGUI.py
