# --------------------------------------------------------------------------------
# File: moves.py
# Developers: Uriel Iram Lezama Lope
# Purpose: Various movements to define neighbourhoods in UC
# --------------------------------------------------------------------------------
import routines 
import copy
import random

# Selector de vecindarios "k" para SHAKING
def neighborhood_k(k, Up, account, TU, TD):
    if k==1:
        Up=totalLS1(Up, account, TU, TD, 10)
    elif k==2:
        Up=totalLS2(Up, account, TU, TD, 10)
    elif k==3:
        Up=totalLS3(Up, account, TU, TD, 20)
    else:
        print ("vecindario k=",k," aún no implementado")
    return Up

# Selector de vecindarios "l" de busquedas locales
def neighborhood_l(l, Up, account, TU, TD, renglon):
    if l==1:
        Up=totalLS4(Up, account, TU, TD)
    elif l==2:
        Up=partialLS5(Up, account, TU, TD)
    elif l==3:
        Up=partialLS6(Up, account, TU, TD, renglon)
    else:
        print ("vecindario l=",l," aún no implementado")
    return Up


# This routine generates the total neighborhood of LS3 moving for LOCAL SEARCH
# Desconecta aleatoriamente por un periodo un generador 
def partialLS6(U, account, TU, TD, g):
    N = len(U)
    Uc = copy.deepcopy(U)    
    g = random.randint(0, N-1) # si se desea hacer aleatorio

    #Genera una versión codificada de un renglón de la solución
    Tio = routines.code(U[g], account[g])   #Codifica un renglón de 1/0
    # print("Tio",Tio)
    t = random.randint(0, len(Tio)-1)
    i = 0
    while i < 5:
        i=i+1
        if Tio[t] > TU[g] and U[g][t]==1 and len(Tio)!=1 and len(Tio)-1!=t:
            print("Tio++",Tio)
            Tio[t] = Tio[t] + 1
            Tio[t+1] = Tio[t+1] - 1
            print("Tio+",Tio)
            if Tio[t+1] != 0 and Tio[t+1] >= TU[g]:
                break

    Tio = routines.decode(Tio, account[g],U[g][0]) #Decodifica un renglón de 1/0
    Uc[g] = Tio
    return Uc

# This routine generates the total neighborhood of LS4 moving for LOCAL SEARCH
# Conecta aleatoriamente por un periodo un generador
def partialLS5(U, account, TU, TD):
    N = len(U)
    Uc = copy.deepcopy(U)    
    g = random.randint(0, N-1)
    #Genera una versión codificada de un renglón de la solución
    Tio = routines.code(U[g], account[g])   #Codifica un renglón de 1/0
    # print("Tio",Tio)
    t = random.randint(0, len(Tio)-1)
    i = 0
    while i < 3:
        i=i+1
        if Tio[t] > TD[g] and U[g][t]==0 and len(Tio)!=1 and len(Tio)-1!=t:
            print("Tio--",Tio)
            Tio[t] = Tio[t] - 1
            Tio[t+1] = Tio[t+1] + 1
            print("Tio-",Tio)
            if Tio[t+1] != 0 and Tio[t+1] >= TD[g]:
                break
    Tio = routines.decode(Tio, account[g],U[g][0]) #Decodifica un renglón de 1/0
    Uc[g] = Tio
    return Uc

# This routine generates a neighborhood of LS5 moving for SHAKING    ranking [] 
# agrega aleatoriamente un porcentaje de generadores una asignación consecutiva de TU
def totalLS3(U, account, TU, TD, percent):
    N = len(U)
    T = len(U[0])
    Uc = copy.deepcopy(U)

    for i in range(int(N*(percent/100))):
        y = random.randint(0, N-1)
        x = random.randint(0, T-1)#-max(TU[y],TD[y])
        for i in range(0,min(len(TU)-1,T-x)):
            Uc[y][x+i] = 1
    return Uc

# This routine generates a neighborhood of LS6 moving for SHAKING    ranking [] 
# agrega un porcentaje aleatorio de una asignación completa de generación de todos los periodos 
def totalLS2(U, account, TU, TD, percent):
    N = len(U)
    T = len(U[0])
    Uc = copy.deepcopy(U)

    for i in range(int(N*(percent/100))):
        y = random.randint(0, N-1)
        for i in range(T):
            Uc[y][i] = 1        
    return Uc

# This routine generates a neighborhood of LS7 moving for SHAKING   ranking [] 
# Repite el status del generador por TU,TD periodos hacia adelante en un porcentaje de unidades
def totalLS1(U, account, TU, TD, percent):
    N = len(U)
    T = len(U[0])
    Uc = copy.deepcopy(U)

    y = random.randint(0, N-1)
    x = random.randint(0, T-1)#-max(TU[y],TD[y])
    # print("random",y,x)

    for i in range(int(N*(percent/100))):

        if( U[y][x] == 1):
            for i in range(0,min(len(TU)-1,T-x)):
                Uc[y][x+i] = 1
        else:
            for i in range(0,min(len(TD)-1,T-x)):
                Uc[y][x+i] = 0
    return Uc

# This routine generates a neighborhood of LS8 moving    ranking [****] 
def totalLS4(U, account, TU, TD):
    N = len(U)
    T = len(U[0])
    Uc = copy.deepcopy(U)

    y = random.randint(0, N-1)
    x = random.randint(0, T-1)#-max(TU[y],TD[y])
    # print("random",y,x)

    if( U[y][x] == 0):
        for i in range(0,min(len(TU)-1,T-x)):
            Uc[y][x+i] = 1
    else:
        for i in range(0,min(len(TD)-1,T-x)):
            Uc[y][x+i] = 0
    return Uc

# This routine generates a neighborhood of LS9 moving       ranking [] 
# Repite el status del generador por TU,TD periodos hacia adelante
def totalLS9(U, account, TU, TD):
    N = len(U)
    T = len(U[0])
    Uc = copy.deepcopy(U)

    y = random.randint(0, N-1)
    x = random.randint(0, T-1)#-max(TU[y],TD[y])
    # print("random",y,x)

    if( U[y][x] == 1):
        for i in range(0,min(len(TU)-1,T-x)):
            Uc[y][x+i] = 1
    else:
        for i in range(0,min(len(TD)-1,T-x)):
            Uc[y][x+i] = 0
    return Uc
