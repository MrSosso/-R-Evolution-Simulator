"""
this module contains classes which control the windows of the graphic interface
"""

import tkinter as tk
from time import time, sleep
from . import frames as frm
from .canvas import PygameCanvas
from .graphics import CreaturesD, ChunkD
from . import var
from . import utility as utl
import threading as thr
import queue as que
import os
from math import ceil
import json
from .world import World
import datetime


class FinishError(BaseException):
    pass


class BaseTkWindow(tk.Tk):
    """
    Template for windows classes
    """
    FRAMES_TEMPLATE = None  # dict composed by (<Frame class>, <Frame args>, <Frame grid position>)
    TITLE = None  # str title of the Window

    def __init__(self, father):
        """
        Creates a new window

        :param father: the father of the window
        :type father: BaseTkWindow
        """
        super(BaseTkWindow, self).__init__()
        self.father = father
        self.active = True
        self.windows = list()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.title(self.TITLE)
        self.frames = {}

    def destroy(self):
        """
        Destroys all dependent windows and then the window itself

        :return:
        """
        for i in self.windows:
            i.destroy()
        self.active = False
        super(BaseTkWindow, self).destroy()

    def get_widget(self, frame, widget):
        """
        Returns the widget object given the frame name and its name

        :param frame: the name of the frame in which the widget is
        :type frame: str
        :param widget: the name of the widget
        :type widget: str
        :return:
        """
        return self.get_frame(frame).get_widget(widget)

    def get_frame(self, frame):
        """
        Returns the frame object given the frame name

        :param frame: the name of the frame
        :type frame: str
        :return:
        """
        return self.frames[frame]

    def frames_load(self):
        """
        Initializes the frames inside the window and adds them to self.frames dict

        :return:
        """
        for i in self.FRAMES_TEMPLATE:
            new = self.FRAMES_TEMPLATE[i][0](self, **self.FRAMES_TEMPLATE[i][1])
            new.grid(**self.FRAMES_TEMPLATE[i][2])
            self.frames[i] = new

    def new_window_dependent(self, wind_class, *args, **kwargs):
        """
        Creates a new dependent window and adds it to windows list

        :param wind_class: the class of the window to create
        :type wind_class: type
        :param args: args to pass to new window __init__
        :param kwargs: kwargs to pass to new window __init__
        :return:
        """
        new = wind_class(self, *args, **kwargs)
        self.windows.append(new)

    def new_window_substitute(self, wind_class, *args, **kwargs):
        """
        Creates a new window dependent from the father window and destroys iteslf

        :param wind_class: the class of the window to create
        :type wind_class: type
        :param args: args to pass to new window __init__
        :param kwargs: kwargs to pass to new window __init__
        :return:
        """
        father = self.father
        self.destroy()
        father.new_window_dependent(wind_class, *args, **kwargs)

    def update(self):
        """
        Updates all dependent windows and the the window itself

        :return:
        """
        for i in self.windows:
            if i.active:
                i.update()
        super(BaseTkWindow, self).update()


class MainMenuWindow(BaseTkWindow):
    """
    Main menu window class
    """
    TITLE = "(R)Evolution Simulator"

    def __init__(self, father):
        """
        Creates a new main menu window

        :param father: the father of the window
        :type father: BaseTkWindow
        """
        self.FRAMES_TEMPLATE = {'logo': (frm.Logo, {}, {'row': 0, 'column': 0}),
                                'options': (frm.MainMenuOptions, {'windows': (self,)}, {'row': 1, 'column': 0})}
        super(MainMenuWindow, self).__init__(father)
        self.frames_load()
        self.windows = list()
        self.canvas = None

    def destroy(self):
        """
        it destroys the object and exit the program

        :return:
        """
        super(MainMenuWindow, self).destroy()
        exit(0)

    def new_sim_window(self):
        """
        Creates a new dependent NewSimWindow

        :return:
        """
        self.new_window_dependent(NewSimWindow)

    def load_sim_window(self):
        """
        Creates a new dependent LoadSimWindow

        :return:
        """
        self.new_window_dependent(LoadSimWindow)


class LoadSimWindow(BaseTkWindow):
    """
    Load simulation window class
    """
    TITLE = "Load Simulation"

    def __init__(self, father):
        """
        Creates a load simulation window

        :param father: the father of the window
        :type father: BaseTkWindow
        """
        self.FRAMES_TEMPLATE = {'load': (frm.LoadSim, {'windows': (self,)}, {'row': 0, 'column': 0})}
        super(LoadSimWindow, self).__init__(father)
        self.frames_load()

    def simulation_file_load(self):
        """
        Destroys itself and creates a new SimReplayControlWindow dependent from father

        :return:
        """
        sim_name = self.get_widget('load', 'entry').get()
        self.new_window_substitute(SimReplayControlWindow, sim_name)


class SimReplayControlWindow(BaseTkWindow):
    """
    Simulation replay control window class
    """
    START_VARIABLES = {
        'tick': 1.0,
        'zoom': 10,
        'speed': 1,
        'max_speed': 100,
        'graph_tick': 100,
    }
    SHOWS_KEYS = ['ch', 'cc', 'cd']

    def __init__(self, father, sim_name):
        """
        Creates a new simulation replay control window

        :param father: the father of the window
        :type father: BaseTkWindow
        :param sim_name: the name of the simulation to load
        :type sim_name: str
        """
        self.FRAMES_TEMPLATE = {'play_control': (frm.PlayControl, {}, {'row': 0, 'column': 0}),
                                'map_set': (frm.SetSuperFrame, {'windows': (self,), }, {'row': 1, 'column': 0}), }
        self.TITLE = sim_name
        super(SimReplayControlWindow, self).__init__(father)
        self.sim_name = sim_name
        self.__dict__.update(self.START_VARIABLES)
        self.is_playing = False
        self._files_load()
        self.sim_width = self.dimension['width'] * self.chunk_dim
        self.sim_height = self.dimension['height'] * self.chunk_dim
        self.shows = dict()
        self.last_frame_time = time()
        for i in self.SHOWS_KEYS:
            self.shows[i] = tk.StringVar(master=self)
        self.diagram_choice = tk.StringVar(master=self)
        self.frames_load()
        self.canvas = PygameCanvas(self)
        self._resize(0)

    def _files_load(self):
        """
        Loads simulation files

        :return:
        """
        self.directories = dict()
        path = os.path.join(var.SIMULATIONS_PATH, self.sim_name)
        for i in var.DIRECTORIES:
            self.directories[i] = os.path.join(path, i)

        try:
            simulation_params = open(os.path.join(path, f"params.{var.FILE_EXTENSIONS['simulation_data']}"))
        except FileNotFoundError:
            self.destroy()
        sim_data = simulation_params.readline()
        restored = utl.get_from_string(sim_data, 0, var.TO_RECORD['simulation'])
        self.__dict__.update(restored)

        files = dict()
        for i in ['chunks', 'creatures']:
            try:
                files[i] = open(os.path.join(self.directories['data'], f"{i}.{var.FILE_EXTENSIONS[i+'_data']}"))
            except FileNotFoundError:
                self.destroy()
        self.chunk_list = []
        for line in files['chunks']:
            self.chunk_list.append(ChunkD(line))

        self.creature_list = set()
        for line in files['creatures']:
            self.creature_list.add(CreaturesD(line))

    def update(self):
        """
        Updates all dependent windows and the the window itself

        :return:
        """
        if self.is_playing:
            self.tick += self.time_diff * self.speed
            if int(self.tick) >= self.lifetime:
                self.start_play()
                self.tick = self.lifetime
            self.graph_tick = ceil(self.tick / 100) * 100
        shows = dict()
        for i in self.shows:
            shows[i] = self.shows[i].get()
        self.canvas.update(int(self.tick), shows)
        self.time_diff = time() - self.last_frame_time
        self.last_frame_time = time()
        try:
            self._upd_fps(round(1.0 / self.time_diff, 1))
        except ZeroDivisionError:
            pass
        self._upd_tick(int(self.tick))
        super(SimReplayControlWindow, self).update()

    def destroy(self):
        """
        Destroys the canvas, all dependent windows and then the window itself

        :return:
        """
        self.canvas.destroy()
        super(SimReplayControlWindow, self).destroy()

    def diagram_window_create(self):
        """
        Gets the choice for the new diagram to open and creates a new diagram window

        :return:
        """
        subject = self.diagram_choice.get()
        self.new_window_dependent(SimDiagramWindow, subject)

    def _resize(self, increase):
        """
        Increases/Reduces the canvas' zoom by a coeff

        :param increase: the increase of the zoom
        :type increase: int
        :return:
        """
        self.zoom = max(1, self.zoom + increase)
        self.canvas.resize()

    def start_play(self):
        """
        Toggles the replay status and label between Play and Pause

        :return:
        """
        self.is_playing = not (self.is_playing)
        if self.is_playing:
            self.get_widget('play_control', 'play').config(text="Pause")
        else:
            self.get_widget('play_control', 'play').config(text="Play")

    def set_tick(self):
        """
        Sets if possible the tick to the specific tick inside tick_entry widget

        :return:
        """
        try:
            self.tick = int(self.get_widget('play_control', 'tick_entry').get())
        except ValueError:
            pass

    def set_speed(self, speed_cursor):
        """
        Changes the speed of the simulation reproduction and updates the speed label

        :param speed_cursor: The new speed
        :return:
        """
        self.speed = int(self.max_speed ** (float(speed_cursor) / 100))
        self._upd_speed()

    def dec_zoom(self):
        """
        Decreases the zoom by one

        :return:
        """
        self._resize(-1)
        self._upd_zoom()

    def inc_zoom(self):
        """
        Increases the zoom by one

        :return:
        """
        self._resize(1)
        self._upd_zoom()

    def _upd_speed(self):
        """
        Updates the speed label

        :return:
        """
        self.get_widget('play_control', 'speed_label').config(text=f"T/s: {self.speed:02d}")

    def _upd_zoom(self):
        """
        Updates the zoom label

        :return:
        """
        self.get_widget('play_control', 'zoom').configure(text=f"zoom: {self.zoom}0%")

    def _upd_fps(self, fps):
        """
        Updates the fps label

        :param fps: The fps to update the label to
        :type fps: float
        :return:
        """
        self.get_widget('play_control', 'fps').config(text=f"fps: {fps:04.1f}")

    def _upd_tick(self, tick):
        """
        Updates the tick label

        :return:
        """
        self.get_widget('play_control', 'tick_label').config(text=f"Tick: {tick:04d}")


class SimDiagramWindow(BaseTkWindow):
    """
    Simulation diagrams window class
    """
    START_VARIABLES = {
        'follow_play': False,
        'show_tick': False,
    }

    def __init__(self, father, subject):
        """
        Creates a new simulation diagram window

        :param father: the father of the window
        :type father: BaseTkWindow
        :param subject: the subject of the new diagram
        :type subject: str
        """
        self.subject = subject
        self.TITLE = self.subject
        self.FRAMES_TEMPLATE = {
            'diagram_canvas': (self._get_frame_class(), {'directory': father.directories['analysis'], 'subject': subject, 'params': father.analysis}, {'row': 0, 'column': 0}),
            'command_bar': (frm.DiagramCommandBar, {'windows': (self, father), 'tick_interval': father.analysis['tick_interval']}, {'row': 1, 'column': 0}), }
        super(SimDiagramWindow, self).__init__(father)
        self.__dict__.update(self.START_VARIABLES)
        self.graph_width = father.analysis['tick_interval']
        self.frames_load()

    def _get_frame_class(self):
        """
        Return the frame class for the given diagram subject

        :return:
        """
        ext = self.subject.split('.')[-1]
        if ext == var.FILE_EXTENSIONS['numeric_analysis']:
            return frm.GeneDiagram
        elif ext == var.FILE_EXTENSIONS['spreading_analysis']:
            return frm.SpreadDiagram
        elif ext == var.FILE_EXTENSIONS['demographic_analysis']:
            return frm.PopulationDiagram
        else:
            self.destroy()

    def graph_width_set(self):
        """
        Sets the graph_width to the value given in the spinbox

        :return:
        """
        try:
            self.graph_width = int(self.get_widget('command_bar', 'graph_width').get())
        except ValueError:
            pass

    def toggle_follow_play(self):
        """
        Toggles the follow_play status

        :return:
        """
        self.follow_play = not self.follow_play

    def dyn_axes_set(self):
        self.get_frame('diagram_canvas').dyn_axes_set(self.father.graph_tick)

    def stat_axes_set(self):
        self.get_frame('diagram_canvas').stat_axes_set(self.father.lifetime)

    def change_show_tick(self):
        self.show_tick = not self.show_tick
        if self.show_tick:
            self.get_frame('diagram_canvas').add_show_tick(self.father.tick)
        else:
            self.get_frame('diagram_canvas').remove_show_tick()

    def tick_line_set(self):
        self.get_frame('diagram_canvas').tick_line_set(self.father.tick)

    def update(self):
        """
        Updates all dependent windows and the the window itself

        :return:
        """

        self.tick_line_set()
        if self.follow_play:
            self.dyn_axes_set()
        else:
            self.stat_axes_set()
        self.get_widget('diagram_canvas', 'canvas').draw()
        super(SimDiagramWindow, self).update()


class NewSimWindow(BaseTkWindow):
    """
    New simulation window class
    """
    TITLE = "New Simulation"

    def __init__(self, father):
        """
        Creates a new simulation window

        :param father: the father of the window
        :type father: BaseTkWindow
        """
        super(NewSimWindow, self).__init__(father)
        self.FRAMES_TEMPLATE = {'new': (frm.NewSim, {}, {'row': 0, 'column': 0})}
        self.frames_load()

    def load_template(self):
        name = self.get_frame('new').load_choice.get()
        with open(os.path.join(var.TEMPLATES_PATH, name)) as file:
            variables = json.loads(file.readline())

            def add_to_sim_variables(obj, to_add):
                if type(to_add) == int or type(to_add) == float:
                    obj.delete(0, tk.END)
                    obj.insert(0, str(to_add))
                elif type(to_add) == tuple or type(to_add) == list:
                    for i in range(len(to_add)):
                        add_to_sim_variables(obj[i], to_add[i])
                else:
                    for i in to_add:
                        add_to_sim_variables(obj[i], to_add[i])

            add_to_sim_variables(self.get_frame('new').sim_variables, variables)

    def _get_from_sim_variables(self, obj):
        if type(obj) == tk.Entry or type(obj) == tk.Entry:
            try:
                return int(obj.get())
            except ValueError:
                return float(obj.get())
        elif type(obj) == tuple or type(obj) == list:
            to_return = list()
            for i in range(len(obj)):
                to_return.append(self._get_from_sim_variables(obj[i]))
            return to_return
        else:
            to_return = dict()
            for i in obj:
                to_return[i] = self._get_from_sim_variables(obj[i])
            return to_return

    def save_template(self):
        name = self.get_frame('new').save_choice.get().split('.')[0]
        with open(os.path.join(var.TEMPLATES_PATH, name + '.' + var.FILE_EXTENSIONS['simulation_template']), 'w') as file:
            file.write(json.dumps(self._get_from_sim_variables(self.get_frame('new').sim_variables)))

    def start_simulation(self):
        frame = self.get_frame('new')
        sim_name = frame.sim_name.get()
        if sim_name != '':
            sim_variables = self._get_from_sim_variables(frame.sim_variables)
            self.new_window_substitute(ProgressStatusWindow, (World, (sim_name, sim_variables), {}))


class ProgressStatusWindow(BaseTkWindow):
    def __init__(self, father, to_call):
        super(ProgressStatusWindow, self).__init__(father)
        self.queues = dict()
        to_pass = dict()
        for key in ['status', 'details', 'percent', 'eta']:
            to_pass[key] = tk.StringVar(self)
            self.queues[key] = que.Queue(1)
        self.__dict__.update(to_pass)
        self.FRAMES_TEMPLATE = {'progress_frame': (frm.ProgressStatus, to_pass, {'row': 0, 'column': 0}), }
        self.percent_int = 0
        self.frames_load()
        self.to_call = to_call
        self.thr_terminating = thr.Event()
        self.thr_terminated = thr.Event()
        self.thread = thr.Thread(target=self.thread_start, daemon=True)
        self.thread.start()

    def update(self):
        for key in self.queues:
            queue = self.queues[key]
            if not queue.empty():
                value = queue.get(False)
                getattr(self, f'_{key}_update')(value)
        super(ProgressStatusWindow, self).update()
        if self.thr_terminating.is_set():
            self.destroy()

    def thread_start(self):
        called = self.to_call[0](*self.to_call[1], **self.to_call[2], progress_queues=self.queues, termination_event=(self.thr_terminating, self.thr_terminated))
        self.destroy()

    def destroy(self):
        self.thr_terminating.set()
        if self.thr_terminated.is_set():
            super(ProgressStatusWindow, self).destroy()

    def _status_update(self, status):
        self.status.set(status)

    def _details_update(self, raw_details):
        try:
            details = raw_details[0]
        except IndexError:
            self.details.set('')
        else:
            try:
                out_of = raw_details[1]
            except IndexError:
                self.details.set(details)
            else:
                self.details.set(f"{details}    {out_of[0]}/{out_of[1]}")

    def _percent_update(self, percent):
        percent *= 100
        if percent:
            self.percent.set(f"{int(percent)} %")
            if percent < self.percent_int:
                percent = 0
        else:
            self.percent.set('')
            percent = 100
        self.get_widget('progress_frame', 'prograss_bar').step(percent - self.percent_int)
        self.percent_int = percent

    def _eta_update(self, eta):
        if eta:
            self.eta.set(f"ETA: {datetime.timedelta(seconds=int(eta))}")
        else:
            self.eta.set('')
