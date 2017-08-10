import sympy
import numpy as np
from matplotlib import pyplot as plt

x = sympy.Symbol('x')

M = np.mat([[10000, 0, 0],
            [0, 10000, 0],
            [0,0, 10000]])

K = np.mat([[55.6, -27.8, 0],
            [-27.8, 55.6, -27.8],
            [0, -27.8, 27.8]])*1e6

# print(M)
# print(K)

D = sympy.Matrix([[55.6e6 - 1e4*x**2, -27.8e6, 0.],
           [-27.8e6, 55.6e6 - 1e4*x**2, -27.8e6],
           [0., -27.8e6, 27.8e6 - 1e4*x**2]])

Ddet = D.det()
# print(Ddet)
eq = sympy.Eq(-1000000000000.0*x**6 + 1.39e+16*x**4 - 4.63704e+19*x**2 + 2.1484952e+22, 0)
sol = sympy.solveset(eq, x)
# print(sol)
freq1 = 95.0084380375478
freq2 = 65.7478791080206
freq3 = 23.4651463763291

D1 = np.mat([[55.6e6 - 1e4*freq1**2, -27.8e6, 0.],
           [-27.8e6, 55.6e6 - 1e4*freq1**2, -27.8e6],
           [0., -27.8e6, 27.8e6 - 1e4*freq1**2]])
D2 = np.mat([[55.6e6 - 1e4*freq2**2, -27.8e6, 0.],
           [-27.8e6, 55.6e6 - 1e4*freq2**2, -27.8e6],
           [0., -27.8e6, 27.8e6 - 1e4*freq2**2]])
D3 = np.mat([[55.6e6 - 1e4*freq3**2, -27.8e6, 0.],
           [-27.8e6, 55.6e6 - 1e4*freq3**2, -27.8e6],
           [0., -27.8e6, 27.8e6 - 1e4*freq3**2]])
D11 = D1[1::, 1::]
D21 = D2[1::, 1::]
D31 = D3[1::, 1::]

# print(D1, D2, D3, sep='\n\n')

phi = np.mat([[1, 1, 1],
              [1.802, 0.445, -1.247],
              [2.247, -0.802, 0.555]])

M1 = phi[:, 0].T * M * phi[:, 0]
M2 = phi[:, 1].T * M * phi[:, 1]
M3 = phi[:, 2].T * M * phi[:, 2]

K1 = phi[:, 0].T * K * phi[:, 0]
K2 = phi[:, 1].T * K * phi[:, 1]
K3 = phi[:, 2].T * K * phi[:, 2]

# print(M1, M2, M3)
# print(K1, K2, K3)

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

    t = np.linspace(0, 5, 2000)
    x = (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) + C * np.sin(omega * t) + D * np.cos(omega * t)
    # print(f'M = {m}\nK = {k}\nP0 = {p0}\nomega = {omega}')
    # print(A, B, C, D, sep='\n')
    return x

x1 = calc_x(M1, K1, 2.52e5)
x2 = calc_x(M2, K2, -1.235e4)
x3 = calc_x(M3, K3, 1.54e4)

xpav1 = x1 + x2 + x3
xpav2 = x1*1.802 + x2*(-0.445) + x3*(-1.247)
xpav3 = x1*2.247 + x2*(-0.802) + x3*0.555

t = np.linspace(0, 5, 2000)

plt.plot(t, xpav3.A1, label='Analitico')

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
# plt.show()
print(K2)