import numpy as np
from .DynaSolver import ODESolver


class OutputData(object):
    def __init__(self, massMatrix, dampingMatrix, stiffnessMatrix, forceMatrix, configurations, tlcd):
        """
        :param massMatrix: np.matrix - Any n by n sized mass matrix
        :param dampingMatrix: np.matrix - Any n by n sized damping matrix
        :param stiffnessMatrix: np.matrix - Any n by n sized stiffness matrix
        :param forceMatrix: np.matrix - Any n by t sized matrix composed of n by 1 sized force vectors (force over time)
        :param configurations: object - Configurations object containing informations like time step.
        :return: None
        """
        self.massMatrix = massMatrix
        self.dampingMatrix = dampingMatrix
        self.stiffnessMatrix = stiffnessMatrix
        self.forceMatrix = forceMatrix

        self.dynamicResponse = ODESolver(self.massMatrix, self.dampingMatrix, self.stiffnessMatrix, self.forceMatrix,
                                         configurations, tlcd)
        self.calc_dmf()

    def calc_dmf(self):
        self.maxDisplacement = []
        self.DMF = []
        for i in range(self.massMatrix.shape[0]):
            x_dyn = max(np.absolute(self.dynamicResponse.x[i, :].A1))
            F = max(np.absolute(self.forceMatrix[i, :].A1))
            K = self.stiffnessMatrix[i, i]
            x_stat = F/K
            if F != 0:
                self.maxDisplacement.append(x_dyn)
                self.DMF.append(x_dyn/x_stat)
