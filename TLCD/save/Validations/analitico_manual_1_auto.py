import sympy
import numpy as np
from matplotlib import pyplot as plt

x = sympy.Symbol('x')

M = np.mat([[10000, 0, 0],
            [0, 10000, 0],
            [0, 0, 10000]])

K = np.mat([[55.6, -27.8, 0],
            [-27.8, 55.6, -27.8],
            [0, -27.8, 27.8]]) * 1e6

F = np.mat([[M[0, 0] * 5],
            [M[0, 0] * 5],
            [M[0, 0] * 5]])
# print(M)
# print(K)
# print(F)

D = []
for i in range(M.shape[0]):
    linha = []
    for j in range(M.shape[1]):
        linha.append(K[i, j] - M[i, j] * x ** 2)

    D.append(linha)

D = sympy.Matrix(D)

Ddet = D.det()
# print(Ddet)
eq = sympy.Eq(-1000000000000.0 * x ** 6 + 1.39e+16 * x ** 4 - 4.63704e+19 * x ** 2 + 2.1484952e+22, 0)
sol = sympy.solveset(eq, x)
# print(sol)
freqs = [i for i in sol if i > 0]
freqs.sort()

Di = []
for i in range(len(freqs)):
    Dii = D.subs(x, freqs[i])
    Dij = []
    l = list(Dii)
    for j in range(len(freqs)):
        Dij.append(l[j * 3:j * 3 + 3])
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

Mi = []
Ki = []
Fi = []
for i in range(len(freqs)):
    Mi.append(phi[:, i].T * M * phi[:, i])
    Ki.append(phi[:, i].T * K * phi[:, i])
    Fi.append(phi[:, i].T * F)


def calc_x(m, k, p0):
    omega_n = np.sqrt(k / m)
    ksi = 0
    omega_d = omega_n * np.sqrt(1 - ksi ** 2)

    omega = 5

    C = (p0 / k) * (
        (1 - (omega / omega_n) ** 2) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))
    D = (p0 / k) * (
        (-2 * ksi * (omega / omega_n)) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))

    x0 = 0
    x10 = 0
    A = x0 - D  # x(0) = 0
    B = (x10 + ksi * omega_n * A - omega * C) / omega_d  # x'(0) = 0

    t = np.linspace(0, 10, 2000)
    x = (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) + C * np.sin(omega * t) + D * np.cos(omega * t)
    # print(f'M = {m}\nK = {k}\nP0 = {p0}\nomega = {omega}')
    # print(A, B, C, D, sep='\n')
    return x


x_mod_i = []
for i in range(len(freqs)):
    x_mod_i.append(calc_x(Mi[i], Ki[i], Fi[i]))

x_pav_i = []
for i in range(len(freqs)):
    x_pav_i.append(sum([j * k for j, k in zip(x_mod_i, phi[i, :].A1)]))

# x1 = calc_x(M1, K1, 2.52e5)
# x2 = calc_x(M2, K2, -1.235e4)
# x3 = calc_x(M3, K3, 1.54e4)
#
# xpav1 = x1 + x2 + x3
# xpav2 = x1*1.802 + x2*(-0.445) + x3*(-1.247)
# xpav3 = x1*2.247 + x2*(-0.802) + x3*0.555
#
t = np.linspace(0, 10, 2000)
#
plt.plot(t, x_pav_i[2].A1, label='analitico')

with open('./SB/Deslocamentos aceleração na base.txt', 'r') as dados:
    t_sap = []
    xpav1_sap = []
    xpav2_sap = []
    xpav3_sap = []
    for i in range(16):
        dados.readline()
    for line in dados:
        line = line.strip('/n')
        line = line.replace(',', '.')
        dado = line.split()
        t_sap.append(float(dado[0]))
        xpav1_sap.append(float(dado[1]))
        xpav2_sap.append(float(dado[2]))
        xpav3_sap.append(float(dado[3]))

    xpav1_sap = np.array(xpav1_sap)
    xpav2_sap = np.array(xpav2_sap)
    xpav3_sap = np.array(xpav3_sap)

plt.plot(t_sap, -xpav3_sap, label='SAP')
plt.legend()
plt.show()
