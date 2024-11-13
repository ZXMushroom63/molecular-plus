from libc.string cimport strlen
#@cython.cdivision(True)
cdef void apply(Particle *par, ParSys *parSys)noexcept nogil:
    #Variable Defs
    global deltatime
    cdef float delta_temperature = 0
    cdef float real_deltatime = 0
    cdef int length = 0

    #ignore dead particles
    if  par.state < 3:
        return

    #Atmospheric Temperature
    real_deltatime = 1 / deltatime
    delta_temperature = parSys.atmospheric_temperature - par.temperature
    par.temperature += delta_temperature * parSys.atmospheric_conductivity * real_deltatime