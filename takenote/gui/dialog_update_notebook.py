"""

    TakeNote
    Update notebook dialog

"""

# python imports
import os, sys, threading, time, traceback, shutil


# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk.glade
import gobject

# takenote imports
import takenote
from takenote.gui import dialog_wait
from takenote import tasklib
from takenote import notebook_update
from takenote import notebook as notebooklib
from takenote.gui import get_resource



class UpdateNoteBookDialog (object):
    """Updates a notebook"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.app = main_window.app

    
    def show(self, notebook_filename):

        self.xml = gtk.glade.XML(get_resource("rc", "takenote.glade"),
                                 "update_notebook_dialog")
        self.dialog = self.xml.get_widget("update_notebook_dialog")
        self.xml.signal_autoconnect(self)
        self.dialog.connect("close", lambda w:
                            self.dialog.response(gtk.RESPONSE_CANCEL))
        self.dialog.set_transient_for(self.main_window)
        
        self.text = self.xml.get_widget("update_message_label")
        self.saved = self.xml.get_widget("save_backup_check")

        
        #self.text.set_text(message)

        ret = False
        response = self.dialog.run()
        
        if response == gtk.RESPONSE_OK:

            # do backup
            if self.saved.get_active():
                while not self.backup(notebook_filename): pass

            # do update
            def func(task):
                notebook_update.update_notebook(
                    notebook_filename,
                    notebooklib.NOTEBOOK_FORMAT_VERSION)
                    
            task = tasklib.Task(func)
            dialog2 = dialog_wait.WaitDialog(self.main_window)
            dialog2.show("Updating Notebook",
                         "Updating notebook...",
                         task)

            ret = not task.aborted()
            ty, err, tb =  task.exc_info()
            if err:
                self.main_window.error("Error while updating", err, tb)
                ret = False
        
        self.dialog.destroy()

        if ret:
            dialog = gtk.MessageDialog(self.main_window, 
            flags= gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            type=gtk.MESSAGE_INFO, 
            buttons=gtk.BUTTONS_OK, 
            message_format="Notebook updated successfully")
            dialog.set_title("Notebook Update Complete")
            dialog.run()
            dialog.destroy()


        return ret


    def backup(self, notebook_filename):
        dialog = gtk.FileChooserDialog("Choose Backup Notebook Name",
            self.main_window, 
            action=gtk.FILE_CHOOSER_ACTION_SAVE, #CREATE_FOLDER,
            buttons=("Cancel", gtk.RESPONSE_CANCEL,
                     "Backup", gtk.RESPONSE_OK))
        dialog.set_current_folder(self.app.pref.new_notebook_path)
        
        response = dialog.run()
        
        new_filename = dialog.get_filename()
        dialog.destroy()

        
        if response == gtk.RESPONSE_OK:
            def func(task):
                shutil.copytree(notebook_filename, new_filename)
            task = tasklib.Task(func)
            dialog2 = dialog_wait.WaitDialog(self.dialog)
            dialog2.show("Backing Up Notebook",
                         "Backing up old notebook...",
                         task)

            # handle errors
            if task.aborted():
                ty, err, tb = task.exc_info()
                if err:
                    self.main_window.error("Error occurred during backup", err, tb)
                else:
                    self.main_window.error("Backup canceled")
                return False
            
        return True
                       


        
            

