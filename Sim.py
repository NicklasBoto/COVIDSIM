import matplotlib.pyplot as plt
import tkinter as tk
import numpy as np

from random import random, randint, seed, randrange
from enum import Enum
from PIL import ImageTk, Image
from matplotlib.animation import FuncAnimation
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#from matplotlib.figure import Figure

T_RATE = 90.0 # percent risk of disease being spread on contact
R_RATE = 2000 # time in ms after contracting the disease until you are removed
R_ZERO = R_RATE / T_RATE

SIZE = 30
WINDOW_SIZE = 800
POPULATION_SIZE = 6

ISOLATION_PERCENT = 0
INFECTED_PERCENT = 0.5

IMAGE_PATH = "Faces/"

class Status(Enum):
    SUSCEPTIBLE = 1
    INFECTED = 2
    RECOVERED = 3
    DEAD = 4

class Person:
    infection_clock = 0

    def __init__(self, window, risk, image, vx_0, vy_0, movable, status=Status.SUSCEPTIBLE):
        self.x = randint(SIZE, WINDOW_SIZE - SIZE)
        self.y = randint(SIZE, WINDOW_SIZE - SIZE)

        self.risk = risk / 1000 # Risk in per mille of dying, having contracted the disease
        self.window = window
        self.file = image
        self.velX = vx_0
        self.velY = vy_0
        self.status = status
        self.movable = movable

        self.image_sized = Image.open(IMAGE_PATH + self.file + status_image[self.status]).resize((SIZE, SIZE), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.image_sized)
        self.face = self.window.create_image(self.x, self.y, image=self.img)
        self.pos = self.window.create_oval(self.x-SIZE, self.y-SIZE, self.x+SIZE, self.y+SIZE)   

    def distance(self, other):
        return np.sqrt(abs(self.x-other.x)**2 + abs(self.y-other.y)**2)

    def expose(self, infect):
        if infect == Status.INFECTED :
            self.status = Status.INFECTED if random() < T_RATE / 100 else self.status

    def move(self, *direction):
        if len(direction) > 0 :
            self.x += direction[0]
            self.y += direction[0]
        else :
            if self.x > WINDOW_SIZE - SIZE or self.x < SIZE:
                self.velX = -self.velX

            if self.y > WINDOW_SIZE - SIZE or self.y < SIZE:
                self.velY = -self.velY

            self.x += self.velX
            self.y += self.velY

            window.move(self.pos, self.velX, self.velY)
            window.move(self.face, self.velX, self.velY)

    def update(self):
        plotPopulation()
        self.image_sized = Image.open(IMAGE_PATH + self.file + status_image[self.status]).resize((SIZE, SIZE), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.image_sized)
        self.window.itemconfig(self.face, image=self.img)

        if self.status != Status.DEAD :
            checkCollision(self)

            self.move()

            if self.status == Status.INFECTED :
                self.infection_clock += 1

                if self.infection_clock > R_RATE * self.risk :
                    self.status = Status.RECOVERED if random() > self.risk else Status.DEAD

            self.window.after(20, self.update)

seed()
np.random.seed(444)

root = tk.Tk()
root.title("COVID-19 spread simulator")
root.resizable(False, False)

window = tk.Canvas(root, height=WINDOW_SIZE, width=WINDOW_SIZE+200)
window.pack()

# These arrays represent the risk in per mille of dying after having contracted the disease.
# The risk data is changed somewhat to fit the age groups.
# Please note that this is not meant to be realistic, or used for anything more than simple simulations.

# Data:
# https://www.statnews.com/2020/03/03/who-is-getting-sick-and-how-sick-a-breakdown-of-coronavirus-risk-by-demographic-factors/
# https://www.indexmundi.com/sweden/age_structure.html

#            0-24   25-54   55-64   65+
age_model = [0.284, 0.3933, 0.1167, 0.206]
#age_risks = [2    , 4     , 13    , 150  ] # actual values
age_risks = [30, 40, 50, 900] # "simulation friendly" values

status_image = {Status.SUSCEPTIBLE : 's.png', Status.INFECTED : 'i.png', Status.RECOVERED : 'r.png', Status.DEAD : 'd.png'}
age_image = {age_risks[0] : "baby_", age_risks[1] : "adult_", age_risks[2] : "boomer_", age_risks[3] : "old_"}

population = []

time = 0
time_steps = []
i_data = []
s_data = []
r_data = []
d_data = []

i_text = window.create_text(WINDOW_SIZE + 100, 100, text="Infected = ")
s_text = window.create_text(WINDOW_SIZE + 100, 200, text="Susceptible = ")
r_text = window.create_text(WINDOW_SIZE + 100, 300, text="Recovered = ")
d_text = window.create_text(WINDOW_SIZE + 100, 400, text="Dead = ")
time_text = window.create_text(WINDOW_SIZE + 100, 500, text="Time = ")

called = 0
def noOverlap(func):
    def wrapper():
        global called
        if called < POPULATION_SIZE :
            called += 1
        if called == POPULATION_SIZE :
            # print ("{} called".format(func.__name__))
            called = 0
            return func()
    return wrapper

@noOverlap
def plotPopulation():
    global time

    # haskell?
    infected    = len(list(filter(lambda x : x.status == Status.INFECTED   , population))) / POPULATION_SIZE
    susceptible = len(list(filter(lambda x : x.status == Status.SUSCEPTIBLE, population))) / POPULATION_SIZE
    recovered   = len(list(filter(lambda x : x.status == Status.RECOVERED  , population))) / POPULATION_SIZE
    dead        = len(list(filter(lambda x : x.status == Status.DEAD       , population))) / POPULATION_SIZE

    window.itemconfig(i_text, text="Infected = {} %".format(infected * 100))
    window.itemconfig(s_text, text="Susceptible = {} %".format(susceptible * 100))
    window.itemconfig(r_text, text="Recovered = {} %".format(recovered * 100))
    window.itemconfig(d_text, text="Dead = {} %".format(dead * 100))
    window.itemconfig(time_text, text="Time {} h".format(time))

    if infected > 0 :
        i_data.append(infected*100)
        s_data.append(susceptible*100)
        r_data.append(recovered*100)
        d_data.append(dead*100)

        time += 1
        time_steps.append(time/24)



def checkCollision(person1):
    for person2 in population :
        if person1 == person2  or person2.status == Status.DEAD : continue

        if person1.distance(person2) < SIZE*2 :
            #overlap = SIZE*2 - person1.distance(person2)
            #person1.move(overlap/np.sqrt(8))
            #person2.move(overlap/np.sqrt(8))

            if not person2.movable :
                person1.velX = -person1.velX
                person1.velY = -person1.velY
            elif person1.movable :
                simpleCollision(person1, person2)

            person1.expose(person2.status)

def simpleCollision(person1, person2):
    # Somehow this looks nicer

    person1.velX, person2.velX = person2.velX, person1.velX
    person1.velY, person2.velY = person2.velY, person1.velY

def graphSim() :
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))

    ax.title.set_text("Disease Spread")

    ax.plot(time_steps, i_data, linestyle=':')
    ax.plot(time_steps, s_data, linestyle='-.')
    ax.plot(time_steps, r_data, linestyle='--')
    ax.plot(time_steps, d_data, linestyle='-')

    ax.legend(labels=['Infected', 'Susceptible', 'Recovered', 'Dead'])
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Population %")

    plt.show()

tk.Button(window, text="Graph", command=graphSim).place(x=WINDOW_SIZE+100, y=600)

def initConditions():
    for i in range(POPULATION_SIZE):
        risk = np.random.choice(age_risks, p=age_model)
        image = age_image[risk]
        vx = randint(-3, 3)
        vy = randint(-3, 3)

        if i < (POPULATION_SIZE * ISOLATION_PERCENT):
            population.append(Person(window, risk, image, 0, 0, False))
        elif i < (POPULATION_SIZE * INFECTED_PERCENT) : 
            population.append(Person(window, risk, image, vx, vy, True, Status.INFECTED))
        else :
            population.append(Person(window, risk, image, vx, vy, True))
    
    for person in population :
        person.update()

@noOverlap
def restartSim():
    for person in population :
        window.delete(person.pos)
        population.remove(person)
        del person

    global time, time_steps, i_data, s_data, r_data, d_data

    time = 0
    time_steps = []
    i_data = []
    s_data = []
    r_data = []
    d_data = []

    initConditions()

tk.Button(window, text="Restart", command=restartSim).place(x=WINDOW_SIZE+100, y=700)

initConditions()
root.mainloop()

#####################################################################################

def longCollision(person1, person2):
    # Using Long Nguyen's collision algorithm
    # https://longbaonguyen.github.io/courses/apcsa/apjava.html

    m1 = randint(50, 150) / 100
    m2 = randint(50, 150) / 100

    angle = np.arctan2(person2.y - person1.y, person2.x - person1.x)

    x1 = 0
    y1 = 0
    x2 = person2.x - person1.x
    y2 = person2.y - person1.y

    vx1 = person1.velX * np.cos(angle) + person1.velY * np.sin(angle)
    vy1 = person1.velY * np.cos(angle) - person1.velX * np.sin(angle)
    vx2 = person2.velX * np.cos(angle) + person2.velY * np.cos(angle)
    vy2 = person2.velY * np.cos(angle) - person2.velX * np.sin(angle)

    fvelX1 = ((m1 - m2)*vx1 + 2 * m2 * vx2) / (m1 + m2)
    fvelX2 = ((m2 - m1)*vx2 + 2 * m2 * vx1) / (m1 + m2)

    vx1 = fvelX1
    vx2 = fvelX2

    overlap = 2*SIZE - abs(x1-x2)
    x1 += vx1 / (abs(vx1) + abs(vx2)) * overlap
    x2 += vx2 / (abs(vx1) + abs(vx2)) * overlap

    fx1 = x1*np.cos(angle) - y1*np.sin(angle)
    fy1 = y1*np.cos(angle) + x1*np.sin(angle)
    fx2 = x2*np.cos(angle) - y2*np.sin(angle)
    fy2 = y2*np.cos(angle) + x2*np.sin(angle)

    person2.x = person1.x + fx2
    person2.y = person1.y + fy2
    person1.x = person2.x + fx1
    person1.y = person2.y + fy1

    person1.velX = vx1*np.cos(angle) - vy1*np.sin(angle)
    person1.velY = vy1*np.cos(angle) + vx1*np.sin(angle)
    person2.velX = vx2*np.cos(angle) - vy2*np.sin(angle)
    person2.velY = vy2*np.cos(angle) + vx2*np.sin(angle)
