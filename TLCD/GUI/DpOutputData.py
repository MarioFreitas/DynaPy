from DynaPy.DynaSolver import ODESolver


class OutputData(object):
    def __init__(self, massMatrix, dampingMatrix, stiffnessMatrix, forceMatrix, configurations):
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
                                         configurations)
        self.calc_dmf()

    def calc_dmf(self):
        x_dyn = max(self.dynamicResponse.x[-2, :].A1)
        F = abs(max(self.forceMatrix[-2, :].A1))
        K = self.stiffnessMatrix[-2, -2]
        x_stat = F/K
        self.DMF = x_dyn/x_stat
