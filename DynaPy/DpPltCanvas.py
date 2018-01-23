from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from itertools import cycle

# TODO add docstrings


class PltCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot_displacement(self, dynamicResponse, plotList, numberOfStories=1):
        self.axes.cla()

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if not ('TLCD' in i):
                    n = int(i.split('Story ')[1]) - 1
                    x = dynamicResponse.x[n, :].A1
                    self.axes.plot(t, x, c=next(cycol), label=i)
                else:
                    tlcdNumber = int(i.strip('TLCD '))
                    n = numberOfStories + tlcdNumber - 1
                    x = dynamicResponse.x[n, :].A1
                    self.axes.plot(t, x, c=next(cycol), label='TLCD {}'.format(tlcdNumber))

        self.axes.legend(fontsize=11)
        self.axes.set_title('Displacement Vs. Time')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel('x (m)')
        self.fig.tight_layout()
        self.draw()

    def plot_velocity(self, dynamicResponse, plotList):
        self.axes.cla()

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if not ('TLCD' in i):
                    n = int(i.split('Story ')[1]) - 1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(t, v, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(t, v, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Velocity Vs. Time')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel('v (m/s)')
        self.fig.tight_layout()
        self.draw()

    def plot_acceleration(self, dynamicResponse, plotList):
        self.axes.cla()

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if not ('TLCD' in i):
                    n = int(i.split('Story ')[1]) - 1
                    a = dynamicResponse.a[n, :].A1
                    self.axes.plot(t, a, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    a = dynamicResponse.a[n, :].A1
                    self.axes.plot(t, a, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Acceleration Vs. Time')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel(r'a (m/$s^2$)')
        self.fig.tight_layout()
        self.draw()

    def plot_excitation(self, t, a, unit='m/$s^2$'):
        self.axes.cla()
        self.axes.plot(t, a)
        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel(r'a ({})'.format(unit))
        self.draw()

    def plot_dmf(self, outputDMF, plotList):
        self.axes.cla()

        cycol = cycle('brgcmk')
        frequencies = outputDMF.frequencies
        dmf = outputDMF.dmf

        for i, j in plotList:
            if j:
                n = int(i.split('Story ')[1]) - 1
                self.axes.plot(frequencies, dmf[:, n].A1, c=next(cycol), label=i)

        self.axes.legend(fontsize=11)
        self.axes.set_title('DMF Vs. Excitation Frequency')
        self.axes.set_xlabel('Excitation Frequency (rad/s)')
        self.axes.set_ylabel('DMF')
        self.fig.tight_layout()
        self.draw()

    def plot_displacement_frequency(self, outputDMF, plotList):
        self.axes.cla()

        cycol = cycle('brgcmk')
        frequencies = outputDMF.frequencies
        x = outputDMF.displacements

        for i, j in plotList:
            if j:
                n = int(i.split('Story ')[1]) - 1
                self.axes.plot(frequencies, x[:, n].A1, c=next(cycol), label=i)

        self.axes.legend(fontsize=11)
        self.axes.set_title('Maximum Displacement Vs. Excitation Frequency')
        self.axes.set_xlabel('Excitation Frequency (rad/s)')
        self.axes.set_ylabel('Maximum Displacement (m)')
        self.fig.tight_layout()
        self.draw()

    def reset_canvas(self):
        self.axes.cla()
        self.draw()

    def plot_dis_vel(self, dynamicResponse, plotList):
        self.axes.cla()

        cycol = cycle('brgcmk')

        for i, j in plotList:
            if j:
                if not ('TLCD' in i):
                    n = int(i.split('Story ')[1]) - 1
                    x = dynamicResponse.x[n, :].A1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(x, v, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    x = dynamicResponse.x[n, :].A1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(x, v, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Displacement Vs. Velocity')

        self.axes.set_xlabel('x (m)')
        self.axes.set_ylabel('v (m/s)')
        self.fig.tight_layout()
        self.draw()
