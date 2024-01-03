from collections import deque
import copy
import csv
from itertools import product
import itertools
from time import sleep

class Solver:

    def __init__(self):

        self.matrix = []
        self.directions = [[0, -1],[0, 1],[1, 0],[-1, 0] ]
        self.pins = {}

        self.drawing_func = None

        self.fields = {}
        self.fields_backup = {}

    def set_hook(self, hook): self.drawing_func = hook
    def set_matrix(self,matrix): self.matrix = self.border_matrix(matrix)
    
    @staticmethod
    def border_matrix(mat):
        new_mat = []
        new_mat.append(["B" for _ in range(len(mat[0])+2)])
        for row in mat: new_mat.append(["B"] + row + ["B"])
        new_mat.append(["B" for _ in range(len(mat[0])+2)])
        return new_mat

    @staticmethod
    def trim_matrix(mat):
        return [row[1:-1] for row in mat[1:-1]]

    def reset_states(self):
        self.matrix = []
        self.pins = {}

    def generate_empty_matrix(self,dim):
        self.reset_states()
        self.matrix = [[0 for _ in range(dim[0])] for _ in range(dim[1])]
        self.matrix = Solver.border_matrix(self.matrix)
        self.drawing_func(matrix = Solver.trim_matrix(self.matrix))

    def read_from_csv(self, path):
        self.reset_states()

        with open(path) as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                self.matrix.append([int(i) if i != "Z" else "Z" for i in row])

        self.matrix = Solver.border_matrix(self.matrix)
        self.drawing_func(matrix = Solver.trim_matrix(self.matrix))
        
    def write_to_csv(self, path):
        with open(path,"w") as file:
            for row in Solver.trim_matrix(self.matrix):
                for el in row[:-1]:
                    file.write(str(el)+",")
                file.write(str(row[-1]) + "\n")

    def get_pins(self):
        for i,row in enumerate(self.matrix):
            for j,el in enumerate(row):
                if not isinstance(el, int) or el == 0: continue
                if not el in self.pins: self.pins[el] = []
                self.pins[el].append([i,j])

    def generate_vector_fields(self):
        for pin in self.pins:
            for pin_poz in self.pins[pin]:
                self.fields[tuple(pin_poz)] = self.generate_one_vector_field(pin_poz,copy.deepcopy(self.matrix))

    def generate_one_vector_field(self,pin_position,field_matrix):
        
        pin_nr = field_matrix[pin_position[0]][pin_position[1]]
        self.prepare_matrix(field_matrix,pin_nr,pin_position[0],pin_position[1])
        field_matrix[pin_position[0]][pin_position[1]] = "F"

        q = deque()
        q.appendleft(pin_position)

        while q:
            next_node = q.pop()
            for dir in self.directions:
                new_node = [n + d for n,d in zip(next_node,dir)]
                if field_matrix[new_node[0]][new_node[1]] in (0,pin_nr):
                    field_matrix[new_node[0]][new_node[1]] = [-i for i in dir]
                    q.appendleft(new_node)

        return field_matrix

    def prepare_matrix(self,mtx,pin_nr,poz_i,poz_j):
        for i, row in enumerate(mtx):
            for j, val in enumerate(row):
                if i == poz_i and j == poz_j: continue
                if val == pin_nr: mtx[i][j] = "B"; continue
                if val not in (0,"B"):
                    for ir,jr in product([-1, 0, 1],[-1, 0, 1]):
                        mtx[i+ir][j+jr] = "B" if mtx[i+ir][j+jr] == 0 else mtx[i+ir][j+jr]

    def check_neighbroing_pins(self,paths,pins):
        neighbor_pins = set()
        for node in paths:
            for ir,jr in product([-2,-1, 0, 1,2],[-2,-1, 0, 1,2]):
                if self.matrix[node[0]+ir][node[1]+jr] in pins:
                    neighbor_pins.add(self.matrix[node[0]+ir][node[1]+jr])

        return neighbor_pins

    def compute_center(self,pin):
        return [int(sum(el[0] for el in self.pins[pin] )/len(self.pins[pin])),int(sum(el[1] for el in self.pins[pin] )/len(self.pins[pin]))]

    def solve(self):

        self.get_pins()
        self.generate_vector_fields()

        unchecked_pins = set(self.pins)
        pending_pins = set()

        while unchecked_pins:
            
            starting_pin,starting_lenght = -1,len(self.matrix)*len(self.matrix[0])
            for pn in unchecked_pins:
                mp = self.compute_center(pn)
                rez = self.generate_elastic_path(pn,*mp)
                if len(rez) < starting_lenght: starting_pin,starting_lenght = pn,len(rez) 

            starting_positions = [[int(i*len(self.matrix)/5),int(j*len(self.matrix[0])/5)] for i,j in product([1,2,3,4],[1,2,3,4])]
            unchecked_pins.remove(starting_pin)
            pending_pins.add(starting_pin)
        
            mp = self.compute_center(starting_pin)
            rez = self.generate_elastic_path(starting_pin,*mp)
            pending_pins.update(self.check_neighbroing_pins(rez,unchecked_pins))
            unchecked_pins.difference_update(pending_pins)

            while(True):
                rez = set()
                for pin in pending_pins: rez.update(self.check_neighbroing_pins(self.pins[pin],unchecked_pins))
                if not rez: break
                pending_pins.update(rez)
                unchecked_pins.difference_update(pending_pins)
            
            self.fields_backup = copy.deepcopy(self.fields)
            for perm in itertools.permutations(pending_pins):
                for sp in starting_positions:
                    deadlock = False
                    all_routs = set()

                    self.fields = copy.deepcopy(self.fields_backup)
                    sol_matrix = copy.deepcopy(self.matrix)
                    new_path = self.generate_elastic_path(perm[0],*sp)
                    all_routs.update(new_path)

                    for poz in new_path:
                        sol_matrix[poz[0]][poz[1]] = perm[0]
                    
                    for pin in pending_pins:
                        for pin_poz in self.pins[pin]:
                            self.fields[tuple(pin_poz)] = self.generate_one_vector_field(pin_poz,copy.deepcopy(sol_matrix))

                    for el in perm[1:]: 
                        rez = self.generate_elastic_path(el,*self.compute_center(el))
                        if rez == -1: deadlock = True; break
                        all_routs.update(rez)

                        for poz in rez:
                            sol_matrix[poz[0]][poz[1]] = el

                        for pin in pending_pins:
                            for pin_poz in self.pins[pin]:
                                self.fields[tuple(pin_poz)] = self.generate_one_vector_field(pin_poz,copy.deepcopy(sol_matrix))

                    if not deadlock and not self.check_neighbroing_pins(all_routs,unchecked_pins):
                        self.matrix = sol_matrix
                        pending_pins = set()
                        break
                
                if not pending_pins:
                    for pin in unchecked_pins:
                        for pin_poz in self.pins[pin]:
                            self.fields[tuple(pin_poz)] = self.generate_one_vector_field(pin_poz,copy.deepcopy(self.matrix))
                    break

        self.drawing_func(matrix = self.trim_matrix(self.matrix))

    def generate_elastic_path(self,pin_nr,i,j):

        paths = set()
        
        start = [i,j]
        while not isinstance(self.fields[tuple(self.pins[pin_nr][0])][start[0]][start[1]],list) :
            if self.fields[tuple(self.pins[pin_nr][0])][start[0]][start[1]] == 0: return -1
            start[0] -= 1
            start[1] -= 1

        prev_poz = []
        corectare = True
        while corectare:

            corectare = False
            dir_set = set()
            for pin_poz in self.pins[pin_nr]:
                if isinstance(self.fields[tuple(pin_poz)][start[0]][start[1]],list):
                    dir_set.add(tuple(self.fields[tuple(pin_poz)][start[0]][start[1]]))
            
            dir_set = list(dir_set)
            
            rez_vec = [sum(x[0] for x in dir_set),sum(x[1] for x in dir_set)]
            if rez_vec != [0,0]:
                nxt = [x+y for x,y in zip(start,rez_vec)]
                if nxt == prev_poz: break
                prev_poz = start
                if isinstance(self.fields[tuple(self.pins[pin_nr][0])][nxt[0]][nxt[1]],list):
                    corectare = True
                    start = nxt

        paths.add(tuple(start))

        for pin_poz in self.pins[pin_nr]:
            pp = self.fields[tuple(pin_poz)]
            nxt = start
            while pp[nxt[0]][nxt[1]] != "F":
                if pp[nxt[0]][nxt[1]] == 0: return -1
                nxt = [x+y for x,y in zip(nxt,pp[nxt[0]][nxt[1]])]
                paths.add(tuple(nxt))

        sol_matrix = copy.deepcopy(self.matrix)
        for node in paths: sol_matrix[node[0]][node[1]] = pin_nr
        
        return paths

    def validate_solution(self):
        
        bad_nodes = set()
        
        for i,row in enumerate(self.matrix):
            for j,el in enumerate(row):
                if isinstance(el, int) and el > 0:
                    for ir,jr in product([-1, 0, 1],[-1, 0, 1]):
                        if self.matrix[i+ir][j+jr] not in (0,"B",el):
                            bad_nodes.add((i,j))

        for node in bad_nodes:
            self.drawing_func("E",node[0],node[1])
    
