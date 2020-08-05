from tkinter import *
from tkinter import ttk
from tkinter.tix import *
from tkintertable import TableCanvas, TableModel
import nimodinst
import niscope
import warnings
import matplotlib
import sys
import time
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

class NIScopeSFP():
    def __init__(self):
        # Basic Vars
        self.blocked = True
        self.tempcounter = 0
        self.meas_array = ["NO_MEASUREMENT"]
        self.dev_name = ""
    
        self.root = Tk()
        self.root.title("NI-SCOPE Measurement Library DEMO")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.scrollwin = ScrolledWindow(self.root)
        self.scrollwin.grid(column=0, row=0)
        self.win = self.scrollwin.window
        self.mainframe = ttk.Frame(self.win)
        self.mainframe.grid(column=0, row=0)
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        
        ### CONFIG FRAME
        self.config_frame = ttk.Frame(self.mainframe, borderwidth=5, height=200, width=400, relief="solid")
        self.config_frame.grid(column=0, row=0, columnspan=6, rowspan=6, sticky=(N, S, E, W))
        self.config_frame.columnconfigure(0, weight=1)
        self.config_frame.rowconfigure(0, weight=1)
        
        self.label_device = ttk.Label(self.config_frame, text="Current Device")
        self.label_device.grid(column=0, row=0, sticky=(W))
        self.curr_device = StringVar()
        self.device_select = ttk.Combobox(self.config_frame, textvariable=self.curr_device)
        self.device_select["values"] = self._get_devices()
        self.device_select.insert(0, self._get_devices()[0])
        self.device_select.grid(column=0, row=1, sticky=(W))
        
        self.label_channels = ttk.Label(self.config_frame, text="Current Channel(s)")
        self.label_channels.grid(column=0, row=2, sticky=(W))
        self.curr_channel = StringVar()
        self.channel_select = ttk.Entry(self.config_frame, textvariable=self.curr_channel)
        self.channel_select.grid(column=0, row=3, sticky=(W))
        self.channel_select.insert(0, 0)
        
        self.label_min_sample_rate = ttk.Label(self.config_frame, text="Min Sample Rate")
        self.label_min_sample_rate.grid(column=1, row=0, sticky=(N, W))
        self.curr_min_sample_rate = Spinbox(self.config_frame, from_=0, to=sys.maxsize)
        self.curr_min_sample_rate.grid(column=1, row=1, sticky=(W))
        self.curr_min_sample_rate.insert(0, 100000)
        
        self.label_min_record_length = ttk.Label(self.config_frame, text="Min Record Length")
        self.label_min_record_length.grid(column=1, row=2, sticky=(W))
        self.curr_min_record_length = Spinbox(self.config_frame, from_=1, to=sys.maxsize)
        self.curr_min_record_length.grid(column=1, row=3, sticky=(W))
        self.curr_min_record_length.insert(1, "000")
        
        self.label_vertical_range = ttk.Label(self.config_frame, text="Vertical Range (V)")
        self.label_vertical_range.grid(column=2, row=0, sticky=(N, W))
        self.curr_vertical_range = Spinbox(self.config_frame, from_=0, to=sys.maxsize)
        self.curr_vertical_range.grid(column=2, row=1, sticky=(W))
        self.curr_vertical_range.delete(0)
        self.curr_vertical_range.insert(0, 1)
        
        self.label_vertical_offset = ttk.Label(self.config_frame, text="Vertical Offset (V)")
        self.label_vertical_offset.grid(column=2, row=2, sticky=(W))
        self.curr_vertical_offset = Spinbox(self.config_frame, from_=0, to=sys.maxsize)
        self.curr_vertical_offset.grid(column=2, row=3, sticky=(W))
        
        self.label_probe_attenuation = ttk.Label(self.config_frame, text="Probe Attenuation")
        self.label_probe_attenuation.grid(column=1, row=4, sticky=(W))
        self.curr_probe_attenuation = Spinbox(self.config_frame, from_=0, to=sys.maxsize)
        self.curr_probe_attenuation.grid(column=1, row=5, sticky=(W))
        self.curr_probe_attenuation.delete(0)
        self.curr_probe_attenuation.insert(0, 1)
        
        self.label_vertical_coupling = ttk.Label(self.config_frame, text="Vertical Coupling")
        self.label_vertical_coupling.grid(column=2, row=4, sticky=(W))
        self.vertical_coupling = StringVar()
        self.curr_vertical_coupling = ttk.Combobox(self.config_frame, textvariable=self.vertical_coupling)
        self.curr_vertical_coupling.grid(column=2, row=5, sticky=(W))
        self.curr_vertical_coupling["values"] = ("AC", "DC", "Ground")
        self.curr_vertical_coupling.insert(0, "AC")
        self.curr_vertical_coupling.config(state="readonly")
        
        self.self_cal_button = ttk.Button(self.config_frame, text="Self Calibration (slow)", command=self.self_cal)
        self.self_cal_button.grid(column=5, row=0, sticky=(N, E))
        self.start_stop_button = ttk.Button(self.config_frame, text="Run", command=self.start)
        self.start_stop_button.grid(column=4, row=0, sticky=(N, W))
        self.error_frame = ttk.Frame(self.config_frame, borderwidth=5, relief="sunken")
        self.error_frame.grid(column=4, row=1, columnspan=2, rowspan=5, sticky=(E))
        self.label_error_text = Text(self.error_frame, width=40, height=10, wrap=WORD)
        self.label_error_text.grid(column=4, row=2)
        self.update_settings_button = ttk.Button(self.config_frame, text="Update Configuration", command=self.update_config)
        self.update_settings_button.grid(column=0, row=5, columnspan=2, sticky=(W))
        
        #TODO: make update button actually do shit + error_text return.
        
        ### ACTIVE FRAME
        self.active_frame = ttk.Frame(self.mainframe, borderwidth=5, height=200, width=400, relief="solid")
        self.active_frame.grid(column=0, row=6, columnspan=6, rowspan=3, sticky=(N, S, E, W))
        self.trigger_notebook = ttk.Notebook(self.active_frame)
        self.trigger_notebook.grid(column=0, row=6, columnspan=2, rowspan=5, sticky=(N, S, E, W))
        self.digital_trigger = ttk.Frame(self.trigger_notebook)
        self.edge_trigger = ttk.Frame(self.trigger_notebook)
        self.hysteresis_trigger = ttk.Frame(self.trigger_notebook)
        self.immediate_trigger = ttk.Frame(self.trigger_notebook)
        self.window_trigger = ttk.Frame(self.trigger_notebook)
        self.trigger_notebook.add(self.digital_trigger, text="Digital")
        self.trigger_notebook.add(self.edge_trigger, text="Edge")
        self.trigger_notebook.add(self.hysteresis_trigger, text="Hysteresis")
        self.trigger_notebook.add(self.immediate_trigger, text="Immediate")
        self.trigger_notebook.add(self.window_trigger, text="Window")
        self.update_trigger_settings_button = ttk.Button(self.active_frame, text="Update Trigger Settings", command=self.update_trigger)
        self.update_trigger_settings_button.grid(column=0, row=11, sticky=(N, W))
        
        # Digital Trigger
        self.label_digital_trigger_source = ttk.Label(self.digital_trigger, text="Trigger Source")
        self.label_digital_trigger_source.grid(column=0, row=6, sticky=(E))
        self.digital_trigger_source = StringVar()
        self.curr_digital_trigger_source = ttk.Entry(self.digital_trigger, textvariable=self.digital_trigger_source)
        self.curr_digital_trigger_source.grid(column=1, row=6, sticky=(W))
        self.curr_digital_trigger_source.insert(0, "PXI_Trig0")
        self.label_digital_trigger_slope = ttk.Label(self.digital_trigger, text="Trigger Slope")
        self.label_digital_trigger_slope.grid(column=0, row=7, sticky=(E))
        self.digital_trigger_slope = StringVar()
        self.curr_digital_trigger_slope = ttk.Combobox(self.digital_trigger, textvariable=self.digital_trigger_slope)
        self.curr_digital_trigger_slope.grid(column=1, row=7, sticky=(W))
        self.curr_digital_trigger_slope["values"] = ("Positive", "Negative")
        self.curr_digital_trigger_slope.insert(0, "Positive")
        self.curr_digital_trigger_slope.config(state="readonly")
        
        # Edge Trigger
        self.label_edge_trigger_source = ttk.Label(self.edge_trigger, text="Trigger Source")
        self.label_edge_trigger_source.grid(column=0, row=6, sticky=(E))
        self.edge_trigger_source = StringVar()
        self.curr_edge_trigger_source = ttk.Entry(self.edge_trigger, textvariable=self.edge_trigger_source)
        self.curr_edge_trigger_source.grid(column=1, row=6, sticky=(W))
        self.curr_edge_trigger_source.insert(0, "0")
        self.label_edge_trigger_level = ttk.Label(self.edge_trigger, text="Trigger Level")
        self.label_edge_trigger_level.grid(column=0, row=7, sticky=(E))
        self.curr_edge_trigger_level = Spinbox(self.edge_trigger, from_=0, to=sys.maxsize)
        self.curr_edge_trigger_level.grid(column=1, row=7, sticky=(W))
        self.label_edge_trigger_slope = ttk.Label(self.edge_trigger, text="Trigger Slope")
        self.label_edge_trigger_slope.grid(column=0, row=8, sticky=(E))
        self.edge_trigger_slope = StringVar()
        self.curr_edge_trigger_slope = ttk.Combobox(self.edge_trigger, textvariable=self.edge_trigger_slope)
        self.curr_edge_trigger_slope.grid(column=1, row=8, sticky=(W))
        self.curr_edge_trigger_slope["values"] = ("Positive", "Negative")
        self.curr_edge_trigger_slope.insert(0, "Positive")
        self.curr_edge_trigger_slope.config(state="readonly")
        self.label_edge_trigger_coupling = ttk.Label(self.edge_trigger, text="Trigger Coupling")
        self.label_edge_trigger_coupling.grid(column=0, row=9, sticky=(E))
        self.edge_trigger_coupling = StringVar()
        self.curr_edge_trigger_coupling = ttk.Combobox(self.edge_trigger, textvariable=self.edge_trigger_coupling)
        self.curr_edge_trigger_coupling.grid(column=1, row=9, sticky=(W))
        self.curr_edge_trigger_coupling["values"] = ("AC", "DC", "HF_REJECT", "LF_REJECT", "AC_PLUS_HF_REJECT")
        self.curr_edge_trigger_coupling.insert(0, "AC")
        self.curr_edge_trigger_coupling.config(state="readonly")
        
        # Hysteresis Trigger
        self.label_hysteresis_trigger_source = ttk.Label(self.hysteresis_trigger, text="Trigger Source")
        self.label_hysteresis_trigger_source.grid(column=0, row=6, sticky=(E))
        self.hysteresis_trigger_source = StringVar()
        self.curr_hysteresis_trigger_source = ttk.Entry(self.hysteresis_trigger, textvariable=self.hysteresis_trigger_source)
        self.curr_hysteresis_trigger_source.grid(column=1, row=6, sticky=(W))
        self.curr_hysteresis_trigger_source.insert(0, "0")
        self.label_hysteresis_trigger_level = ttk.Label(self.hysteresis_trigger, text="Trigger Level")
        self.label_hysteresis_trigger_level.grid(column=0, row=7, sticky=(E))
        self.curr_hysteresis_trigger_level = Spinbox(self.hysteresis_trigger, from_=0, to=sys.maxsize)
        self.curr_hysteresis_trigger_level.grid(column=1, row=7, sticky=(W))
        self.label_hysteresis = ttk.Label(self.hysteresis_trigger, text="Hysteresis")
        self.label_hysteresis.grid(column=0, row=8, sticky=(E))
        self.curr_hysteresis = Spinbox(self.hysteresis_trigger, from_=0, to=sys.maxsize)
        self.curr_hysteresis.grid(column=1, row=8, sticky=(W))
        self.label_hysteresis_trigger_slope = ttk.Label(self.hysteresis_trigger, text="Trigger Slope")
        self.label_hysteresis_trigger_slope.grid(column=0, row=9, sticky=(E))
        self.hysteresis_trigger_slope = StringVar()
        self.curr_hysteresis_trigger_slope = ttk.Combobox(self.hysteresis_trigger, textvariable=self.hysteresis_trigger_slope)
        self.curr_hysteresis_trigger_slope.grid(column=1, row=9, sticky=(W))
        self.curr_hysteresis_trigger_slope["values"] = ("Positive", "Negative")
        self.curr_hysteresis_trigger_slope.insert(0, "Positive")
        self.curr_hysteresis_trigger_slope.config(state="readonly")
        self.label_hysteresis_trigger_coupling = ttk.Label(self.hysteresis_trigger, text="Trigger Coupling")
        self.label_hysteresis_trigger_coupling.grid(column=0, row=10, sticky=(E))
        self.hysteresis_trigger_coupling = StringVar()
        self.curr_hysteresis_trigger_coupling = ttk.Combobox(self.hysteresis_trigger, textvariable=self.hysteresis_trigger_coupling)
        self.curr_hysteresis_trigger_coupling.grid(column=1, row=10, sticky=(W))
        self.curr_hysteresis_trigger_coupling["values"] = ("AC", "DC", "HF_REJECT", "LF_REJECT", "AC_PLUS_HF_REJECT")
        self.curr_hysteresis_trigger_coupling.insert(0, "AC")
        self.curr_hysteresis_trigger_coupling.config(state="readonly")
        
        # Immediate Trigger
        self.label_immediate_trigger = ttk.Label(self.immediate_trigger, text="N/A")
        self.label_immediate_trigger.grid(column=0, row=6, sticky=(N))
        
        # Window Trigger
        self.label_window_trigger_source = ttk.Label(self.window_trigger, text="Trigger Source")
        self.label_window_trigger_source.grid(column=0, row=6, sticky=(E))
        self.window_trigger_source = StringVar()
        self.curr_window_trigger_source = ttk.Entry(self.window_trigger, textvariable=self.window_trigger_source)
        self.curr_window_trigger_source.grid(column=1, row=6, sticky=(W))
        self.curr_window_trigger_source.insert(0, "0")
        self.label_window_mode = ttk.Label(self.window_trigger, text="Window Mode")
        self.label_window_mode.grid(column=0, row=7, sticky=(E))
        self.window_mode = StringVar()
        self.curr_window_mode = ttk.Combobox(self.window_trigger, textvariable=self.window_mode)
        self.curr_window_mode.grid(column=1, row=7, sticky=(W))
        self.curr_window_mode["values"] = ("Entering", "Leaving")
        self.curr_window_mode.insert(0, "Entering")
        self.curr_window_mode.config(state="readonly")
        self.label_window_low_level = ttk.Label(self.window_trigger, text="Window Low Level")
        self.label_window_low_level.grid(column=0, row=8, sticky=(E))
        self.curr_window_low_level = Spinbox(self.window_trigger, from_=-sys.maxsize, to=sys.maxsize)
        self.curr_window_low_level.grid(column=1, row=8, sticky=(W))
        self.curr_window_low_level.delete(0, "end")
        self.curr_window_low_level.insert(0, 0)
        self.label_window_high_level = ttk.Label(self.window_trigger, text="Window High Level")
        self.label_window_high_level.grid(column=0, row=9, sticky=(E))
        self.curr_window_high_level = Spinbox(self.window_trigger, from_=-sys.maxsize, to=sys.maxsize)
        self.curr_window_high_level.grid(column=1, row=9, sticky=(W))
        self.curr_window_high_level.delete(0, "end")
        self.curr_window_high_level.insert(0, 0)
        self.label_window_trigger_coupling = ttk.Label(self.window_trigger, text="Trigger Coupling")
        self.label_window_trigger_coupling.grid(column=0, row=10, sticky=(E))
        self.window_trigger_coupling = StringVar()
        self.curr_window_trigger_coupling = ttk.Combobox(self.window_trigger, textvariable=self.window_trigger_coupling)
        self.curr_window_trigger_coupling.grid(column=1, row=10, sticky=(W))
        self.curr_window_trigger_coupling["values"] = ("AC", "DC", "HF_REJECT", "LF_REJECT", "AC_PLUS_HF_REJECT")
        self.curr_window_trigger_coupling.insert(0, "AC")
        self.curr_window_trigger_coupling.config(state="readonly")
        
        ### GRAPH FRAME
        
        self.graph_frame = ttk.Frame(self.active_frame, borderwidth=5, relief="sunken")
        self.graph_frame.grid(column=2, row=6, columnspan=4, rowspan=6, sticky=(N, S, E, W))
        self.graph_plot = Figure(figsize=(5,5), dpi=100)
        self.subplot = self.graph_plot.add_subplot(111)
        self.subplot.plot([0],[0])
        self.graph_canvas = FigureCanvasTkAgg(self.graph_plot, self.graph_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().grid(column=2, row=6, columnspan=4, rowspan=6, sticky=(N, S, E, W))
        
        # TODO: make graph functional
        
        ### MEASUREMENTS FRAME
        
        self.measurements_frame = ttk.Frame(self.mainframe)
        self.measurements_frame.grid(column=0, row=12, columnspan=6, sticky=(N, S, E, W))
        self.meas_label = ttk.Label(self.measurements_frame, text="Measurements")
        self.meas_label.grid(column=0, row=12, columnspan=2, sticky=(W))
        self.add_meas = ttk.Button(self.measurements_frame, text="+", command=self.add_measurement)
        self.add_meas.grid(column=2, row=12)
        self.remove_meas = ttk.Button(self.measurements_frame, text="-", command=self.remove_measurement)
        self.remove_meas.grid(column=3, row=12)
        
        self.table_frame = ttk.Frame(self.mainframe)
        self.table_frame.grid(column=0, row=13)
        self.test_data = {"MEAS_1": {"Measurement": "NO_MEASUREMENT", "Channel": 0, "Result": 0, "Mean": 0, "StDev": 0, "Min": 0, "Max": 0, "Num in Stats": 0}}
        self.table = TableCanvas(self.table_frame, data=self.test_data, read_only=True)
        self.table.show()
        
        #TODO: make table read from actual measurements in live time (w/ stats)
        
        # Setup functions
        self.session = None
        self.update_config()
        self.update_trigger()
        self._set_message("Ready!")
        
        self.root.mainloop()
    
    def _get_devices(self):
        with nimodinst.Session("niscope") as session:
            return [dev.device_name for dev in session.devices]
            
    def _get_measurements(self):
        return [i.name for i in niscope.enums.ScalarMeasurement if not i.name in self.meas_array]
    
    def _set_message(self, text):
        self.label_error_text.config(state=NORMAL)
        self.label_error_text.delete(1.0, "end")
        self.label_error_text.insert(1.0, text)
        self.label_error_text.config(state=DISABLED)
        
    def _start_fetching(self):
        if self.blocked:
            return
                
        self.update_graph()
        self.update_table()
        self.root.after(1000, self._start_fetching)
    
    def add_measurement(self):
        self.add_meas_window = Toplevel(self.root)
        add_meas_window_frame = ttk.Frame(self.add_meas_window)
        add_meas_window_frame.grid(column=0, row=0)
        add_meas_label = ttk.Label(add_meas_window_frame, text="Choose a measurement to add.")
        add_meas_label.grid(column=1, row=0, sticky=(N))
        meas_to_add = StringVar()
        self.add_meas_combobox = ttk.Combobox(add_meas_window_frame, textvariable=meas_to_add)
        possible_meas = self._get_measurements()
        self.add_meas_combobox.grid(column=1, row=1, sticky=(N))
        self.add_meas_combobox["values"] = possible_meas
        self.add_meas_combobox.insert(0, possible_meas[1])
        self.add_meas_combobox.config(state="readonly")
        add_meas_button = ttk.Button(add_meas_window_frame, text="Add", command=self.confirm_measurement)
        add_meas_button.grid(column=0, row=2, sticky=(W))
        cancel_meas_button = ttk.Button(add_meas_window_frame, text="Cancel", command=self.cancel_measurement)
        cancel_meas_button.grid(column=2, row=2, sticky=(E))
    
    def cancel_measurement(self):
        self.add_meas_window.destroy()
        
    def confirm_measurement(self):
        self.meas_array.append(self.add_meas_combobox.get())
        self._set_message("Measurement {0} added!".format(self.add_meas_combobox.get()))
        self.add_meas_window.destroy()
        self.update_table()
    
    def dummy(self):
        self.channel_select.delete(0, "end")
        self.channel_select.insert(0, "dummy")
    
    def remove_measurement(self):
        if(len(self.meas_array) == 0):
            self._set_message("No measurements to remove!")
        else:
            del self.meas_array[-1]
            self.update_table()
        
    def self_cal(self):
        self._set_message("Now calibrating...")
        self.stop()
        try:
            with self.session as session:
                session.self_cal()
        except Exception as e:
            self._set_message(str(e))
        else:
            self._set_message("Self calibration successful!")

    def start(self):
        # Begin indefinitely fetching
        self.start_stop_button.configure(text="Stop", command=self.stop)
        self.blocked = False
        self._start_fetching()
    
    def stop(self):
        # Stop indefinitely fetching
        self.start_stop_button.configure(text="Run", command=self.start)
        self.blocked = True
        
    def update_config(self):
        try:
            self.config_channels = int(self.curr_channel.get())
        except:
            self.config_channels = self.curr_channel.get()
        
        self.cached_absolute_initial_x = 0.0
        self.cached_x_increment = 0.0
        
        try:
            if self.dev_name != self.curr_device.get():
                if self.session is not None:
                    self.session.close()
                self.session = niscope.Session(self.curr_device.get())
                self.dev_name = self.curr_device.get()
            self.session.configure_vertical(range=float(self.curr_vertical_range.get()), 
            coupling=niscope.VerticalCoupling[self.curr_vertical_coupling.get()], 
            offset=float(self.curr_vertical_offset.get()), probe_attenuation=float(self.curr_probe_attenuation.get()))
            self.session.configure_horizontal_timing(min_sample_rate=float(self.curr_min_sample_rate.get()), 
            min_num_pts=int(self.curr_min_record_length.get()), ref_position=50.0, num_records=1, enforce_realtime=True)
        except Exception as e:
            self._set_message(str(e))
        else:
            self._set_message("Successfully updated configuration!")
    
    def update_graph(self):
        if self.blocked:
            return
        try:
            with self.session.initiate():
                wfm_infos = self.session.channels[self.config_channels].fetch(num_samples=int(self.curr_min_sample_rate.get()))
            if self.cached_x_increment != wfm_infos[0].x_increment or self.cached_absolute_initial_x != wfm_infos[0].absolute_initial_x:
                self.cached_x_axis_values = []
                for i in range(int(self.curr_min_sample_rate.get())):
                    self.cached_x_axis_values.append(wfm_infos[0].absolute_initial_x + (i * wfm_infos[0].x_increment))
                self.cached_x_increment = wfm_infos[0].x_increment
                self.cached_absolute_initial_x = wfm_infos[0].absolute_initial_x
                self.subplot.clear()
                for wfm_info in wfm_infos:
                    self.subplot.plot(self.cached_x_axis_values, wfm_info.samples)
                self.graph_canvas.draw()
        except Exception as e:
            self._set_message(str(e))
        
    def update_table(self):
        try:
            temp_dict = {}
            for meas in self.meas_array:
                with self.session.initiate():
                    measurement_stat = self.session.channels[self.config_channels].fetch_measurement_stats(
                    niscope.enums.ScalarMeasurement[meas], 5.0)
                    for stat in measurement_stat:
                        inner_temp_dict = {}
                        inner_temp_dict["Measurement"] = meas
                        inner_temp_dict["Channel"] = stat.channel
                        inner_temp_dict["Result"] = stat.result
                        inner_temp_dict["Mean"] = stat.mean
                        inner_temp_dict["StDev"] = stat.stdev
                        inner_temp_dict["Min"] = stat.min_val
                        inner_temp_dict["Max"] = stat.max_val
                        inner_temp_dict["Num in Stats"] = stat.num_in_stats
                        key = meas + "_" + stat.channel
                        temp_dict[key] = inner_temp_dict
            self.table = TableCanvas(self.table_frame, data=temp_dict, read_only=True)
            self.table.show()
        except Exception as e:
            self._set_message(str(e))
        
    def update_trigger(self):
        self.session.trigger_modifier = niscope.enums.TriggerModifier.AUTO
        self.trigger_type = self.trigger_notebook.tab(self.trigger_notebook.select(), "text")
        try:
            if self.trigger_type == "Digital":
                self.session.configure_trigger_digital(self.digital_trigger_source.get(), 
                niscope.enums.TriggerSlope[self.digital_trigger_slope.get().upper()])
            elif self.trigger_type == "Edge":
                self.session.configure_trigger_edge(self.edge_trigger_source.get(), 
                float(self.curr_edge_trigger_level.get()),
                niscope.enums.TriggerCoupling[self.edge_trigger_coupling.get().upper()],
                niscope.enums.TriggerSlope[self.edge_trigger_slope.get().upper()])
            elif self.trigger_type == "Hysteresis":
                self.session.configure_trigger_hysteresis(self.hysteresis_trigger_source.get(),
                float(self.curr_hysteresis_trigger_level.get()), float(self.curr_hysteresis.get()),
                niscope.enums.TriggerCoupling[self.hysteresis_trigger_coupling.get().upper()],
                niscope.enums.TriggerSlope[self.hysteresis_trigger_slope.get().upper()])
            elif self.trigger_type == "Immediate":
                self.session.configure_trigger_immediate()
            elif self.trigger_type == "Window":
                self.session.configure_trigger_window(self.window_trigger_source.get(),
                float(self.curr_window_low_level.get()), float(self.curr_window_high_level.get()),
                niscope.enums.TriggerWindowMode[self.window_mode.get().upper()],
                niscope.enums.TriggerCoupling[self.window_trigger_coupling.get().upper()])
        except Exception as e:
            self._set_message(str(e))
        else:
            self._set_message("Successfully updated trigger settings!")
        
main = NIScopeSFP()