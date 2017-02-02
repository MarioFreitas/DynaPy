from DynaPy.DynaSolver import ODESolver


class OutputData(object):
    def __init__(self, massMatrix, dampingMatrix, stiffnessMatrix, forceMatrix, configurations):
        self.massMatrix = massMatrix
        self.dampingMatrix = dampingMatrix
        self.stiffnessMatrix = stiffnessMatrix
        self.forceMatrix = forceMatrix

        self.dynamicResponse = ODESolver(self.massMatrix, self.dampingMatrix, self.stiffnessMatrix, self.forceMatrix,
                                         configurations)
