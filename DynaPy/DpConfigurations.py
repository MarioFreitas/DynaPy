class Configurations(object):
    def __init__(self, method='Finite Differences Method', timeStep=0.005,
                 initialDisplacement=0., initialVelocity=0.,
                 dampingRatio=0.02,
                 liquidSpecificMass=998.2071, kineticViscosity=1.003e-6, gravity=9.807, pipeRoughness=0.0015e-3,
                 dmfDiscretizationPoints=200, dmfUpperLimitFactor=2,
                 nonLinearAnalysis=True, structureType='Shear Building'):
        """
        :param method: str - ODE solution method to be used by DynaSolver.ODESolver()
        :param timeStep: float - time step between iterations (s)
        :param initialDisplacement: float - initial displacement of all stories
        :param initialVelocity: float - initial velocity of all stories
        :param dampingRatio: float - Relative damping ratio of the building
        :param liquidSpecificMass: float - Tlcd liquid specific mass (kg/m**3)
        :param kineticViscosity: float - Tlcd liquid kinetic viscosity (m**2/s)
        :param gravity: float - Gravity acceleration (m/s**2)
        :return: None
        """
        self.method = method
        self.timeStep = timeStep
        self.initialDisplacement = initialDisplacement
        self.initialVelocity = initialVelocity
        self.dampingRatio = dampingRatio
        self.liquidSpecificMass = liquidSpecificMass  # Water specific mass (20 °C) (kg/m3)
        self.kineticViscosity = kineticViscosity  # Water kinetic viscosity (20 °C) (m2/s)
        self.gravity = gravity       # Gravity acceleration (m/s2)
        self.pipeRoughness = pipeRoughness
        self.dmfDiscretizationPoints = dmfDiscretizationPoints
        self.dmfUpperLimitFactor = dmfUpperLimitFactor
        self.nonLinearAnalysis = nonLinearAnalysis
        self.structureType = structureType
