#!/usr/bin/env python
# Simple iDevice GUI by Luke Bryan
# Based on:
# Libimobiledevice (http://www.libimobiledevice.org/), ifuse
# Python libimobiledevice examples, (https://github.com/upbit/python-imobiledevice_demo)
# and using the GPL Book2Pad transfer script. (https://github.com/rk700/book2pad)

from gi.repository import Gtk, GdkPixbuf, Gdk
import urllib
import os
import shutil
import subprocess
from threading import Thread
from subprocess import Popen, check_output
TARGET_TYPE_URI_LIST = 80

class GUIdeviceWindow():
	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file("MainWin.glade")
		#
		self.builder.connect_signals({
			'selectAppDoc' : self.onSelectRow,
			'iDeviceChanged': self.onDeviceChanged,
			'changeTab' : self.onChangeTab,
			'changeInfoTab' : self.onChangeInfoTab,
			'screenShot' : self.onScreenshot,
			'saveScreenshot': self.saveScreenshot
		})
		#self.appListStore = gtk.ListStore(str, gtk.gdk.Pixbuf)
		self.window = self.builder.get_object("mainwin")
		self.window.connect('drag_data_received', self.on_drag_data_received)
		self.window.drag_dest_set( Gtk.DestDefaults.MOTION|
						  Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,
						  [Gtk.TargetEntry.new("text/uri-list", 0, 80)], Gdk.DragAction.COPY)
		
		self.AppsListBox = self.builder.get_object("appsDocumentListBox")
		self.lastAppCount = 0
		self.sysLogging = False
		
	def setAppListing(self):
		import instproxy_browse_installed_app
		listing = instproxy_browse_installed_app.list_installed_app("User")
		if self.lastAppCount == len(listing):
			pass #no change?
		else:
			print "updating list"
			for item in self.AppsListBox.get_children():
				self.AppsListBox.remove(item)
			#list cleared, add:
			for app in listing:
				app_name = app["CFBundleName"].get_value().encode("utf8")
				#print "%s - %s %s" % (app["CFBundleIdentifier"], app_name, app["CFBundleVersion"])
				self.addApp( app["CFBundleIdentifier"], "%s %s" % (app_name, app["CFBundleVersion"]) )
			self.AppsListBox.show_all()
			self.lastAppCount = len(listing)
				
		
	def onDeviceChanged(self, fileChooser):
		iPadDir = self.get_file_path_from_dnd_dropped_uri( self.builder.get_object("filechooser").get_uri() )
		if iPadDir.find("/afc") > -1:
			print iPadDir
		else:
			self.msgBox("Please select an iPhone/iPad/iPod device.", Gtk.MessageType.WARNING)
	
	def onScreenshot(self, obj):
		self.screenshot()
		
	def saveScreenshot(self, obj):
		dialog = Gtk.FileChooserDialog("Please choose a file", self.window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		#TODO: Convert to other formats?
		filterTif = Gtk.FileFilter()
		filterTif.set_name("TIF Image")
		filterTif.add_mime_type("image/tiff")
		dialog.add_filter(filterTif)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			shutil.copy('/tmp/iosTmp.tif', dialog.get_filename())
		elif response == Gtk.ResponseType.CANCEL:
			print("Cancel clicked")
		dialog.destroy()
		
	def screenshot(self):
		if os.system('idevicescreenshot /tmp/iosTmp.tif') == 0:
			pix = GdkPixbuf.Pixbuf.new_from_file('/tmp/iosTmp.tif')
			pix = pix.scale_simple( pix.get_width()/4, pix.get_height()/4, GdkPixbuf.InterpType.BILINEAR)
			self.builder.get_object('screenshotImage').set_from_pixbuf(pix)
		else:
			self.msgBox('Failed to run idevicescreenshot')
			
	def msgBox(self, message, type=Gtk.MessageType.ERROR):
		messagedialog = Gtk.MessageDialog(parent=self.window,
		  flags=Gtk.DialogFlags.MODAL,
		  type=type,
		  buttons=Gtk.ButtonsType.OK,
		  message_format=message)
		messagedialog.run()
		messagedialog.destroy()
	
	def onChangeTab(self, notebook, contents, nth):
		if 1 == nth:
			try:
				self.setAppListing()
			except Exception, e:
				self.msgBox('Error:\n' + e.message)
		elif 2 == nth:
			self.screenshot()
		elif 3 == nth:
			self.showDeviceDetail()
			
	def onChangeInfoTab(self, notebook, contents, nth):
		#TODO syslog maybe?
		if 1 == nth and not self.sysLogging:
			proc = Popen(['idevicesyslog'],stdout=subprocess.PIPE)
			buffer = self.builder.get_object('sysLogTextView').get_buffer()
			while True:
				line = proc.stdout.readline()
				buffer.insert(buffer.get_end_iter(), line)
				
		
	def addApp(self, id, title ):
		row = AppHandlerRow(str(id), str(title)) #Gtk.ListBoxRow()
		self.AppsListBox.add(row)
	
	def onSelectRow(self, listBox, AppRow):
		AppRow.setup()
		
	def showDeviceDetail(self):
		info = check_output(['ideviceinfo'])
		self.builder.get_object('deviceInfoTextView').get_buffer().set_text(info)
		
	@staticmethod
	def get_file_path_from_dnd_dropped_uri(uri):
		# get the path to file
		path = ""
		if uri.startswith('file:\\\\\\'): # windows
			path = uri[8:] # 8 is len('file:///')
		elif uri.startswith('file://'): # nautilus, rox
			path = uri[7:] # 7 is len('file://')
		elif uri.startswith('file:'): # xffm
			path = uri[5:] # 5 is len('file:')

		path = urllib.url2pathname(path) # escape special chars
		path = path.strip('\r\n\x00') # remove \r\n and NULL

		return path

	def on_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):
		if target_type == TARGET_TYPE_URI_LIST:
			uri = selection.get_data().strip('\r\n\x00')
			self.builder.get_object('droppableLabel').set_text("Please wait...")
			#print 'uri', uri
			uri_splitted = uri.split() # we may have more than one file dropped
			url_splitted = [ self.get_file_path_from_dnd_dropped_uri(fixed) for fixed in uri_splitted ]
			#for uri in uri_splitted:
				#path = self.get_file_path_from_dnd_dropped_uri(uri)
				#print 'path to open', path
				#if os.path.isfile(path): # is it file?
					#data = file(path).read()
					#print data
			rawSelection = self.builder.get_object("filechooser").get_uri()
			if rawSelection:
				iPadDir = self.get_file_path_from_dnd_dropped_uri( rawSelection )
				print 'Transfer to: ' + iPadDir
				import book2pad
				book2pad.addbooks( iPadDir, url_splitted )
				self.builder.get_object('droppableLabel').set_text("Done!")
			else:
				self.msgBox('Please select the device to transfer to iBooks.')
			
#My own subclass of ListBoxRow to hold info about the particular app:
class AppHandlerRow(Gtk.ListBoxRow):
	ICONSIZE = Gtk.IconSize.BUTTON 
	
	def __init__(self, id, title):
		Gtk.ListBoxRow.__init__(self)
		self.id = id
		self.title = title
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
		self.add(hbox)
		hbox.pack_start(Gtk.Label( title, xalign=0), True, True, 10)
		self.icon = Gtk.Image.new_from_stock( Gtk.STOCK_CONNECT, self.ICONSIZE)
		hbox.pack_start(self.icon, False, False, 10)
		self.connected = False
		
	def setIcon(self):
		if self.connected:
			self.icon.set_from_stock(Gtk.STOCK_DISCONNECT, self.ICONSIZE)
		else:
			self.icon.set_from_stock(Gtk.STOCK_CONNECT, self.ICONSIZE)
	
	def setup(self):
		MOUNTS = '/tmp/iDeviceMount'	
		if not os.path.exists( MOUNTS ):
			os.mkdir( MOUNTS )
		mountdir = os.path.join( MOUNTS, self.id )
		
		if not self.connected: #connect:
			if not os.path.exists( mountdir ):
				os.mkdir( mountdir )
			cmd = "ifuse --documents " + self.id + " " + mountdir
		else:
			cmd = "fusermount -u " + mountdir + "; rmdir " + mountdir
		
		if os.system(cmd) == 0:
			print 'Success, switched'
			self.connected = not self.connected
			if self.connected:
				Popen(["xdg-open", mountdir])
			self.setIcon()
		else:
			print "FAIL with "+self.id
			self.icon.set_from_stock(Gtk.STOCK_DIALOG_ERROR, self.ICONSIZE)
			try:
				os.rmdir( mountdir )
			except OSError: #directory not empty
				pass
				


gui =GUIdeviceWindow()
gui.window.show_all()
Gtk.main()
