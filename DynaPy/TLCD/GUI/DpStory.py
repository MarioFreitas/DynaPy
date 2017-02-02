from math import sqrt


class Story(object):
    def __init__(self, mass=10.e3, height=3., width=.35, depth=.35, E=25.e9, vinculum='Engastado-Engastado',
                 tlcd=None, **kwargs):
        """
        :param mass: float - mass of the story (kg)
        :param height: float - height of the story (m)
        :param width: float - width of the column (m)
        :param depth: float - depth of the column (m)
        :param E: float - Elasticity module of the column (Pa)
        :param vinculum: str - Type of vinculation o the column base
        :param tlcd: object - Data of the building tlcd
        :param kwargs: any type - Used for implamentation of future parameters
        :return:
        """
        self.mass = mass
        self.height = height
        self.width = width
        self.depth = depth
        self.E = E
        self.vinculum = vinculum
        self.tlcd = tlcd

        for (i, j) in kwargs.items():
            exec('self.{} = {}'.format(i, j))

        self.I = (self.width*self.depth**3)/12
        if vinculum == 'Engastado-Engastado':
            self.stiffness = 24*self.E*self.I/(self.height**3)
        elif vinculum == 'Engastado-Apoiado' or vinculum == 'Apoiado-Engastado':
            self.stiffness = 15*self.E*self.I/(self.height**3)
        elif vinculum == 'Apoiado-Apoiado':
            self.stiffness = 6*self.E*self.I/(self.height**3)

        if self.tlcd is None:
            self.naturalFrequency = sqrt(self.stiffness/self.mass)
            self.criticalDamping = 2*self.mass*self.naturalFrequency
        else:
            self.naturalFrequency = sqrt(self.stiffness/(self.mass + self.tlcd.mass))
            self.criticalDamping = 2*(self.mass + self.tlcd.mass)*self.naturalFrequency

    def calc_damping_ratio(self, relativeDampingRatio):
        self.dampingRatio = self.criticalDamping * relativeDampingRatio
