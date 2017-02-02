from PyQt4.QtGui import QSizePolicy
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from itertools import cycle

# TODO add docstrings


class PltCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.hold(False)  # Clears the plot whenever plot() is called again

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot_displacement(self, dynamicResponse, plotList):
        self.axes.hold(False)
        self.axes.plot([], [])
        self.axes.hold(True)

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if i != 'TLCD':
                    n = int(i.split('Pavimento ')[1]) - 1
                    x = dynamicResponse.x[n, :].A1
                    self.axes.plot(t, x, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    x = dynamicResponse.x[n, :].A1
                    self.axes.plot(t, x, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Deslocamento em Função do Tempo')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel('x (m)')
        self.fig.tight_layout()
        self.draw()

    def plot_velocity(self, dynamicResponse, plotList):
        self.axes.hold(False)
        self.axes.plot([], [])
        self.axes.hold(True)

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if i != 'TLCD':
                    n = int(i.split('Pavimento ')[1]) - 1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(t, v, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    v = dynamicResponse.v[n, :].A1
                    self.axes.plot(t, v, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Velocidade em Função do Tempo')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel('v (m/s)')
        self.fig.tight_layout()
        self.draw()

    def plot_acceleration(self, dynamicResponse, plotList):
        self.axes.hold(False)
        self.axes.plot([], [])
        self.axes.hold(True)

        cycol = cycle('brgcmk')

        t = dynamicResponse.t

        for i, j in plotList:
            if j:
                if i != 'TLCD':
                    n = int(i.split('Pavimento ')[1]) - 1
                    a = dynamicResponse.a[n, :].A1
                    self.axes.plot(t, a, c=next(cycol), label=i)
                else:
                    n = len(plotList) - 1
                    a = dynamicResponse.a[n, :].A1
                    self.axes.plot(t, a, c=next(cycol), label='TLCD')

        self.axes.legend(fontsize=11)
        self.axes.set_title('Aceleração em Função do Tempo')

        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel(r'a (m/$s^2$)')
        self.fig.tight_layout()
        self.draw()

    def plot_excitation(self, t, a):
        self.axes.plot(t, a)
        self.axes.set_xlabel('t (s)')
        self.axes.set_ylabel(r'a (m/$s^2$)')
        self.draw()
