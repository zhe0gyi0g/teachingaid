'''
Written by Tan Zheng Ying for his capstone project 'A Teaching Aid for Spinal Mobilisation'
NOTE:
-Ensure that the Arduino Mega 2560 microcontroller is connected to the laptop at all times
-Close the GUI window only when there is no recording in progress
'''

'''Constants'''
TIME_INCREASE = 0.5                      # Number of seconds that the elapsed time is increasing
NUM_DISPLAYED_POINTS = 100               # Number of data points to display on real-time graph
HIGH_RED = 4.0                           # Max value for threshold of red colour
HIGH_ORANGE = 7.0                        # Max value for threshold of orange colour
MICROCONTROLLER = "Arduino Mega 2560"    # Name of microcontroller connected through serial port
BAUD_RATE = 9600                         # Baud rate for serial communication
NODE_RADIUS = 30                         # Node radius in pixels

'''Libraries and Modules'''
# Package to create GUI (TK interface is the standard Python interface to the Tcl/Tk GUI toolkit)
import tkinter as tk
# Import Canvas class (display graphical elements like lines or text)
# Import Label class (display text and bitmaps)
# Import Button (add buttons)
from tkinter import Canvas, Label, Button

# Module to plot figures
import matplotlib.pyplot as plt
# Class to plot Matplotlib figures inside Tkinter GUI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Library for data manipulation and analysis
import pandas as pd

# Import pySerial module to access serial port
import serial
# Module to list available COM/serial ports
import serial.tools.list_ports

# Library to manipulate time values
import time
# From datetime module (manipulate dates and times)
# Import datetime class (combination of a date and a time)
# Import timedelta class (difference between two datetimes)
from datetime import datetime, timedelta

'''Define class for GUI'''
class LumbarSpineGUI:

    '''Initialise GUI as an object'''
    def __init__(self, root):
        self.root = root
        self.root.title("Spinal Mobilisation Teaching Aid")

        '''Configure grid layout for dynamic resizing'''
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)

        '''Left Frame (Lumbar Spine Map)'''
        self.left_frame = tk.Frame(root)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas = Canvas(self.left_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        '''Right Frame (Real-Time Graph, Different Parameters and Buttons)'''
        self.right_frame = tk.Frame(root)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        # Real-Time Graph
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Force Reading")
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Force (Newtons)")
        self.ax.grid(True)
        self.canvas_graph = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # Labels for Frequency, Max Force, Min Force, Difference and Period
        self.frequency_label = Label(self.right_frame, text="Frequency: 0 presses/sec", font=("Arial", 12, "bold"))
        self.frequency_label.pack()
        self.max_force_label = Label(self.right_frame, text="Max. force: 0.0N", font=("Arial", 12, "bold"))
        self.max_force_label.pack()
        self.min_force_label = Label(self.right_frame, text="Min. force: 0.0N", font=("Arial", 12, "bold"))
        self.min_force_label.pack()
        self.diff_force_label = Label(self.right_frame, text="Difference: 0.0N", font=("Arial", 12, "bold"))
        self.diff_force_label.pack()
        self.period_label = Label(self.right_frame, text="Period: 0 secs", font=("Arial", 12, "bold"))
        self.period_label.pack()

        # Recording Buttons
        self.start_button = Button(self.right_frame, text="Start Recording", command=self.start_recording,
                                   state=tk.NORMAL)
        self.start_button.pack()
        self.stop_button = Button(self.right_frame, text="Stop Recording", command=self.stop_recording,
                                  state=tk.DISABLED)
        self.stop_button.pack()
        self.status_label = Label(self.right_frame, text="Ensure microcontroller is connected!", font=("Arial", 12))
        self.status_label.pack()

        '''Initialize Nodes & Labels'''
        self.node_centres = []    # List of coordinates of the centre of each node
        self.node_edges = []      # List of coordinates of the edges of each node
        self.bone_labels = []     # List of bone labels of each node (e.g. L1L)
        self.force_labels = []    # List of force values of each node (e.g. 2.3N)
        self.node_lines = []      # List of coordinates of each line between nodes of the same vertebra
        self.init_nodes()         # Initialise the nodes

        '''Force values tracking'''
        self.time_elapsed = 0               # Variable for total duration so far
        self.force_readings = [0.0] * 15    # List of 15 force readings
        self.max_force = 0.0                # Variable for max force (highest force so far)
        self.min_force = 0.0                # Variable for min force (lowest force so far)
        self.high_force_data = []           # Variable for values of y-axis (sensor with highest force in a moment)
        self.time_data = []                 # Variable for values of x-axis (current duration)
        self.num_presses = 0                # Variable for total number of presses

        # Serial connection
        self.serial_port = None         # Serial/COM port for serial communication
        self.ser_conn = None            # Variable to create a serial connection as an object
        self.isRecording = False        # Check if recording now
        self.isFirstRecording = True    # Check if first recording

        # Excel setup
        self.excel_filename = None  # Variable to define Excel log file's name
        self.columns = []           # List of the different headers (timestamp, duration, bone labels)
        self.start_time = 0.0       # Variable to define start time of recording
        self.writer = None

        '''Handle window resizing dynamically'''
        self.root.bind("<Configure>", self.resize)

    '''Initialise the nodes'''
    def init_nodes(self):
        self.canvas.delete("all")  # Clear canvas on resize
        self.node_centres = []     # Clear list
        self.node_edges = []       # Clear list
        self.bone_labels = []      # Clear list
        self.force_labels = []     # Clear list
        self.node_lines = []       # Clear list

        width = self.canvas.winfo_width() or 250  # Return width of widget (or default width)
        height = self.canvas.winfo_height() or 500  # Return height of widget (or default height)

        y_spacing = height // 6                                       # Vertically space out vertebrae evenly
        x_positions = [(width // 5), (width // 2), (4 * width // 5)]  # Left, centre, right positions
        labels = ["L", "C", "R"]                                      # Left, centre, right labels

        for i in range(5):              # For every vertebra,
            y = y_spacing * (i + 1)     # y-coordinate of vertebra
            vertebra_nodes = []         # list of coordinates of centre of each node in the same vertebra
            for j, x in enumerate(x_positions): # For every position on the vertebra,
                # Append coordinates of node
                self.node_centres.append((x, y))
                # Create node as a circle
                node_id = self.canvas.create_oval(x - NODE_RADIUS, y - NODE_RADIUS, x + NODE_RADIUS, y + NODE_RADIUS,
                                                  fill="red", outline="black")
                self.node_edges.append(node_id)   # Append node edges
                # Create node label inside the node (e.g. L1L)
                label_text = f"L{i + 1}{labels[j]}"
                label_id = self.canvas.create_text(x, y - 10, text=label_text, font=("Arial", 12, "bold"),
                                                   fill="black")
                self.bone_labels.append(label_id)   # Append bone label
                vertebra_nodes.append((x, y))       # Append coordinates of node label
                # Create force label below node label (e.g. 2.3N)
                force_label_id = self.canvas.create_text(x, y + 10, text="0.0N", font=("Arial", 10, "bold"),
                                                         fill="black")
                self.force_labels.append(force_label_id)  # Append force value of node
            # Connect left-centre-right nodes of the same vertebra (between left and centre)
            self.node_lines.append(self.canvas.create_line(vertebra_nodes[0][0] + NODE_RADIUS, vertebra_nodes[0][1],
                                                           vertebra_nodes[1][0] - NODE_RADIUS, vertebra_nodes[1][1],
                                                           fill="black", width=2))
            # Connect left-centre-right nodes of the same vertebra (between centre and right)
            self.node_lines.append(self.canvas.create_line(vertebra_nodes[1][0] + NODE_RADIUS, vertebra_nodes[1][1],
                                                           vertebra_nodes[2][0] - NODE_RADIUS, vertebra_nodes[2][1],
                                                           fill="black", width=2))
            # Connect centre nodes from different vertebrae (vertical spine)
            if i > 0:
                prev_centre = self.node_centres[(i - 1) * 3 + 1]  # Centre of previous vertebra
                curr_centre = self.node_centres[i * 3 + 1]        # Centre of current vertebra
                # Draw line between previous and current vertebrae
                self.node_lines.append(self.canvas.create_line(prev_centre[0], prev_centre[1] + NODE_RADIUS,
                                                               curr_centre[0], curr_centre[1] - NODE_RADIUS,
                                                               fill="black", width=3))

    '''Dynamically resize nodes'''
    def resize(self, event):
        self.init_nodes()

    '''Returns traffic light colour based on force reading'''
    def get_colour(self, value):
        if value < HIGH_RED:
            return "red"     # Low force (represents "Not There")
        elif value < HIGH_ORANGE:
            return "orange"  # Medium force (represents "Almost There") (amber is not recognised as a colour)
        else:
            return "green"   # High force (represents "Accurate")

    '''Update GUI'''
    def update_GUI(self):
        if self.isRecording:
            force_string = self.ser_conn.readline().decode().strip()
            force_list = force_string.split(',')
            for f in range(0,len(force_list)):
                try:
                    # Convert each element from string to float
                    self.force_readings[f] = float(force_list[f])
                # In case the force value is not a number (e.g. blank)
                except ValueError:
                    # Set element to zero if cannot convert to float
                    self.force_readings[f] = 0.0

            # Log the force readings
            self.logging()

            # Get highest and lowest force values from the list of force readings
            high_force = max(self.force_readings)
            low_force = 0
            for f in self.force_readings:
                if low_force == 0:              # To avoid using zero as lowest force in the list
                    low_force = f
                if f < low_force and f != 0:    # To assign lowest non-zero force in the list to low_force variable
                    low_force = f

            # Update max force if the highest force is higher
            self.max_force = max(self.max_force, high_force)

            # Update min force only if the new min is non-zero, or it is the first update
            if self.min_force == 0 and low_force != 0:
                    self.min_force = low_force  # Update min force if lowest force is lower

            # Update node colors and force values
            for i, force in enumerate(self.force_readings):
                colour = self.get_colour(force)
                self.canvas.itemconfig(self.node_edges[i], fill=colour)
                self.canvas.itemconfig(self.force_labels[i], text=f"{force:.1f}N")
                # Count number of presses to calculate frequency
                if colour == "green":
                    self.num_presses += 1

            # Update graph
            self.time_elapsed += TIME_INCREASE  # Increment
            self.high_force_data.append(high_force)
            self.time_data.append(round(self.time_elapsed, 2))

            # Limit number of displayed data points for smooth graphing
            if len(self.high_force_data) > NUM_DISPLAYED_POINTS:
                self.high_force_data.pop(0)
                self.time_data.pop(0)

            # Update the graph
            self.ax.clear()
            self.ax.plot(self.time_data, self.high_force_data, marker="o", linestyle="-", color="blue")
            self.ax.set_title("Real-Time Max Force Reading")
            self.ax.set_xlabel("Time (seconds)")
            self.ax.set_ylabel("Force (Newtons)")
            self.ax.grid(True)
            self.canvas_graph.draw()    # Draw the graph

            # Update labels
            self.frequency_label.config(text=f"Frequency: {round((self.num_presses/self.time_elapsed),2)}presses/sec")
            self.max_force_label.config(text=f"Max. force: {self.max_force}N")
            self.min_force_label.config(text=f"Min. force: {self.min_force}N")
            self.diff_force_label.config(text=f"Difference: {round((self.max_force - self.min_force),2)}N")
            self.period_label.config(text=f"Period: {round(self.time_elapsed, 2)} seconds")

            # Schedule next update as a loop
            self.root.after(500, self.update_GUI)

    '''Start recording the inputs'''
    def start_recording(self):
        # Set recording status to true
        self.isRecording = True

        # Disable 'Start Recording' button
        self.start_button.config(state=tk.DISABLED)
        # Enable 'Stop Recording' button
        self.stop_button.config(state=tk.NORMAL)

        # Start serial connection
        self.connection()

        # If not first recording, need to refresh the GUI before updating GUI
        if not self.isFirstRecording:
            self.num_presses = 0            # Restart number of presses so far
            self.time_elapsed = 0           # Restart duration
            self.max_force = 0.0            # Clear maximum force
            self.min_force = 0.0            # Clear minimum force
            self.high_force_data.clear()    # Clear values in y-axis (high force data)
            self.time_data.clear()          # Clear values in x-axis (current duration)
            self.ax.clear()                 # Clear data points in graph

        # Use current date and current time as for unique naming of Excel file
        filename_date = datetime.now().strftime("%Y%m%d_%H%M%S")  # E.g. 20250223_223501
        # Calculate duration since start of recording
        self.start_time = time.time_ns()
        # Write filename
        self.excel_filename = filename_date + "_log.xlsx"
        # Create column headers
        self.columns = ['Timestamp', 'Duration',
        'L1L','L1C','L1R', 'L2L','L2C','L2R', 'L3L','L3C','L3R', 'L4L','L4C','L4R', 'L5L','L5C','L5R']
        # Write column headers to Excel file
        pd.DataFrame(columns=self.columns).to_excel(self.excel_filename, index=False)
        # Create file as ExcelWriter object then as 'writer'
        self.writer = pd.ExcelWriter(self.excel_filename, mode="a", if_sheet_exists="overlay", engine="openpyxl")

        # Update GUI
        self.update_GUI()

    '''Stop recording the inputs'''
    def stop_recording(self):
        # Set recording status to false
        self.isRecording = False
        # Enable 'Start Recording' button
        self.start_button.config(state=tk.NORMAL)
        # Disable 'Stop Recording' button
        self.stop_button.config(state=tk.DISABLED)
        # Stop logging
        self.logging()
        # Stop serial connection
        self.connection()
        if self.isFirstRecording:           # If first recording,
            self.isFirstRecording = False   # set status to not the first recording

    '''Start/Stop serial communication'''
    def connection(self):
        # When 'Start Recording' button is clicked,
        if self.isRecording:
            # Get list of available serial ports
            ports = serial.tools.list_ports.comports()
            # Check all serial ports in list
            for p in ports:
                # If the serial port is connected to the microcontroller,
                if MICROCONTROLLER in p.description:  # Example of 'description' -> 'Arduino Mega 2560 (COM4)'
                    self.serial_port = p.device       # Example of 'device' -> 'COM4'
                    break                             # Break loop when serial port is found
            # Create serial connection
            self.ser_conn = serial.Serial(self.serial_port, BAUD_RATE, timeout=1)
        # When 'Stop Recording' button is clicked,
        else:
            # Close serial communication if open
            if self.ser_conn and self.ser_conn.is_open:
                self.ser_conn.close()

    '''Start/Stop logging'''
    def logging(self):
        # When 'Start Recording' button is clicked,
        if self.isRecording:
            # Current timestamp, specify up to milliseconds
            timestamp = datetime.now().isoformat(sep='_', timespec='milliseconds')
            # Difference between current and start times in nanoseconds
            elapsed_time = (time.time_ns() - self.start_time)

            # Show duration in terms of hours, minutes, seconds and milliseconds
            # Seconds -> integer division of elapsed_time by 1 trillion
            # Milliseconds -> modulus division of elapsed_time by 1 trillion (first 3 digits)
            duration = str(timedelta(seconds=(elapsed_time // 1000000000))) + "." + \
                       str(int(elapsed_time % 1000000000))[0:3]

            # Append new data row
            new_row = [timestamp, duration] + self.force_readings   # Append force values to timestamp and duration
            df = pd.DataFrame([new_row], columns=self.columns)      # Form new row with data under respective columns

            # Write to file starting from the row that has not been written, without writing row and column names
            df.to_excel(self.writer, index=False, header=False, startrow=self.writer.sheets["Sheet1"].max_row)
        # When 'Stop Recording' button is clicked,
        else:
            # Save the file by closing it
            self.writer.close()

'''Main function'''
if __name__ == "__main__":
    # Create a top-level widget, which is the main window
    root = tk.Tk()                  # Create main window as an instance of Tk class
    # Create GUI using main window
    app = LumbarSpineGUI(root)      # Create GUI as an instance of LumbarSpineGUI class
    # Start GUI in an infinite loop
    root.mainloop()
