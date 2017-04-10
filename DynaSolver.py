import numpy as np
from matplotlib import pyplot as plt
from DynaPy.TLCD.GUI.DpConfigurations import Configurations


class ODESolver(object):
    def __init__(self, mass, damping, stiffness, force, configurations=Configurations()):
        """ ODE solver for dynamics problems.

        :param mass: np.matrix - Mass matrix including structure and damper masses.
        :param damping: np.matrix - Damping matrix including structure and damper damping coefficients.
        :param stiffness: np.matrix - Stiffness matrix including structure and damper stiffness coefficients.
        :param force: np.matrix - Force vector representing force over time in each DOF.
        :param configurations: object - Object containing boundary conditions and other configurations.

                configurations.method: str - Name of the method to be used in the solver. Possible names:
                    'Finite Differences', 'Average Acceleration', 'Linear Acceleration', 'RK4'

                configurations.timeStep: float - Time step between iterations.
                configurations.initialDisplacement: float - Initial displacement of the base.
                configurations.initialVelocity: float - Initial velocity of the base

        :return: None
        """
        self.mass = mass
        self.damping = damping
        self.stiffness = stiffness
        self.force = force
        self.configurations = configurations

        if configurations.method == 'Método das Diferenças Finitas':
            self.fem_solver()

    def unpack(self):
        self.M = self.mass
        self.C = self.damping
        self.K = self.stiffness
        self.F = self.force
        self.dt = self.configurations.timeStep
        self.x0 = self.configurations.initialDisplacement
        self.v0 = self.configurations.initialVelocity

        self.x = 0. * self.F
        self.v = 0. * self.F
        self.a = 0. * self.F
        self.t = [i * self.dt for i in range(self.F.shape[1])]

        # TODO make initialDisplacement and initialVelocity vectors that represent both parameters at each DOF
        self.x[:, 0] = self.x0
        self.v[:, 0] = self.v0

        self.a0 = self.M.I * (self.F[:, 0] - self.C * self.v[:, 0] - self.K * self.x[:, 0])
        self.a[:, 0] = self.a0

    def fem_solver(self):
        self.unpack()

        self.alpha = (self.M / (self.dt ** 2) - self.C / (2 * self.dt))
        self.beta = (self.K - 2 * self.M / (self.dt ** 2))
        self.gamma = (self.M / (self.dt ** 2) + self.C / (2 * self.dt))

        self.xm1 = self.x[:, 0] - self.v[:, 0] * self.dt + (self.a[:, 0] * self.dt ** 2) / 2
        self.x[:, 1] = self.gamma.I * (self.F[:, 0] - self.beta * self.x[:, 0] - self.alpha * self.xm1)

        for i in list(range(1, len(self.t[1:]))):
            self.x[:, i + 1] = self.gamma.I * (self.F[:, i] - self.beta * self.x[:, i] - self.alpha * self.x[:, i - 1])

        i = len(self.t[1:])
        self.xM1 = self.gamma.I * (self.F[:, i] - self.beta * self.x[:, i] - self.alpha * self.x[:, i - 1])
        self.xMais1 = np.concatenate((self.x[:, 1:], self.xM1), axis=1)
        self.xMenos1 = np.concatenate((self.xm1, self.x[:, 0:-1]), axis=1)

        self.v = (self.xMais1 - self.xMenos1) / (2 * self.dt)
        self.a = (self.xMais1 - 2 * self.x + self.xMenos1) / (self.dt ** 2)

    def plot_displacement(self):
        plt.plot(self.t, self.x[0].A1, 'r-')
        # plt.plot(self.t, self.x[1].A1, 'b-')
        #
        # plt.title('Structure/TLD Displacements\nh = %.2f m / b =  %.2f m / D = %.2f m' % (h, b, D))
        # plt.legend(['Structure Displacement', 'TLD Displacement'])
        plt.xlabel('t (s)', fontsize=20)
        plt.ylabel('x (m)', fontsize=20)
        plt.grid()
        plt.show()

    def plot_velocity(self):
        plt.plot(self.t, self.v[0].A1, 'r-')
        # plt.plot(self.t, self.v[1].A1, 'b-')
        #
        # plt.title('Structure/TLD Velocities\nh = %.2f m / b =  %.2f m / D = %.2f m' % (h, b, D))
        # plt.legend(['Structure Velocity', 'TLD Velocity'])
        plt.xlabel('t (s)')
        plt.ylabel('v (m/s)')
        plt.grid()
        plt.show()

    def plot_acceleration(self):
        plt.plot(self.t, self.a[0].A1, 'r-')
        # plt.plot(self.t, self.a[1].A1, 'b-')
        #
        # plt.title('Structure/TLD Accelerations\nh = %.2f m / b =  %.2f m / D = %.2f m' % (h, b, D))
        # plt.legend(['Structure Acceleration', 'TLD Acceleration'])
        plt.xlabel('t (s)')
        plt.ylabel('a (m/s2)')
        plt.grid()
        plt.show()


def assemble_mass_matrix(stories, tlcd):
    """ Function that takes a dictionary of building story objects and a tlcd object to return its mass matrix.

    :param stories: dict - Dictionary of objects containing data of each story of the building.
    :param tlcd: object - Data of the building tlcd.
    :return: np.matrix - Mass matrix of the building equiped with tlcd.
    """
    if tlcd is None:
        n = len(stories)

        M = np.mat(np.zeros((n, n)))

        for i in range(n):
            M[i, i] = stories[i + 1].mass
    else:
        n = len(stories)

        M = np.mat(np.zeros((n + 1, n + 1)))

        for i in range(n):
            M[i, i] = stories[i+1].mass

        M[n-1, n-1] += tlcd.mass
        M[n, n] = tlcd.mass
        M[n, n-1] = (tlcd.width/tlcd.length)*tlcd.mass
        M[n-1, n] = (tlcd.width/tlcd.length)*tlcd.mass

    return M


def assemble_damping_matrix(stories, tlcd):
    """ Function that takes a dictionary of building story objects and a tlcd object to return its damping matrix.

    :param stories: dict - Dictionary of objects containing data of each story of the building.
    :param tlcd: object - Data of the building tlcd.
    :return: np.matrix - Damping matrix of the building equiped with tlcd.
    """
    if tlcd is None:
        n = len(stories)

        C = np.mat(np.zeros((n, n)))

        for i in range(n):
            C[i, i] = stories[i + 1].dampingRatio
    else:
        n = len(stories)

        C = np.mat(np.zeros((n + 1, n + 1)))

        for i in range(n):
            C[i, i] = stories[i+1].dampingRatio

        C[n, n] = tlcd.dampingRatio

    return C


def assemble_stiffness_matrix(stories, tlcd):
    """ Function that takes a dictionary of building story objects and a tlcd object to return its stiffness matrix.

    :param stories: dict - Dictionary of objects containing data of each story of the building.
    :param tlcd: object - Data of the building tlcd.
    :return: np.matrix - Stiffness matrix of the building equiped with tlcd.
    """
    if tlcd is None:
        n = len(stories)

        K = np.mat(np.zeros((n, n)))

        for i in range(n):
            K[i, i] = stories[i + 1].stiffness

        for i in range(n, 1, -1):
            K[i - 1, i - 2] = -stories[i].stiffness
            K[i - 2, i - 1] = -stories[i].stiffness
            K[i - 2, i - 2] += stories[i].stiffness
    else:
        n = len(stories)

        K = np.mat(np.zeros((n + 1, n + 1)))

        for i in range(n):
            K[i, i] = stories[i+1].stiffness

        for i in range(n, 1, -1):
            K[i-1, i-2] = -stories[i].stiffness
            K[i-2, i-1] = -stories[i].stiffness
            K[i-2, i-2] += stories[i].stiffness

        K[n, n] = tlcd.stiffness

    return K


def assemble_force_matrix(excitation, mass, configurations):
    """ Function that takes an excitation object, a mass matrix and configurations object to return force vector
    evaluated over time.

    :param excitation: object - Object containing type of excitation and its parameteres (measured by acceleration).
    :param mass: np.matrix - Mass matrix of any system.
    :param configurations: object - Object containing time step of iterations.
    :return: np.matrix - Force vector evaluated over time.
    """
    tlcd = excitation.tlcd
    step = configurations.timeStep
    totalTimeArray = np.mat(np.arange(0, excitation.anlyDuration + step, step))
    excitationTimeArray = np.mat(np.arange(0, excitation.exctDuration + step, step))
    force = 0.*totalTimeArray
    if tlcd is None:
        numberOfStories = mass.shape[0]
    else:
        numberOfStories = mass.shape[0] - 1

    for i in range(numberOfStories-1):
        force = np.concatenate((force, 0.*totalTimeArray), 0)

    if excitation.type == 'Seno':
        # TODO check assumptions for excitation of multiple stories
        for i in range(force.shape[0]):
            storyMass = mass[i, i]
            forceAmplitude = storyMass*excitation.amplitude
            for j in range(excitationTimeArray.shape[1]):
                force[i, j] = forceAmplitude*np.sin(excitation.frequency*totalTimeArray[0, j])

        if tlcd is None:
            return force
        else:
            force = np.concatenate((force, 0.*force[0, :]), 0)
            return force


if __name__ == '__main__':
    from math import pi
    from DynaPy.TLCD.GUI.DpStory import Story
    # TODO test same example with assemble functions
    r = 1

    # TLD Parameters (input parameters) - considering that the tank has appropriate dimensions for sloshing
    h = 1.0  # TLD height (m)
    b = 6.0  # TLD length (m)
    D = 0.9  # TLD diameter (m)

    # Structure Parameters (Square cross-section (0.25x0.25) - Concrete)
    E = 25e9  # Young's Module (Pa)
    I = (0.25 * 0.25 ** 3) / 12  # Moment of Inertia (m^4)
    H = 10  # Structure height (m)
    m_s = 10e3  # Structure Mass (kg)

    # Other Properties
    g = 9.807  # Gravity acceleration (m/s2)
    ro = 998.2071  # Water specific mass (20 °C) (kg/m3)
    nu = 1.003e-6  # Water kinetic viscosity (20 °C) (m2/s)

    # TLD Properties (calculated)
    A = 0.25 * pi * D ** 2
    L = b + 2 * h
    m_f = L * A * ro  # (b + 2*h)*(0.25*pi*D**2)*ro
    c_f = 8 * pi * L * nu * ro
    k_f = pi * (D ** 2) * ro * g / 2
    omega_f = np.sqrt((2 * g) / L)

    # Structure Properties
    k_s = 24 * E * I / (H ** 3)  # Structure Stiffness
    omega_s = np.sqrt(k_s / (m_s + m_f))  # Structure Natural Frequency of Vibration
    Cc_s = 2 * (m_s + m_f) * omega_s  # Structure Critical Damping
    c_s = Cc_s * 0.025  # Structure Damping (2,5% of critical)
    dtc = min(2 / omega_s, np.pi / (5 * omega_s))  # Critical Time Step (s)

    # m_f = 1e-21
    # c_f = 1e-21
    # k_f = 1e-21

    # Mass, Stiffness and Damping matrices (input values for CDM)
    m = np.mat(([m_s + m_f, (b / L) * m_f], [(b / L) * m_f, m_f]))  # (kg)
    c = np.mat(([c_s, 0], [0, c_f]))  # (N.s/m)
    k = np.mat(([k_s, 0], [0, k_f]))  # (N/m)

    # Step size, total time analysed and time vector (plot precision and length configurations)
    dt = 0.01  # Step size (s)
    tt = 40  # Total duration (s)
    t = np.arange(0, tt + dt, dt)  # Time vector used om iterations (s)

    # Quake duration arrays
    zero = [0. for i in t]  # Null vector for use on directions with {F(t)} = 0
    tq = 40  # Duration of the quake
    tq_ar = np.arange(0, tq + dt, dt)  # Quake duration vector
    zeros_q = np.array(([0. for i in list(range(len(t) - len(tq_ar)))]))  # Null vector for use on t higher than tq

    # Assembly of the force matrix (concatenation of multiple {F(t)} for different times)
    OMEGA = omega_s * r  # (rad/s)
    F0 = (m_s + m_f) * (0.10 * g)  # (Acceleration amplitude)/OMEGA**2 (N)
    F = np.array([F0 * np.sin(OMEGA * i) for i in tq_ar])  # First Part of the quake equation [F1(t)]
    F = np.append(F, zeros_q)  # Second part of the quake equation [F1(t)] (zeros)
    F = np.vstack((F, zero))  # Assembly of force vector [[F1(t)],[F2(t)],...,[Fn(t)]]
    F = np.mat(F)

    config = Configurations(timeStep=dt)

    test_case = ODESolver(m, c, k, F, config)
    test_case.plot_displacement()
