#@cython.cdivision(True)
cdef void collide(Particle *par)noexcept nogil:
    global kdtree
    global deltatime
    global deadlinks
    cdef int *neighbours = NULL
    cdef Particle *par2 = NULL
    cdef float stiff = 0
    cdef float target = 0
    cdef float sqtarget = 0
    cdef float lengthx = 0
    cdef float lengthy = 0
    cdef float lengthz = 0
    cdef float sqlength = 0
    cdef float length = 0
    cdef float invlength = 0
    cdef float factor = 0
    cdef float ratio1 = 0
    cdef float ratio2 = 0
    cdef float factor1 = 0
    cdef float factor2 = 0
    cdef float *col_normal1 = [0, 0, 0]
    cdef float *col_normal2 = [0, 0, 0]
    cdef float *ypar_vel = [0, 0, 0]
    cdef float *xpar_vel = [0, 0, 0]
    cdef float *yi_vel = [0, 0, 0]
    cdef float *xi_vel = [0, 0, 0]
    cdef float friction1 = 0
    cdef float friction2 = 0
    cdef float damping1 = 0
    cdef float damping2 = 0
    cdef int i = 0
    cdef int check = 0
    cdef float Ua = 0
    cdef float Ub = 0
    cdef float Cr = 0
    cdef float Ma = 0
    cdef float Mb = 0
    cdef float Va = 0
    cdef float Vb = 0
    cdef float force1 = 0
    cdef float force2 = 0
    cdef float mathtmp = 0
    cdef float effective_conductivity = 0
    cdef float delta_energy = 0

    if  par.state < 3:
        return
    if par.sys.selfcollision_active == False and par.sys.othercollision_active == False:
        return

    neighbours = par.neighbours

    # for i in range(kdtree.num_result):
    for i in range(par.neighboursnum):
        check = 0
        if parlist[i].id == -1:
            check += 1
        par2 = &parlist[neighbours[i]]
        if par.id == par2.id:
            check += 10
        if arraysearch(par2.id, par.collided_with, par.collided_num) == -1:
        # if par2 not in par.collided_with:
            if par2.sys.id != par.sys.id :
                if par2.sys.othercollision_active == False or \
                        par.sys.othercollision_active == False:
                    check += 100

            if par2.sys.collision_group != par.sys.collision_group:
                check += 1000

            if par2.sys.id == par.sys.id and \
                    par.sys.selfcollision_active == False:
                check += 10000

            stiff = deltatime
            target = (par.size + par2.size) * 0.999
            sqtarget = target * target

            if check == 0 and par2.state >= 3 and \
                    arraysearch(
                        par2.id, par.link_with, par.link_withnum
                    ) == -1 and \
                    arraysearch(
                        par.id, par2.link_with, par2.link_withnum
                    ) == -1:

            # if par.state <= 1 and par2.state <= 1 and \
            #       par2 not in par.link_with and par not in par2.link_with:
                lengthx = par.loc[0] - par2.loc[0]
                lengthy = par.loc[1] - par2.loc[1]
                lengthz = par.loc[2] - par2.loc[2]
                sqlength  = square_dist(par.loc, par2.loc, 3)
                if sqlength != 0 and sqlength < sqtarget:
                    length = sqrt(sqlength)
                    # length = sqlength ** 0.5
                    invlength = 1 / length
                    factor = (length - target) * invlength
                    ratio1 = (par2.mass / (par.mass + par2.mass))
                    ratio2 = 1 - ratio1

                    mathtmp = factor * stiff
                    force1 = ratio1 * mathtmp
                    force2 = ratio2 * mathtmp
                    par.vel[0] -= lengthx * force1
                    par.vel[1] -= lengthy * force1
                    par.vel[2] -= lengthz * force1
                    par2.vel[0] += lengthx * force2
                    par2.vel[1] += lengthy * force2
                    par2.vel[2] += lengthz * force2

                    col_normal1[0] = (par2.loc[0] - par.loc[0]) * invlength
                    col_normal1[1] = (par2.loc[1] - par.loc[1]) * invlength
                    col_normal1[2] = (par2.loc[2] - par.loc[2]) * invlength
                    col_normal2[0] = col_normal1[0] * -1
                    col_normal2[1] = col_normal1[1] * -1
                    col_normal2[2] = col_normal1[2] * -1

                    factor1 = dot_product(par.vel,col_normal1)

                    ypar_vel[0] = factor1 * col_normal1[0]
                    ypar_vel[1] = factor1 * col_normal1[1]
                    ypar_vel[2] = factor1 * col_normal1[2]
                    xpar_vel[0] = par.vel[0] - ypar_vel[0]
                    xpar_vel[1] = par.vel[1] - ypar_vel[1]
                    xpar_vel[2] = par.vel[2] - ypar_vel[2]

                    factor2 = dot_product(par2.vel, col_normal2)

                    yi_vel[0] = factor2 * col_normal2[0]
                    yi_vel[1] = factor2 * col_normal2[1]
                    yi_vel[2] = factor2 * col_normal2[2]
                    xi_vel[0] = par2.vel[0] - yi_vel[0]
                    xi_vel[1] = par2.vel[1] - yi_vel[1]
                    xi_vel[2] = par2.vel[2] - yi_vel[2]

                    friction1 = 1 - (((par.sys.friction + par2.sys.friction) * 0.5) * ratio1
                    )

                    friction2 = 1 - (((par.sys.friction + par2.sys.friction) * 0.5) * ratio2
                    )

                    damping1 = 1 - (((
                        par.sys.collision_damp + par2.sys.collision_damp
                    ) * 0.5) * ratio1)

                    damping2 = 1 - (((
                        par.sys.collision_damp + par2.sys.collision_damp
                    ) * 0.5) * ratio2)

                    par.vel[0] = ((ypar_vel[0] * damping1) + (yi_vel[0] * \
                        (1 - damping1))) + ((xpar_vel[0] * friction1) + \
                        ( xi_vel[0] * ( 1 - friction1)))

                    par.vel[1] = ((ypar_vel[1] * damping1) + (yi_vel[1] * \
                        (1 - damping1))) + ((xpar_vel[1] * friction1) + \
                        ( xi_vel[1] * ( 1 - friction1)))

                    par.vel[2] = ((ypar_vel[2] * damping1) + (yi_vel[2] * \
                        (1 - damping1))) + ((xpar_vel[2] * friction1) + \
                        ( xi_vel[2] * ( 1 - friction1)))

                    par2.vel[0] = ((yi_vel[0] * damping2) + (ypar_vel[0] * \
                        (1 - damping2))) + ((xi_vel[0] * friction2) + \
                        ( xpar_vel[0] * ( 1 - friction2)))

                    par2.vel[1] = ((yi_vel[1] * damping2) + (ypar_vel[1] * \
                        (1 - damping2))) + ((xi_vel[1] * friction2) + \
                        ( xpar_vel[1] * ( 1 - friction2)))

                    par2.vel[2] = ((yi_vel[2] * damping2) + (ypar_vel[2] * \
                        (1 - damping2))) + ((xi_vel[2] * friction2) + \
                        ( xpar_vel[2] * ( 1 - friction2)))

                    par2.collided_with[par2.collided_num] = par.id
                    par2.collided_num += 1
                    par2.collided_with = <int *>realloc(
                        par2.collided_with,
                        (par2.collided_num + 1) * cython.sizeof(int)
                    )

                    if (((par.sys.relink_chance + par2.sys.relink_chance) / 2) > 0) or (((par.sys.freezing_point - par.temperature) >= 0) and ((par2.sys.freezing_point - par2.temperature) >= 0) and ((par.sys.thermodynamic_linking * par2.sys.thermodynamic_linking) == 1)):
                        create_link(par.id,par.sys.link_max * 2, par2.id)
                    
                    par.vel[0] *= par.sys.motion_multiplier
                    par.vel[1] *= par.sys.motion_multiplier
                    par.vel[2] *= par.sys.motion_multiplier
                    par2.vel[0] *= par2.sys.motion_multiplier
                    par2.vel[1] *= par2.sys.motion_multiplier
                    par2.vel[2] *= par2.sys.motion_multiplier
                    
                    #thermodynamics pain
                    #ignores mass and capacity right now
                    mathtmp = 1 / deltatime
                    effective_conductivity = (par.sys.conductivity + par2.sys.conductivity) / 2
                    delta_energy = effective_conductivity * (par2.temperature - par.temperature) * mathtmp
                    par.temperature += delta_energy
                    par2.temperature -= delta_energy