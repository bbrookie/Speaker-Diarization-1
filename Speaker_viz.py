import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
#from gtk_pyplot import gtk_pyplot
from inference import infer_one_file
from AudioWave import AudioWave
import numpy as np
from matplotlib.figure import Figure
from numpy import arange, pi, random, linspace
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from GtkAudioWave import GtkAudioWave
from SpeakerDiarization import SpeakerDiarization
UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <separator />
      <menuitem action='FileOpen' />
      <menuitem action='FileQuit' />
    </menu>
    <menu action='Help'>
      <separator />
      <menuitem action='About' />
    </menu>
  </menubar>
</ui>
"""

class StartupWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Speaker Diarization")

        self.set_default_size(400, 400)

        action_group = Gtk.ActionGroup(name="my_actions")

        self.add_file_menu_actions(action_group)
        #self.add_edit_menu_actions(action_group)
        #self.add_choices_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(menubar, False, False, 0)

        #toolbar = uimanager.get_widget("/ToolBar")
        #box.pack_start(toolbar, False, False, 0)

        eventbox = Gtk.EventBox()
        eventbox.connect("button-press-event", self.on_button_press_event)
        box.pack_start(eventbox, True, True, 0)

        label = Gtk.Label(label="""""")
        label.set_markup("""<span foreground="#27A5CB"> <b> Welcome to our Speaker Diarization App. This App Implements the Google LSTM Diarization using Dvectors and \n Spectral Clustering.</b> </span>""")
        box.pack_start(label, False, False, 0)

        self.logo_label = Gtk.Label()
        icon = Gtk.Image().new_from_file('Images/logo.png')
        #self.logo_label.set_image(icon)
        box.pack_start(icon, False, False, 0)

        

        self.popup = uimanager.get_widget("/PopupMenu")

        self.add(box)

    def add_file_menu_actions(self, action_group):
        action_filemenu = Gtk.Action(name="FileMenu", label="File")
        action_group.add_action(action_filemenu)

        action_fileopen = Gtk.Action(name="FileOpen",  stock_id=Gtk.STOCK_OPEN)
        action_fileopen.connect("activate", self.on_menu_open_wav)
        action_group.add_action(action_fileopen)

        action_filequit = Gtk.Action(name="FileQuit", stock_id=Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

        Help_filemenu = Gtk.Action(name="Help", label="Help")
        action_group.add_action(Help_filemenu)

        action_About = Gtk.Action(name="About",  stock_id=Gtk.STOCK_ABOUT)
        action_About.connect("activate", self.on_menu_action_about)
        action_group.add_action(action_About)


    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def on_menu_file_quit(self, widget):
        Gtk.main_quit()

    def on_menu_action_about(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="About",
        )

        dialog.set_markup("""<span foreground="#2DAAF1"><b> This Application targets speaker diarization problem. It is built upon the Google LSTM Diarization system. For more info 
           Please visit our <a href = "https://github.com/Mahmoud-Selim/Speaker-Diarization.git"> GitHub Repository: </a> </b> </span>""")
        dialog.run()
        print("INFO dialog closed")

        dialog.destroy()
        
    def on_menu_open_wav(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            #print("Open clicked")
            print("File selected: " + dialog.get_filename())
            try:
                window = MainWindow(dialog.get_filename())
                window.connect("destroy", Gtk.main_quit)
                window.show_all()
            except:
                print("Error has occured")
            #self.main_quit()
            #Gtk.main()
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_wav = Gtk.FileFilter()
        filter_wav.set_name("Wav files")
        filter_wav.add_pattern("*.wav")
        dialog.add_filter(filter_wav)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def on_menu_others(self, widget):
        print("Menu item " + widget.get_name() + " was selected")

    def on_menu_choices_changed(self, widget, current):
        print(current.get_name() + " was selected.")

    def on_menu_choices_toggled(self, widget):
        if widget.get_active():
            print(widget.get_name() + " activated")
        else:
            print(widget.get_name() + " deactivated")

    def on_button_press_event(self, widget, event):
        # Check if right mouse button was preseed
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.popup.popup(None, None, None, None, event.button, event.time)
            return True  # event has been handled


class MainWindow(Gtk.Window):
    def __init__(self, file_name = "../test_3_16_mono.wav"):
        Gtk.Window.__init__(self, title="Speaker Diarization Viz")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        #self.resize(1280, 800)
        vseparator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vseparator.colors = Gdk.color_parse('black')
        #self.original_wave = GtkAudioWave("Original Sound Wave", "../testdr3_converted.wav").make_visualization().get_visualization()
        #vbox.pack_start(self.original_wave, True, True, 0)
        #vbox.pack_start(vseparator, True, True, 0)
        diarization = SpeakerDiarization(file_name)
        diarization_box = diarization.run_diarization()
        original_wave = diarization.combine_speakers_visualization()
        vbox.pack_start(original_wave, True, True, 0)
        diarization_box.set_size_request(-1, 400)
        vbox.pack_start(diarization_box, True, True, 0)


if __name__ == '__main__':
    window = StartupWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()