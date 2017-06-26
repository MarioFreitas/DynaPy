import sympy
import numpy as np
from matplotlib import pyplot as plt
from DynaPy.TLCD.GUI.DpConfigurations import Configurations
from copy import copy


class ODESolver(object):
    def __init__(self, mass, damping, stiffness, force, configurations=Configurations(), tlcd=None):
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
        self.tlcd = tlcd

        if configurations.method == 'Finite Differences Method':
            if configurations.nonLinearAnalysis and (self.tlcd is not None):
                self.fdm_solver_non_linear()
            else:
                self.fdm_solver()

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

    def fdm_solver(self):
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

    def fdm_solver_non_linear(self):
        self.unpack()

        C_original = copy(self.C)
        correctionStart = self.C.shape[1] - 1
        correctionStop = correctionStart - self.tlcd.amount
        self.dampingVelocityArray = copy(self.v[-1, :])

        velocity = self.dampingVelocityArray[0, 0]

        correctionFactor = self.tlcd.calculate_damping_correction_factor(velocity)
        for i in range(correctionStart, correctionStop, -1):
            self.C[i, i] *= correctionFactor

        self.alpha = (self.M / (self.dt ** 2) - self.C / (2 * self.dt))
        self.beta = (self.K - 2 * self.M / (self.dt ** 2))
        self.gamma = (self.M / (self.dt ** 2) + self.C / (2 * self.dt))

        self.xm1 = self.x[:, 0] - self.v[:, 0] * self.dt + (self.a[:, 0] * self.dt ** 2) / 2
        self.x[:, 1] = self.gamma.I * (self.F[:, 0] - self.beta * self.x[:, 0] - self.alpha * self.xm1)

        for i in list(range(1, len(self.t[1:]))):
            if i >= 2:
                self.C = copy(C_original)
                self.dampingVelocityArray[0, i + 1] = (self.x[-1, i-2] - self.x[-1, i]) / (2 * self.dt)
                velocity = abs(self.dampingVelocityArray[0, i + 1])

                correctionFactor = self.tlcd.calculate_damping_correction_factor(velocity)
                for j in range(correctionStart, correctionStop, -1):
                    self.C[j, j] *= correctionFactor

                self.alpha = (self.M / (self.dt ** 2) - self.C / (2 * self.dt))
                self.beta = (self.K - 2 * self.M / (self.dt ** 2))
                self.gamma = (self.M / (self.dt ** 2) + self.C / (2 * self.dt))

            self.x[:, i + 1] = self.gamma.I * (self.F[:, i] - self.beta * self.x[:, i] - self.alpha * self.x[:, i - 1])

        i = len(self.t[1:])
        self.xM1 = self.gamma.I * (self.F[:, i] - self.beta * self.x[:, i] - self.alpha * self.x[:, i - 1])
        self.xMais1 = np.concatenate((self.x[:, 1:], self.xM1), axis=1)
        self.xMenos1 = np.concatenate((self.xm1, self.x[:, 0:-1]), axis=1)

        self.v = (self.xMais1 - self.xMenos1) / (2 * self.dt)
        self.a = (self.xMais1 - 2 * self.x + self.xMenos1) / (self.dt ** 2)

    def modal_superposition_solver(self):
        pass

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
    :return: np.matrix - Mass matrix of the building equipped with tlcd.
    """
    if tlcd is None:
        n = len(stories)

        M = np.mat(np.zeros((n, n)))

        for i in range(n):
            M[i, i] = stories[i + 1].mass
    else:
        lastStory = len(stories) - 1
        n = len(stories) + tlcd.amount

        M = np.mat(np.zeros((n, n)))

        for i in range(lastStory + 1):
            M[i, i] = stories[i + 1].mass

        M[lastStory, lastStory] += tlcd.mass * tlcd.amount
        for i in range(lastStory + 1, n):
            M[i, i] = tlcd.mass
            M[i, lastStory] = (tlcd.width / tlcd.length) * tlcd.mass
            M[lastStory, i] = (tlcd.width / tlcd.length) * tlcd.mass

        # M[n - 1, n - 1] += tlcd.mass
        # M[n, n] = tlcd.mass
        # M[n, n - 1] = (tlcd.width / tlcd.length) * tlcd.mass
        # M[n - 1, n] = (tlcd.width / tlcd.length) * tlcd.mass

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
            C[i, i] = stories[i + 1].dampingCoefficient
    else:
        lastStory = len(stories) - 1
        n = len(stories) + tlcd.amount

        C = np.mat(np.zeros((n, n)))

        for i in range(lastStory + 1):
            C[i, i] = stories[i + 1].dampingCoefficient

        for i in range(lastStory + 1, n):
            C[i, i] = tlcd.dampingCoefficient

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
        lastStory = len(stories) - 1
        n = len(stories) + tlcd.amount

        K = np.mat(np.zeros((n, n)))

        for i in range(lastStory + 1):
            K[i, i] = stories[i + 1].stiffness

        for i in range(lastStory + 1, 1, -1):
            K[i - 1, i - 2] = -stories[i].stiffness
            K[i - 2, i - 1] = -stories[i].stiffness
            K[i - 2, i - 2] += stories[i].stiffness

        for i in range(lastStory + 1, n):
            K[i, i] = tlcd.stiffness

    return K


def assemble_force_matrix(excitation, mass, configurations):
    """ Function that takes an excitation object, a mass matrix and configurations object to return force vector
    evaluated over time.

    :param excitation: object - Object containing type of excitation and its parameters (measured by acceleration).
    :param mass: np.matrix - Mass matrix of any system.
    :param configurations: object - Object containing time step of iterations.
    :return: np.matrix - Force vector evaluated over time.
    """
    tlcd = excitation.tlcd
    step = configurations.timeStep
    totalTimeArray = np.mat(np.arange(0, excitation.anlyDuration + step, step))
    excitationTimeArray = np.mat(np.arange(0, excitation.exctDuration + step, step))
    force = 0. * totalTimeArray
    if tlcd is None:
        numberOfStories = mass.shape[0]
    else:
        numberOfStories = mass.shape[0] - tlcd.amount

    for i in range(numberOfStories - 1):
        force = np.concatenate((force, 0. * totalTimeArray), 0)

    if excitation.type == 'Sine Wave':
        for i in range(force.shape[0]):
            storyMass = mass[i, i]
            forceAmplitude = storyMass * excitation.amplitude
            for j in range(excitationTimeArray.shape[1]):
                force[i, j] = forceAmplitude * np.sin(excitation.frequency * totalTimeArray[0, j])

        if tlcd is None:
            return force
        else:
            for i in range(tlcd.amount):
                force = np.concatenate((force, 0. * force[0, :]), 0)
            return force
    elif excitation.type == 'General Excitation':
        a = []
        t0 = 0
        time = [round(t / step, 0) * step for t in list(totalTimeArray.A1)]
        for t in time:
            if t in excitation.t_input:
                t0 = t
                t0_index = excitation.t_input.index(t)
                a.append(excitation.a_input[t0_index])
            else:
                t1 = excitation.t_input[t0_index + 1]
                a0 = excitation.a_input[t0_index]
                a1 = excitation.a_input[t0_index + 1]
                at = ((a1 - a0) / (t1 - t0)) * (t - t0) + a0
                a.append(at)

        # print(list(zip(list(totalTimeArray.A1), a)))
        a = np.array(a)
        for i in range(force.shape[0]):
            storyMass = mass[i, i]
            force[i, :] = storyMass * a

        if tlcd is None:
            return force
        else:
            for i in range(tlcd.amount):
                force = np.concatenate((force, 0. * force[0, :]), 0)
            return force


def get_natural_frequencies_by_modal(mass, stiffness):
    return assemble_modes_matrix(mass, stiffness, only_frequencies=True)


def assemble_modes_matrix(mass, stiffness, return_frequencies=False, only_frequencies=False):
    M = mass
    K = stiffness
    n = len(M[0, :].A1)

    x = sympy.Symbol('x')

    D = []
    for i in range(M.shape[0]):
        linha = []
        for j in range(M.shape[1]):
            linha.append(K[i, j] - M[i, j] * x ** 2)

        D.append(linha)

    D = sympy.Matrix(D)

    Ddet = D.det()
    eq = sympy.Eq(Ddet, 0)
    sol = sympy.solveset(eq, x)
    freqs = [i for i in sol if i > 0]
    freqs.sort()

    if only_frequencies:
        return freqs

    Di = []
    for i in range(len(freqs)):
        Dii = D.subs(x, freqs[i])
        Dij = []
        l = list(Dii)
        for j in range(len(freqs)):
            Dij.append(l[j * n:j * n + n])
        Dii = np.mat(Dij, dtype='float')
        Di.append(Dii)

    phi = []
    for i in range(len(freqs)):
        b = np.zeros(len(freqs) - 1)
        b[0] = -Di[i][1, 0]

        A = Di[i][1:, 1:]
        x = np.linalg.solve(A, b)
        z = np.ones(1)
        z = np.concatenate((z, x))
        phi.append(z)

    phi = np.mat(phi).T

    if return_frequencies:
        return phi, freqs
    else:
        return phi


def assemble_modal_mass_vector(modes, mass):
    phi = modes
    M = mass
    n = len(phi[0, :].A1)

    Mi = []
    for i in range(n):
        Mi.append(phi[:, i].T * M * phi[:, i])

    return Mi


def assemble_modal_stiffness_vector(modes, stiffness):
    phi = modes
    K = stiffness
    n = len(phi[0, :].A1)

    Ki = []
    for i in range(n):
        Ki.append(phi[:, i].T * K * phi[:, i])

    return Ki


def assemble_modal_force_vector(modes, force_amplitude):
    phi = modes
    F = force_amplitude
    n = len(phi[0, :].A1)

    Fi = []
    for i in range(n):
        Fi.append(phi[:, i].T * F)

    return Fi


def solve_sdof_system(m, ksi, k, p0, omega, t_lim, x0=0, v0=0):
    omega_n = np.sqrt(k / m)
    omega_d = omega_n * np.sqrt(1 - ksi ** 2)

    C = (p0 / k) * (
        (1 - (omega / omega_n) ** 2) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))
    D = (p0 / k) * (
        (-2 * ksi * (omega / omega_n)) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))

    A = x0 - D  # x(0) = 0
    B = (v0 + ksi * omega_n * A - omega * C) / omega_d  # x'(0) = 0

    t = np.linspace(0, t_lim, 2000)
    x = np.exp(-ksi * omega_n * t) * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) + C * np.sin(
        omega * t) + D * np.cos(omega * t)

    return x


if __name__ == '__main__':
    from DynaPy.TLCD.GUI.DpTLCD import TLCD
    from DynaPy.TLCD.GUI.DpStory import Story
    from DynaPy.TLCD.GUI.DpConfigurations import Configurations
    from DynaPy.TLCD.GUI.DpExcitation import Excitation
    from matplotlib import pyplot as plt

    np.set_printoptions(linewidth=100, precision=2)

    dt = 0.001
    frequency = 3.8
    tt = 50

    diameter = 0.1
    width = 1
    waterHeight = 0.2
    amount = 3

    height = 10.

    config_linear = Configurations(nonLinearAnalysis=False, timeStep=dt)
    config_nonlinear = Configurations(nonLinearAnalysis=True, timeStep=dt)

    stories = {1: Story(height=height), 2: Story(height=height), 3: Story(height=height)}
    tlcd_linear = TLCD(diameter=diameter, width=width, waterHeight=waterHeight,
                       amount=amount, configurations=config_linear)
    excitation_linear = Excitation(frequency=frequency, structure=stories, tlcd=tlcd_linear,
                                   exctDuration=tt, anlyDuration=tt)

    for i in stories.values():
        i.calc_damping_coefficient(0.02)

    M_linear = assemble_mass_matrix(stories, tlcd_linear)
    C_linear = assemble_damping_matrix(stories, tlcd_linear)
    K_linear = assemble_stiffness_matrix(stories, tlcd_linear)
    F_linear = assemble_force_matrix(excitation_linear, M_linear, config_linear)
    dynamicResponse_linear = ODESolver(M_linear, C_linear, K_linear, F_linear,
                                       configurations=config_linear, tlcd=tlcd_linear)

    tlcd_nonlinear = TLCD(diameter=diameter, width=width, waterHeight=waterHeight,
                          amount=amount, configurations=config_nonlinear)
    excitation_nonlinear = Excitation(frequency=frequency, structure=stories, tlcd=tlcd_nonlinear,
                                      exctDuration=tt, anlyDuration=tt)

    for i in stories.values():
        i.calc_damping_coefficient(0.02)

    M_nonlinear = assemble_mass_matrix(stories, tlcd_nonlinear)
    C_nonlinear = assemble_damping_matrix(stories, tlcd_nonlinear)
    K_nonlinear = assemble_stiffness_matrix(stories, tlcd_nonlinear)
    F_nonlinear = assemble_force_matrix(excitation_nonlinear, M_nonlinear, config_nonlinear)
    dynamicResponse_nonlinear = ODESolver(M_nonlinear, C_nonlinear, K_nonlinear, F_nonlinear,
                                          configurations=config_nonlinear, tlcd=tlcd_nonlinear)

    t = dynamicResponse_nonlinear.t
    vc = -dynamicResponse_nonlinear.dampingVelocityArray[-1, :].A1
    vd = dynamicResponse_nonlinear.v[-1, :].A1
    vl = dynamicResponse_linear.v[-1, :].A1

    plt.plot(t, vl, '--', c='g', label='Velocidade Linear')
    plt.plot(t, vc, '--', c='b', label='Velocidade De Correção')
    plt.plot(t, vd, '.-', c='r', label='Velocidade De Deslocamento')
    plt.grid()
    plt.legend()

    plt.figure()
    xd = dynamicResponse_nonlinear.x[-1, :].A1
    xl = dynamicResponse_linear.x[-1, :].A1
    plt.plot(t, xl, '--', c='g', label='Deslocamento Linear')
    plt.plot(t, xd, '.-', c='r', label='Deslocamento Não Linear')
    plt.grid()
    plt.legend()

    plt.show()
