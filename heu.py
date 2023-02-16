# --------------------------------------------------------------------------------
# File: heu.py
# Adapted from: Adaptive general variable neighborhood search heuristics for solving
# the unit commitment problem R. Todosijević et. al. 2106
# Developers: Uriel Iram Lezama Lope
# Purpose: Various functions that are used in the heu.py program
# --------------------------------------------------------------------------------

import copy
# from typing import AwaitableGenerator
from egret.parsers.pglib_uc_parser import create_ModelData
from egret.models.unit_commitment import solve_unit_commitment
from egret.model_library.unit_commitment.uc_model_generator import UCFormulation, generate_model
from datetime import date
from datetime import datetime
from timeit import timeit
import routines
import repair
import moves
import util
import time
import os
import sys
import time
import unit_commitment
import pyomo.environ as pyo
import random
import outfiles

if len(sys.argv) != 3:
    print("!!! something went wrong, try something like: $python3 heu.py name_instance.json yalma")
    print("!!! or: $python3 heu.py name_instance.json thinkpad")
    print("archivo:  ", sys.argv[1])
    print("ambiente: ", sys.argv[2])
    sys.exit()
ambiente = sys.argv[2]

# fecha y hora
localtime = time.asctime(time.localtime(time.time()))
#ruta = '/home/uriel/GIT/UCVNS/ucvns/'
ruta = ''
#instancia = 'instancia.json'
instancia = sys.argv[1]

md = create_ModelData(ruta+instancia)  # large instance
#md = create_ModelData('/home/uriel/GIT/UCVNS/ucvns/ca/Scenario400_reserves_5.json')
# md = create_ModelData('/home/uriel/GIT/UCVNS/ucvns/anjosmodificado.json')   # small instance

# Append a list as new line to an old csv file
# row_file = [localtime,instancia]
# util.append_list_as_row('solution.csv', row_file)
print(localtime, ' ', 'solving --->', instancia)

# /home/uriel/Egret-main/egret/data/model_data.py
N = 0       # generators number
c = []      # cost
pc = []     # piecewise cost
Piecewise = {}    # piecewise cost
d = []      # load
r = []      # reserve_requirement
p_min = []  # power min
p_max = []  # power max
RU = []     # ramp_up_limit", "ramp_up_60min"
RD = []     # ramp_down_limit", "ramp_down_60min"
SU = []     # ramp_startup_limit", "startup_capacity"
SD = []     # ramp_shutdown_limit", "shutdown_capacity"
TU = []     # time_up_minimum
TD = []     # time_down_minimum
p_0 = []    # power_output_t0
t_0 = []    # unit_on_t0, "initial_status"
M = []      # averange cost

T = len(md.data['system']['time_keys'])  # time periods

# to get the data from the generators
j = 0
for i, gen in md.elements("generator", generator_type="thermal", in_service=True):

    aux = gen["p_cost"]["values"]
    c.append(aux[len(aux)-1][1])
    p_min.append(gen["p_min"])
    p_max.append(gen["p_max"])
    RU.append(gen["ramp_up_60min"])
    RD.append(gen["ramp_down_60min"])
    SU.append(gen["startup_capacity"])
    SD.append(gen["shutdown_capacity"])
    TU.append(gen["min_up_time"])
    TD.append(gen["min_down_time"])
    t_0.append(gen["initial_status"])
    p_0.append(gen["initial_p_output"])
    N = N + 1
    #    Piecewise dictionary
    Piecewise[j] = aux

r = md.data['system']['reserve_requirement']["values"]  # reserve requierement

for obj, dem in md.elements("load"):   # load demand
    d = dem["p_load"]["values"]

t_o = time.time()  # Start of the calculation time count

# todo{almacenar en una clase Solution}
# soluc = Solution()

# Makes a empty-solution with all generators off
U = [[0 for x in range(T)] for y in range(N)]

i = 0
# calculate priority list M
for obj, gen in md.elements("generator", generator_type="thermal", in_service=True):
    aux = gen["p_cost"]["values"]  # to obtain the piecewise cost generators
    # print(aux)
    pc.append(aux)
    f = routines.Fo(aux, (p_min[i]+p_max[i])/2)
    M.append(2 * f / (p_max[i]+p_min[i]))
    i = i + 1

# list of consecutive generators
PL = list(range(len(M)))

# Sort the list 'PL' in ascending order by average cost 'M'
# to get the priority list (PL) with the indices of the generators
M, PL = zip(*sorted(zip(M, PL)))  # ; print("M:", M); print("PL:", PL)

# print("PL:",PL)

# Auxiliary variables to account for the minimum up and down times
# Ton = [[0 for x in range(T)] for y in range(N)]
Toff = [[0 for x in range(T)] for y in range(N)]
must = [[0 for x in range(T)] for y in range(N)]

# print("TU:",TU)
# print("TD:",TD)
#print("t_0:", t_0)

# "lacks" list storage the number of periods must be in the current state.
# "account" list storage the number of periods that have been in current state.
# "status" list stores the state of unit 0/1
lacks = []
status = []
account = []
for i in range(N):
    if p_0[i] > 0:  # TIMES IN ON
        mustON = TU[i] - t_0[i]
        if mustON < 0:
            mustON = 0
        # print("mustON",mustON)
        status.append(1)
        lacks.append(mustON)
        account.append(TU[i]-mustON)
    else:  # TIMES IN OFF
        mustOFF = TD[i] + t_0[i]
        if mustOFF < 0:
            mustOFF = 0
        # print("mustOFF",mustOFF)
        status.append(0)
        lacks.append(mustOFF)
        account.append(TD[i]-mustOFF)
# print("status:",status) # lastly status "on" or "off"
# print("lacks:",lacks) # amount of periods "on" or "off" must be keep
# print("account:",account) # amount of periods "on" or "off" that have been

# amount of periods "on" or "off"

# The must list store the fixed "status" of generators
# Must is the number of perios that the generator is obligate to be ON
for i in range(N):
    for t in range(lacks[i]):
        must[i][t] = 1
# print("must",must)

# Put the must "on" in the solution "U"
for i in range(N):
    for t in range(T):
        if status[i] == 1:
            for j in range(lacks[i]):
                U[i][j] = 1
# print("U+must:",U)
# tpdp{must cuando deba estar apagada}

#  Calculate the initial solution like GREEDY method
#  Primary solution
for t in range(T):
    k = 0
    print("sum:", t, sum)
    sum = 0
    while sum <= d[t] + r[t]:
        if k == N:
            print(">>> not enough generation in the period:", t)
            break
        if must[PL[k]][t] != 1:
            U[PL[k]][t] = 1
            sum = sum + ((p_max[k])/1) * U[k][t]

        k = k + 1

# -test-Unit schedule
# U = [[ 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
#      [ 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
#      [ 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]]
# U=[[ 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
# U=[[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#    [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#    [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
# account = [2,2,2]
# N=3
# T=20

#print("Primary solution")
#print("Uo:", U)

# to check for violations of minimum up and down constraints, the ON and OFF states of units are determined in advance.
# The ON/OFF states at hour t are calculated using the following formulas:
Ton = routines.time_on(T, N, U, account)
Toff = routines.time_off(T, N, U, account)
# print("Ton:",Ton)
# print("Toff:",Toff)
# print('repair')
# Urep = repair.repair2(T, N, U, TU, TD, status, account)
# print('Urep',Urep)

# # Repair todo{pasar la rutina a un archivo separado}
# Repairing minimum up and down time
# The feasibility of this solution can be changed by repairing
# minimum up and down time using the next heuristic procedure
for t in range(T):
    #print("t = ",t)
    for i in range(N):
        #print("i = ",i)
        if t == 0:
            if status[i] == 1 and U[i][t] == 0 and account[i] < TU[i]:
                U[i][t] = 1
                # print("status[",i,"]",status[i])
                # print("U:",U)

            if status[i] == 1 and U[i][t] == 0 and account[i] < TD[i]:
                U[i][t] = 1
                # print("status[",i,"]",status[i])
                # print("U:",U)

            Ton = routines.time_on(T, N, U, account)
            Toff = routines.time_off(T, N, U, account)
        else:
            if U[i][t-1] == 1 and U[i][t] == 0 and Ton[i][t-1] < TU[i]:
                U[i][t] = 1
                # print("Ton[",i,"][",t-1,"]",Ton[i][t-1])
                # print("U:",U)
            if t < (T-TD[i]):  # -1
                if U[i][t-1] == 1 and U[i][t] == 0 and Toff[i][t+TD[i]-1] < TD[i]:
                    U[i][t] = 1
                    # print("Toff[",i,"][",t-1,"]",Toff[i][t-1])
                    # print("U:",U)

            Ton = routines.time_on(T, N, U, account)
            Toff = routines.time_off(T, N, U, account)

    # print("Ton*:",Ton)
    # print("Toff*:",Toff)

t_const = time.time() - t_o
print("t_const", t_const)

# Unit test schedule
#U=[[ 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0]]
#U=[[ 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1]]
# N=1
# # T=20
# U=[[1, 0, 1, 0, 0, 1], [0, 1, 1, 1, 1, 1], [0, 1, 1, 1, 1, 0]]
#print("U_repaired", U)

# Verify feasibility on a row
#routines.feasiblerow(U[i], TU[i], TD[i], account[i])

tim = 1
gen = 0
Nk = []  # arreglo de vecinos del vecindario k

#Nk = moves.totalLS1(U, account)
#Nk = moves.totalLS2(U, account, TU, TD)

# Up = moves.totalLS3(U, account, TU, TD)
# print("|Up|", len(Up))
# print(Up)

# T = [1, 2, 3, 4]
# G = [1, 2]
# c = [10, 5]
# De = [160,160,160,160]
# Re = [10,10,10,10]

# Pmax = [50, 90]
# Pmin = [30, 20]

# x=random.randint(0, len(Nk)-1)
# print("random",x)

# Nd = []
# Nd = moves.decode_solution(Nk[x], account, status)

print('MILP')
z_exact = 0
t_o = time.time()  # Start of the calculation time count
FixShedu = False   # True si se fija la solución entera U, False, si se desea resolver de manera exacta
Relax = False      # True si se relaja la solución entera U, False, si se desea resolver de manera entera
model = unit_commitment.solve(
    N, T, c, Piecewise, p_max, p_min, TU, TD, d, r, FixShedu, Relax, U, ambiente)
z_exact = pyo.value(model.obj)
t_exact = time.time() - t_o
print("z_exact = ", z_exact)
print("t_exact = ", t_exact)

print('RELAXED')
z_relax = 0
t_o = time.time()  # Start of the calculation time count
FixShedu = False   # True si se fija la solución entera U, False, si se desea resolver de manera exacta
Relax = True       # True si se relaja la solución entera U, False, si se desea resolver de manera entera
model = unit_commitment.solve(
    N, T, c, Piecewise, p_max, p_min, TU, TD, d, r, FixShedu, Relax, U, ambiente)
z_relax = pyo.value(model.obj)
t_relax = time.time() - t_o
print("z_relax = ", z_relax)
print("t_relax = ", t_relax)

# IMPRIME SOLUCIÓN RELAJADA
# for t in range(T):
#     for g in range(N):
#         print(g, t, int(model.u[(g, t)].value), model.p[(g, t)].value)


z = float("inf")
print('FIXED SOLUTION')
FixShedu = True  # True si se fija la solución entera U, False, si se desea resolver de manera exacta
Relax = False    # True si se relaja la solución entera U, False, si se desea resolver de manera entera
model = unit_commitment.solve(
    N, T, c, Piecewise, p_max, p_min, TU, TD, d, r, FixShedu, Relax, U, ambiente)
if model != None:
    z = pyo.value(model.obj)
    print("z = ", z)

# Guarda en archivo csv la solución Ugvns
#outfiles.sendtofileU(U,"Uconst_" + instancia + ".csv")
#outfiles.sendtofileTUTD(TU,TD,"timesTUTD_" + instancia + ".csv")

print('GVNS')
# Here a basic general variable neighborhood serch is implemented
#aux=int(N/3)
Ntotal_l = [15,5,5]
exitos_l = [0,0,0] #cuenta el numero de veces que hace una mejora el vecindario l
exitos_k = [0,0,0] #cuenta el numero de veces que hace una mejora el vecindario k
Uo = copy.deepcopy(U)  #se guarda la primera solución U
Up = copy.deepcopy(U)  #variable Uprima
Upp = copy.deepcopy(U) #variable Uprimaprima
Ubest = copy.deepcopy(U) 
nNeighborhood_l = 3    #numero de vecindarios l
nNeighborhood_k = 3    #numero de vecindarios k
tmax = 200  # segundos
itermax = 20
t = 0; k = 1; l = 1; i = 0
z_inc = z; zp = z ; zpp = z; zstat = []; movel = []; movek = []
zstat.append(z); movel.append(-1); movek.append(-1)

to = time.time()  # Start of the calculation time count

while t <= tmax:
    k = 1
    while k <= nNeighborhood_k:
        Up = moves.neighborhood_k(k, U, account, TU, TD)  # shake
        iter = 0
        l = 1
        while l < nNeighborhood_l:
            for i in range(Ntotal_l[l]):
                print("k=", k)
                print("l=", l)
                print("i=", i)
                Upp = moves.neighborhood_l(l, Up, account, TU, TD, PL[i])
                model = unit_commitment.solve(N, T, c, Piecewise, p_max, p_min, TU, TD, d, r, True, False, Upp, ambiente)
                if model != None:
                    zpp = pyo.value(model.obj)
                if (zpp < zp):
                    Up = copy.deepcopy(Upp)
                    zp = zpp
                    zstat.append(zp)
                    movek.append(k)
                    movel.append(l)
                    exitos_l[l-1] = exitos_l[l-1]+1
                    l = 0
                    print("Mejor vecino encontrado ---------------------------------->",zp)
                    break    
            l = l + 1

        if(zp < z_inc):
            U = copy.deepcopy(Up)
            exitos_k[k-1] = exitos_k[k-1]+1
            k = 0
            z_inc = zp
            print("Óptimo local  ---------------------------------->",z_inc)
        k = k + 1
    t = time.time() - to # Start of the calculation time count
print("GVNS terminación por tiempo máximo t_CPU",t )

# Guarda en archivo csv la solución Ugvns
#outfiles.sendtofileU(U,"Ugvns_" + instancia + ".csv")

# Resultados GVNS
print("z_exact = ", z)
print("z_gvns = ", z_inc)
print("zstat = ", zstat)
print("exitos_k = ", exitos_k)
print("exitos_l = ", exitos_l)

# Append a list as new line to an old csv file
gap_gvng = abs(((z_exact - z_inc) / z_exact))
gap_cost = abs(((z_exact - z) / z_exact))
row_file = [localtime, instancia, T, N, 
round(z_exact,1), round(z_relax,1), round(z,1), round(z_inc,1), 
t_exact, t, gap_cost, gap_gvng, 
int(exitos_k[0]), int(exitos_k[1]), int(exitos_k[2]), 
int(exitos_l[0]), int(exitos_l[1]), int(exitos_l[2])]  # data to csv
util.append_list_as_row('stat.csv', row_file)

# row_file1 = [localtime, instancia]
# row_file2 = z_exact

# # Append a new line to an old csv file
# util.append_list_as_row('descenso.csv', row_file1)
# util.append_list_as_row('descenso.csv', row_file2)
# util.append_list_as_row('descenso.csv',movek )
# util.append_list_as_row('descenso.csv',movel )