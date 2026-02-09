import math
import numpy as np

def simulate_motor(
    R_out,
    R_core,
    L_core,
    Density,
    P_target,
    P_exit,
    n,
    a,
    fins,
    W_fins,
    L_fins,
    D_fins,
    Cd_nozzle,
    gamma,
    T,
    R,
    Cf
):
    burn_rate = a * (P_target / 1e6)**n

    def Cf_calc(eps):
        term1 = (2 * gamma**2 / (gamma - 1))
        term2 = (2 / (gamma + 1))**((gamma + 1) / (gamma - 1))
        term3 = 1 - (P_exit / P_target)**((gamma - 1) / gamma)
        Cf_ideal = math.sqrt(term1 * term2 * term3)
        return Cf_ideal

    def burn_time():
        Delta_w = R_out - R_core
        return Delta_w / burn_rate

    def mass_flow(T_burn):
        V_cylinder = (R_out**2 - R_core**2) * math.pi * L_core
        V_fins = fins * (W_fins * L_fins * (D_fins - R_core))
        V = V_cylinder - V_fins
        Mass = V * Density
        M_dot_avg = Mass / T_burn
        return Mass, M_dot_avg

    def exit_velocity():
        term = 1.0 - (P_exit / P_target)**((gamma - 1.0) / gamma)
        return math.sqrt((2.0 * gamma / (gamma - 1.0)) * R * T * term)

    def expansion_ratio():
        P_ratio = P_exit / P_target
        Me = math.sqrt(P_ratio**(-(gamma - 1) / gamma) - 1) * math.sqrt(2 / (gamma - 1))
        term = (2 / (gamma + 1)) * (1 + (gamma - 1) / 2 * Me**2)
        return (1 / Me) * term**((gamma + 1) / (2 * (gamma - 1)))

    def nozzle_geometry(M_dot, exp):
        A_throat = (M_dot * math.sqrt(T)) / P_target * math.sqrt(R / gamma) * ((gamma + 1) / 2)**((gamma + 1) / (2 * (gamma - 1)))
        R_throat = math.sqrt(A_throat / math.pi)
        A_exit = A_throat * exp
        R_exit = math.sqrt(A_exit / math.pi)
        L_exp = np.tan(15 * math.pi / 180)
        return R_throat, R_exit, L_exp, A_throat

    # Run simulation
    T_burn = burn_time()
    Mass, M_dot = mass_flow(T_burn)
    exp = expansion_ratio()
    Ve = exit_velocity()
    R_throat, R_exit, L_exp, A_throat = nozzle_geometry(M_dot, exp)
    Cf_val = Cf_calc(exp)

    F_avg = M_dot * Ve
    F_max = F_avg * Cf_val
    I_total = F_avg * T_burn

    return {
        "burn_time": T_burn,
        "mass": Mass,
        "mass_flow": M_dot,
        "expansion_ratio": exp,
        "exit_velocity": Ve,
        "throat_diameter": R_throat * 2,
        "exit_diameter": R_exit * 2,
        "expansion_length": L_exp,
        "total_impulse": I_total,
        "peak_thrust": F_max,
        "average_thrust": F_avg
    }
