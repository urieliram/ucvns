from routines import code, decode

# Repairing minimum up and down time
# The feasibility of this solution can be changed by repairing
# minimum up and down time using the next heuristic procedure

def repair2(T, N, U, TU, TD, status, account):

    Urep = []    
    for i in range(N):
        print("i = ", i)
        Tio = []
        Tio = code(U[i], account[i]) #Code the solution in number on, number off, number on,..., and so on.
        print("status = ", status[i],"Tio = ", Tio)


        Tio = decode(Tio, account[i], status[i]) #decode the solution
        Urep.append(Tio)


    return Urep
