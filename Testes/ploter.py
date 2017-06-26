from matplotlib import pyplot as plt

plotList = []

def read_csv(filename):
    with open(filename, 'r') as file:
        x = []
        y = []
        for line in file:
            line = line.strip('\n')
            line = line.split(', ')
            x.append(float(line[0]))
            y.append(float(line[1]))

        return (x, y)

data1 = read_csv('C:\Python36\Lib\site-packages\DynaPy\TLCD\save\Resultados/5 story pressure/sem tlcd.csv')
data2 = read_csv('C:\Python36\Lib\site-packages\DynaPy\TLCD\save\Resultados/5 story pressure/com tlcd.csv')

plt.plot(*data1, label='Without TLCD')
plt.plot(*data2, label='With TLCD')
plt.grid()
plt.xlabel('t (s)')
plt.ylabel('x (m)')
plt.title('Displacement Vs. Time')
plt.legend()
plt.show()
