def get_hurt_pulse(cur):
    sth = (100, 100, 100, 100)
    # 0->10 1->150
    feq = (int(cur * (70 - 10) + 10) for i in range(4))
    return feq, sth


# def get_death_pulse(cur):
#     sth = (100, 100, 100, 100)
#     feq = (10, 10, 10, 10)
#     return feq, sth
