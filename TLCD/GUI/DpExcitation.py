from numpy import sqrt


class Excitation(object):
    def __init__(self, exctType='Seno', amplitude=5., frequency=20.,
                 relativeFrequency=True, exctDuration=3., anlyDuration=5.,
                 structure=None, tlcd=None, **kwargs):
        """
        :param exctType: str - Type of excitation to be used by DynaSolver.assemble_force_matrix()
        :param amplitude: float - Amplitude of the the wave, mesured by the acceleration (m/s**2)
        :param frequency: float - Frequency of the wave (rad/s)
        :param relativeFrequency: bool - True if relative frequency was passed and False if abs. frequency was passed
        :param exctDuration: float - Duration of the excitation (s)
        :param anlyDuration: float - Duration of analysis (s)
        :param structure: dict - Dictionary of objects including all data of each story
        :param tlcd: object - Data of the building tlcd including every paramater
        :param kwargs: any type - Used for future implementation of new parameters
        :return: None
        """
        self.type = exctType
        self.amplitude = amplitude
        self.frequency = frequency
        self.frequencyInput = frequency
        self.exctDuration = exctDuration
        self.anlyDuration = anlyDuration
        self.relativeFrequency = relativeFrequency

        self.structure = structure
        self.tlcd = tlcd

        for (i, j) in kwargs.items():
            exec('self.{} = {}'.format(i, j))

        self.calc_frequency()

    def calc_frequency(self):
        if self.relativeFrequency:
            if self.tlcd is None:
                mass = self.structure[len(self.structure)].mass
            else:
                mass = self.structure[len(self.structure)].mass + self.tlcd.mass

            stiffness = self.structure[len(self.structure)].stiffness
            self.frequency = self.frequencyInput * sqrt(stiffness / mass)
