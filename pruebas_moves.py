import moves
# Unit test schedule
#U=[[ 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0]]
#U=[[ 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1]]
N=3
T=6
U=[[1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,1,1,1,1,1,1,1,1],
   [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,1,1,1,1,1,1,1],
   [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1],
   [1,0,0,0,0,1,1,1,0,0,0,1,1,0,0,0,0,1,1,1,0,0,0,1],
   [1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,1]]

TU=[3,3,3,3,3]
TD=[2,2,2,2,2]

account =[2,3,4,5,6] #numero de periodos que lleva en 1/O
renglon = 0
Usolucion = moves.partialLS4(U, account, TU,TD)
Usolucion = moves.partialLS3(U, account, TU,TD)


# Verify feasibility on a row
#routines.feasiblerow(U[i], TU[i], TD[i], account[i])
