from math import pi

import numpy as np
from .DpConfigurations import Configurations


class TLCD(object):
    def __init__(self, tlcdType='Basic TLCD', diameter=0.6, width=20., waterHeight=1.,
                 gasHeight=0.1, gasPressure=202650,
                 amount=1, contraction=1,
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
        self.pipeRoughness = configurations.pipeRoughness
        self.nonLinearAnalysis = configurations.nonLinearAnalysis
        self.gravity = configurations.gravity
        self.amount = amount
        self.contraction = contraction

        for (i, j) in kwargs.items():
            exec('self.{} = {}'.format(i, j))

        self.area = 0.25 * pi * self.diameter ** 2

        if self.type == 'Basic TLCD':
            self.length = self.width + 2 * self.waterHeight
            self.mass = pi * ((self.diameter / 2) ** 2) * self.length * self.liquidSpecificMass
            self.stiffness = pi * (self.diameter ** 2) * self.liquidSpecificMass * self.gravity / 2
            self.naturalFrequency = (self.stiffness / self.mass) ** 0.5

        if self.type == 'Pressurized TLCD':
            self.gasHeight = gasHeight
            self.gasPressure = gasPressure

            self.length = self.width + 2 * self.waterHeight
            self.liquidMass = pi * ((self.diameter / 2) ** 2) * self.length * self.liquidSpecificMass
            self.gasMass = 0
            self.mass = self.liquidMass + self.gasMass
            self.liquidStiffness = pi * (self.diameter ** 2) * self.liquidSpecificMass * self.gravity / 2
            self.gasStiffness = 1.4 * self.gasPressure / self.gasHeight * pi * (self.diameter ** 2) / 2
            self.stiffness = self.liquidStiffness + self.gasStiffness
            self.naturalFrequency = (self.stiffness / self.mass) ** 0.5
        
        if self.nonLinearAnalysis:
            self.dampingCoefficientConstant = pi * self.length * self.diameter * self.liquidSpecificMass / 8
            self.dampingCoefficient = 0
        else:
            self.dampingCoefficient = 8 * pi * self.length * self.kineticViscosity * self.liquidSpecificMass

        self.contracionDampingConstant = self.calculate_contraction_damping_constant()

    def calculate_reynolds(self, velocity):
        return velocity * self.diameter / self.kineticViscosity

    def calculate_friction_factor(self, velocity):
        if velocity == 0.:
            return 0

        Re = self.calculate_reynolds(velocity)
        k = self.pipeRoughness
        D = self.diameter

        b = (k / (3.7 * D) - (5.16 / Re) * np.log10((k / 3.7 * D) + (5.09 / (Re ** 0.87))))

        if b < 0:
            return 0

        a = -2 * np.log10(b)
        f = (1 / a) ** 2
        return f

    def calculate_damping_correction_factor(self, velocity):
        f = self.calculate_friction_factor(velocity)
        return f * velocity

    def calculate_contraction_damping_constant(self):
        return 0.5 * self.liquidSpecificMass * self.area * (1 / self.contraction - 1) ** 2

    def calculate_contraction_damping(self, velocity):
        return self.contracionDampingConstant * velocity
