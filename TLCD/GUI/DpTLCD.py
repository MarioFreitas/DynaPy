from math import pi
from DynaPy.TLCD.GUI.DpConfigurations import Configurations


class TLCD(object):
    def __init__(self, tlcdType='Basic TLCD', diameter=0.6, width=20., waterHeight=1.,
                 gasHeight=0.1, gasPressure=202650,
                 amount=1,
                 configurations=Configurations(), **kwargs):
        """
        :param tlcdType: str - Type of TLCD to be used on the calculation of TLCD parameters
        :param diameter: float - Diameter of the tlcd tube (m)
        :param width: float - Width of the tlcd tube (m)
        :param waterHeight: float - Water height inside the tlcd at rest (m)
        :param configurations: object - Configurations containing fluid parameters and gravity acceleration
        :param kwargs: any type - Used for future implementation of new parameters
        :return:
        """
        self.type = tlcdType
        self.diameter = diameter
        self.width = width
        self.waterHeight = waterHeight
        self.liquidSpecificMass = configurations.liquidSpecificMass
        self.kineticViscosity = configurations.kineticViscosity
        self.gravity = configurations.gravity
        self.amount = amount

        for (i, j) in kwargs.items():
            exec('self.{} = {}'.format(i, j))

        if self.type == 'Basic TLCD':
            self.length = self.width + 2 * self.waterHeight
            self.mass = pi * ((self.diameter / 2) ** 2) * self.length * self.liquidSpecificMass
            self.dampingCoefficient = 8 * pi * self.length * self.kineticViscosity * self.liquidSpecificMass
            self.stiffness = pi * (self.diameter ** 2) * self.liquidSpecificMass * self.gravity / 2
            self.naturalFrequency = (self.stiffness/self.mass)**0.5

        if self.type == 'Pressurized TLCD':
            self.gasHeight = gasHeight
            self.gasPressure = gasPressure

            self.length = self.width + 2 * self.waterHeight
            self.liquidMass = pi * ((self.diameter / 2) ** 2) * self.length * self.liquidSpecificMass
            self.gasMass = 0
            self.mass = self.liquidMass + self.gasMass
            self.dampingCoefficient = 8 * pi * self.length * self.kineticViscosity * self.liquidSpecificMass
            self.liquidStiffness = pi * (self.diameter ** 2) * self.liquidSpecificMass * self.gravity / 2
            self.gasStiffness = 1.4 * self.gasPressure / self.gasHeight * pi * (self.diameter ** 2) / 2
            self.stiffness = self.liquidStiffness + self.gasStiffness
            self.naturalFrequency = (self.stiffness / self.mass) ** 0.5