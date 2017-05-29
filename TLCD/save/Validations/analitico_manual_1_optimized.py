import numpy as np
from matplotlib import pyplot as plt
from DynaPy.DynaSolver import *

M = np.mat([[10000, 0, 0],
            [0, 10000, 0],
            [0, 0, 10000]])

K = np.mat([[55.6, -27.8, 0],
            [-27.8, 55.6, -27.8],
            [0, -27.8, 27.8]]) * 1e6

F = np.mat([[M[0, 0] * 5],
            [M[0, 0] * 5],
            [M[0, 0] * 5]])

phi = assemble_modes_matrix(M, K)
M_ = assemble_modal_mass_vector(phi, M)
K_ = assemble_modal_stiffness_vector(phi, K)
F_ = assemble_modal_force_vector(phi, F)

x_mod_i = []
for i in range(len(phi[0].A1)):
    x_mod_i.append(solve_sdof_system(M_[i], 0, K_[i], F_[i], 5, 10))

x_pav_i = []
for i in range(len(phi[0].A1)):
    x_pav_i.append(sum([j * k for j, k in zip(x_mod_i, phi[i, :].A1)]))

t = np.linspace(0, 10, 2000)
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